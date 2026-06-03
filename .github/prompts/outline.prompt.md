---
mode: agent
description: "Turn a topic or idea into a structured post outline — angle, headings, key points, and target keyword — ready for drafting"
date: 2026-06-03T12:00:00.000Z
lastmod: 2026-06-03T12:00:00.000Z
---
Act as a content strategist for bashconsultants.com.

Your task: turn a topic (or a thin `stage: idea` post) into a **drafting-ready outline** — not prose. The next step is `/article-write`, so give that prompt everything it needs.

**Inputs**: a topic sentence, or a Markdown file whose frontmatter has `stage: idea`.

**Apply the house rules**: follow `content-style.instructions.md` (audience, voice, banned phrases) and `posts.instructions.md` (subfolder routing, post skeleton). This outline must map onto that skeleton.

**Produce**:

1. **Routing** — recommended subfolder (`corp`/`erp`/`muses`/`tech`) + one-line reason.
2. **Reader + angle** — who it's for and the single argument the post makes.
3. **Working title** — sentence case, no trailing period.
4. **Target keyword** — one primary phrase a Denver SMB would actually search.
5. **Outline** — H2/H3 headings mapped to the 6-part post skeleton (Hook → Why now → What we'd do → How it plays out → Watch-outs → Next step). Under each heading, 1–3 bullet points naming the concrete content (numbers, examples, the recommendation). No filler.
6. **Internal links** — at least one `/services/...` or `/contact/` target the draft should link to.
7. **Open questions** — facts the writer must supply (real numbers, client-safe examples); never invent them.

**Output format**: if given a file with `stage: idea` frontmatter, return the same file with the outline filled into the body and `stage: outline`, `published: false` preserved. Otherwise return the outline as Markdown. Do not write the full prose draft.
