---
title: "BASH OS — Autonomy & Blast-Radius Policy"
description: "How semi-autonomous AI changes are classified and gated: Green auto-commits, Yellow opens a PR, Red is draft-only."
status: draft
author: "Amr Abdel-Motaleb"
date: 2026-06-02
lastmod: 2026-06-02
---

# Autonomy & Blast-Radius Policy

This is the human-readable companion to the machine-readable config at
[`tools/bashos/policy/blast-radius.yml`](../../tools/bashos/policy/blast-radius.yml).
Together they make "**semi-autonomous**" ([PLAN.md](./PLAN.md) decision) safe and
auditable: the AI gets speed on chores and gated review on anything a client or
auditor will ever see.

## The three classes

| Class | Meaning | What the AI may do |
|---|---|---|
| 🟢 **Green** | Low-risk, easily reversible, not customer-facing in a published form | **Auto-commit** to a bot branch; auto-merge once CI passes |
| 🟡 **Yellow** | Customer-facing or structurally significant | **Open a PR**; a human reviews and merges |
| 🔴 **Red** | Sensitive: client data, money, secrets, deploy/CI config | **Draft only** — surface for a human; never commit |

### Examples

- 🟢 New post saved as `draft: true`, generated preview image, link/alt-text fix, `CHANGELOG.md` entry, dependency **lock** bump, docs.
- 🟡 Publishing a post (`draft: false`), edits to `about/services/index`, new service pages, marketing copy that goes out, changes to prompts/instructions/skills, layout/theme.
- 🔴 Anything under `_data/private|clients|leads|proposals`, pricing, contracts, sending external comms, `.env`/secrets, `_config*.yml`, `.github/workflows/**`, dependency **manifests** (`Gemfile`, `package.json`).

## How a change is classified

1. **Path match, most-restrictive-wins.** Each changed path is tested against `red` globs, then `yellow`, then `green` (first match wins). If a single changeset touches paths in more than one class, the **whole changeset is escalated to the highest class present**. (One Red file makes the entire change Red.)
2. **Unknown paths → Yellow.** The `default` is `yellow`, never `green`. New, unclassified paths are never auto-committed.
3. **Unpublished condition.** Posts under `pages/_posts/**` are Green **only while `published: false`** (Jekyll-native, build-excluded). Promoting to `published: true` (or removing it) is the act of publishing and reclassifies the change to Yellow. ⚠ In this repo `draft: true` is *decorative* — Jekyll still publishes it — so the real gate is `published: false`, not `draft`.
4. **Secret backstop.** If the diff's *added lines* match any `secret_patterns` (e.g. `sk-…`, `ghp_…`, `AKIA…`, private-key blocks), the change is force-escalated and blocked from auto-commit regardless of path. This complements AGENTS.md rule #5.

## Enforcement points

| Where | How |
|---|---|
| **`bashos` CLI** (local + headless) | Reads the config, classifies the working-tree diff before any commit, and refuses to auto-commit anything above Green. |
| **CI agents** (`.github/workflows/ai-*.yml`) | Route output by class: Green → commit + auto-merge; Yellow → open PR; Red → fail the job and post the draft as a comment/artifact for a human. |
| **GitHub branch protection + CODEOWNERS** | Backstop the policy in the platform: Yellow/Red paths require human approval by configuration, not goodwill. (Set up in Phase 1.) |

## Audit

Every AI-authored commit records, in its body, the prompt/skill used, the model + version, the inputs, and the resulting class. This makes each action reproducible and defensible — git is the audit log ([PLAN.md §7](./PLAN.md#7-governance--trust-layer)).

## Changing the policy

The policy config lives under `tools/bashos/policy/` and is itself a **Yellow** path
(it sits under the framework, not `_data/`) — edits to it go through PR review. Tighten
freely; loosen deliberately. When in doubt, a path belongs in a more restrictive class.
