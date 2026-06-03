#!/usr/bin/env node
// bashos — the BASH OS AI engine CLI.
// Runs the versioned prompt library against the working tree with Claude,
// gated by the blast-radius autonomy policy. See docs/ai-framework/.
import { Command } from "commander";
import { findRepoRoot } from "./lib/repo.js";
import { listPrompts } from "./lib/prompts.js";
import { runCommand } from "./commands/run.js";
import { classifyCommand } from "./commands/classify.js";
import { boardCommand, stageCommand, contentRun, newCommand } from "./commands/content.js";
import type { Tier } from "./lib/claude.js";

const program = new Command();

program
  .name("bashos")
  .description("BASH OS — AI consulting operating system CLI")
  .version("0.0.1");

program
  .command("prompts")
  .description("List available prompts from .github/prompts")
  .action(() => {
    const names = listPrompts(findRepoRoot());
    if (!names.length) console.log("No prompts found.");
    else console.log(names.map((n) => `  /${n}`).join("\n"));
  });

program
  .command("classify")
  .description("Show the blast-radius autonomy verdict for the current working tree")
  .option("--json", "output machine-readable JSON")
  .action((opts) => classifyCommand(opts));

program
  .command("run")
  .description("Run a prompt against a file with Claude")
  .argument("<prompt>", "prompt slug, e.g. article-review")
  .argument("<file>", "target file path")
  .option("-t, --tier <tier>", "model tier: opus | sonnet | haiku", "opus")
  .option("-w, --write", "write the result back to the file (default: print)")
  .option("--max-tokens <n>", "max output tokens", (v) => parseInt(v, 10))
  .action((prompt: string, file: string, opts: { tier: Tier; write?: boolean; maxTokens?: number }) =>
    runCommand(prompt, file, { tier: opts.tier, write: opts.write, maxTokens: opts.maxTokens }),
  );

// Content Studio (Phase 1): the idea→publish pipeline.
const content = program
  .command("content")
  .description("Content Studio — the idea→draft→review→publish pipeline");

content
  .command("board")
  .description("Show every post by pipeline stage (no API key needed)")
  .action(() => boardCommand());

content
  .command("new")
  .description("Scaffold a new post at stage:idea, published:false (build-safe)")
  .requiredOption("-s, --subfolder <name>", "corp | erp | muses | tech")
  .requiredOption("-T, --title <title>", "post title")
  .option("--slug <slug>", "kebab-case slug (default: derived from title)")
  .action((opts: { subfolder: string; title: string; slug?: string }) => newCommand(opts));

content
  .command("stage")
  .description("Move a post to a pipeline stage (sets the published flag accordingly)")
  .argument("<file>", "post path")
  .argument("<stage>", "stage id: idea|outline|drafting|review|seo|scheduled|published")
  .action((file: string, stage: string) => stageCommand(file, stage));

for (const verb of ["outline", "draft", "review", "seo"] as const) {
  content
    .command(verb)
    .description(`Run the ${verb} prompt against a post with Claude`)
    .argument("<file>", "post path")
    .option("-t, --tier <tier>", "model tier: opus | sonnet | haiku", "opus")
    .option("-w, --write", "write the result back to the file (default: print)")
    .option("--max-tokens <n>", "max output tokens", (v) => parseInt(v, 10))
    .action((file: string, opts: { tier: Tier; write?: boolean; maxTokens?: number }) =>
      contentRun(verb, file, { tier: opts.tier, write: opts.write, maxTokens: opts.maxTokens }),
    );
}

program.parseAsync().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
