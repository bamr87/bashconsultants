# Automation: scheduled workflows and the AI chat proxy

This page documents the repo's automation: the GitHub Actions workflows and
the Azure Functions app in `api/` that powers the site's AI chat widget. It is
an internal operations doc — `docs/` is excluded from the Jekyll build.

The workflows: **build & validate** (the PR gate), **site health** (nightly),
**content gardener** (weekly new-post draft), **content review** (weekly
expand-or-add), **PR to upstream** (fork sync), and **the preacher** (weekly
doctrine enforcement — see [`the-preacher.md`](./the-preacher.md)).

## What runs where

The repo deploys to two hosts from the same source:

| Host | Deployed by | Serves |
| --- | --- | --- |
| GitHub Pages | GitHub's built-in Pages build (github-pages gem + `remote_theme`) | Static site only. There is no server side, so `/api/chat` does not exist here. |
| Azure Static Web Apps (SWA) — app `proud-pond-06dc10c1e` | `.github/workflows/azure-static-web-apps-proud-pond-06dc10c1e.yml` | Static site plus managed Azure Functions under `/api/`, and a temporary staging environment per pull request. |

The AI chat widget therefore only has a working backend on the SWA-served
host. If the production domain is served by GitHub Pages, either leave
`ai_chat.proxy_ready: false` there or point `ai_chat.endpoint` in `_config.yml`
at the absolute SWA URL (for example
`https://proud-pond-06dc10c1e.<region>.azurestaticapps.net/api/chat`) —
cross-origin requests from the production domains are already on the
function's origin allowlist.

> **Current state:** the Azure SWA deploy workflow has been retired (see the
> CHANGELOG). Production is **GitHub Pages only**, so `/api/chat` is not deployed
> today; the `api/` app and `staticwebapp.config.json` remain for a future Azure
> reconfiguration. The LinkedIn automation below runs entirely in GitHub Actions
> and needs no server-side host.

## The chat proxy (`api/`)

`api/src/functions/chat.js` is an Azure Functions app (Node.js v4 programming
model) that SWA builds and hosts automatically because the deploy workflow
sets `api_location: "api"`. It implements the zer0-mistakes theme's chat proxy
contract, ported from the theme's Cloudflare Worker reference implementation
(`templates/deploy/chat-proxy/worker.js` in the theme repo) — chat route only.

What it does, in order:

1. Answers `OPTIONS` preflight; rejects anything that isn't `POST`.
2. Rejects requests whose `Origin` header isn't on the allowlist
   (production domains, this SWA's own hostnames including per-PR staging
   hostnames, plus anything in the `ALLOWED_ORIGINS` setting).
3. Returns `503` when `ANTHROPIC_API_KEY` isn't configured, so an
   accidentally enabled widget fails cleanly.
4. Applies a fixed-window in-memory rate limit per client IP
   (default 20 requests per minute per function instance).
5. Caps the request body size (default 512 KB) and validates the JSON shape
   (`messages` must be a non-empty array).
6. Forwards `{model, max_tokens, system, messages, tools, stream: true}` to
   the Anthropic Messages API with the server-held credential, capping
   `max_tokens` (default cap 4096) and pinning the model server-side
   (`CHAT_MODEL`, else the default) — the client's `model` field is ignored so
   a tampered request can't select a costlier model.
7. Streams the Server-Sent Events response back unchanged. The widget also
   accepts a buffered or plain-JSON response, so `CHAT_BUFFER_RESPONSE=true`
   is available as a fallback.

**Auth: Claude Code OAuth preferred, API key fallback.** The proxy picks its
credential by precedence:

1. `CLAUDE_CODE_OAUTH_TOKEN` — a long-lived Claude Code OAuth token from
   `claude setup-token` (Claude Pro/Max). Used by default when set. Sent as
   `Authorization: Bearer <token>` with the `anthropic-beta: oauth-2025-04-20`
   header. Because subscription OAuth must identify as Claude Code, the proxy
   forces the first `system` block to the Claude Code identity and keeps the
   site assistant's own prompt as the following block.
2. `ANTHROPIC_API_KEY` — a standard workspace `x-api-key`. The fallback, used
   only when no OAuth token is set.

Set exactly one (OAuth wins if both are present). The rotating-refresh OAuth
mode from the theme's Cloudflare worker is not ported — it needs a key/value
store SWA functions don't provide, so use the long-lived setup-token instead.

