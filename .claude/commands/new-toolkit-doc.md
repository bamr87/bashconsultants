---
description: Scaffold a new BASH toolkit doc (business or partner track) with correct frontmatter and nav wiring
argument-hint: "<business|partners> \"<Title>\" [topic]"
allowed-tools: Read, Write, Edit, Bash(python3 scripts/content_lint.py:*)
---

Create a new toolkit doc following the **`toolkit-doc`** skill. Arguments: `$ARGUMENTS` — `<track> "<Title>" [topic]` where track is `business` or `partners`.

**Do this:**

1. Read the `toolkit-doc` skill and an existing sibling in the same track as a template (e.g.
   `pages/_toolkit/qualification.md` for partners).
2. Create `pages/_toolkit/<slug>.md` with complete frontmatter: `categories: [<track>]` (drives the
`/tools/<track>/<slug>/` URL), a fitting `topic`/`topic_label` (reuse an existing one — check the track landing page), `level`, `order`, `author: "Amr Abdel-Motaleb"`, `description` 120–155 chars, `lastmod` today, `sidebar: nav: toolkit`, `permalink`.
3. Draft the body to the track's audience — business: plain-language, ROI/risk-first; partners:
senior-practitioner depth under the BASH doctrine. Obey the `content-editorial` and `wikilinks` skills (pipeless `[[Title]]`, root pages via markdown, one H1, sentence-case headings).
4. Wire a sidebar entry into `_data/navigation/toolkit.yml` under the correct track group.
5. Validate: `python3 scripts/content_lint.py` (repo-wide gate; zero errors in the new doc), then
   confirm the build and that the doc surfaces in its topic group on the track landing page.

If the topic or level is ambiguous from the arguments, ask before inventing a new topic group.
