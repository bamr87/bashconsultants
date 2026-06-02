// Blast-radius / autonomy policy engine.
// Loads tools/bashos/policy/blast-radius.yml and classifies a changeset into
// green | yellow | red. See docs/ai-framework/AUTONOMY-POLICY.md.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { minimatch } from "minimatch";
import { parse as parseYaml } from "yaml";
import { readFileSafe } from "./repo.js";

export type RiskClass = "green" | "yellow" | "red";
const ORDER: Record<RiskClass, number> = { green: 0, yellow: 1, red: 2 };

interface PolicyFile {
  version: number;
  default: RiskClass;
  classes: Record<RiskClass, { globs?: string[]; conditions?: { require_draft?: string[] } }>;
  secret_patterns?: string[];
}

export interface PathVerdict {
  path: string;
  cls: RiskClass;
  reason: string;
}

export interface Verdict {
  cls: RiskClass; // highest class across the changeset
  paths: PathVerdict[];
  secretHits: string[];
  autoCommit: boolean; // true only when cls === "green" and no secret hits
}

export function loadPolicy(repoRoot: string): PolicyFile {
  const p = join(repoRoot, "tools/bashos/policy/blast-radius.yml");
  return parseYaml(readFileSync(p, "utf8")) as PolicyFile;
}

const matchesAny = (path: string, globs: string[] = []): string | undefined =>
  globs.find((g) => minimatch(path, g, { dot: true }));

/** Classify a single path (red > yellow > green; default for no match). */
function classifyPath(repoRoot: string, policy: PolicyFile, path: string): PathVerdict {
  for (const cls of ["red", "yellow"] as const) {
    const hit = matchesAny(path, policy.classes[cls]?.globs);
    if (hit) return { path, cls, reason: `matches ${cls} glob "${hit}"` };
  }
  const greenHit = matchesAny(path, policy.classes.green?.globs);
  if (greenHit) {
    // Draft condition: a green post stays green only while draft: true.
    const requiresDraft = matchesAny(path, policy.classes.green?.conditions?.require_draft);
    if (requiresDraft) {
      const body = readFileSafe(join(repoRoot, path));
      const isDraft = /^\s*draft:\s*true\s*$/m.test(body);
      if (!isDraft)
        return { path, cls: "yellow", reason: `published (not draft) — escalated from green` };
    }
    return { path, cls: "green", reason: `matches green glob "${greenHit}"` };
  }
  return { path, cls: policy.default, reason: `unmatched — default ${policy.default}` };
}

/** Classify an entire changeset (most-restrictive-wins) and scan added lines for secrets. */
export function classifyChangeset(
  repoRoot: string,
  policy: PolicyFile,
  paths: string[],
  addedLines: string[] = [],
): Verdict {
  const verdicts = paths.map((p) => classifyPath(repoRoot, policy, p));
  let cls: RiskClass = verdicts.reduce<RiskClass>(
    (acc, v) => (ORDER[v.cls] > ORDER[acc] ? v.cls : acc),
    "green",
  );

  const secretHits: string[] = [];
  for (const pat of policy.secret_patterns ?? []) {
    const re = new RegExp(pat);
    if (addedLines.some((l) => re.test(l))) secretHits.push(pat);
  }
  if (secretHits.length) cls = "red";

  return { cls, paths: verdicts, secretHits, autoCommit: cls === "green" && secretHits.length === 0 };
}
