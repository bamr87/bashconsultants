---
name: feedback-recurring-issues
description: Recurring editorial issues across bashconsultants service pages and posts — heading case, acronym placement, duplicate CTAs, unverified vendor quotes
metadata:
  type: project
---

Recurring issues found in bashconsultants content review (first observed on `pages/_services/index.md`, 2026-06-21):

**Why:** These patterns repeat across the service pages and the house style guide forbids them, so they are worth checking on every review.

**How to apply — check each review for:**
1. **Title-case H2s** where the style guide mandates sentence case (e.g. "AI Solutions and Intelligent Automation" should be "AI solutions and intelligent automation"). The same page often mixes title case and sentence case ("How we work", "Get started"), so flag for internal consistency too. Sibling pages (cloud/data/dev/erp/fintech/strat) all violate this — pre-existing, not yet fixed.
2. **Undefined acronyms on first use** (OCR, ETL, KPI, ARM) — guide requires spell-out on first mention.
3. **FAQ duplication** — `faq_items` in frontmatter (drives JSON-LD per commit history) AND a body "Frequently asked questions" section can repeat near-verbatim, risking duplicate content. Decide one canonical home or differentiate.
4. **Description nudging over 155 chars** (160 is hard limit).
5. **Multiple CTAs** vs the "one CTA per page" rule — defensible on a hub page but note the tradeoff.

**Additionally observed in `pages/_posts/erp/` (2026-09-07 update pass):**
6. **Acronyms expanded in the wrong shape or the wrong place** — reversed (`CEO (Chief Executive Officer)`), stuffed into a heading (`(IT — Information Technology — tribe)`), wedged into a character name (`Alex, API (Application Programming Interface) Alex`), or expanded *after* first use (`4GL` used, then defined two sections later). Fix by moving the expansion into the nearest body sentence and leaving the heading/joke clean, or by dropping the acronym entirely when the plain word works.
7. **A second CTA hiding as an HTML button** — `<a href="/contact/" class="btn btn-primary btn-lg px-4">` appended after an in-body CTA wikilink. The lint does not check CTA count, so this must be caught by eye.
8. **A CTA that is not the last link** — a "for the curious, see [vendor docs]" paragraph placed after the Next step. Move the reference up to the section that discusses it.
9. **Quotes attributed to vendor docs that are paraphrases** — always fetch the source page (Microsoft Learn via the `microsoft-learn` MCP) and match verbatim before shipping quotation marks.
10. **Tags that restate the primary category** (`erp` tag on an `erp` post) and **missing `keywords`** on older posts.

**Additionally observed in `pages/_posts/muses/` (2026-09-07 update pass):**
11. **Device labels hiding in the `excerpt`, not the body** — the body enacted cleanly while the card copy described the bit ("A frantic ensemble sings its way around…"). Always read `excerpt` and `sub-title` against the enact-don't-announce rule, not just the body.
12. **A section heading that names the joke** — "The part that isn't a joke", "The song's funniest line is the truest". The pivot from performance to essay needs a heading about the *subject*, not about the performance.
13. **A second CTA disguised as an in-body service-page link** — "which is exactly the shape of work our [data and BI practice](/services/data/) does for…". Swap it for a toolkit-doc wikilink, which reads as a reference instead of a pitch.
14. **A trailing italic invitation after the real CTA** ("*Tired of singing the same chorus on loop? Let's help you step off the wheel.*") — delete it; the Next-step link is the CTA.
15. **`SMB` used before it is expanded** — very common in muses ledes, where the essay opens on metaphor and the first business sentence drops the acronym cold.
16. **An unsourced percentage in an otherwise well-sourced essay** ("often 70–85%") — cut it rather than range it when there is no source at all; the sentence usually reads better without.
17. **Authoring/brief language leaking into prose** — "the thing under your brief". Grep for "brief", "per the prompt", "as requested".
18. **`# comment` lines inside fenced bash blocks look like stray H1s** to naive checks — verify fence state before "fixing" one. All muses shell comments are legitimate.

See [[reference-content-style]] and [[reference-post-standards]] for the authoritative rules.
