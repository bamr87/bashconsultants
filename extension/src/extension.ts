import * as vscode from 'vscode';
import { PromptManager, PromptTemplate } from './promptManager';
import { PromptExplorerProvider } from './promptExplorer';
import { ChatIntegration } from './chatIntegration';
import { ClaudeProvider, Tier } from './claudeProvider';
import { loadInstructionContext } from './instructionContext';

export function activate(context: vscode.ExtensionContext) {
	console.log('Prompt Orchestrator is now active');

	// Get workspace root
	const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
	if (!workspaceFolder) {
		vscode.window.showWarningMessage('Prompt Orchestrator requires an open workspace');
		return;
	}

	// Get configuration
	const config = vscode.workspace.getConfiguration('promptOrchestrator');
	const promptsDirectory = config.get<string>('promptsDirectory', '.github/prompts');

	// Initialize managers
	const workspaceRoot = workspaceFolder.uri.fsPath;
	const output = vscode.window.createOutputChannel('Prompt Orchestrator');
	context.subscriptions.push(output);
	const promptManager = new PromptManager(workspaceRoot, promptsDirectory);
	const chatIntegration = new ChatIntegration();
	const claude = new ClaudeProvider(context.secrets, output);
	const promptExplorer = new PromptExplorerProvider(promptManager);

	// Anthropic API key management (stored in Secret Storage, never settings.json)
	context.subscriptions.push(
		vscode.commands.registerCommand('prompt-orchestrator.setClaudeApiKey', () => claude.setApiKey()),
		vscode.commands.registerCommand('prompt-orchestrator.clearClaudeApiKey', () => claude.clearApiKey()),
	);

	// Register tree view
	const treeView = vscode.window.createTreeView('promptOrchestratorExplorer', {
		treeDataProvider: promptExplorer
	});

	// Register commands
	context.subscriptions.push(
		vscode.commands.registerCommand('prompt-orchestrator.refreshPrompts', async () => {
			await promptManager.loadPrompts();
			promptExplorer.refresh();
			vscode.window.showInformationMessage('Prompts refreshed');
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('prompt-orchestrator.executePrompt', async (promptName?: string) => {
			// If no prompt name provided, show quick pick
			if (!promptName) {
				const prompts = promptManager.getAllPrompts();
				if (prompts.length === 0) {
					await promptManager.loadPrompts();
				}
				
				const items = promptManager.getAllPrompts().map(p => ({
					label: p.name,
					description: p.frontmatter?.agent || ''
				}));

				const selected = await vscode.window.showQuickPick(items, {
					placeHolder: 'Select a prompt to execute'
				});

				if (!selected) {
					return;
				}
				promptName = selected.label;
			}

			const prompt = promptManager.getPrompt(promptName);
			if (!prompt) {
				vscode.window.showErrorMessage(`Prompt "${promptName}" not found`);
				return;
			}

			// Get active editor or ask user to select file
			const editor = vscode.window.activeTextEditor;
			let fileUri: vscode.Uri | undefined;

			if (editor) {
				fileUri = editor.document.uri;
			} else {
				const files = await vscode.window.showOpenDialog({
					canSelectFiles: true,
					canSelectMany: false,
					openLabel: 'Select file for prompt context'
				});
				fileUri = files?.[0];
			}

			if (!fileUri) {
				vscode.window.showWarningMessage('No file selected');
				return;
			}

			// Format prompt with context
			const formattedPrompt = await promptManager.formatPromptWithContext(prompt, fileUri);

			// Ask user for execution method
			const method = await vscode.window.showQuickPick([
				{ label: 'Execute with Claude (Anthropic)', value: 'claude' },
				{ label: 'Send to Chat (Copilot)', value: 'chat' },
				{ label: 'Execute with Language Model', value: 'model' },
				{ label: 'Copy to Clipboard', value: 'clipboard' }
			], {
				placeHolder: 'How do you want to execute this prompt?'
			});

			if (!method) {
				return;
			}

			switch (method.value) {
				case 'claude':
					await runWithClaude(claude, workspaceRoot, prompt, fileUri, output);
					break;
				case 'chat':
					await chatIntegration.sendToChat(formattedPrompt);
					break;
				case 'model':
					await chatIntegration.executePromptWithModel(formattedPrompt);
					break;
				case 'clipboard':
					await vscode.env.clipboard.writeText(formattedPrompt);
					vscode.window.showInformationMessage('Prompt copied to clipboard');
					break;
			}
		})
	);

	// Register specific prompt commands
	const promptCommands = ['review', 'refactor', 'test', 'docs', 'debug'];
	for (const cmd of promptCommands) {
		context.subscriptions.push(
			vscode.commands.registerCommand(`prompt-orchestrator.${cmd}`, async () => {
				await vscode.commands.executeCommand('prompt-orchestrator.executePrompt', cmd);
			})
		);
	}

	// Auto-load prompts on activation
	promptManager.loadPrompts().then(() => {
		promptExplorer.refresh();
	});

	context.subscriptions.push(treeView);
}

/**
 * Run a prompt against a file with the first-class Claude provider: matched
 * instruction files become the cached system context, the prompt body is the
 * cached instruction, and the file content is the variable input. The result
 * opens in a new editor for review (the extension never writes files silently).
 */
async function runWithClaude(
	claude: ClaudeProvider,
	workspaceRoot: string,
	prompt: PromptTemplate,
	fileUri: vscode.Uri,
	output: vscode.OutputChannel,
): Promise<void> {
	const config = vscode.workspace.getConfiguration('promptOrchestrator');
	const tier = config.get<Tier>('claudeModelTier', 'opus');
	const maxTokens = config.get<number>('claudeMaxTokens', 4096);

	if (!(await claude.hasApiKey())) {
		const pick = await vscode.window.showWarningMessage(
			'No Anthropic API key set for Prompt Orchestrator.',
			'Set API Key',
		);
		if (pick === 'Set API Key') {
			await claude.setApiKey();
		}
		if (!(await claude.hasApiKey())) {
			return;
		}
	}

	const fileBytes = await vscode.workspace.fs.readFile(fileUri);
	const text = Buffer.from(fileBytes).toString('utf-8');
	const rel = vscode.workspace.asRelativePath(fileUri);
	const systemContext = await loadInstructionContext(workspaceRoot, fileUri, output);
	const userInput = `Target file: ${rel}\n\nCurrent contents:\n\n\`\`\`\n${text}\n\`\`\``;

	try {
		const result = await vscode.window.withProgress(
			{
				location: vscode.ProgressLocation.Notification,
				title: `Running /${prompt.name} with Claude (${tier})…`,
				cancellable: true,
			},
			(_progress, token) =>
				claude.complete({ systemContext, promptBody: prompt.content, userInput, tier, maxTokens }, token),
		);

		if (result) {
			const doc = await vscode.workspace.openTextDocument({ content: result, language: 'markdown' });
			await vscode.window.showTextDocument(doc, { preview: false });
		}
	} catch (error) {
		const message = error instanceof Error ? error.message : String(error);
		output.appendLine(`[claude] error: ${message}`);
		vscode.window.showErrorMessage(`Claude request failed: ${message}`);
	}
}

export function deactivate() {}
