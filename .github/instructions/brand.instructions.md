---
applyTo: "pages/**/*.md,index.md,about.md,contact.md,tools.md,ai-operations.md,_layouts/**,_includes/**,assets/brand/**,.claude/**"
description: "The BASH brand — name, mission, voice, colors, logo, and doctrine — the single source of truth every agent and author follows"
date: 2026-07-07T12:00:00.000Z
lastmod: 2026-07-07T12:00:00.000Z
---

# The BASH brand

This is the **single source of truth** for who BASH is and how it presents itself. When copy, a layout, an asset, or an agent has to make an identity decision, it is made here — not from memory and not per-page. Editorial mechanics (banned phrases, SEO limits, formatting) live in [`content-style.instructions.md`](./content-style.instructions.md); this file is the layer above it: what the brand *is*.

## Name and etymology

- **BASH Consulting** — trading name of the practice. Also written **BASH Consultants**.
- **BASH** expands to **Bourne Again Solutions Hero** — a deliberate play on the Unix **Bourne Again
SHell** (`bash`), the tool that turns typed intent into executed work. The name says the thing the firm does: it is where a business's terminal-level intent becomes real, running systems.
- **Capitalization:** the brand is **BASH** in full caps. The shell is lowercase `bash` in
monospace. Never write the brand as "Bash" or "bash". "BASH Consulting" on first mention; "BASH" thereafter.
- **Founder:** Amr Abdel-Motaleb (BS Finance, MS Information Systems), Denver, Colorado. He is the
  author byline on all content: `Amr Abdel-Motaleb`.

## Mission and positioning

**Mission.** Bring enterprise-grade IT — cloud, Enterprise Resource Planning (ERP), customer and asset management, data architecture, and an AI overlay — within reach of small and medium businesses (SMBs) that were priced out of it. People over profits: we scope honestly, tell a client when something is not a fit, and build systems a business can own and leave with.

**Positioning line (canonical).** *Enterprise-grade IT for small business — cloud, ERP, data, and AI-augmented automation, from Denver, Colorado.*

**Who we serve.** Owners, operators, and in-house IT leads at SMBs (roughly 5–200 staff), Denver metro first, remote across the United States. Full reader profile in `content-style.instructions.md`.

## The doctrine (what makes the brand coherent)

Every page, service, and internal tool should be legible as an expression of four commitments. They are the through-line partners are held to and clients are sold on.

1. **Deterministic foundations first, AI as an overlay — never the load-bearing wall.** If a step can
be a script, it is a script. The model is spent where judgment is genuinely needed. Deterministic steps fail loudly and predictably; keep them under anything a model touches.
2. **Governed, not improvised.** Rules live in files, recurring work runs from versioned playbooks,
automation checks work before it ships, and a named person approves anything customer-facing. This repository is the reference implementation — see [`/ai-operations/`](../../ai-operations.md).
3. **Build in the open; own what you build.** Systems are documented, inspectable, and portable so a
   client is never locked in — to a vendor or to us. Partners demonstrate this in public.
4. **Easy but hard.** The door is open to anyone; the bar is the best work. This is the ethos behind
the partner path ([`/tools/partners/qualification/`](../../pages/_toolkit/qualification.md)) and the tone of everything: welcoming at the entrance, uncompromising on quality.

## Verbal identity

Voice mechanics are governed by `content-style.instructions.md` (confident-not-boastful, plain English first, active voice, lead with the business outcome, one CTA, enact-don't-announce). The brand layer adds:

- **We are a practitioner, not a platform.** Write from experience — "we've migrated dozens of
  QuickBooks shops" — never from hype. No "revolutionary", "cutting-edge", "world-class".
- **Terminal literacy is part of the personality.** The `bash` motif can surface lightly and
knowingly (a prompt, a command, a shell metaphor) where it earns its place — never as costume, and never at the expense of a reader who does not live in a terminal.
- **Finance + IT is the differentiator.** Speak both languages: close, consolidation, AR/AP, TCO on
  one side; landing zone, integration, RPO/RTO on the other. That dual fluency is the brand's edge.
- **Never claim** certifications, headcount, client logos, revenue, or awards. Describe *categories*
  of work and what compliance frameworks *require*; never claim BASH is certified.

## Visual identity

The theme (`bamr87/zer0-mistakes`, skin **`aqua`**) carries typography and layout — do not override it mid-page. The brand-specific assets and values:

### Logo

- Canonical mark: [`assets/brand/favicon.svg`](../../assets/brand/favicon.svg) (masthead + favicon).
- Logo library: [`assets/brand/logo/`](../../assets/brand/logo/) — the **B** mark and full BASH
  wordmark in versioned variants. Prefer the latest `v2` files.
- Standards (sizes, clear space, layouts): [`assets/brand/logo-standards.txt`](../../assets/brand/logo-standards.txt).
- Never stretch, recolor, or add effects to the mark. On busy imagery, use the mark on a solid chip.

### Color

The **logo palette** is the brand's identity color set; the **theme palette** carries the UI. Keep them distinct — do not repaint the UI in logo colors or vice versa.

| Role | Name | Hex |
|---|---|---|
| Logo — primary | Red | `#a11111` |
| Logo — accent | Yellow | `#ffe900` |
| Logo — deep | Teal | `#376986` |
| UI — primary (theme) | Blue | `#007bff` |
| UI — muted (theme) | Secondary gray | `#6c757d` |

Full UI ramp lives in `_config.yml` under `theme_color:` (hex values **must** stay quoted — an unquoted `#` starts a YAML comment and parses to null). The logo palette is mirrored in [`assets/brand/color_scheme`](../../assets/brand/color_scheme).

### Imagery

- Article and page banners are **AI-generated** from each piece's own title and description by the
preview pipeline (`scripts/generate-preview-images.sh`), then stored under `assets/images/previews/`. Regenerate after a title changes — the image derives from it.
- Alt text describes the *content* of an image, never "banner" or "screenshot of…".
- Prefer SVG for diagrams, PNG for screenshots. Diagrams (Mermaid) inherit theme colors.

## Where the brand lives (practice what we preach)

The brand is a set of files, not a memory. Change it in one place and everything inherits the change:

| Brand element | File of record |
|---|---|
| Name, mission, voice, doctrine (this doc) | `.github/instructions/brand.instructions.md` |
| Editorial mechanics | `.github/instructions/content-style.instructions.md` |
| Identity + positioning strings, `powered_by`, socials | `_config.yml` |
| Logo + favicon + palette assets | `assets/brand/` |
| Section voice profiles | `_data/taxonomy.yml` |
| Public statement of the operating model | `ai-operations.md`, `pages/_toolkit/` |

**Before shipping identity-bearing work,** run the `brand-guardian` agent or `/brand-check`. It reads this file and reports drift.
