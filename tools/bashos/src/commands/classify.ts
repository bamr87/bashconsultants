// `bashos classify` — show the blast-radius verdict for the current working tree.
// No API key needed; pure policy evaluation.
import { findRepoRoot, changedPaths, addedDiffLines } from "../lib/repo.js";
import { loadPolicy, classifyChangeset } from "../lib/policy.js";

const ICON = { green: "🟢", yellow: "🟡", red: "🔴" } as const;

export function classifyCommand(opts: { json?: boolean }): void {
  const root = findRepoRoot();
  const policy = loadPolicy(root);
  const paths = changedPaths(root);

  if (paths.length === 0) {
    console.log("No changes in the working tree.");
    return;
  }

  const verdict = classifyChangeset(root, policy, paths, addedDiffLines(root));

  if (opts.json) {
    console.log(JSON.stringify(verdict, null, 2));
    return;
  }

  console.log(`\nChangeset verdict: ${ICON[verdict.cls]} ${verdict.cls.toUpperCase()}\n`);
  for (const v of verdict.paths) {
    console.log(`  ${ICON[v.cls]} ${v.path}  — ${v.reason}`);
  }
  if (verdict.secretHits.length) {
    console.log(`\n  ⚠ secret-like content in diff: ${verdict.secretHits.join(", ")}`);
  }
  console.log(
    `\n→ ${
      verdict.autoCommit
        ? "Eligible for AI auto-commit (Green)."
        : `NOT auto-committable (${verdict.cls}). ${
            verdict.cls === "red" ? "Human-only." : "Open a PR for review."
          }`
    }\n`,
  );

  // Exit non-zero when not auto-committable so CI can branch on it.
  if (!verdict.autoCommit) process.exitCode = 2;
}
