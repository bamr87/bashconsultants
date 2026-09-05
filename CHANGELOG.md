# Change Log

All notable changes to the BASH Consultants repository will be documented in this file.

Check [Keep a Changelog](http://keepachangelog.com/) for recommendations on how to structure this file.

## [Unreleased]

Platform transformation: activated the site's dormant AI capabilities, wired the dead conversion paths, added CI quality gates, and expanded the content and services catalog.

### Added
- **Constellation, the particle engine behind the hero, opened into a framework** — `assets/js/constellation.js` (replacing `bash-mark.js`) renders any shape as the same interactive light. **Sources** turn something into star targets: `svg` (any inline or fetched SVG — filled paths with `data-shape="hole"` cut-outs, stroked paths at their stroke width, and basic shapes), `text` (any string in any font), `terminal` (a scripted shell session typed live, glyph by glyph, with roles for prompt/input/output/error colors and a blinking cursor), `points` (a 3D point cloud from inline data, a JSON URL, or the built-in `sphere`/`torus`/`helix`/`cube` generators), and `image` (a same-origin image sampled by alpha); `Constellation.registerSource()` adds more. **Scenes and timelines are YAML** under `_data/constellations/`, rendered by `_includes/constellation.html` (stage `size`, `aspect`, `shape`, `fallback`, `label`, `hint`), so animations are designed as data and reviewed in a diff; a timeline morphs the same stars from scene to scene, and stars a scene does not need wait as background dust the next scene recruits. **Every presentation and interaction knob is configuration**: palette and weights, per-kind sizes and alphas, twinkle, jitter, `soft`/`point` glow, halo, backdrop stars, camera, idle spin and nod, star spring/damping, drag and keys, the pointer-speed hover physics, and a new **click shockwave** (an outward pop under the click, then a travelling ring that pushes stars as it passes and flashes them; Enter or Space fires it from the keyboard). Ships with five scene files (the mark, a typed terminal session, text, a helix, and a mark → terminal → torus timeline), `scripts/sample_mesh_points.py` (samples a Wavefront OBJ surface uniformly by area into a point-cloud JSON, deterministic, stdlib only), and a partner-track toolkit doc with live demos and the full reference at `/tools/partners/constellation-engine/`.
- **Interactive B-mark hero** — the homepage hero is now the BASH mark rendered as a rotating cloud of a few thousand glowing particles (`_includes/bash-mark.html`, now a thin wrapper over the constellation engine), in the spirit of the draggable logo on OpenAI's GPT-6 Astra page. Drag turns it, and a flick keeps it spinning with inertia; a hovering pointer scatters the nearby particles with a small physics model (each particle has a velocity, a spring home, and damping): a resting pointer only dents the mark, a fast sweep hits harder, reaches wider, and flings particles along its direction of travel, a quick swipe nudges the turn, and the letter springs back into shape over a few seconds with a little overshoot, all in the mark's own space so a dent turns with it; the arrow keys turn and tilt it for keyboard users (Home resets); it turns gently on its own when idle and pauses when scrolled out of view or in a background tab. Dependency-free: a 2D canvas, `Path2D` hit-testing to scatter particles inside the mark's outline (denser and brighter along the edge), a thin extrusion so the turn has depth, and additive-blended glow sprites, which also removes any need to depth-sort. Deterministic by design — a seeded generator means every visitor sees the same constellation and screenshots are reproducible. Honors `prefers-reduced-motion` (renders once, moves only on input), keeps the static mark as the no-JavaScript fallback, labels the drag surface for assistive tech, and lets vertical touch drags scroll the page. Colors are the logo palette read from `theme_color` in `_config.yml`, so the brand's file of record stays the single source of truth. Verified in headless Chromium: drag, keyboard, idle spin, reduced motion, mobile, and no-JS paths, with no console errors.
- **`scripts/generate_mark_shape.py`** — generates `_includes/brand/mark-shape.svg`, the geometry the hero's svg source samples, from the canonical `assets/brand/favicon.svg` by Inkscape label (`outer-B`, `inner-c`, and the layer's translate), so the outline is never hand-copied and cannot drift from the mark; `--check` fails when the include is stale.
- **The content loop** — the site's own autopilot, modeled on the lifehacker.dev harness and rebuilt in this repo's idiom: a daily, variable-gated routine (`.github/workflows/content-loop.yml`, OFF until the `CONTENT_LOOP_ENABLED` repo variable is `true`) that turns the practice's own recent work into **one new article every other day** and **one improvement to an existing page on the days between**. Ideas are mined, not brainstormed: `scripts/loop/signals.py` groups this repository's commits into stories by the `Claude-Session:` trailer, by pull request, or by day, marks AI-assisted work by its `Co-Authored-By: Claude` trailer, pulls in CHANGELOG lines and the committed AI-session trace, and (best-effort, read-only) the sister repositories in `_data/loop/sources.yml`; `scripts/loop/plan.py` decides new / improve / idle deterministically from the ledger (`_data/loop/runs/`, one record per run), honors an open-PR backpressure cap, rotates the four post sections most-overdue first, and boosts improve candidates whose subject the recent work touched. The writer — the `loop-writer` agent following the `content-loop` skill — reads the story's diffs for real, translates it for the SMB reader in the section's voice, gates it with the existing scripts, records the run, and opens ONE pull request; a human merges. A `SessionEnd` hook (`.claude/hooks/session-trace.sh` → `scripts/loop/trace.py`) records each Claude Code session's intent, files, and commits as scrubbed metadata in a local queue that `trace.py --sync` folds into `_data/loop/sessions.jsonl` for a human to commit. `/loop-run` runs a cycle by hand. While the loop is enabled the weekly gardener and content-review schedules stand down (manual runs still work). Every script is stdlib-only with a `--self-test`. Operator's guide: `docs/content-loop.md`.
- **Two new muses essays** — "Your best programmer thinks they're just good at Excel" (2026-08-15), on the load-bearing spreadsheet as unmanaged production software and its maintainer as an unrecognized programmer, and "Best practice is the interest of the stronger" (2026-08-19), reading vendor "best practice," case studies, and lock-in through Thrasymachus's argument in Plato's Republic. Preview banners to be generated before the posts' dates.
- **Author profiles on every post** — `_data/authors.yml`, the data file the theme's author card and "About the Author" box read. `remote_theme` does not ship `_data/`, so with the file missing every post byline rendered a bare name string, a generic person icon, and no bio; the "About the Author" block at the foot of each article was an empty shell. Adds entries for the two bylines actually used (`Amr Abdel-Motaleb`, `BASH Consulting Team`) — role, tagline, bio, location, headshot, GitHub/LinkedIn links, and expertise chips — every value taken from the repo's own identity files (`pages/_about/organization/amr.md`, `_data/entity/info.yml`, `brand.instructions.md`), with nothing invented. Because posts are bylined by display name, the `name:` values must stay byte-identical to the front-matter strings.
- **`.theme-overrides.yml`** — declares the four files that intentionally shadow the zer0-mistakes theme (the bespoke `landing.html`, the no-op Google Tag Manager stub, the PostHog privacy fork, and our own `wizard-on-journey.png`), each with a reason, so the theme's `audit-consumer` reports real drift instead of four false positives. The PostHog entry carries an `upstream:` retirement note; `CLAUDE.md` now points at this file as the source of truth for overrides.
- **New partner-track toolkit doc: "Google Workspace to Microsoft 365 migration"** (`pages/_toolkit/google-workspace-to-microsoft-365.md`, `/tools/partners/google-workspace-to-microsoft-365/`) — an advanced reference for the manual Google Workspace to Exchange Online mailbox migration, the first Cloud-topic partner doc since the landing zones guide. Covers the two-routing-subdomain model that makes the staged migration recoverable (with a mermaid diagram of the mid-migration routing state), the Google-side service account/API/domain-wide-delegation setup, the three-address shape every mail user needs, the batch and completion flow in the new Exchange admin center, and the failure modes that only surface after a batch starts (the 30-day license window, MRM policies faking data loss, blocked forwarding permissions, propagation windows). Adds a read-only pre-flight for establishing where mail actually flows before planning anything, a "when this is the wrong tool" section (single mailbox, or an MX record that already moved), and a scripted Exchange Online PowerShell pre-flight that generates the batch CSV from tenant state and fails loudly on malformed mail users, per the deterministic-first doctrine. Every claim cites a verified-live Microsoft Learn or Google primary source; wired into the toolkit sidebar nav.
- **Toolkit doc hardened against a real failure, with redacted screenshots** — the Google Workspace guide documents a live diagnosis rather than only the happy path. Corrects a widely-repeated misreading of Microsoft's docs: `https://www.google.com/m8/feeds/` is a legacy **alias** for `auth/contacts` (Contacts API turned down 2022-01-19), so Google silently dedupes it and Microsoft's five-entry example string stores only four grants — meaning a four-scope list is the correct end state and Microsoft's "verify four" instruction is right, not a trap. Adds guidance to verify scopes by name rather than by count; a decode of `TooManyTransientFailureRetriesPermanentException` wrapping `SyncProviderTokenUnexpectedInvalidationException`; a "try the free action first" rule (`Resume migration` before minting keys or switching tools, noting it sits beside `Complete migration batch` and `Delete` in the same toolbar); and a failure mode noting that a batch-level `Failed` can sit atop a mailbox-level `Perfect`/0-skipped copy that resume continues incrementally. Four redacted screenshots under `assets/images/toolkit/` with content-describing alt text, each documenting a step actually performed: the stored delegation scope list, the Edit-scopes dialog (whose one-scope-per-row storage explains the alias dedupe), the per-mailbox failure report, and the batch back in `Syncing` after a resume. Captured by CSS-masking identifiers *before* the screenshot so unredacted pixels are never written, then re-read and confirmed visually.
- **Toolkit doc: the real root cause of `SyncProviderTokenUnexpectedInvalidationException`, from a completed migration** — the Google Workspace guide now names the actual fault behind the failure it documents, established by running the migration to completion rather than by inference. A Google API that is **not enabled in the Cloud project** is rejected at the *service-usage* layer with `SERVICE_DISABLED` (HTTP 403) before the request reaches the API — and Exchange surfaces that 403 as a token-invalidation error. So a disabled **People API** (which now serves contacts; the old Contacts API was turned down 2022-01-19), with a valid key and correct scopes, presents as an authentication failure that no amount of credential auditing will explain. Compounding it, the Cloud console's error graph for that API reads **zero errors**, because an API that is not enabled has no metrics to populate — a clean dashboard is not evidence of healthy calls. Replaces the previous credential-first triage with an ordered five-step table that puts **API enablement first** and credentials last, and adds: how to read the per-user report (`Migrating <sub-providers>` names every provider whose failure kills the whole job; `Copy progress` *denominators* — `0/0 messages` disproves any bad-message theory; `retry (N/60)` is a fixed ceiling, not a measurement); how to bisect by **content type** rather than folder, noting the folder filter constrains Mail only and so cannot test anything else; and a correction that `Syncing` status is not proof a resume worked — only climbing `Data migrated` and `folders completed` are, since a batch can sit in `Syncing` transferring zero bytes indefinitely. Adds a redacted screenshot of the Cloud console showing an `Enable` (not `Manage`) button as the unambiguous tell. Also tempers the scope section: a correct four-scope list is the normal case and rarely the fault, so verify by name and move on to API enablement.
- **Toolkit doc: the MX-target trap, and the principle underneath both failures** — the Google Workspace guide now documents a second production failure found by running the migration to completion: a tenant-generated MX record whose target hostname does not exist. The admin center publishes `<domain-with-hyphens>.mail.protection.outlook.com`, marks it `OK`, reports the domain **Healthy** — and the hostname returns `NXDOMAIN` from every public resolver, so all inbound internet mail defers for ~24 hours and then bounces. **Internal tenant-to-tenant mail keeps working perfectly** because intra-tenant delivery never performs an MX lookup, which is exactly what hides it: the obvious test (mailing the address from another account in the same tenant) passes. The tell is a message trace with plenty of traffic to the tenant's other addresses and none at all to the affected domain. Adds MX-target resolution across multiple resolvers to the read-only pre-flight (the previous version checked the record but never resolved what it pointed at), a new pre-flight finding for the NXDOMAIN case, and a full failure mode covering why `Check health` misses it, why the admin center refuses to add or edit an MX while Exchange is enabled for the domain (and why accepting its "disable the Exchange service" suggestion is the wrong trade — it converts deferred mail into permanent bounces), and the safe repair: move DNS to a provider you control, rebuild the zone **before** switching nameservers, then flip once. Notes that a dormant registrar zone is often years stale and may still carry the *source* provider's MX records, which would silently route mail back to the system just migrated away from. Also frames the principle both failures share — **confirming a setting exists is not confirming it works**: a scope can be granted against a disabled API, an MX can name a server that does not exist, and a vendor console reports `OK` for both.
- **Domains & email runbook** — `docs/domains-and-email.md`, the internal ops doc for the M365 tenant: the domain portfolio (DNS lives on Microsoft's own `bdm.microsoftonline.com` nameservers, managed in the admin center — not Squarespace/Google), the one-mailbox-two-addresses email architecture (`amr@bash-365.com` primary, `amr@bashconsultants.com` receiving alias), and the 2026-08-10 MX outage post-mortem: Microsoft decommissioned `bashconsultants-com.mail.protection.outlook.com` (NXDOMAIN globally) while the tenant's expected records and health check still reference it, silently killing inbound mail to the legacy domain. Documents the standing workaround (custom priority-10 MX → the tenant's live `bash365-com01b` endpoint — do not remove until Microsoft re-provisions), the new `bash-365.com` DMARC record, the Conditional-Access gotcha for admin scripting (device-code auth blocked; use interactive), and the legacy-Google-records cleanup backlog.
- **Favicon config block** — `favicon:` in `_config.yml` (ico + brand SVG) for the zer0-mistakes theme's new config-driven `core/favicon.html` include. Inert on the pinned v1.26.0 theme; activates on the next pin bump. The root `favicon.ico` keeps serving via the browser's implicit probe meanwhile.
- **Privacy policy page** — `privacy.md` (`/privacy/`), an honest, plain-English privacy policy grounded in what the site actually collects: PostHog analytics (opt-in, consent-gated, session recording off), the mailto-based contact/newsletter forms, the currently-dormant AI chat assistant, and GitHub Pages hosting. Covers cookies, the consent banner, service providers, data retention, and rights under the GDPR, CCPA/CPRA, and Colorado Privacy Act — without claiming any certification. Linked from the contact page; `content_lint.py` now also gates root `privacy.md`. Doubles as a prerequisite for the LinkedIn Community Management API application.
- **PostHog analytics integration (server-side API)** — corrected the site's client key in `_config.yml` (it was the zer0-mistakes theme's bundled demo key, so the site's analytics never reached our own project — project 504877 had ingested zero events) and enabled IP anonymization on the project. Added `scripts/features/posthog/` (stdlib Python) which uses the private `POSTHOG_API_KEY` personal key to `verify` the site is wired to the correct project and its privacy settings haven't drifted, print `settings`, and post deploy `annotate` markers; `.env.example` documents the key. Event retention is plan-controlled on PostHog Cloud and cannot be set through the API.
- **LinkedIn company-page publishing** — a governed draft→approve→publish pipeline for the BASH LinkedIn page (`urn:li:organization:64517157`). The stdlib-only Python publisher `scripts/features/linkedin/` posts article link-shares of blog posts and standalone text updates via the Posts API, uploads the post's `preview` image as the card thumbnail via the Images API, and records each share in an idempotency ledger (`.github/linkedin-log.json`) so nothing double-posts; `--dry-run` renders the exact payload with no API calls, and it reuses `content_lint.py`'s frontmatter reader and banned-phrase list as a mechanical brand guard. A `/linkedin-draft` command + `linkedin-share` skill draft on-brand commentary into `drafts/linkedin/` (`status: pending`) and open a PR — the human merge is the approval. Two workflows: `linkedin-publish.yml` (manual dispatch + merge-triggered `from-drafts`, commits the ledger back with `[skip ci]`) and `linkedin-token-health.yml` (weekly warning before the 60-day token expiry). The company page is wired into `_config.yml`, `_data/entity/info.yml`, and the JSON-LD `sameAs`; `.env.example` documents the server-side-only `LINKEDIN_*` credentials.
- **Weekly content review — automation + a full first-pass review** — a governed AI agent that moves the site's content forward by one unit each week: it reviews the corpus and opens a PR that either expands an existing article or writes a new one, never pushing to `main`. Ships the `content-curator` charter (`.claude/agents/content-curator.md`), the `content-review.yml` workflow (Thursdays), and `scripts/content_inventory.py` — a deterministic thin/stale shortlist that seeds the weekly run (the same script-first pattern as the preacher). The first run was an exhaustive parallel review of all ~40 content pages; its top verified findings are applied below.
- **New post: "When the numbers say it's time to leave QuickBooks"** (`pages/_posts/corp/`) — the CFO-level decision post for the practice's flagship QuickBooks-to-ERP line, which the review found named everywhere but never given a decision piece: the threshold signals, the honest cost-of-inaction math, total cost in ranges, and vendor-neutral targets, citing Oracle NetSuite and Microsoft Dynamics 365 Business Central primary docs. Cross-linked with the ERP service and the outgrowing-QuickBooks guide.
- **The preacher — automated "practice what we preach" enforcement** — a governed AI agent that runs every Saturday (`.github/workflows/preacher.yml`) and holds the repo to the doctrine the site sells (the adapted principles DFF/KIS/DRY/REnO/MVP/COLAB/AIPD plus deterministic-first, governed, build-in-the-open). Two modes: when it finds violations it opens ONE GitHub issue; when the repo is clean it mechanizes one recurring AI-review burden into a deterministic check and opens a PR — so the deterministic floor rises and future enforcement costs less AI. Ships with `scripts/doctrine_check.py` (an extensible check registry; seed check `DRY-CONTACT` catches the exact contact-info duplication that prompted this), the `preacher` subagent charter (`.claude/agents/preacher.md`), and the canon/runbook (`docs/the-preacher.md`). It never pushes to `main` — issues and PRs only. Also reconciled `docs/automation.md` (added the preacher + pr-to-upstream, marked the retired Azure workflow).
- **Upstream sync automation** — `.github/workflows/pr-to-upstream.yml` opens (and keeps) a pull request from `bamr87:main` up to the repository this was forked from (`amr-bash/bashconsultants`) on every push to `main`. Idempotent (won't duplicate an open PR, skips when already in sync) and safe (skips cleanly when the `UPSTREAM_PR_TOKEN` secret is absent). Landed alongside a keep-ours reconcile merge so `bamr87/main` cleanly supersedes upstream's older post pass, keeping those PRs conflict-free.
- **Native Claude context framework** — turned the repo's AI tooling into a first-class Claude Code framework and made the repository its own reference implementation of the governed-AI model the site sells. Added a root `CLAUDE.md` (the canonical Claude entry point, routing into the existing `AGENTS.md`/instructions/prompts plus the operating rules) and `.claude/README.md` (the map of the layer). Codified the brand as a single source of truth (`.github/instructions/brand.instructions.md` — name/etymology, mission, voice, doctrine, colors, logo). Added four **skills** (`.claude/skills/{content-editorial,toolkit-doc,wikilinks,brand}`), two **subagents** (`.claude/agents/{jekyll-build-validator,brand-guardian}`), and three **commands** (`.claude/commands/{lint-content,new-toolkit-doc,brand-check}`) — the agents the practice describes at `/ai-operations/` now exist as files. Documented the whole pattern on-site as a partner-track guide, `pages/_toolkit/claude-context-framework.md` (`/tools/partners/claude-context-framework/`), with a mermaid architecture diagram.
- **The BASH toolkit collection** — turned the single `/tools/` page into a two-track docs/training library (`toolkit` collection under `pages/_toolkit/`, served at `/tools/business/…` and `/tools/partners/…`). The **business track** is 10 plain-English DIY guides for SMB owners (IT foundations, adopting AI, cloud migration, outgrowing QuickBooks, faster close, dashboards, integrations, IT roadmap, security baseline, backups); the **partner track** is 10 advanced technical references for consultants (engagement method, deterministic-first doctrine, AI-native practice, production AI/RAG, cloud landing zones, ERP architecture, record-to-report, modern data stack, integration architecture, security architecture), several with mermaid architecture diagrams. Data-driven hub + track landings, a `toolkit` sidebar nav, and a "Toolkit" top-nav dropdown; the old internal-tooling content moved into the partner-track "Running an AI-native consulting practice" doc. Cross-linked with Obsidian wiki-links; every doc cites a verified-live primary source.
- **Two new service pages** — `pages/_services/ai.md` (`/services/ai/`) and `pages/_services/managed-it.md` (`/services/managed-it/`), completing the eight-service catalog; the flagship AI offering previously existed only as a hub section with the landing card mis-linked to `/services/dev/`.
- **Case studies collection** — `pages/_case_studies/` (six anonymized engagement snapshots + index), registered in `_config.yml`, surfaced in the landing proof band.
- **`/tools/` and `/ai-operations/`** — root pages presenting the firm's own AI toolchain (prompt playbook, VS Code orchestrator, image pipeline, governance stack) as client-relevant proof, with `_data/playbook.yml` auto-generated from the prompt/instruction files by `scripts/generate_playbook_data.py`.
- **Four pillar posts** (2026-07-06) — an SMB AI acceptable-use policy, cyber-insurance renewal questions, MCP for the back office, and the AI audit trail for finance; plus the promoted `bashos` post from `drafts/`.
- **AI chat proxy** — `api/` Azure Functions app implementing the theme's chat-proxy contract (server-held Anthropic key, model pinned server-side, per-IP rate limiting keyed on the trusted proxy hop, body-size and token caps); `staticwebapp.config.json` pins the managed-functions runtime to Node 20.
- **CI and automation** — `.github/workflows/build-validate.yml` (builds both production stacks + content lint on every push/PR), `site-health.yml` (nightly), and `content-gardener.yml` (weekly draft PRs); `scripts/content_lint.py` mechanically enforces the editorial contract.
- **AI-search layer** — `/llms.txt`, site-wide + per-type JSON-LD (Article/Service) in `_includes/structured-data.html`, and a wired `/search/` page over `search.json`.
- **`_data/taxonomy.yml`**, `docs/preview-images.md`, `docs/automation.md`, and `.devcontainer/` — codified the section voice profiles, preview-image and automation runbooks, and a container dev environment.

### Changed
- **Landing hero restyled as a dark band** — the hero now sits on a deep-navy radial gradient with a scoped `data-bs-theme="dark"`, so the existing Bootstrap text utilities flip to light automatically whatever color mode the visitor chose (the band re-applies `color: var(--bs-body-color)` because the scoped theme only redefines variables), and the secondary call-to-action became `btn-outline-light` for contrast. Replaces the theme's `particles.js` background and its two script tags in `_layouts/landing.html`; `.theme-overrides.yml` and `CLAUDE.md` now describe the hero as the interactive mark.
- **PostHog privacy settings moved into `_config.yml`, ahead of retiring the fork** — the theme upstreamed this site's three PostHog privacy deltas in v1.28.0 as `posthog.privacy.{respect_gpc, require_consent, geoip_disable}`, so those keys are now set in `_config.yml` and are the declared source of truth. The local `_includes/analytics/posthog.html` override **stays for now**: `remote_theme` is pinned to `@v1.26.0`, which does not read those keys, so deleting the fork today would silently restore capture-before-consent and IP geolocation and break what `/privacy/` promises readers. The file's header and `.theme-overrides.yml` now record the exact retirement condition — bump the pin to ≥ v1.28.0 (with `Gemfile.azure`), verify, then delete.
- **Gemfile comments corrected** — the path-gem note claimed the local `/zer0-mistakes` mount was a stopgap "until a gem version with admin includes is published"; the published gem has shipped `_layouts/admin.html` and `_includes/navigation/admin-nav.html` since v1.26.0. It now describes what the path gem actually is — a deliberate local-dev mount (overridable with `ZER0_MISTAKES_PATH`) that production and CI never use. Also repointed the dangling `docs/systems/ZERO_PIN_STRATEGY.md` citation at the theme repo where that doc actually lives, and noted the two places this repo departs from the zero-pin philosophy it inherits (the hard `path:` pin, and no committed `Gemfile.lock`).
- **`CLAUDE.md` build-stacks table corrected** — it told contributors to validate with the local-dev Docker stack without saying that CI (`build-validate.yml`) builds only the Pages and Azure stacks. The table now names each stack's theme source and whether CI builds it, and says plainly that a green PR is evidence about Pages and Azure only.
- **Canonical domain set to `bash-365.com`.** The repo referenced `bashconsultants.com` (now a separate mirror — the `bash-amr` fork) as the site URL, so canonical tags, the sitemap, structured data (`_data/entity/info.yml`), the logo link, the LinkedIn publisher's share URLs, and the privacy policy all pointed at a stale mirror whose `/privacy/` 404s. Switched `_config.yml url`, the entity data, the LinkedIn base URL default, docs, and the README/privacy references to the live main domain `bash-365.com`. Email has since migrated too — `amr@bash-365.com` is the primary address with `amr@bashconsultants.com` kept as a receiving alias (see `docs/domains-and-email.md`).
- **Analytics privacy hardening (live-validation follow-up)** — after end-to-end testing on the deployed site, closed two gaps the validation surfaced: disabled PostHog IP geolocation (`$geoip_disable` in the `posthog.html` override) so no city/region/postal is derived from a visitor's IP (the project's `anonymize_ips` only stops the raw IP being *stored*, not GeoIP enrichment), and made PostHog persistence in-memory until analytics consent is stored, so no PostHog cookie or localStorage is written before opt-in. Corrected the privacy policy's IP wording to match. The same validation confirmed prior opt-in, GPC/Do-Not-Track suppression, zero Google tracking, and IP-not-stored were all already working.
- **Removed Google tracking; PostHog is now the sole analytics.** Disabled Google Analytics 4 (commented `google_analytics` in `_config.yml`) and neutralized the theme's hardcoded Google Tag Manager container with a local no-op override at `_includes/analytics/google-tag-manager-head.html`. Hardened PostHog to true prior opt-in via a local `_includes/analytics/posthog.html` override: it initializes opted-out (`opt_out_capturing_by_default: true`) so it captures nothing before consent, and it honors Global Privacy Control (GPC) alongside Do Not Track — under either signal PostHog does not load. Closes the consent-enforcement gaps the privacy-policy review surfaced.
- **Service pages expanded and reconciled** (first content-review pass) — `pages/_services/erp.md` gained a "Moving off QuickBooks to a mid-market ERP" section (naming Oracle NetSuite and Microsoft Dynamics 365 Business Central as destinations) and a "What it changes" outcomes block in honest categories, and its QAD versions are now labeled legacy. The services hub (`index.md`) description now names all eight services (adding AI and managed IT), the three divergent financial-systems platform lists were reconciled (dropping the unsupported Anaplan outlier), the QAD/legacy-ERP versions are labeled "versions we've worked on" with a link to QAD's current Adaptive ERP line, and the IT-strategy roadmap horizon was aligned so the hub no longer contradicts the strategy page.
- **Contact info deduplicated to a single source of truth** — the identical email/phone/LinkedIn/website block that was copy-pasted at the foot of all eight service pages is now one shared include, `_includes/contact-methods.html`, rendered from `_data/entity/info.yml` (`contact-email`, `contact-phone`), the socials list, and the canonical `info.url`. The remaining hardcoded contact values on `contact.md`, `about.md`, `pages/_services/index.md`, and the founder page's hero + contact tiles now read from that same data (personal email from `site.email`), so the phone number, address, and domain each live in exactly one place. Changing a value once updates it everywhere.
- **Founder page redesigned** (`/about/amr/`) — added a designed profile hero (avatar, identity, social links, consultation call-to-action), a stat band mixing career numbers with live GitHub stats for `@bamr87` (30 repos, 19 stars, 17 followers, coding in public since 2015), a row of open-source project cards (it-journey, zer0-mistakes — the theme this site runs on — bamr87.github.io, aieo), and technical-skills and strengths as badge groups; the full CV detail is preserved. The GitHub stats are deterministic-first: real static values render without JavaScript and a small client-side script only ever *updates* them from the GitHub API, never blanks them. The Education, Professional experience, and Project record sections were then restyled to match — education as cards, experience as a blue timeline (with each role's dates, and Navistar's three roles and nested location lists preserved), the project record as per-employer panels with project-count pills, and the contact block as a grid of icon tiles with `tel:`/`mailto:` links — with all CV detail intact. Accent color uses the UI blue per the brand palette — the `brand-guardian` agent caught an initial use of logo-teal as the UI accent, which the brand SSOT forbids.
- **Registered the Claude layer and standardized the brand name** — `AGENTS.md` and `.github/copilot-instructions.md` now point to `CLAUDE.md`, the brand SSOT, and the `.claude/` primitives; the file-scoped instruction map routes brand-bearing files to `brand.instructions.md`. Aligned the `BASH` expansion to the canonical **Bourne Again Solutions Hero** (the form that actually spells the acronym) in `llms.txt`, matching `README.md`.
- **Landing page** rebuilt as data-driven sections (`_layouts/landing.html` + `index.md` frontmatter + `_data/entity/*.yml`): hero, eight service cards, six industry pain-point cards, process, an "AI-augmented practice" section, proof band, and FAQ; removed the Thrasymachus epigraph.
- **Hero particle background fixed** — the `#particles-js` element was a Bootstrap `.container` (capped at 1140px, centered), so the particle canvas rendered as a bounded box; it now fills the hero edge-to-edge with the content layered above.
- **Obsidian wiki-links** — internal cross-references across service, post, and case-study pages now use pipeless `[[Page Title]]` wiki-links (Obsidian-native, vault-portable), resolved to real links by the theme's client-side resolver over `wiki-index.json`. Pipeless is required: the server-side plugin can't run under GitHub Pages safe mode, and kramdown mangles the `|` of aliased wiki-links into broken tables. Root-page and CTA links (`/tools/`, `/ai-operations/`, `/contact/`) stay markdown.
- **`powered_by` refreshed** — corrected to the real toolchain (Ruby 3.3, Jekyll 3.10, zer0-mistakes 1.26.0, Bootstrap 5.3.3, Claude, OpenAI gpt-image, Python 3.13, Docker, GitHub Pages/Actions, Azure Static Web Apps); dropped the removed Algolia and the stale HTML/CSS/JS/jQuery filler.
- **Conversion forms wired** — the contact and newsletter forms now POST to config-driven endpoints (`site.forms.*`) with graceful `mailto:` fallbacks; previously both had no handler.
- **Theme pinned** — `remote_theme` pinned to `bamr87/zer0-mistakes@v1.26.0` and `Gemfile.azure` raised to the matching `~> 1.26.0` (with `jekyll-include-cache`); a registered `aqua` skin replaces the invalid `dark` value; `theme_color` hex values quoted so they stop parsing as null.
- **Editorial debt burn-down** — sentence-cased service-page titles, removed unbacked "robust/seamless/scalable", stripped trailing periods from service descriptions, retitled the ERP section off its self-labeling name, and realigned `article-review.prompt.md` and the reviewer agent to the house rules they enforce.
- **`content_statistics_generator.rb`** made Jekyll-3/4 compatible (Azure stack was crashing on `Theme#root_dir`).

### Removed
- **`assets/particles.json`** — a byte-identical shadow of the theme's own copy, kept only for the retired `particles.js` hero. Per `.theme-overrides.yml`, an identical override is drift; the theme still ships its copy for any layout that wants it.
- **Azure Static Web Apps deploy workflow** — retired `.github/workflows/azure-static-web-apps-proud-pond-06dc10c1e.yml`. It was failing the CI gate independently of any change (its deployment token is unset, and its Oryx build can't run `bundle`), while GitHub Pages is the primary and working deploy target. The Azure *build* is still validated by `build-validate.yml` (`Gemfile.azure` + `_config.azure.yml`), and `staticwebapp.config.json` / `api/` remain for a future reconfiguration if Azure hosting is revived.
- **Stale artifacts** — the drifted `scripts/lib/preview_generator.py`, clipboard-era `scripts/{vscode-integration.sh,demo-docs-generation.js,test-docs-prompt.js}`, the broken `Rakefile`, and the stale Algolia config block; rewrote the root `README.md` from stale marketing copy (wrong `bash-365.com` contact, 3-of-8 services) into a repo-facing developer doc.

### Fixed
- **Internal repo docs were being published on the marketing site** — `bash-365.com/CLAUDE.md`, `/AGENTS.md`, `/CHANGELOG.md`, and `/README.md` all returned 200 (raw markdown), and because those files carry no front matter the `github-pages` gem's `jekyll-optional-front-matter` also rendered them as pages at `/CLAUDE/`, `/AGENTS/`, and `/CHANGELOG/` — internal AI-agent operating instructions, the developer readme, and the changelog served from a customer-facing consulting domain. `_config.yml`'s `exclude:` never listed them; every other zer0-mistakes consumer in the fleet does. Added the four docs plus `Dockerfile`, `docker-compose.yml`, `package.json`, and `frontmatter.json` to `exclude:`, mirrored into `_config_dev.yml` (Jekyll replaces rather than merges `exclude:`), and left `CNAME`, `staticwebapp.config.json`, `favicon.ico`, `LICENSE`, and `llms.txt` published on purpose. Nothing in the site linked to any of them; the Pages and Azure builds are otherwise byte-comparable (51 search items in both, JSON-LD and sanity checks unchanged).

## [1.5.0] - 2026-06-21

### Added
- **`pages/_posts/muses/2025-01-24-bash-consulting-breaking.md`** — New satirical press-release post ("If a press release about ethical capitalism wrote itself") covering ESG accounting for Denver SMBs; includes a straight practical section on what's buildable on QuickBooks today.
- **`.github/prompts/article-write.prompt.md`** — New `/article-write` agent prompt for drafting new bashconsultants.com posts end-to-end.

### Changed
- **`pages/_posts/muses/2025-08-12-innovation-paradox.md`** — Frontmatter updated (author, description, keywords, lastmod, tags normalized); content rewritten for voice and SMB focus.
- **`pages/_posts/tech/2025-08-12-ai-integration-reality.md`** — Frontmatter updated; content rewritten with honest SMB-first framing on AI implementation.
- **`pages/_posts/tech/2025-11-19-prompts-are-the-new-command-line.md`** — Frontmatter normalized (author, lastmod, categories/tags as YAML lists); content already updated to SMB voice.
- **Site-wide content review** — Rewrote `about.md`, `contact.md`, and all service pages (`pages/_services/{cloud,erp,data,dev,fintech,strat}.md`) to comply with `content-style.instructions.md`: removed banned marketing phrases, switched to sentence-case headings and the 8-section service-page structure, defined acronyms on first use, and added inline images with descriptive alt text.
- **`pages/_services/index.md`** — Rebuilt as a card-based hub linking to all six real service pages (it previously listed generic categories that did not match the site's actual services).
- **`_data/entity/info.yml`** — Cleaned banned phrases from the About / Founder / Mission copy that feeds the landing page.
- **Blog posts** — Added a next-step call-to-action to posts that lacked one; normalized `preview:` paths to the `/assets/images/previews/` convention; bumped `lastmod` on edited posts.
- **All 11 blog posts (`pages/_posts/{corp,erp,muses,tech}/*.md`)** — Full editorial pass aligning every post to `content-style.instructions.md` and `posts.instructions.md`: heavy rewrite to the business-outcome-first voice, acronyms defined on first use, banned marketing phrases removed, sentence-case headings, and a single next-step CTA plus one outbound primary-source link in every post. Tightened titles to sentence case ≤ 60 chars and `description` to 120–155 chars.
- **Creative voice — show, don't announce** — Removed raw genre/device labels ("satire", "parody", "reality show", "Broadway-style musical number", "exposé") from reader-facing text so each post *enacts* its device (the press release, the show conceit, the song, the Frankenstein metaphor) instead of narrating it.
- **`pages/_posts/tech/2025-08-12-ai-integration-reality.md`** — Published the post (was `draft: true` with duplicated `author`/`description` keys); kept the stronger "AI for small business: what the pilots don't tell you" version and rewrote the body as an SMB-first AI-adoption guide.
- **Post frontmatter normalized site-wide** — `author: "Amr Abdel-Motaleb"` everywhere (replacing "BASH Consulting Team" / "bamr87"); lowercase `categories`; flow-style `tags` / `keywords` lists; duplicate keys removed; `lastmod` set to 2026-06-21.
- **Preview images** — Regenerated 9 AI preview banners (`gpt-image-2`, retro pixel-art) to match the rewritten titles and content; standardized all post `preview:` paths to the `/images/previews/<slug>.png` short form (auto-normalized by the theme).

### Removed
- **`pages/_posts/tech/2025-01-24-bash-consulting-breaking.md`** — Deleted from `tech/`; replaced by the muses rewrite above.
- **Invented case studies and unverifiable metrics** — Removed fabricated results ("40% cost reduction", "99.9% uptime", "300% revenue increase", "30+ ERP projects", "over 15 years") and overreaching capability claims (e.g., AI/ML clinical decision support, fraud detection) from the service pages, per the "never invent customer wins" rule.

### Fixed
- **Dead sidebar nav modes** — Replaced the pre-1.x sidebar values `searchCats` (pages scope) and `dynamic` (about, case-studies, posts scopes) with `auto` in `_config.yml`; the pinned theme's sidebar resolver no longer recognizes the legacy names, so those sidebars silently never rendered.
- **Broken images** — Renamed `assets/images/red-rocks.JPG` → `red-rocks.jpg` so the lowercase reference resolves on case-sensitive production builds; repointed the missing `office-594119.png` `og_image` to `office.jpg` in `_config.yml` and `pages/_about/site/_config.yml`; repointed the missing `bamr-avatar.png` avatar to `Amr-Headshot_v2.jpg`.
- **Contact-info consistency** — Standardized all customer pages to `bashconsultants.com` / `info@bashconsultants.com` / `(720) 352-4641`; replaced the stale `bash-365.com` details on `about.md` and `contact.md`; fixed the `contact-email: info@consultants.com` typo in `_config.yml` that broke the landing page's "Email Now" button.

---

### Added
- **`.github/instructions/`** — Six file-scoped instruction files for AI agents:
  - `content-style.instructions.md` (applyTo `pages/**`, `index.md`, `about.md`, `contact.md`) — shared editorial voice, audience profile (Denver SMBs 5–200 employees), target-industry table, banned phrases, SEO + accessibility rules
  - `posts.instructions.md` (applyTo `pages/_posts/**/*.md`) — blog post structure + subfolder routing (corp/erp/muses/tech)
  - `services.instructions.md` (applyTo `pages/_services/**/*.md`) — service-page conversion structure + industry-fit naming
  - `jekyll-theme.instructions.md` (applyTo theme override paths) — local override rules for the remote theme
  - `extension.instructions.md` (applyTo `extension/**`) — VS Code Prompt Orchestrator dev rules
  - `prompts.instructions.md` (applyTo `.github/{prompts,instructions}/**`) — schema + slash-hard body style
- **AGENTS.md** — Cross-tool entry point for AI coding agents (Copilot, Codex, Cursor, Aider, Claude Code). Points to canonical guidance.
- **`.github/prompts/commit-publish.prompt.md`** — Standard commit + push + deploy workflow for the direct-to-main publishing model.
- **Canonical frontmatter reference** — `.github/FRONTMATTER.md` documents the required schema for `.prompt.md` and `.instructions.md` files.

### Changed
- **`.github/copilot-instructions.md`** — Rewritten to reflect the actual dual-purpose repo (Jekyll site + `extension/` sub-project). Previous content described only the extension and was stale.
- **`.github/prompts/` frontmatter normalized** — All `.prompt.md` files updated to canonical `mode: agent` + `description` + `date` + `lastmod` schema. Body content already concise (≤100 lines per file); no further compression needed.

### Removed
- **`.github/prompts/docs.prompt.md`** — superseded by `documentation.prompt.md`.

## [1.4.0] - 2026-04-06

### Changed
- **Theme Upgrade**: Updated zer0-mistakes theme from v0.21.6 to v0.22.10
  - `Gemfile.azure`: Updated `jekyll-theme-zer0` from `~> 0.21.2` to `~> 0.22.10`
  - `pages/_about/site/_config.yml`: Updated `remote_theme` pin from `v0.21.6` to `v0.22.10`
  - `_data/README.md` and `_data/navigation/README.md`: Updated version references to v0.22+
  - Notable theme changes since v0.21.6:
    - Admin layout and configuration dashboards (v0.22.10)
    - Cross-platform installation compatibility fixes (v0.22.8)
    - Hero layout and scroll animation stabilization (v0.22.3)
    - Various documentation and CI improvements

## [1.3.0] - 2026-03-31

### Changed
- **Theme Upgrade**: Updated zer0-mistakes theme from v0.18.0 to v0.21.6
  - `Gemfile`: Updated `jekyll-theme-zer0` from `~> 0.18.0` to `~> 0.21.2` (latest on RubyGems)
  - `Gemfile.azure`: Added version pin `~> 0.21.2`
  - `_config.yml`: Pinned `remote_theme` to `bamr87/zer0-mistakes@v0.21.6`

- **Layout Standardization**: Aligned post and section layouts with theme v0.20.3+ conventions
  - Changed default post layout from `journals` to `article` in `_config.yml` defaults
  - Updated 9 posts with explicit `layout: journals` or `layout: blog` to `layout: article`
  - Updated 6 category/index pages to use `layout: default` (theme's `section` layout uses `/news/` URLs)
  - Renamed category pages with date prefixes for proper Jekyll `_posts` processing

- **New Features Enabled**:
  - Added `search.json` for GitHub Pages compatible search (theme v0.20.2 feature)
  - Added `mermaid` diagram configuration for client-side rendering
  - Added `jekyll-include-cache` plugin for improved build performance
  - Updated vendor exclusion paths to support `assets/vendor/` publishing

- **Configuration Updates**:
  - Updated Bootstrap version reference from 5.2.0 to 5.3.3 in `powered_by`
  - Updated version references in `_data/README.md` and `_data/navigation/README.md` to v0.21+
  - Synced `pages/_about/site/_config.yml` remote_theme pin and post layout default

### Fixed
- **404 Page**: Fixed broken `/blog` navigation link to use correct `/posts` path
- **Navigation**: Removed broken links to non-existent pages (`/docs/`, `/about/org/`, `/about/portfolio/`)
- **Navigation**: Fixed `/home/` links to `/` across navigation data files
- **Blog Index**: Fixed hardcoded post URLs using slug format to use date-based format
- **Category Pages**: Added missing `permalink` to muses category page

## [1.2.0] - 2026-01-24

### Changed
- **Development Port Standardization**: Updated all development ports from 4002 to 4042 for consistency
  - `Dockerfile`: Changed EXPOSE and CMD to use port 4042
  - `docker-compose.yml`: Updated port mapping to 4042:4042
  - `.vscode/tasks.json`: Updated Jekyll local serve port to 4042
  - `.vscode/launch.json`: Updated all debug configuration URLs to localhost:4042

- **VS Code Development Environment**: Complete overhaul of development configurations
  - `.vscode/launch.json`: Added 6 new debug configurations:
    - 🐳 Debug BASH Consultants (Docker) - Primary Docker debugging
    - 🔗 Attach to Running Jekyll (Docker) - Attach to running container
    - 🔄 Docker Rebuild & Debug - Force rebuild with debugging
    - 🖥️ Debug BASH Consultants (Local) - Local development debugging
    - 📱 Mobile Debug (Docker) - Mobile responsive testing
    - 🎯 Performance Debug (Docker) - Performance profiling
  - `.vscode/tasks.json`: Added 12 comprehensive tasks:
    - Docker operations (up, stop, down, rebuild, logs)
    - Jekyll serve/build (Docker and Local)
    - Maintenance tasks (clean up, update dependencies)

- **Theme Version**: Updated jekyll-theme-zer0 to v0.18.0
  - `Gemfile`: Updated gem version constraint to `~> 0.18.0`
  - `_config.yml`: Simplified remote_theme to `bamr87/zer0-mistakes` (uses latest)

- **Gemfile Cleanup**: Simplified dependencies
  - Removed redundant jekyll_plugins group (already included in github-pages gem)
  - Removed pinned versions for ffi and webrick (use latest compatible)
  - Removed commonmarker pin (resolved upstream)

### Added
- **`.gitignore`**: Added `logs/` directory for debug trace logs

### Fixed
- **Dockerfile**: Added newline at end of file

## [1.1.0] - 2026-01-24

### Changed
- **Navigation Data Structure** (`_data/navigation/`): Updated to zer0-mistakes theme v0.17+ format
  - Migrated from `sublinks` to `children` property for nested navigation items
  - Added Bootstrap Icons (`bi-*` prefix) to all navigation items
  - Added consistent Home links to sidebar navigation files
  - Added trailing slashes to all URLs for consistency

### Added
- **New Navigation Files** (`_data/navigation/`)
  - `home.yml` - Homepage quick navigation with icons
  - `services.yml` - Services sidebar navigation
  - `README.md` - Navigation schema documentation with migration guide

### Fixed
- Fixed HTML entity `&amp;` in about.yml to proper `&` character
- Fixed inconsistent URL trailing slashes across navigation files

## [1.0.0] - 2026-01-24

### Added
- **Prompt Orchestrator VS Code Extension** (`extension/`): New VS Code extension for orchestrating AI agent workflows using structured prompts
  - Discovers and loads prompt templates from `.github/prompts/` directory
  - Execute prompts via Command Palette or sidebar tree view
  - Integration with VS Code Chat API and Language Model API
  - Commands: refreshPrompts, executePrompt, review, refactor, test, docs, debug
  - Configuration settings for prompts directory and auto-refresh
  
- **Prompt Engineering Toolkit** (`.github/prompts/`)
  - `docs.prompt.md` - Technical documentation generation
  - Additional prompts for requirements analysis, system design, code implementation, test generation, code refactoring, and debugging

- **Automation Scripts** (`scripts/`)
  - `routine-maintenance.sh` - Prepare prompt workflows for VS Code Chat
  - `demo-docs-generation.js` - Demonstrate documentation prompt generation
  - `test-docs-prompt.js` - Standalone test script for prompt loading
  - `vscode-integration.sh` - VS Code CLI integration helper

- **Blog Posts** (`pages/_posts/`)
  - "Prompts: The New Command Line" - Exploring the paradigm shift in development
  - "From Prompts to Pipelines: Agentic Workflows in VS Code" - Extension design and agentic workflows

### Changed
- **Repository Structure**: Reorganized to separate Jekyll website from VS Code extension
  - Jekyll site configs remain at root level
  - Extension code moved to dedicated `extension/` directory
  - Updated `.gitignore` for new structure
  
- **VS Code Workspace Configuration** (`.vscode/`)
  - Updated `launch.json` for Jekyll-focused development
  - Updated `tasks.json` for Jekyll build tasks
  - Updated `settings.json` for Liquid/Jekyll file associations
  - Updated `extensions.json` with Jekyll-relevant recommendations

- **Root `package.json`**: Clean Jekyll-only build configuration for Azure Static Web Apps

- **README.md**: Added Tools and Resources section documenting prompt engineering toolkit

### Removed
- Extension files from root directory (moved to `extension/`)
  - `tsconfig.json`, `esbuild.js`, `eslint.config.mjs` (now in `extension/`)
  - `src/`, `out/`, `dist/` directories (now in `extension/`)
  - `.vscode-test.mjs`, `.vscodeignore`, `vsc-extension-quickstart.md`, `EXTENSION-README.md`