---
description: Audit copy, layouts, or assets against the BASH brand single source of truth
argument-hint: "[path …] (default: staged/changed identity-bearing files)"
allowed-tools: Read, Grep, Glob, Bash(git status:*), Bash(git diff:*)
---

Audit for brand drift against `.github/instructions/brand.instructions.md`.

**Target:** `$ARGUMENTS` if provided; otherwise the changed identity-bearing files (content pages, `_layouts/**`, `_includes/**`, `assets/brand/**`) from `git status --short`.

**Do this:** delegate to the **`brand-guardian`** agent (via the Agent tool) with the target files. It reads the brand SSOT and reports:

- **Blockers** — unverified claims, certification/compliance language, `BASH` name misuse.
- **Drift** — voice ("revolutionary"/"world-class"/hype), positioning, off-palette color, logo
  misuse.
- **On-brand** — what's already correct.

For a quick self-check without spawning the agent, apply the **`brand`** skill directly. Report the verdict (On-brand / Minor drift / Off-brand) with `file:line` citations and concrete fixes. This is an audit — surface findings; don't rewrite copy unless asked.
