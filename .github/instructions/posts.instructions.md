---
applyTo: "pages/_posts/**/*.md"
description: "Blog post standards for bashconsultants.com — frontmatter, voice, and SEO rules for the _posts collection"
date: 2026-05-18T12:00:00.000Z
lastmod: 2026-06-03T12:00:00.000Z
---

# Blog Post Instructions

Posts live in `pages/_posts/` and are organized by subfolder (`corp/`, `erp/`, `muses/`, `tech/`). They render via the `article` or `news` layout.

> **Voice, audience, banned phrases, and universal checklist** → see [`content-style.instructions.md`](content-style.instructions.md). This file covers post-specific rules only.

## Subfolder routing

| Subfolder | Topic | Typical reader |
|---|---|---|
| `corp/` | Corporate IT, governance, vendor strategy | SMB owner / CFO |
| `erp/` | ERP, financial systems, QuickBooks-to-X migrations | Controller, operations manager |
| `muses/` | Opinion, industry commentary, longer-form | Mixed |
| `tech/` | How-tos, vendor walk-throughs, architecture notes | In-house IT lead |

If a post doesn't fit, default to `tech/` and revisit at next site audit.

## Required frontmatter

```yaml
---
title: "Sentence-case title, no trailing period"
description: "120–155 chars. One sentence. Business outcome first, tech second."
author: "Amr Abdel-Motaleb"   # or a real contributor name
layout: article                # or "news" for the news index
date: YYYY-MM-DDTHH:MM:SS.000Z
lastmod: YYYY-MM-DDTHH:MM:SS.000Z
draft: false
categories: [Category]         # YAML list, never bare string
tags: [tag1, tag2]             # YAML list
preview: /images/previews/<slug>.png
---
```

## Filename

`YYYY-MM-DD-kebab-case-title.md` under the appropriate subfolder. Date in filename must match `date:` in frontmatter.

## Post-specific structure

A typical post should follow this skeleton (skip sections that don't apply, don't pad):

1. **Hook** — 1–2 sentences naming the problem in the reader's language
2. **Why it matters now** — cost, risk, or opportunity, with a real number when you have one
3. **What we'd actually do** — the recommendation, in plain terms
4. **How it plays out** — phased approach, timeline ranges, what the reader's team has to do
5. **Watch-outs** — the 2–3 things that go wrong in practice
6. **Next step** — link to the relevant `/services/...` page or `/contact/`

## Content Studio pipeline (optional)

Posts authored through the BASH OS Content Studio carry two extra fields:

- `stage:` — pipeline position (`idea`→`outline`→`drafting`→`review`→`seo`→`scheduled`→`published`). See [`_data/pipeline.yml`](../../_data/pipeline.yml).
- `published:` — **Jekyll-native build flag.** `published: false` excludes the post from the build (genuinely not live); `published: true` (or omitting it) puts it live. This is the real publish gate, **not** `draft:`.

> ⚠ `draft: true` is **decorative** here — Jekyll still builds and publishes it. To keep an in-progress post off the live site use `published: false`. Promoting to `published: true` is the human-gated (🟡 Yellow) act; see [`docs/ai-framework/AUTONOMY-POLICY.md`](../../docs/ai-framework/AUTONOMY-POLICY.md).

## Hard don'ts

- Don't set `published: true` (or remove it) on an in-progress post — that puts it live. Keep `published: false` until a human approves.
- Don't reference internal URLs that don't exist; verify with the local build.
- Don't include literal API keys, even as examples — use `${env:VAR}` placeholders.
- Don't bump `date:` on edits — bump `lastmod:` instead.
- Don't write "thought leadership" posts with no recommendation or next step.

## Before commit

- [ ] Subfolder matches topic table above
- [ ] Universal checklist in `content-style.instructions.md` passes
- [ ] Post links to at least one service page or `/contact/`
- [ ] `lastmod` updated
- [ ] Build passes locally
