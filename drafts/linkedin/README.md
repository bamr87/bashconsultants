# `drafts/linkedin/` — the approval queue

A staging area, not an outbox. Each `*.md` here is one proposed LinkedIn company-page post waiting on a human.

The gate: `/linkedin-draft` writes a file here at `status: pending` and opens a pull request. A person edits it and **merges** — the merge is the approval. Only then does `.github/workflows/linkedin-publish.yml` run `from-drafts` live, post it, and flip the file to `status: published`.

Two things keep a stray file from publishing:

- **`status` must be exactly `pending`.** Anything else is skipped.
- **Top level only.** `from-drafts` globs `*.md` in this directory and does not recurse, so `examples/` is never picked up.

Format and the full drafting rules: `.claude/skills/linkedin-share/SKILL.md`. Preview a payload without touching the network: `python3 scripts/features/linkedin from-drafts --dry-run`.