The credential is read from the environment at request time and is never sent
to the browser, logged, or echoed in error messages. The rate limit keys on the
last `X-Forwarded-For` hop (the value Azure's trusted front end appends), not
the client-supplied first entry, so a caller can't spoof its way around the cap.

**Response-time ceiling.** SWA managed functions enforce a hard 45-second HTTP
response limit. The default model is `claude-opus-4-8` with `MAX_TOKENS_CAP`
4096; a long Opus generation can approach that ceiling. If the widget starts
timing out under load, lower `MAX_TOKENS_CAP` (2048 is a comfortable public
default) or pin a faster model via `CHAT_MODEL`.

Not ported from the worker: the rotating-refresh OAuth mode (needs Cloudflare
KV) and the `/api/github/issue` and `/api/github/pull-request` routes (this site
runs `ai_chat.github.mode: 'url'`, which opens pre-filled github.com forms and
needs no token).

### Application settings (Azure portal → Static Web App → Environment variables)

| Setting | Required | Default | Purpose |
| --- | --- | --- | --- |
| `CLAUDE_CODE_OAUTH_TOKEN` | One of these two to activate chat | — | Claude Code OAuth token (`claude setup-token`). **Preferred** — used when set. |
| `ANTHROPIC_API_KEY` | One of these two to activate chat | — | Workspace API key with a spend cap. Fallback, used only when no OAuth token. |
| `CHAT_MODEL` | No | `claude-opus-4-8` | Model, pinned server-side; the client's `model` field is always ignored. |
| `MAX_TOKENS_CAP` | No | `4096` | Upper bound on client-requested `max_tokens`. Consider `2048` for the public widget (SWA's 45s response ceiling). |
| `MAX_BODY_BYTES` | No | `524288` | Request body cap in bytes. |
| `ALLOWED_ORIGINS` | No | production + SWA hostnames | Comma-separated extra origins (e.g. `http://localhost:4000` while testing). |
| `RATE_LIMIT_MAX` / `RATE_LIMIT_WINDOW_MS` | No | `20` / `60000` | Requests per window per IP, and window length. |
| `CHAT_BUFFER_RESPONSE` | No | unset | Set `true` to buffer the upstream response instead of streaming it. |

### Activating the chat widget (two switches)

1. **Azure application setting** — in the Azure portal, open the Static Web
   App → Environment variables → add `CLAUDE_CODE_OAUTH_TOKEN` (preferred; run
   `claude setup-token` to mint one) **or** `ANTHROPIC_API_KEY` for the
   production environment (and staging, if chat should work on PR previews).
2. **Site config** — in `_config.yml`, flip `ai_chat.proxy_ready` to `true`.
   The widget renders nothing until this is true, so the order is safe: set
   the credential first, then flip the flag.

To roll back, flip `proxy_ready` back to `false`; the function keeps running
but nothing calls it.

Note on the API runtime: SWA picks the managed-functions Node.js version from
`platform.apiRuntime` in `staticwebapp.config.json` (in the app source
folder). The function uses the Node v4 programming model, which requires
Node 18 or newer — the config file should set `"platform": { "apiRuntime":
"node:20" }`.

## Workflow: Build & validate

File: `.github/workflows/build-validate.yml`

Runs on every push to `main` and on pull requests (with `paths-ignore:
extension/**`). It is the quality gate in front of the deploy — the Azure
workflow deploys with no validation of its own, so this catches breakage
before it ships. Three jobs:

- **build-pages** — builds the production GitHub Pages stack (`github-pages`
  gem + `remote_theme: bamr87/zer0-mistakes@v1.26.0`, `_config.yml` only,
  `--safe`) in a `ruby:3.3` container, proving the Pages build stays green.
- **build-azure** — builds the Azure stack (`BUNDLE_GEMFILE=Gemfile.azure`,
  `jekyll-theme-zer0 ~> 1.26.0`, `--config _config.yml,_config.azure.yml`),
  proving the SWA deploy will succeed.
- **content-lint** — runs `python3 scripts/content_lint.py` to enforce the
  editorial contract (frontmatter completeness, description length,
  banned-phrase scan, `draft: true` blocker, filename/date match).

Gems are cached between runs; no deploy steps. If any job fails, the PR is
blocked (once these checks are made required in branch protection).

## Workflow: Azure Static Web Apps CI/CD — retired

The Azure SWA deploy workflow was **retired** (its deployment token was unset and
its Oryx build could not run `bundle`); GitHub Pages is the primary deploy target.
The Azure *build* is still validated by the `build-azure` job in build-validate.yml,
and the `api/` chat proxy plus `staticwebapp.config.json` remain for a future
reconfiguration if Azure hosting is revived. The hosting notes above describe that
dormant path; reconciling them fully is a good first task for the preacher.

## Workflow: Site health (nightly)

File: `.github/workflows/site-health.yml`
Schedule: `17 9 * * *` UTC (roughly 2–3 AM Denver), plus manual dispatch.

Steps, all with the built-in `GITHUB_TOKEN` — no extra secrets needed:

1. **Smoke build** — builds the site with the github-pages gem and
   `remote_theme`, the same stack production GitHub Pages uses. A CI-only
   Gemfile is generated in the run because the repo's `Gemfile` carries a
   local-path theme gem meant for Docker development.
2. **Content lint** — runs `scripts/content_lint.py --warn-only` when the
   script exists; otherwise prints a notice and moves on.
3. **Link check** — runs `htmlproofer` against the built `_site`, internal
   links only (`--disable-external`). Ignores `/api/` URLs (those only resolve
   on the SWA host), the theme-emitted `/tags/…`, `/archives/…`, and bare
   `#<tag>` anchor links (the site publishes no tag/archive index pages yet),
   and the published `CLAUDE`/`AGENTS` agent-context pages (their relative
   repo-file links are not site URLs).
4. **On failure** — writes an error annotation and a step summary describing
   the failure. Issues are disabled on this repository, so no issue is filed;
   check the Actions tab (or the failure notification email) for red nightly
   runs.

## Workflow: Content gardener (weekly)

File: `.github/workflows/content-gardener.yml`
Schedule: `23 14 * * 1` UTC (Mondays, morning in Denver), plus manual
dispatch with an optional topic override.

Uses `anthropics/claude-code-action@v1` to draft **one** new blog post per
week and open a pull request — it never pushes to `main`. The prompt requires
it to:

- read `.github/instructions/content-style.instructions.md`,
  `.github/instructions/posts.instructions.md`, and
  `.github/prompts/article-write.prompt.md` first;
- pick an uncovered topic from `_data/taxonomy.yml` (falling back to the
  service catalog in `_data/entity/services.yml`) and the existing post list
  under `pages/_posts/`;
- write a single file into `drafts/` with `draft: true` and standards-compliant
  frontmatter;
- open a PR titled `content(posts): weekly draft — <topic>` whose body
  includes the reviewer's promotion checklist (move to
  `pages/_posts/<subfolder>/`, flip `draft:` to `false`, confirm or
  regenerate the preview image).

### Activating the gardener

Add a `CLAUDE_CODE_OAUTH_TOKEN` repository secret (preferred — `claude
setup-token`) **or** an `ANTHROPIC_API_KEY` repository secret (repo → Settings
→ Secrets and variables → Actions). When both are set, `claude-code-action`
uses the OAuth token. Without either, the workflow logs a notice and skips —
scheduled runs never fail red just because the credential is absent. These are
separate from the Azure application settings above; they can be different
credentials with different spend caps.

Optional: add a `GARDENER_GITHUB_TOKEN` secret — a fine-grained personal
access token with Contents and Pull requests read/write on this repo. Pull
requests opened with the default `GITHUB_TOKEN` can't trigger other
workflows, so the SWA staging build only runs on gardener PRs when this
token is set (or after any human push to the PR branch). Review still works
fine without it; you just review the markdown instead of a staged preview.

## Workflow: LinkedIn publishing

Publishes to the BASH LinkedIn **company page** (`urn:li:organization:64517157`)
the same way the gardener drafts posts: **agents draft, a human approves, a
script posts.** It handles article link-shares of blog posts and standalone text
updates. Native long-form LinkedIn Articles are not API-publishable — "article"
here means a link-share card.

**The engine** — `scripts/features/linkedin/` (stdlib-only Python, run as
`python3 scripts/features/linkedin <command>`). It maps a post's frontmatter to
the Posts API payload, uploads the post's `preview` image as the card thumbnail
via the Images API, posts to `/rest/posts`, and records the returned URN in
`.github/linkedin-log.json` so a source is never posted twice. `--dry-run`
renders the exact payload with zero API calls. Full usage:
`scripts/features/linkedin/README.md`.

**The governed flow.** `/linkedin-draft <post|text>` (the
`.claude/commands/linkedin-draft.md` command + the `linkedin-share` skill) drafts
on-brand commentary into `drafts/linkedin/<date>-<slug>.md` at `status: pending`
and opens a PR. A human edits and **merges** it — the merge is the approval.

Files:

- `.github/workflows/linkedin-publish.yml` — runs on `workflow_dispatch` (post
  one article or text update, dry-run by default) and on push to `main` under
  `drafts/linkedin/**` (a merged draft runs `from-drafts` live). It commits the
  ledger and the flipped draft status back with `[skip ci]` so the write never
  retriggers the workflow.
- `.github/workflows/linkedin-token-health.yml` — weekly; validates the token
  with a cheap authenticated call and fails the run with an error annotation and
  step summary when it is rejected or within 7 days of its 60-day expiry
  (Issues are disabled on this repository, so no issue is filed).

### Activating LinkedIn publishing

The app must already have Community Management API access (scopes
`w_organization_social` + `r_organization_social`). Then:

1. Generate a 60-day token at
   <https://www.linkedin.com/developers/tools/oauth/token-generator>, authorized
   by a page admin, and add repo **secrets** (Settings → Secrets and variables →
   Actions): `LINKEDIN_ACCESS_TOKEN` (required), and — only if the app has
   programmatic refresh — `LINKEDIN_REFRESH_TOKEN`, `LINKEDIN_CLIENT_ID`,
   `LINKEDIN_CLIENT_SECRET`.
2. Optionally set repo **variables** (non-secret) `LINKEDIN_ORG_URN`,
   `LINKEDIN_BASE_URL`, `LINKEDIN_API_VERSION` to override the built-in defaults
   (`urn:li:organization:64517157`, `https://bash-365.com`, `202606`).
3. Without `LINKEDIN_ACCESS_TOKEN`, both workflows skip with a notice — scheduled
   runs never fail red just because the credential is absent.

**Token lifecycle.** Access tokens last 60 days; programmatic refresh is gated to
approved partners. If refresh is enabled, `python3 scripts/features/linkedin
refresh-token` renews it; otherwise regenerate manually when the token-health
workflow warns. The `LinkedIn-Version` string also expires ~yearly — bump
`LINKEDIN_API_VERSION`.
## Workflow: Content review (weekly)

File: `.github/workflows/content-review.yml`
Schedule: `37 14 * * 4` UTC (Thursdays, morning in Denver), plus manual dispatch with
optional `mode` (expand / new / auto) and `focus` inputs.

The content counterpart to the preacher. It adopts the content-curator charter
(`.claude/agents/content-curator.md`) and moves the site's content forward by ONE
unit each week: it reviews the corpus — starting from the deterministic
`scripts/content_inventory.py --focus` shortlist of thin/stale pages — and opens a PR
that either **expands** an existing article with more relevant, current information or
**writes** a new article filling a real gap. It follows the same editorial authorities
as the gardener, gates on `content_lint.py`, and never pushes to `main`.

This complements the **content gardener** (which only drafts brand-new posts): the
gardener grows breadth, the curator reviews everything and chooses between depth and
breadth. Activate it the same way (a `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`
secret; optional `CONTENT_REVIEW_GITHUB_TOKEN`).

## Workflow: PR to upstream (weekly)

File: `.github/workflows/pr-to-upstream.yml`
Trigger: Mondays 15:00 UTC, plus manual dispatch. (Once the PR is open it tracks
`main` and updates itself on every push, so a per-push trigger only re-confirmed a
PR GitHub already keeps fresh — the weekly probe just re-opens it after a
merge/close.)

Opens (and keeps) a pull request from this fork up to the repository it was forked
from, `amr-bash/bash-365.com`. Idempotent — it won't duplicate an already-open PR
and skips when upstream is already in sync — and safe: it skips cleanly when the
`UPSTREAM_PR_TOKEN` secret is absent (the default `GITHUB_TOKEN` can't open cross-repo
PRs). Add a fine-grained PAT with Pull requests + Contents on the upstream repo as
`UPSTREAM_PR_TOKEN` to activate.

## Workflow: The preacher (weekly)

File: `.github/workflows/preacher.yml`
Schedule: `42 14 * * 6` UTC (Saturdays, morning in Denver), plus manual dispatch with
an optional `focus` lens.

The reflexive "practice what we preach" enforcer. It runs the deterministic gates
(`scripts/doctrine_check.py`, `scripts/content_lint.py`) first, then does an AI
judgment pass against the canon, and either opens ONE findings PR listing doctrine
violations (Mode A — Issues are disabled on this repository, so the channel is a PR)
or — when the repo is clean — mechanizes one recurring AI-review
burden into a new check in `doctrine_check.py` and opens a PR (Mode B). It never pushes
to `main`. Full canon and design: [`the-preacher.md`](./the-preacher.md). Activate it
the same way as the gardener (a `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` secret;
optional `PREACHER_GITHUB_TOKEN`).

## Cost and safety notes

- Both Anthropic credentials should be workspace-scoped keys with spend caps
  set in the Anthropic console.
- The chat function enforces model, token, origin, body-size, and rate
  limits server-side; a modified client can't raise them.
- The gardener writes only to `drafts/` on a new branch, and the preacher only
  opens PRs — neither ever pushes to `main`; a human merges or closes
  every PR. The site-health workflow has read-only repo access.
- Scheduled workflows run only from the default branch, so changes to them
  take effect after merge to `main`.
