#!/usr/bin/env node
// BASH OS — prompt/instruction structural eval ("start light").
//
// Deterministic, dependency-free, no API calls: validates that every
// .prompt.md and .instructions.md conforms to the canonical frontmatter schema
// (.github/FRONTMATTER.md) and the body-style rules (prompts.instructions.md).
// Catches prompt drift on edits and across model upgrades before it ships.
//
// Output-quality evals (LLM-graded golden sets) are a later, opt-in layer that
// needs ANTHROPIC_API_KEY; this structural gate runs free in CI on every PR.
//
// Usage: node tools/bashos/evals/validate-prompts.mjs [--quiet]
// Exit:  0 = all pass, 1 = at least one hard error.

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const PROMPTS_DIR = join(REPO_ROOT, ".github/prompts");
const INSTRUCTIONS_DIR = join(REPO_ROOT, ".github/instructions");

const DESC_MAX = 160;
const BODY_SOFT_MAX = 100; // "Target <= 100 lines per file" — warn, don't fail.
const ISO_DATE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;

const errors = [];
const warnings = [];

function listMd(dir) {
  try {
    return readdirSync(dir)
      .filter((f) => f.endsWith(".md"))
      .map((f) => join(dir, f))
      .filter((p) => statSync(p).isFile());
  } catch {
    return [];
  }
}

// Minimal frontmatter splitter: returns {fm: rawYamlLines[], bodyLineCount}.
function parse(file) {
  const text = readFileSync(file, "utf8");
  const lines = text.split("\n");
  if (lines[0]?.trim() !== "---") return null;
  const end = lines.indexOf("---", 1);
  if (end === -1) return null;
  return { fm: lines.slice(1, end), bodyLineCount: lines.length - end - 1 };
}

// Pull a top-level scalar key from raw frontmatter lines (good enough for this schema).
function field(fmLines, key) {
  const re = new RegExp(`^${key}:\\s*(.*)$`);
  for (const line of fmLines) {
    const m = line.match(re);
    if (m) return m[1].trim();
  }
  return undefined;
}

function unquote(v) {
  if (v == null) return v;
  return v.replace(/^["']/, "").replace(/["']$/, "");
}

function checkCommon(file, fm, kind) {
  const rel = file.replace(REPO_ROOT, "");
  const desc = unquote(field(fm, "description"));
  if (!desc) errors.push(`${rel}: missing \`description\``);
  else if (desc.length > DESC_MAX)
    errors.push(`${rel}: description is ${desc.length} chars (max ${DESC_MAX})`);

  for (const k of ["date", "lastmod"]) {
    const v = field(fm, k);
    if (!v) errors.push(`${rel}: missing \`${k}\``);
    else if (!ISO_DATE.test(unquote(v)))
      errors.push(`${rel}: \`${k}\` is "${unquote(v)}", expected ISO YYYY-MM-DDTHH:MM:SS.000Z`);
  }
}

function checkPrompt(file) {
  const rel = file.replace(REPO_ROOT, "");
  const parsed = parse(file);
  if (!parsed) return errors.push(`${rel}: no valid frontmatter block`);
  const { fm, bodyLineCount } = parsed;
  const mode = field(fm, "mode");
  if (mode !== "agent") errors.push(`${rel}: \`mode\` must be "agent" (got "${mode ?? "—"}")`);
  checkCommon(file, fm, "prompt");
  if (bodyLineCount > BODY_SOFT_MAX)
    warnings.push(`${rel}: body is ${bodyLineCount} lines (target <= ${BODY_SOFT_MAX})`);
}

function checkInstruction(file) {
  const rel = file.replace(REPO_ROOT, "");
  const parsed = parse(file);
  if (!parsed) return errors.push(`${rel}: no valid frontmatter block`);
  const { fm, bodyLineCount } = parsed;
  const applyTo = unquote(field(fm, "applyTo"));
  if (!applyTo) errors.push(`${rel}: missing \`applyTo\``);
  else if (/,\s+/.test(applyTo))
    errors.push(`${rel}: \`applyTo\` has a space after a comma (must be comma-separated, no spaces)`);
  checkCommon(file, fm, "instruction");
  if (bodyLineCount > BODY_SOFT_MAX)
    warnings.push(`${rel}: body is ${bodyLineCount} lines (target <= ${BODY_SOFT_MAX})`);
}

const prompts = listMd(PROMPTS_DIR);
const instructions = listMd(INSTRUCTIONS_DIR);
prompts.forEach(checkPrompt);
instructions.forEach(checkInstruction);

const quiet = process.argv.includes("--quiet");
const checked = prompts.length + instructions.length;

if (!quiet || warnings.length) {
  for (const w of warnings) console.log(`  ⚠ ${w}`);
}
if (errors.length) {
  for (const e of errors) console.error(`  ✖ ${e}`);
  console.error(`\nprompt-evals: FAIL — ${errors.length} error(s) across ${checked} file(s).`);
  process.exit(1);
}
console.log(
  `prompt-evals: PASS — ${checked} file(s) valid` +
    (warnings.length ? `, ${warnings.length} warning(s)` : "") +
    ".",
);
