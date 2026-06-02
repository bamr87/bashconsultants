---
title: "BASH OS — AI Consulting Operating System"
description: "Comprehensive plan to turn this static site into an all-in-one, AI-augmented consulting operating system, reusable by other consultants."
status: draft
author: "Amr Abdel-Motaleb"
date: 2026-06-02
lastmod: 2026-06-02
---

# BASH OS — An AI Consulting Operating System

> **Working name:** **BASH OS** — *Bourne Again Solutions Hero, Operating System.*
> A self-hostable, AI-augmented operating system for a one-person (or small) consultancy, built **on top of** a static site. The architecture is the brand: a **deterministic, git-versioned, scriptable foundation** with a **Claude-powered AI overlay**. Prompts are the new command line; the machine underneath stays auditable enough to ship.

This document is the master plan. It is intentionally comprehensive and phased. Nothing here is built yet beyond the foundations already in the repo (see [§2](#2-what-already-exists)). The plan is scoped to three locked decisions:

| Decision | Choice | Consequence |
|---|---|---|
| **Hosting / runtime** | **GitHub Pages** (pure static) | AI runs at **build-time (CI agents)** and in **local authoring tools**. No serverless runtime. Visitor-facing live AI is out of scope (optional third-party embed only). |
| **Phase-1 focus** | **Content Studio** | The idea→draft→review→publish pipeline is built deepest first; other modules are scaffolded. |
| **AI autonomy** | **Semi-autonomous** | AI may auto-commit *low-risk* changes (drafts in a `draft:` state, link fixes, image gen, formatting). *Customer-facing / business-critical* changes go through PR review. The governance layer ([§7](#7-governance--trust-layer)) defines and enforces the blast radius. |

---

## 1. Vision & Principles

**Vision.** A single repository that runs a consulting practice end-to-end — the marketing site, the content engine, the idea backlog, the marketing distribution, and client communications — with Claude as the intelligence layer and git as the system of record. It works for BASH Consulting today, and any other independent consultant can fork it, fill in their `_data/entity/`, add an API key, and have the same machine.

**Principles** (each maps to the existing brand positioning):

1. **Deterministic foundation, AI overlay.** Every artifact is a plain file (Markdown/YAML) in git. AI proposes and drafts; the deterministic layer (Jekyll build, schema validation, CI, human review) decides what ships. No hidden state, no black box.
2. **Git is the database and the audit log.** Clients, leads, ideas, campaigns, and content states all live as version-controlled files. Every AI action is a commit with a traceable prompt, inputs, model version, and diff.
3. **Prompts and skills are versioned assets.** Build on the existing `.github/prompts/` + `.github/instructions/` libraries rather than ad-hoc prompting. Treat them like code: reviewed, tested with evals, reused.
4. **Portable by default, premium where it pays.** Core features work on plain GitHub Pages with no paid infra beyond the Claude API. Anything heavier is an optional, clearly-isolated module.
5. **Reusable, not bespoke.** Practice-specific facts live in `_data/` and config; framework logic lives in scripts, plugins, prompts, and the extension. The two never mix, so a fork is a config change, not a rewrite.
6. **Human-in-the-loop where it counts.** Semi-autonomous by policy: speed on drafts and chores, gated review on anything a client or auditor will see.

---

## 2. What Already Exists

The repo is further along than a greenfield. The plan **formalizes and connects** these, it does not replace them:

| Asset | Location | Role in BASH OS |
|---|---|---|
| Jekyll marketing site | root, `pages/`, `_layouts/`, `_data/` | The **foundation** + the public face |
| Structured prompt library (11) | `.github/prompts/*.prompt.md` | The **skills** the AI engine runs |
| File-scoped instructions (6) | `.github/instructions/*.instructions.md` | Guardrails / house style per file type |
| Agent entry point | `AGENTS.md`, `.github/copilot-instructions.md` | Cross-tool agent guide |
| Frontmatter schema | `.github/FRONTMATTER.md`, `frontmatter.json` | Canonical content metadata contract |
| "Prompt Orchestrator" VS Code extension | `extension/` | **Local authoring** surface (TypeScript) |
| AI Ruby plugins | `_plugins/preview_image_generator.rb`, `content_statistics_generator.rb` | Build-time AI (preview images, stats) |
| Automation scripts | `scripts/*.sh`, `scripts/*.js`, `scripts/lib/*.py` | Maintenance, preview gen, docs gen |
| CI | `.github/workflows/` | Where **build-time agents** will live |
| Entity data | `_data/entity/{info,services}.yml` | Practice config → becomes the fork's config |

**Implication:** Phase 0 is mostly *connective tissue and a Claude engine*, not new concepts.

---

## 3. Architecture (Layered — the Brand Made Literal)

```
┌─────────────────────────────────────────────────────────────────┐
│  DISTRIBUTION LAYER        template repo · create-bash-os CLI ·   │
│  (other consultants)       docs · theme gem (optional)           │
├─────────────────────────────────────────────────────────────────┤
│  CAPABILITY MODULES        Content Studio · Idea Vault ·          │
│  ("the apps")              Marketing Engine · Comms Hub · Site Ops│
├─────────────────────────────────────────────────────────────────┤
│  AI ENGINE LAYER           Claude Agent SDK CLI  +  CI agents     │
│  (the overlay)             (Claude Code GitHub Action) +          │
│                            VS Code extension  · prompts · skills  │
├─────────────────────────────────────────────────────────────────┤
│  GOVERNANCE / TRUST        autonomy policy · blast-radius config ·│
│  (the guardrails)          audit log · prompt evals · secrets     │
├─────────────────────────────────────────────────────────────────┤
│  DATA LAYER                _data/*.yml · collections · frontmatter│
│  (deterministic store)     (clients, leads, ideas, campaigns…)    │
├─────────────────────────────────────────────────────────────────┤
│  FOUNDATION LAYER          Jekyll · git · GitHub Pages · CI ·     │
│  (exists)                  shell scripts · Ruby plugins           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1 AI execution surfaces (given GitHub Pages = no serverless)

There are exactly **two** places AI runs. Both are deterministic-foundation-friendly because their output is always a file diff a human can see.

1. **Local authoring (interactive).**
   - A new **`bashos` CLI** (Node, wraps the **Claude Agent SDK** + Anthropic SDK with **prompt caching**) that runs the prompt library against the working tree from the terminal.
   - The existing **VS Code "Prompt Orchestrator" extension**, upgraded from a Copilot/GPT-4o passthrough to first-class **Claude** support (Agent SDK / Messages API) and wired to the same prompt + instruction libraries.
   - Claude Code itself (CLI / web) using `CLAUDE.md` + skills.

2. **Build-time / CI agents (automated, semi-autonomous).**
   - **GitHub Actions** workflows that invoke the **Claude Code GitHub Action** (or the `bashos` CLI headless) to perform scheduled or event-triggered work: generate content ideas, draft posts, repurpose for social, run maintenance/SEO audits, generate preview images.
   - Output routing follows the autonomy policy ([§7](#7-governance--trust-layer)): low-risk → direct commit on a bot branch + auto-merge; everything else → **open a PR** for human review.

> **No runtime/visitor-facing AI.** A live chat widget or semantic search would require a serverless function, which GitHub Pages can't host. If wanted later, it is an isolated optional module (third-party embed or a separate Cloudflare/Azure function), explicitly out of the core.

### 3.2 Claude integration map

| Claude capability | Where used | Why |
|---|---|---|
| **Claude Agent SDK** | `bashos` CLI, CI agents | Multi-step autonomous workflows (research → draft → self-review → write files) |
| **Messages API + prompt caching** | CLI, extension, plugins | Cache the large, stable instruction/style context; pay only for the variable part |
| **Claude Code GitHub Action** | `.github/workflows/` | Repo-native automation: issue/label/schedule → PR |
| **Subagents** | CLI + CI | Specialized roles: *Editor*, *SEO Analyst*, *Marketer*, *Strategist*, *Researcher* |
| **Skills** (`.claude/skills/`) | Claude Code sessions | Package the prompt library as invocable skills with progressive disclosure |
| **MCP servers** | CLI + Claude Code | Connect external tools later: analytics, email, calendar, CRM, web search |
| **`CLAUDE.md` / `AGENTS.md`** | All agents | Single source of project + voice guidance (already present) |

---

## 4. Capability Modules

Each module = a **data shape** in `_data/` or a collection, a set of **prompts/skills**, optional **plugins/scripts**, and a **UI surface** (Jekyll page and/or CLI command). Phase 1 builds **Content Studio** deepest; the rest are scaffolded with their data shape + at least one prompt, then deepened in later phases.

### 4.1 Content Studio *(Phase 1 — deepest)*
The idea→ship pipeline for the marketing site.
- **Pipeline states** (frontmatter `draft:` already exists; formalize): `idea → outline → drafting → review → seo → scheduled → published`.
- **Prompts/skills:** reuse `article-write`, `article-review`, `documentation`; add `outline`, `seo-audit`, `repurpose`, `editorial-calendar`.
- **Agents:** *Writer* (draft to house style), *Editor* (structure + voice per `content-style.instructions.md`), *SEO Analyst* (titles, meta, internal links, schema).
- **Surfaces:** `bashos content <verb>` CLI; extension commands; a private `/studio/` dashboard page rendered from content frontmatter (status board).
- **Autonomy:** drafts auto-commit in `draft: true`; promotion to `published` requires human merge.

### 4.2 Idea Vault *(scaffold P1 → deepen P2)*
Capture and triage what to make.
- **Data:** `_data/ideas/` or an `_ideas` collection — one file per idea with `score`, `status`, `themes`, `source`.
- **Agents:** *Strategist* clusters, de-dupes, scores against audience/ICP (`content-style.instructions.md` audience profile), and promotes top ideas into Content Studio outlines.
- **Surface:** weekly CI agent proposes 5 ranked ideas as an issue/PR.

### 4.3 Marketing Engine *(P2)*
Distribution and repurposing.
- **Repurpose:** one published post → LinkedIn post, newsletter section, X thread, preview image (reuse `preview_image_generator.rb`).
- **Calendar:** `_data/campaigns/` with scheduled items; CI agent drafts the week's social from the calendar.
- **Surface:** `bashos market repurpose <post>`; campaign board page.

### 4.4 Comms Hub *(P3)*
Client-facing communication and business ops.
- **Data:** `_data/clients/`, `_data/leads/`, `_data/proposals/` (private; see [§6](#6-data-layer--privacy) on privacy/split-repo).
- **Agents:** draft emails/follow-ups, generate proposals/SOWs from a brief + service catalog (`_data/entity/services.yml`), turn meeting notes → action items.
- **Lead intake:** GitHub Pages can't process forms server-side — use the existing static form provider (or Formspree/email) and have a CI agent triage new leads committed via webhook→issue. (Document the constraint clearly.)

### 4.5 Site Ops & Maintenance *(scaffold P1, ongoing)*
Keep the foundation healthy.
- Extend `scripts/routine-maintenance.sh`: AI-assisted broken-link scan, content freshness audit, alt-text/accessibility check, dependency PRs, changelog drafting.
- Mostly **low-risk → auto-commit** territory.

---

## 5. Repository Structure (target)

New/added paths shown with `+`. Practice-specific data is isolated so a fork only edits `_data/` + config.

```
bashconsultants/
├─ _data/
│  ├─ entity/                  # practice identity (fork edits this)
│ +├─ ideas/                   # Idea Vault items
│ +├─ campaigns/               # Marketing calendar
│ +├─ clients/  leads/  proposals/   # Comms Hub (consider private split-repo)
│ +└─ pipeline.yml             # content pipeline state config
├─ .github/
│  ├─ prompts/                 # existing skills (extend)
│  ├─ instructions/            # existing guardrails (extend)
│ +└─ workflows/
│ +   ├─ ai-content-ideas.yml  # scheduled: propose ideas
│ +   ├─ ai-draft.yml          # issue-triggered: draft a post → PR
│ +   ├─ ai-maintenance.yml    # scheduled: link/SEO/freshness audit
│ +   └─ ai-repurpose.yml      # on publish: social drafts → PR
│ +├─ .claude/skills/          # prompt library as Claude skills
│ +├─ CLAUDE.md                # Claude-native guidance (or symlink AGENTS.md)
├─ tools/
│ +└─ bashos/                  # the AI engine CLI (Node + Agent SDK)
│ +   ├─ src/                  # commands: content, idea, market, comms, ops
│ +   ├─ lib/                  # claude client (cached), prompt loader, audit
│ +   └─ policy/               # autonomy / blast-radius config
├─ extension/                  # existing VS Code ext → add Claude provider
├─ _plugins/                   # existing AI plugins (extend)
├─ pages/
│ +└─ _studio/                 # private dashboards (status boards), noindex
├─ docs/
│ +└─ ai-framework/
│ +   ├─ PLAN.md               # this file
│ +   ├─ ARCHITECTURE.md       # diagrams + ADRs
│ +   ├─ AUTONOMY-POLICY.md    # the blast-radius rules
│ +   └─ ADOPT.md              # "fork this for your own practice" guide
└─ scripts/                    # existing automation (extend)
```

---

## 6. Data Layer & Privacy

- **Public vs. private.** Content, ideas, and campaigns are fine in the public repo. **Clients, leads, proposals, and meeting notes are not.** Options, decide in Phase 3:
  1. **Private submodule / sibling repo** (`bashconsultants-ops`) mounted at `_data/private/`, never built into the public site (`exclude:` in `_config.yml`).
  2. **Encrypted at rest** (git-crypt / SOPS) within this repo.
  - *Recommendation:* private sibling repo — simplest, cleanest blast radius.
- **Schemas.** Every data type gets a documented schema (extend `frontmatter.json` + `.github/FRONTMATTER.md`) so both humans and Claude produce valid files; validate in CI.
- **Single source of truth.** `_data/entity/` already drives the site; it also feeds proposals, email signatures, and the adoption scaffolder. One edit, everywhere.

---

## 7. Governance / Trust Layer

This layer makes "semi-autonomous" safe and is the literal embodiment of the brand's "AI overlay *with guardrails*" promise. Documented in `docs/ai-framework/AUTONOMY-POLICY.md`.

**Blast-radius classification** (config-driven, enforced in CLI + CI):

| Class | Examples | AI may… |
|---|---|---|
| **Green (low-risk)** | new `draft: true` post, link fixes, alt text, formatting, preview images, changelog entries, dependency bumps | **Auto-commit** to a bot branch + auto-merge after CI passes |
| **Yellow (review)** | publishing a post (`draft:false`), edits to `about/services/index`, marketing copy that goes out, new service pages | **Open a PR**, request human review |
| **Red (human-only)** | anything in `clients/leads/proposals`, pricing, contracts, sending external comms, secrets, deploy config | **Draft only**, never commit; surface for a human to act |

**Mechanisms:**
- **Audit trail:** every AI action logs prompt + inputs + model version + output to the commit body and an `ai-actions.log` (or PR description). Reproducible and defensible.
- **Prompt evals:** a small golden-set test harness (`tools/bashos/evals/`) run in CI on any prompt/instruction change — catches prompt drift across model upgrades (the risk called out in the "Prompts are the new command line" post).
- **CODEOWNERS + branch protection:** Yellow/Red paths require human approval by config, not goodwill.
- **Secrets:** `ANTHROPIC_API_KEY` in GitHub Actions secrets / local `.env` (already `.gitignore`d; `.env.example` exists). Pre-commit guard rejects `sk-*`, `ghp_*`, `AKIA*` (already an AGENTS.md rule).
- **Cost guard:** per-run token budget + prompt caching on the stable context.

---

## 8. Distribution / Reusability (for other consultants)

The goal: a consultant clones, runs a setup wizard, and is live.

1. **GitHub Template Repository.** Mark the repo as a template; a fork is a working practice.
2. **`create-bash-os` scaffolder** (`npx create-bash-os`): interactive wizard writing `_data/entity/`, choosing enabled modules, setting the autonomy policy, and dropping in `ANTHROPIC_API_KEY`. Reuses/extends `scripts/setup-*.sh`.
3. **Clean separation contract:** framework code (scripts, plugins, prompts, CLI, extension, theme) carries *zero* BASH-specific facts; everything specific lives in `_data/` + config. CI test asserts no hard-coded "BASH"/"Amr"/Denver strings outside `_data/`.
4. **`docs/ai-framework/ADOPT.md`:** the adoption guide — prerequisites, setup, customizing voice (`content-style.instructions.md`), enabling modules, costs.
5. **Optional theme gem:** the existing remote `jekyll-theme-zer0` already separates presentation; document how to swap it.
6. **License & positioning:** MIT (already). This becomes a credible BASH Consulting *product/lead-magnet* — eat-your-own-dogfood proof of the "AI overlay" thesis.

---

## 9. Phased Roadmap

Each phase ends with something usable and is sized for incremental PRs (per AGENTS.md: minimal, validated, conventional commits, changelog updated).

### Phase 0 — Foundations & Claude engine *(enabler)*
- Add `CLAUDE.md` (or reconcile with `AGENTS.md`); add `.claude/skills/` wrapping existing prompts.
- Scaffold `tools/bashos/` CLI with the Claude client (Agent SDK + caching), prompt loader, and audit logger.
- Write `AUTONOMY-POLICY.md` + blast-radius config; add `ANTHROPIC_API_KEY` handling.
- Stand up the prompt eval harness + a CI job.
- **Deliverable:** `bashos run <prompt> <file>` works locally and in CI with full audit logging.

### Phase 1 — Content Studio *(focus, deepest)*
- Formalize pipeline states in frontmatter + `_data/pipeline.yml`; build the `/studio/` status board page.
- CLI verbs: `bashos content {idea,outline,draft,review,seo,publish}`; new prompts `outline`, `seo-audit`.
- CI: `ai-draft.yml` (label an idea issue → Claude drafts a `draft:true` post → PR), `ai-maintenance.yml` (link/SEO/freshness, Green auto-commits).
- Upgrade VS Code extension to a Claude provider.
- **Deliverable:** idea → AI draft (auto-committed draft) → human review/merge → published, end to end.

### Phase 2 — Idea Vault + Marketing Engine
- `_data/ideas/` + weekly `ai-content-ideas.yml` (5 ranked ideas as an issue).
- `_data/campaigns/` + `ai-repurpose.yml` (on publish → social/newsletter drafts as PR).
- **Deliverable:** continuous backlog feeding the studio; one post → multi-channel drafts.

### Phase 3 — Comms Hub + private data
- Private sibling repo for `clients/leads/proposals`; proposal/SOW generation from `services.yml`; email/follow-up drafting; lead triage from static-form webhook.
- **Deliverable:** brief → proposal draft; meeting notes → action items.

### Phase 4 — Productize for other consultants
- Template repo flag; `create-bash-os` wizard; `ADOPT.md`; the "no hard-coded practice facts" CI assertion; theme-swap docs.
- **Deliverable:** a second consultant can stand up their own instance in under an hour.

### Phase 5 (optional) — Runtime overlay
- Only if hosting moves off pure GitHub Pages: isolated serverless module for visitor chat / semantic search / live lead qualification. Explicitly out of core.

---

## 10. Tech Stack Summary

| Concern | Choice | Notes |
|---|---|---|
| Site | Jekyll + `jekyll-theme-zer0`, GitHub Pages | exists |
| AI models | **Claude** (Opus for hard reasoning/drafting, Sonnet/Haiku for bulk/chores) | model tiering controls cost |
| AI orchestration | **Claude Agent SDK** + Anthropic Messages API w/ **prompt caching** | cache stable instruction context |
| Repo automation | **Claude Code GitHub Action** in `.github/workflows/` | semi-autonomous, PR-routed |
| Local authoring | `tools/bashos` Node CLI + VS Code extension | two surfaces, one prompt library |
| Data store | Markdown + YAML in `_data/` / collections | git = DB + audit log |
| Image gen | existing `preview_image_generator.rb` (OpenAI/Stability) | keep; Claude orchestrates |
| Validation | JSON-schema frontmatter + Jekyll build + prompt evals, all in CI | the deterministic gate |
| Secrets | GitHub Actions secrets + local `.env` | never committed |

---

## 11. Cost, Risk, Metrics

**Cost (rough, solo practice):** dominated by Claude API. With prompt caching + model tiering (Haiku/Sonnet for chores, Opus for hard drafting) and CI agents on schedules rather than constant polling, target **low tens of dollars/month**. Image gen is the only other variable. No infra cost on GitHub Pages.

**Top risks & mitigations:**
| Risk | Mitigation |
|---|---|
| Prompt drift on model upgrades | Eval harness in CI ([§7]) |
| AI publishes something off-brand | Yellow/Red gating + `content-style.instructions.md` + human merge |
| Private client data leaking into public repo/build | Private sibling repo + `_config.yml exclude` + CI secret scan |
| Scope creep / never ships | Strict phasing; Phase 1 alone is independently valuable |
| Vendor lock-in to one model | Thin client abstraction; prompts kept readable/portable |
| Cost surprise | Per-run token budget + caching + scheduled (not constant) agents |

**Success metrics:**
- Time from idea → published post (target: hours, not days).
- Posts/month at house-style quality without manual rewrite.
- % of maintenance handled by Green auto-commits.
- Setup time for a new consultant adopting the template (target: < 1 hour).
- Zero Red-class actions ever auto-committed (audit assertion).

---

## 12. Resolved Decisions

These were the open questions; all five are now decided (2026-06-02) and the plan above reflects them.

1. **Agent docs:** **`AGENTS.md` is the single source of truth; `CLAUDE.md` is a symlink to it.** Zero drift, one canonical file, satisfies tools that auto-load `CLAUDE.md`. (See §3.2, §5.)
2. **CLI language:** **Node/TypeScript.** Shares tooling and types with the existing VS Code extension and has first-class Claude Agent SDK + Anthropic SDK support — one ecosystem, not two. (See §3.2, §5, §10.)
3. **Private data home:** **Private sibling repo** (`bashconsultants-ops`) mounted at `_data/private/` and excluded from the Jekyll build. Cleanest blast radius; client data can never leak into the public site. (See §6.)
4. **Eval depth:** **Start light** — golden-set assertions (valid frontmatter, on-voice tone, required sections) in CI. Upgrade to LLM-graded evals only if model-upgrade drift proves to be a real problem. (See §7.)
5. **Product branding:** **Neutral product name (BASH OS), decoupled from the practice.** Framework code carries zero BASH-specific facts (those live only in `_data/`), so other consultants adopt it without inheriting BASH branding — and it doubles as a clean BASH lead-magnet/product. (See §8.)

---

## 13. Immediate Next Step

If this plan is approved, **Phase 0** is the first PR: scaffold `tools/bashos/` + the Claude client with prompt caching, add `CLAUDE.md`/`.claude/skills/`, write `AUTONOMY-POLICY.md` + blast-radius config, and stand up the eval CI job. That unlocks Phase 1 (Content Studio) without touching any customer-facing content until a human approves it.
