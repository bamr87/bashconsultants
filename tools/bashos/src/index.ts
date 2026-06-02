#!/usr/bin/env node
// bashos — the BASH OS AI engine CLI.
// Runs the versioned prompt library against the working tree with Claude,
// gated by the blast-radius autonomy policy. See docs/ai-framework/.
import { Command } from "commander";
import { findRepoRoot } from "./lib/repo.js";
import { listPrompts } from "./lib/prompts.js";
import { runCommand } from "./commands/run.js";
import { classifyCommand } from "./commands/classify.js";
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

program.parseAsync().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
