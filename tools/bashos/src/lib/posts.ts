// Reads the _posts collection and the pipeline config for Content Studio.
// The studio board is a CLI view (not a Jekyll page) because pre-publish posts
// carry `published: false`, which removes them from site.posts — so Liquid
// cannot see them, but the filesystem can.
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { parse as parseYaml } from "yaml";

export interface PipelineStage {
  id: string;
  label: string;
  description: string;
  published: boolean;
  risk: "green" | "yellow" | "red";
}
export interface Pipeline {
  field: string;
  stages: PipelineStage[];
  transitions: Record<string, string[]>;
  prompts: Record<string, string>;
}

export interface PostInfo {
  path: string; // repo-relative
  title: string;
  stage: string; // pipeline stage, or "—" if unset
  published: boolean; // resolved Jekyll-native published flag (default true)
  subfolder: string;
}

const POSTS_DIR = "pages/_posts";

export function loadPipeline(repoRoot: string): Pipeline {
  return parseYaml(readFileSync(join(repoRoot, "_data/pipeline.yml"), "utf8")) as Pipeline;
}

function walkMd(dir: string): string[] {
  if (!existsSync(dir)) return [];
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walkMd(full));
    else if (entry.name.endsWith(".md")) out.push(full);
  }
  return out;
}

function frontmatter(text: string): string[] {
  const lines = text.split("\n");
  if (lines[0]?.trim() !== "---") return [];
  const end = lines.indexOf("---", 1);
  return end === -1 ? [] : lines.slice(1, end);
}

function scalar(fm: string[], key: string): string | undefined {
  const m = fm.find((l) => new RegExp(`^${key}:\\s`).test(l));
  if (!m) return undefined;
  return m.replace(new RegExp(`^${key}:\\s*`), "").replace(/^["']|["']$/g, "").trim();
}

export function readPost(repoRoot: string, absPath: string): PostInfo {
  const fm = frontmatter(readFileSync(absPath, "utf8"));
  const rel = relative(repoRoot, absPath);
  const publishedRaw = scalar(fm, "published");
  return {
    path: rel,
    title: scalar(fm, "title") ?? "(untitled)",
    stage: scalar(fm, "stage") ?? "—",
    published: publishedRaw !== "false", // Jekyll default is true
    subfolder: rel.split("/").at(-2) ?? "",
  };
}

export function listPosts(repoRoot: string): PostInfo[] {
  return walkMd(join(repoRoot, POSTS_DIR)).map((p) => readPost(repoRoot, p));
}

/** Rewrite (or insert) a top-level scalar frontmatter key in place. */
export function setFrontmatterField(absPath: string, key: string, value: string): void {
  const text = readFileSync(absPath, "utf8");
  const lines = text.split("\n");
  if (lines[0]?.trim() !== "---") throw new Error(`No frontmatter in ${absPath}`);
  const end = lines.indexOf("---", 1);
  if (end === -1) throw new Error(`Unterminated frontmatter in ${absPath}`);
  const idx = lines.findIndex((l, i) => i > 0 && i < end && new RegExp(`^${key}:\\s`).test(l));
  if (idx !== -1) lines[idx] = `${key}: ${value}`;
  else lines.splice(end, 0, `${key}: ${value}`);
  writeFileSync(absPath, lines.join("\n"));
}
