// Loads the prompt library (.github/prompts) and file-scoped instruction
// context (.github/instructions) so the AI engine reuses the same versioned
// assets as every other agent surface.
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { basename, join } from "node:path";
import { minimatch } from "minimatch";

export interface LoadedPrompt {
  name: string; // slug, e.g. "article-write"
  path: string;
  body: string; // prompt text with frontmatter stripped
}

function stripFrontmatter(text: string): string {
  const lines = text.split("\n");
  if (lines[0]?.trim() !== "---") return text;
  const end = lines.indexOf("---", 1);
  return end === -1 ? text : lines.slice(end + 1).join("\n").trim();
}

export function listPrompts(repoRoot: string): string[] {
  const dir = join(repoRoot, ".github/prompts");
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(".prompt.md"))
    .map((f) => basename(f, ".prompt.md"))
    .sort();
}

export function loadPrompt(repoRoot: string, name: string): LoadedPrompt {
  const path = join(repoRoot, ".github/prompts", `${name}.prompt.md`);
  if (!existsSync(path)) {
    const available = listPrompts(repoRoot).join(", ");
    throw new Error(`Unknown prompt "${name}". Available: ${available}`);
  }
  return { name, path, body: stripFrontmatter(readFileSync(path, "utf8")) };
}

/** Parse an instruction file's `applyTo` globs (comma-separated, no spaces). */
function applyToGlobs(text: string): string[] {
  const m = text.match(/^applyTo:\s*["']?(.+?)["']?\s*$/m);
  return m ? m[1].split(",").map((g) => g.trim()).filter(Boolean) : [];
}

/**
 * Instruction files whose `applyTo` matches `targetPath`, concatenated.
 * This is the large, stable context worth prompt-caching.
 */
export function instructionContextFor(repoRoot: string, targetPath: string): string {
  const dir = join(repoRoot, ".github/instructions");
  if (!existsSync(dir)) return "";
  const parts: string[] = [];
  for (const f of readdirSync(dir).filter((f) => f.endsWith(".instructions.md"))) {
    const text = readFileSync(join(dir, f), "utf8");
    if (applyToGlobs(text).some((g) => minimatch(targetPath, g, { dot: true }))) {
      parts.push(`<!-- ${f} -->\n${stripFrontmatter(text)}`);
    }
  }
  return parts.join("\n\n---\n\n");
}
