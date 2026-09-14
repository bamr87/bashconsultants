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

**Additionally observed in `pages/_posts/muses/` (2026-09-14 review of the "relics" essay):**
19. **The preview image is the most-missed pre-publish item.** `content_lint.py` does NOT check that the file at `preview:` exists, and only ~25 images live in `assets/images/previews/`. Always run `ls assets/images/previews/ | grep <slug>` by hand; a brand-new post almost always needs `./scripts/generate-preview-images.sh`. The slug is derived from `title:` (lowercase, non-alphanumeric runs → `-`, truncated to 50 chars) — verify it matches the frontmatter string exactly, since a retitle silently orphans the image.
20. **An acronym trapped inside a wikilink title cannot be expanded in place** — e.g. `[[Integration architecture: APIs, events, legacy]]` renders "APIs" as reader-facing text but the title must match byte-for-byte. Fix by expanding the term in the lead-in sentence before the link, never by editing the bracket text.
21. **Partial quotes that don't complete the introducing verb.** e.g. `NASA noted "consulting original, decades-old documents…"` — you cannot "note consulting". Re-cut the quote so the introducing clause and the quoted fragment form one grammatical sentence, and check it against the source's own sentence.
22. **Verbatim quotes shipped without quotation marks**, usually when the quote is also the link anchor. If the phrase is word-for-word from a source, it takes quotation marks even when linked. Also keep the trailing period *outside* the link.
23. **A source under-read in the essay's own favor.** The essay said "several" where GAO said "eight of the 11" — the harder number was already in the cited document. When a claim is hedged, re-read the source: the stronger, still-accurate number is often free.
24. **Repeated concrete details inside one paragraph** ("launched in 1977" … "left Earth in 1977" two sentences later). Common in long multi-example paragraphs; also a signal the paragraph should be split, since the style guide's reader is on mobile.
25. **Meta self-reference to the piece** — "Here is the claim this essay rests on", "the reason is this essay in one line". Not a banned device label, so the lint and the enact-don't-announce rule both miss it, but it flattens the muses register. Cut or recast as a plain assertion.
26. **Register drift inside muses:** a contraction-free body ("it is", "we will", "cannot") reads stiffer than the section's siblings, which use contractions freely. Worth raising as a judgment call, especially in the CTA.
27. **Apparent internal contradictions from technically-correct precision** — "the same decree in three scripts … a bilingual artifact" (the Rosetta Stone is three scripts, two languages). Add the half-clause that resolves it rather than dropping the precise word.

**Muses ending convention has shifted (observed 2026-09-14):** the Jun-2026 muses closed with an italic `*At BASH Consulting we…*` sign-off; the Aug-2026 and later muses (`best-practice-is-the-interest-of-the-stronger`, `your-best-programmer…`) use a `## Next step` H2 + a descriptive imperative anchor to `/contact/` and never name BASH in the body. Referring to the firm as "this practice" is on-convention, not a gap — do not flag it.

See [[reference-content-style]] and [[reference-post-standards]] for the authoritative rules.
