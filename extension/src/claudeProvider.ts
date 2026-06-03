import * as vscode from 'vscode';
import Anthropic from '@anthropic-ai/sdk';

export type Tier = 'opus' | 'sonnet' | 'haiku';

// Model IDs per the project environment. Opus for hard drafting/reasoning,
// Sonnet/Haiku for bulk and chores (mirrors tools/bashos and PLAN.md §10).
const MODELS: Record<Tier, string> = {
    opus: 'claude-opus-4-8',
    sonnet: 'claude-sonnet-4-6',
    haiku: 'claude-haiku-4-5-20251001',
};

const SECRET_KEY = 'promptOrchestrator.anthropicApiKey';

export interface CompleteArgs {
    /** Stable, cacheable context (matched instruction files + house style). */
    systemContext: string;
    /** The prompt/skill body (also fairly stable). */
    promptBody: string;
    /** The variable input (target file content + the ask). */
    userInput: string;
    tier: Tier;
    maxTokens: number;
}

/**
 * First-class Claude provider for the extension. Uses the Anthropic Messages API
 * directly (not the VS Code LM passthrough), with prompt caching on the large,
 * stable instruction + prompt context — the same engine the bashos CLI uses.
 * The API key is kept in VS Code SecretStorage (never in settings.json).
 */
export class ClaudeProvider {
    constructor(
        private readonly secrets: vscode.SecretStorage,
        private readonly output: vscode.OutputChannel,
    ) {}

    async getApiKey(): Promise<string | undefined> {
        return (await this.secrets.get(SECRET_KEY)) ?? process.env.ANTHROPIC_API_KEY ?? undefined;
    }

    async hasApiKey(): Promise<boolean> {
        return Boolean(await this.getApiKey());
    }

    async setApiKey(): Promise<void> {
        const key = await vscode.window.showInputBox({
            prompt: 'Anthropic API key (stored in VS Code Secret Storage, not settings)',
            password: true,
            ignoreFocusOut: true,
            placeHolder: 'sk-ant-...',
        });
        if (!key) {
            return;
        }
        await this.secrets.store(SECRET_KEY, key.trim());
        vscode.window.showInformationMessage('Anthropic API key saved to Secret Storage.');
    }

    async clearApiKey(): Promise<void> {
        await this.secrets.delete(SECRET_KEY);
        vscode.window.showInformationMessage('Anthropic API key cleared from Secret Storage.');
    }

    async complete(args: CompleteArgs, token: vscode.CancellationToken): Promise<string> {
        const apiKey = await this.getApiKey();
        if (!apiKey) {
            throw new Error(
                'No Anthropic API key. Run "Prompt Orchestrator: Set Anthropic API Key" or set ANTHROPIC_API_KEY.',
            );
        }

        const model = MODELS[args.tier];
        const client = new Anthropic({ apiKey });

        const controller = new AbortController();
        const sub = token.onCancellationRequested(() => controller.abort());

        try {
            const msg = await client.messages.create(
                {
                    model,
                    max_tokens: args.maxTokens,
                    system: [
                        {
                            type: 'text',
                            text: 'You are the BASH OS content/automation agent. Follow the house instructions and the prompt exactly. Produce only the requested artifact.',
                        },
                        { type: 'text', text: args.systemContext },
                        { type: 'text', text: args.promptBody, cache_control: { type: 'ephemeral' } },
                    ],
                    messages: [{ role: 'user', content: args.userInput }],
                },
                { signal: controller.signal },
            );

            const u = msg.usage;
            this.output.appendLine(
                `[claude] ${model}  in=${u.input_tokens} out=${u.output_tokens} ` +
                    `cache_read=${u.cache_read_input_tokens ?? 0} cache_create=${u.cache_creation_input_tokens ?? 0}`,
            );

            return msg.content
                .filter((b): b is Anthropic.TextBlock => b.type === 'text')
                .map((b) => b.text)
                .join('\n');
        } finally {
            sub.dispose();
        }
    }
}
