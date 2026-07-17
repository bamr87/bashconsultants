---
description: Run the BASH editorial gate on changed (or named) content and fix what it reports
argument-hint: "[file-or-glob …] (default: changed content files)"
allowed-tools: Bash(python3 scripts/content_lint.py:*), Bash(git status:*), Bash(git diff:*), Read, Edit
---

Run the governed editorial gate on customer-facing content.

**Focus:** `$ARGUMENTS` if provided; otherwise the changed content files — `git status --short`, selecting those under `pages/**`, `index.md`, `about.md`, `contact.md`, `tools.md`, `ai-operations.md`.

**Do this:**

1. Run the mechanical gate (it lints the **whole repo**; there is no per-file argument):
   ```bash
   python3 scripts/content_lint.py             # exit 1 on errors
   ```
2. Follow the **`content-editorial`** skill to fix every issue it reports in the focus files —
banned phrases, description length (120–155, no trailing period), heading case, undefined acronyms — plus the brand and content-style rules the linter can't see (one CTA, enact-don't-announce, no invented claims). Leave pre-existing findings in other files alone unless asked.
3. Re-run the linter until it reports **zero errors**.
4. Report a short table: file → issues found → issues fixed → remaining (should be none). If a fix is
   a judgment call about voice, note it for the author rather than forcing it.

Do not edit anything outside the target files. The final voice/polish read-through is done with Opus 4.8.
