// Git/repo helpers for the bashos CLI.
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

/** Walk up from `start` until a directory containing `.git` is found. */
export function findRepoRoot(start = process.cwd()): string {
  let dir = resolve(start);
  for (;;) {
    if (existsSync(join(dir, ".git"))) return dir;
    const parent = dirname(dir);
    if (parent === dir) throw new Error("Not inside a git repository.");
    dir = parent;
  }
}

function git(root: string, args: string[]): string {
  return execFileSync("git", args, { cwd: root, encoding: "utf8" });
}

/** Paths changed in the working tree (staged + unstaged + untracked), repo-relative. */
export function changedPaths(root: string): string[] {
  const out = git(root, ["status", "--porcelain=v1", "--untracked-files=all"]);
  const paths = new Set<string>();
  for (const line of out.split("\n")) {
    if (!line.trim()) continue;
    // Format: "XY <path>" or "XY <old> -> <new>" for renames.
    let p = line.slice(3).trim();
    const arrow = p.indexOf(" -> ");
    if (arrow !== -1) p = p.slice(arrow + 4);
    paths.add(p.replace(/^"|"$/g, ""));
  }
  return [...paths];
}

/** Added lines (lines starting with "+" in the diff) across the working tree. */
export function addedDiffLines(root: string): string[] {
  const out = git(root, ["diff", "HEAD", "--unified=0"]);
  return out
    .split("\n")
    .filter((l) => l.startsWith("+") && !l.startsWith("+++"))
    .map((l) => l.slice(1));
}

export function readFileSafe(path: string): string {
  return existsSync(path) ? readFileSync(path, "utf8") : "";
}
