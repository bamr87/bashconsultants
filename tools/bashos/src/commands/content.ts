// `bashos content <verb>` — Content Studio: the idea→publish pipeline.
//   board                 status of every post by pipeline stage (no API key)
//   stage <file> <stage>  move a post to a pipeline stage (sets published flag)
//   outline|draft|review|seo <file>   run the stage's prompt with Claude
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { findRepoRoot } from "../lib/repo.js";
import { loadPipeline, listPosts, readPost, setFrontmatterField, type PipelineStage } from "../lib/posts.js";
import { runCommand, type RunOpts } from "./run.js";

const RISK_ICON = { green: "🟢", yellow: "🟡", red: "🔴" } as const;

export function boardCommand(): void {
  const root = findRepoRoot();
  const pipeline = loadPipeline(root);
  const posts = listPosts(root);
  const order = new Map(pipeline.stages.map((s, i) => [s.id, i]));

  console.log("\nContent Studio — pipeline board\n");
  for (const stage of pipeline.stages) {
    const inStage = posts.filter((p) => p.stage === stage.id);
    console.log(`${RISK_ICON[stage.risk]} ${stage.label}  (${inStage.length})`);
    for (const p of inStage) {
      const warn = p.published && !stage.published ? "  ⚠ published:true but pre-publish stage" : "";
      console.log(`    · ${p.title}  — ${p.path}${warn}`);
    }
  }
  const unstaged = posts.filter((p) => p.stage === "—");
  if (unstaged.length) {
    console.log(`\n⚪ No stage set  (${unstaged.length})`);
    for (const p of unstaged) {
      const live = p.published ? " [live]" : " [published:false]";
      console.log(`    · ${p.title}  — ${p.path}${live}`);
    }
  }
  console.log("");
}

export function stageCommand(file: string, stageId: string): void {
  const root = findRepoRoot();
  const pipeline = loadPipeline(root);
  const target: PipelineStage | undefined = pipeline.stages.find((s) => s.id === stageId);
  if (!target) {
    console.error(`Unknown stage "${stageId}". Stages: ${pipeline.stages.map((s) => s.id).join(", ")}`);
    process.exitCode = 1;
    return;
  }
  const abs = resolve(file);
  const before = readPost(root, abs);

  setFrontmatterField(abs, pipeline.field, stageId);
  setFrontmatterField(abs, "published", String(target.published));

  console.log(`${before.title}: ${before.stage} → ${stageId} (published: ${target.published})`);
  if (target.id === "published" || target.published) {
    console.log(
      "⚠ This makes the post customer-facing (Yellow). It must go through human PR review " +
        "before reaching main — do not auto-merge. See docs/ai-framework/AUTONOMY-POLICY.md.",
    );
  }
}

const SUBFOLDERS = ["corp", "erp", "muses", "tech"] as const;
type Subfolder = (typeof SUBFOLDERS)[number];

const slugify = (s: string): string =>
  s.toLowerCase().trim().replace(/[^a-z0-9\s-]/g, "").replace(/\s+/g, "-").replace(/-+/g, "-").slice(0, 60);

export interface NewOpts {
  subfolder: string;
  title: string;
  slug?: string;
}

/**
 * Scaffold a new post at `stage: idea`, `published: false` (build-safe — never
 * goes live until a human promotes it). Prints the created path.
 */
export function newCommand(opts: NewOpts): void {
  const root = findRepoRoot();
  const subfolder = opts.subfolder as Subfolder;
  if (!SUBFOLDERS.includes(subfolder)) {
    console.error(`Invalid subfolder "${opts.subfolder}". Use one of: ${SUBFOLDERS.join(", ")}`);
    process.exitCode = 1;
    return;
  }
  const now = new Date();
  const iso = now.toISOString().replace(/\.\d+Z$/, ".000Z");
  const dateOnly = iso.slice(0, 10);
  const slug = opts.slug ? slugify(opts.slug) : slugify(opts.title);
  const rel = join("pages/_posts", subfolder, `${dateOnly}-${slug}.md`);
  const abs = join(root, rel);
  if (existsSync(abs)) {
    console.error(`Refusing to overwrite existing file: ${rel}`);
    process.exitCode = 1;
    return;
  }
  mkdirSync(dirname(abs), { recursive: true });
  const fm = [
    "---",
    `title: "${opts.title.replace(/"/g, "'")}"`,
    `description: "TODO — 120-155 chars, outcome first"`,
    `author: "Amr Abdel-Motaleb"`,
    `layout: article`,
    `date: ${iso}`,
    `lastmod: ${iso}`,
    `stage: idea`,
    `published: false`,
    `draft: true`,
    `categories: [${subfolder}]`,
    `tags: []`,
    `preview: /images/previews/${slug}.png`,
    "---",
    "",
    `<!-- stage: idea — outline next with \`bashos content outline ${rel} --write\` -->`,
    "",
  ].join("\n");
  writeFileSync(abs, fm);
  console.log(rel);
}

/** Map a working verb to its prompt and run it with Claude. */
export async function contentRun(verb: string, file: string, opts: RunOpts): Promise<void> {
  const root = findRepoRoot();
  const pipeline = loadPipeline(root);
  const prompt = pipeline.prompts[verb];
  if (!prompt) {
    console.error(`No prompt mapped for content verb "${verb}".`);
    process.exitCode = 1;
    return;
  }
  await runCommand(prompt, file, opts);
}
