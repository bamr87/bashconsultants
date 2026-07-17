# The preacher — practicing what we preach, automatically

The site sells a doctrine. This repository is supposed to be its reference
implementation — governed by files, deterministic first, built in the open. But a
doctrine drifts the moment no one is watching, and watching by hand is exactly the
kind of expensive, skippable judgment the doctrine says to script.

The **preacher** is the answer to that: a governed AI agent that runs every Saturday
and holds the repo to its own principles — and, crucially, keeps lowering the cost of
doing so. It is the practice's core principle turned on itself: *deterministic
foundations first, AI as an overlay.*

> Origin story: the block of contact info (email, phone, LinkedIn, website) was once
> copy-pasted, byte-for-byte, at the foot of all eight service pages — a textbook DRY
> violation on a site that literally preaches "configuration over duplication." It was
> caught and fixed by hand. The preacher exists so the *next* one is caught by a
> script, not a person.

## The canon it enforces

The preacher does not enforce from memory. The authoritative texts live in the repo:

- **The adapted principles** — [`pages/_toolkit/engagement-method.md`](../pages/_toolkit/engagement-method.md), section *"The principles we adapt"*:
  **DFF** (design for failure) · **KIS** (keep it simple, clarity over cleverness) ·
  **DRY** (one system of record per entity; configuration over duplication — the
  deliberate exception is *teaching*, which we repeat on purpose) · **REnO** (release
  early and often) · **MVP** (smallest slice that delivers value) · **COLAB** (open,
  portable, standards-based; the client owns the repo) · **AIPD** (AI behind human
  review and a deterministic gate) · *start where you are, progress over perfection.*
- **The repo doctrine** — [`CLAUDE.md`](../CLAUDE.md) and the brand single source of
  truth [`.github/instructions/brand.instructions.md`](../.github/instructions/brand.instructions.md).
- **The SSOTs** — brand, editorial (`content-style.instructions.md`), contact/entity
  (`_data/entity/info.yml`, `_config.yml`), taxonomy (`_data/taxonomy.yml`).
  Duplicating anything with an SSOT is a DRY violation.

## How it works

Every run has the same three beats.

### 1. Deterministic gates first
```bash
python3 scripts/doctrine_check.py            # structural doctrine (DRY, SSOT, …)
python3 scripts/content_lint.py --warn-only  # editorial contract
```
These are ground truth. The preacher reads their findings; it does not re-judge what a
script has already decided. This is the whole philosophy in one step — spend the model
only on what a script cannot yet catch.

### 2. Judgment pass — only what the scripts miss
Reading the recent diff against the canon, the preacher looks for drift no script can
catch yet: DRY beyond contact info, over-engineering (KIS/MVP), a load-bearing step
done by hand that should be a script (deterministic-first), new lock-in (COLAB),
brand/voice/claims drift, stale docs, dead code. It is a **high-precision** critic —
every finding carries a `file:line` and the principle it breaks. A preacher that cries
wolf gets tuned out.

### 3. One of two modes

**Mode A — violations found → one findings PR.** Issues are disabled on this
repository, so violations arrive as a pull request carrying
`docs/preacher-findings.md` — grouped by principle, most severe first, each with the
fix. One PR per run; if an open `Preacher:` PR already exists it gets a comment, not
a duplicate. A human triages: fix and close, or merge to keep the record.

**Mode B — repo clean → mechanize one thing → a PR.** This is the mode that matters.
The preacher picks the single highest-value recurring AI-review burden and converts it
into a new deterministic check in [`scripts/doctrine_check.py`](../scripts/doctrine_check.py)
— with a self-test — then opens a PR. Next week that judgment is a script, and the AI
pass is a little cheaper. **The deterministic floor rises over time; the weekly AI pass
shrinks.** That is the design goal, stated plainly: automate an AI responsibility until
it is no longer one.

The preacher **never pushes to main.** PRs only; a human approves. That is
AIPD, not a limitation.

## Running it

- **Scheduled:** automatically every **Saturday** (`.github/workflows/preacher.yml`,
  cron `42 14 * * 6` ≈ 7–8 AM Denver).
- **On demand (CI):** the workflow's **Run workflow** button (`workflow_dispatch`),
  with an optional `focus` lens (e.g. `DRY`, `deterministic-first`, `brand`).
- **Locally, in Claude Code:** invoke the `preacher` subagent
  ([`.claude/agents/preacher.md`](../.claude/agents/preacher.md)) via the Agent tool for
  an ad-hoc "are we practicing what we preach" audit.
- **Just the deterministic half, anytime:**
  ```bash
  python3 scripts/doctrine_check.py          # exit 1 on any violation
  python3 scripts/doctrine_check.py --list   # list the registered checks
  python3 scripts/doctrine_check.py --self-test
  ```

## Activation

The workflow skips gracefully (a notice, not a failure) until credentials are set.
Under **Settings → Secrets and variables → Actions** add, OAuth preferred:

1. `CLAUDE_CODE_OAUTH_TOKEN` — from `claude setup-token` (Claude Pro/Max). Used by default.
2. `ANTHROPIC_API_KEY` — workspace API key. Fallback.

Optional: `PREACHER_GITHUB_TOKEN` — a fine-grained PAT (Contents + Issues + Pull
requests read/write) so the preacher's PRs trigger the normal build checks.

## Extending the deterministic floor

Adding a check is the preacher's standing job — and yours, when you spot a rule worth
mechanizing. In `scripts/doctrine_check.py`:

```python
@check("DRY-CONFIG", "Repeated literal that should be a _data/ or _config value.")
def dry_config(root: Path) -> list[Finding]:
    findings = []
    # ...scan content_files(root); append Finding(...) per violation...
    return findings
```

Rules of the house: **high precision** (a false positive costs more trust than a missed
nit), a **self-test fixture** for every check (a bad case that must flag and a good case
that must not), and a `Finding.fix` that tells the author exactly what to use instead.
When a check proves stable and the repo is clean of it, promote it from advisory to a
blocking gate by adding `doctrine_check.py` to `.github/workflows/build-validate.yml`.

## Where the pieces live

| Piece | Path |
|---|---|
| Charter (the agent) | [`.claude/agents/preacher.md`](../.claude/agents/preacher.md) |
| Weekly workflow | [`.github/workflows/preacher.yml`](../.github/workflows/preacher.yml) |
| Deterministic checks | [`scripts/doctrine_check.py`](../scripts/doctrine_check.py) |
| Editorial gate (companion) | [`scripts/content_lint.py`](../scripts/content_lint.py) |
| This document | `docs/the-preacher.md` |
