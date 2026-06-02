// `bashos run <prompt> <file>` — run a prompt from .github/prompts against a
// target file with Claude, using cached instruction context. Writes the result
// (or prints it) and reports the autonomy verdict. Never auto-commits in Phase 0
// — committing is gated behind the policy and added in a later phase.
import { writeFileSync } from "node:fs";
import { relative } from "node:path";
import { findRepoRoot, readFileSafe, changedPaths, addedDiffLines } from "../lib/repo.js";
import { loadPrompt, instructionContextFor } from "../lib/prompts.js";
import { loadPolicy, classifyChangeset } from "../lib/policy.js";
import { run as runClaude, hasApiKey, type Tier } from "../lib/claude.js";
import { summarize } from "../lib/audit.js";

export interface RunOpts {
  tier?: Tier;
  write?: boolean; // write result back to the target file (default: print to stdout)
  maxTokens?: number;
}

export async function runCommand(prompt: string, file: string, opts: RunOpts): Promise<void> {
  const root = findRepoRoot();

  if (!hasApiKey()) {
    console.error(
      "ANTHROPIC_API_KEY is not set.\n" +
        "Set it (e.g. `export ANTHROPIC_API_KEY=sk-...` or a .env entry) and retry.\n" +
        "Tip: `bashos classify` and `bashos prompts` work without a key.",
    );
    process.exitCode = 1;
    return;
  }

  const rel = relative(root, file) || file;
  const loaded = loadPrompt(root, prompt);
  const systemContext = instructionContextFor(root, rel);
  const target = readFileSafe(file);

  const result = await runClaude({
    systemContext,
    promptBody: loaded.body,
    userInput:
      `Target file: ${rel}\n\n` +
      (target ? `Current contents:\n\n\`\`\`\n${target}\n\`\`\`\n` : "(file does not exist yet)\n"),
    tier: opts.tier,
    maxTokens: opts.maxTokens,
  });

  if (opts.write) {
    writeFileSync(file, result.text.endsWith("\n") ? result.text : result.text + "\n");
    const policy = loadPolicy(root);
    const verdict = classifyChangeset(root, policy, changedPaths(root), addedDiffLines(root));
    console.error(summarize({ prompt, target: rel, result, cls: verdict.cls }));
    console.error(
      verdict.autoCommit
        ? "→ Green: eligible for auto-commit."
        : `→ ${verdict.cls}: review required before committing (run \`bashos classify\`).`,
    );
  } else {
    process.stdout.write(result.text + "\n");
    console.error(summarize({ prompt, target: rel, result, cls: "green" }));
  }
}
