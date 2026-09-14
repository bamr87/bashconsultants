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

**Additionally observed in `pages/_posts/muses/` (2026-09-14, "IT is the new finance department"):**
19. **A wikilink introduced with structural scaffolding that names the wrong section** — "already written down in this section: [[The AI audit trail…]]" where that post is `categories: [erp, ai]`, not muses. Two faults at once: the claim is false, and the siblings never scaffold a link (they inline it: "which is the route [[…]] walks through step by step"). Always check the linked doc's own `categories:`/folder before a post says "in this section" / "elsewhere in this series".
20. **Regulatory claims that omit "public company"** — a Sarbanes-Oxley / Section 404 / ICFR sentence written as if it applied to every audited company. SOX 404 and PCAOB IT-general-controls testing reach SEC registrants; private SMBs meet the same logic through cyber-insurance questionnaires and customer due diligence, not statute. Scope the sentence; it also reads better.
21. **An "actually" tic** — 5 uses in 1,866 words. Keep the ones doing real work (actual-vs-nominal: "who *actually* does", "one backup is *actually* restored", "what's *actually* on the card statements"); cut the filler ones ("where its power actually comes from").
22. **A chiasmus that eats its own tail at the essay's climax** — "a function that can see everything deserves to be run like one that can." The muses closer is the highest-leverage sentence in the piece; if a mirrored construction doesn't resolve its predicate, replace it rather than tune it.
23. **Expanding an acronym inside a possessive** — "a managed service provider's (MSP's) ticket queue". Recast so the expansion sits in a plain noun phrase: "the ticket queue of a managed service provider (MSP)".
24. **Rhetorical specifics that read as data** — "on corporate cards in six departments", "it takes a week to build and an hour a month to keep true". House style wants ranges when there is no audited number, even when the figure is obviously illustrative.

See [[reference-content-style]] and [[reference-post-standards]] for the authoritative rules.
