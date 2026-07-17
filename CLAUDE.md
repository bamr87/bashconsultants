# CLAUDE.md — Native Claude context for bashconsultants

> The canonical entry point for **Claude Code** in this repository. Read this first, every session.
>
> This repo is a working demonstration of what BASH Consulting sells: a practice that runs on
> **governed AI** — rules in files, reusable playbooks, agents that draft, humans who approve. The
> `.claude/` directory below is the reference implementation of that model. When you work here, you
> are also maintaining the showcase. Practice what we preach.

## What this repository is

A dual-purpose repository. Treat the two sub-projects independently — **never mix them in one commit.**

1. **Jekyll site** (repo root) — `bashconsultants.com`, built on the `bamr87/zer0-mistakes` remote
   theme, deployed to GitHub Pages on every push to `main`. This is the primary project.
2. **VS Code extension** (`extension/`) — *Prompt Orchestrator*, a self-contained TypeScript
   sub-project that runs the shared `.github/prompts/` library from inside the editor.

The site builds **Docker-first** (host Ruby is usually too old). See [`AGENTS.md`](./AGENTS.md) for the cross-tool overview and [`.github/copilot-instructions.md`](./.github/copilot-instructions.md) for the full project reference. This file does not repeat them — it adds the Claude-native layer.

## The context framework — where guidance lives

Guidance is layered. Read from the top; the deeper layers auto-load or are pulled in on demand.

| Layer | Location | Loaded |
|---|---|---|
| **Claude entry point** | `CLAUDE.md` (this file) | Always, automatically |
| **Cross-tool entry point** | [`AGENTS.md`](./AGENTS.md) | Read once per session |
| **Project reference** | [`.github/copilot-instructions.md`](./.github/copilot-instructions.md) | Read once per session |
| **Brand — the single source of truth** | [`.github/instructions/brand.instructions.md`](./.github/instructions/brand.instructions.md) | Before any brand/voice/identity work |
| **Content style** | [`.github/instructions/content-style.instructions.md`](./.github/instructions/content-style.instructions.md) | Editing any customer-facing page |
| **File-scoped rules** | `.github/instructions/*.instructions.md` | Auto-matched by `applyTo` glob |
| **Frontmatter schema** | [`.github/FRONTMATTER.md`](./.github/FRONTMATTER.md) | Editing any `.prompt.md` / `.instructions.md` |
| **Content taxonomy** | [`_data/taxonomy.yml`](./_data/taxonomy.yml) | Categorizing or voicing a post |

### The Claude-native primitives (`.claude/`)

Four primitives, one job each. See [`.claude/README.md`](./.claude/README.md) for the full map.

| Primitive | Directory | Use it when |
|---|---|---|
| **Skills** | `.claude/skills/*/SKILL.md` | You need a *governed procedure* — the same steps done the same way every time (editorial gate, authoring a toolkit doc, wikilink discipline, brand application). |
| **Subagents** | `.claude/agents/*.md` | You want to *delegate* a bounded job to a fresh context (editorial review, build validation, brand audit). Invoke via the Agent tool. |
| **Commands** | `.claude/commands/*.md` | You want a discoverable `/`-entry point that runs a common workflow (`/lint-content`, `/new-toolkit-doc`, `/brand-check`). |
| **Memory + hooks** | `.claude/agent-memory/`, `.claude/hooks/`, `.claude/settings.json` | Agents carry decisions across sessions; hooks enforce policy automatically. |

**Skills vs. prompts:** `.github/prompts/*.prompt.md` are the *cross-tool* library (Copilot, the extension, Cursor). `.claude/skills/` are the *Claude-native* equivalents — richer, with optional scripts. When both exist, prefer the skill inside Claude Code; keep the two in sync when you change a shared workflow.

## Operating rules

These are the hard rules for working in this repo. The brand and content-style files add detail; these are the ones you cannot skip.

1. **Minimal, surgical changes.** Match the surrounding style. Do not refactor adjacent code, and do
   not restructure the remote theme — override via `_includes/`, `_layouts/`, `_sass/`, `_data/`.
2. **Validate before declaring done.**
   - Jekyll changes → run the Docker build:
     `docker-compose exec -T jekyll bundle exec jekyll build --config '_config.yml,_config_dev.yml'`
   - Content changes → run the editorial gate (lints the whole repo, exit 1 on errors): `python3 scripts/content_lint.py`
   - Extension changes → `cd extension && npm run lint && npm run compile`
3. **Governed content.** Customer-facing copy obeys `content-style.instructions.md` and
`brand.instructions.md`: no banned phrases, acronyms expanded on first use, sentence-case headings, one H1, `description` 120–155 chars with no trailing period, one CTA. **Enact, don't announce** — never name a piece's own creative device in reader-facing text.
4. **Never invent** metrics, client names, logos, or certifications. Describe categories of work and
   what compliance frameworks require; never claim BASH is certified.
5. **Deterministic-first.** If a step can be a script, it is a script (`scripts/`). Spend the model
where judgment is needed. Generated data (`_data/playbook.yml`, tool tables) comes from scripts, not hand-editing — change the source, regenerate.
6. **Author is `Amr Abdel-Motaleb`.** Conventional commits: `<type>(<scope>): <subject>`
   (type ∈ `feat fix docs refactor chore ci`; scope ∈ `posts pages services config extension prompts docs toolkit`).
7. **Update `CHANGELOG.md`** (`[Unreleased]`) for user-visible changes.
8. **No secrets, ever.** Refuse to commit literal `ghp_*`, `sk-*`, `AKIA*`. API keys live
   server-side (`api/`, Azure app settings) — never in the repo or the browser.
9. **Commit to the working branch; do not push** unless explicitly asked. The final polish pass on
   any content is done with Opus 4.8.
10. **Don't commit** `_site/`, `node_modules/`, `vendor/`, `.playwright-mcp/`.

## Obsidian wikilinks (a repeated foot-gun)

Internal cross-links use Obsidian `[[Page Title]]` syntax, resolved client-side. Two rules save hours:

- **Pipeless only.** `[[Page Title]]` survives the kramdown GFM parser; the aliased form `[[a|b]]`
  gets mangled into a table. Reword instead of aliasing.
- **Collection docs + non-root pages only.** The wiki index covers collection docs and pages with an
`output_ext` of `.html`; it does **not** index root-level pages (`tools.md`, `ai-operations.md`). Link to those with a normal markdown link. Full detail: the `wikilinks` skill.

## Build stacks (know which config you're in)

| Stack | Config | Notes |
|---|---|---|
| **Local dev** | `_config.yml,_config_dev.yml` | Docker, port 4042, livereload. `_plugins/` run here. |
| **GitHub Pages** | `_config.yml` alone | **Safe mode** — local `_plugins/` do **not** run in production. |
| **Azure Static Web Apps** | `_config.yml,_config.azure.yml` | `Gemfile.azure` pins the theme as a gem. |

Anything that depends on a local plugin (e.g. server-side wikilink resolution) must also work in Pages safe mode, or it is broken in production. Validate the change against the stack it ships on.
