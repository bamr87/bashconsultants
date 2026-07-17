---
name: linkedin-share
description: Draft on-brand LinkedIn company-page commentary for a blog post or a standalone update, and stage it for human approval. Use when composing anything that will publish to the BASH company page via scripts/features/linkedin.
---

# LinkedIn share drafting

The governed way to write copy for the BASH Consulting company page (`urn:li:organization:64517157`). The publisher (`scripts/features/linkedin`) is mechanical; **the judgment is here.** Agents draft, a human approves by merging the draft, and only then does it post — the same rules-in-files, humans-approve model the site sells. Follow this in order.

## Sources of truth (read, don't restate)

- **Brand / identity:** [`.github/instructions/brand.instructions.md`](../../../.github/instructions/brand.instructions.md)
- **Voice + mechanics:** [`.github/instructions/content-style.instructions.md`](../../../.github/instructions/content-style.instructions.md)
- **Section voice profiles:** [`_data/taxonomy.yml`](../../../_data/taxonomy.yml) — corp / erp / muses / tech
- **The publisher + queue format:** [`scripts/features/linkedin/README.md`](../../../scripts/features/linkedin/README.md)

## What LinkedIn adds on top of the house style

Everything in `content-editorial` still applies (no banned phrases, acronyms expanded on first use, enact-don't-announce, no invented metrics/clients/certs, US English, no exclamation marks). LinkedIn-specific rules:

- **Commentary is the hook above the card, not the card.** For an article share
the card already shows the post title + description — do **not** restate the description. Write 2–4 sentences that give someone a reason to click.
- **Front-load the first ~140 characters.** LinkedIn truncates with "…see more";
  the payoff must land before the fold.
- **Length:** hard max 3000 characters; aim for ~600–1200. Shorter reads better.
- **Exactly one call to action**, pointing at the reader's next step. For an
article the card is the link, so the CTA is a soft "read it / here's why it matters," never a second URL dump.
- **2–3 hashtags**, CamelCase, business-relevant (`#SmallBusiness #ERP #AI`).
  No hashtag walls. Acronym tags stay upper-case.
- **Voice matches the post's section** (see `taxonomy.yml`): corp = owner/CFO
  register, erp = back-office wry, muses = essayistic, tech = practitioner.
- **Never invent.** Describe categories of work and what frameworks require;
  never claim BASH is certified, and never fabricate a result or client.

## Procedure

1. **Resolve the target.** For an article, load the post under
`pages/_posts/<section>/` and note its `title`, `description`, `sub-title`, `tags`, and section. For a standalone update, take the topic from the caller.
2. **Draft the commentary** to the rules above, in the section's voice.
3. **Write the draft file** to `drafts/linkedin/YYYY-MM-DD-<slug>.md` (this dir
   is git-tracked but excluded from the Jekyll build). Frontmatter + body:
   ```
   ---
   type: article            # or: update
   source: <section/YYYY-MM-DD-slug>   # article only; omit for update
   status: pending          # never publish until a human sets this by merging
   title: "<post title>"    # informational, for the reviewer
   url: <canonical URL>     # informational
   ---
   <the commentary — this body is exactly what posts to LinkedIn>
   ```
4. **Preview it** with the publisher's dry-run — it renders the exact payload and
   runs the mechanical brand guard (banned phrases, length):
   ```bash
   python3 scripts/features/linkedin from-drafts --dry-run
   ```
   Fix anything the guard flags. The commentary body must be clean.
5. **Hand off for approval.** The draft sits at `status: pending`. A human edits
and **merges** it; the publish workflow (or `from-drafts` live) posts it and flips it to `published`. Do not post from this skill.

## Guardrails

- One `status: pending` draft never becomes a live post without a human merge.
- The mechanical guard is a floor, not the ceiling — it can't see voice, an
  invented claim, or a second CTA. Read the draft as the reviewer will.
- The final voice pass on anything customer-facing is done with Opus 4.8.
