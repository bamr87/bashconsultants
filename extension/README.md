# Prompt Orchestrator

A VS Code extension that orchestrates AI agent workflows using structured prompts from `.github/prompts/`.

## Features

- **Discover Prompts**: Automatically loads prompt templates from `.github/prompts/` directory
- **Execute Commands**: Run prompts on files via Command Palette or sidebar
- **Chat Integration**: Send prompts to GitHub Copilot Chat or Language Model API
- **Sidebar View**: Browse and execute available prompts from the Explorer
- **Context-Aware**: Automatically includes file content as context

## Installation & Usage

### Development Setup

1. **Navigate to extension directory:**
   ```bash
   cd extension
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Compile and run:**
   Press `F5` in VS Code to launch Extension Development Host

### Configure Prompts Directory

The extension looks for prompts in `.github/prompts/` by default. You can change this in Settings:
```json
{
  "promptOrchestrator.promptsDirectory": ".github/prompts"
}
```

### Available Commands

Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`):

- **Prompt Orchestrator: Refresh Prompts** - Reload prompt templates
- **Prompt Orchestrator: Execute Prompt on File** - Choose prompt and file
- **Prompt Orchestrator: Review Article** - Run article-review prompt
- **Prompt Orchestrator: Refactor Code** - Run refactoring prompt
- **Prompt Orchestrator: Generate Tests** - Run test-generation prompt
- **Prompt Orchestrator: Generate Documentation** - Run documentation prompt
- **Prompt Orchestrator: Debug Code** - Run debugging prompt
- **Prompt Orchestrator: Set Anthropic API Key** - Store your Claude key in VS Code Secret Storage
- **Prompt Orchestrator: Clear Anthropic API Key** - Remove the stored key

### Execution Methods

When executing a prompt, choose:
1. **Execute with Claude (Anthropic)** - First-class Claude provider (see below)
2. **Send to Chat (Copilot)** - Opens in Chat panel with prompt ready to paste
3. **Execute with Language Model** - Directly calls the VS Code LM API (Copilot)
4. **Copy to Clipboard** - Copies formatted prompt for manual use

### Claude (Anthropic) provider

The first-class provider calls the Anthropic Messages API directly — the same
engine as the [`bashos` CLI](../tools/bashos/) — so it shares the prompt library
**and** the instruction library:

- **House rules, automatically:** before each call it loads the
  `.github/instructions/*.instructions.md` files whose `applyTo` matches the
  active file and sends them as **cached** system context. Editing a post obeys
  `content-style` + `posts` rules without you pasting anything.
- **Prompt caching:** the stable instruction + prompt context is marked
  cacheable, so repeat runs only pay full price for the variable file content.
- **Model tiers:** `promptOrchestrator.claudeModelTier` = `opus` (default) /
  `sonnet` / `haiku`; `promptOrchestrator.claudeMaxTokens` caps output.
- **Key storage:** your `ANTHROPIC_API_KEY` lives in VS Code **Secret Storage**
  (set it via the command above), never in `settings.json`. The env var is used
  as a fallback. Results open in a new editor — the extension never writes files
  silently.

## Prompt Template Format

Create `.prompt.md` files in `.github/prompts/`:

```markdown
---
agent: agent
---
Act as an expert [role].

Your task is to [description].

[Instructions...]
```

## Development

```bash
# Navigate to extension directory
cd extension

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch mode
npm run watch

# Run tests
npm test

# Package extension
npm run package
```

## Project Structure

```
extension/
├── src/
│   ├── extension.ts          # Main extension entry point
│   ├── promptManager.ts      # Prompt discovery and loading
│   ├── promptExplorer.ts     # Sidebar tree view provider
│   ├── chatIntegration.ts    # VS Code Chat API integration
│   └── test/
│       ├── extension.test.ts
│       └── promptManager.test.ts
├── .vscode/
│   ├── launch.json           # Debug configurations
│   ├── tasks.json            # Build tasks
│   └── extensions.json       # Recommended extensions
├── package.json              # Extension manifest
├── tsconfig.json             # TypeScript configuration
├── esbuild.js                # Build configuration
├── eslint.config.mjs         # Linting rules
└── .vscodeignore             # Files to exclude from package
```

## Requirements

- VS Code 1.96.0 or higher
- GitHub Copilot (optional, for chat integration)

## Extension Settings

- `promptOrchestrator.promptsDirectory`: Directory containing prompt files
- `promptOrchestrator.autoRefresh`: Auto-refresh prompts on file changes

---

Built for BASH Consultants
