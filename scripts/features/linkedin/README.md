# `features/linkedin` — company-page publisher

Publishes to the BASH Consulting LinkedIn **company page** (`urn:li:organization:64517157`) from this repo: article link-shares of blog posts and standalone text updates. Stdlib-only Python (no `pip install`), same zero-dependency discipline as `scripts/content_lint.py`.

It is the mechanical half of a **governed** pipeline — *agents draft, a human approves, the script posts*:

```
/linkedin-draft  →  PR with a drafts/linkedin/*.md  →  human edits + merges  →  publish
```

## Run it

Invoke the directory as a module (imports resolve with no setup):

```bash
python3 scripts/features/linkedin self-test                     # offline shape checks, no network
python3 scripts/features/linkedin post-article tech/2026-07-06-mcp-for-the-back-office --dry-run
python3 scripts/features/linkedin post-text --message "…" --dry-run
python3 scripts/features/linkedin from-drafts --dry-run         # process the approved queue
python3 scripts/features/linkedin check-token                   # validate + warn near 60-day expiry
python3 scripts/features/linkedin verify --urn urn:li:share:123 # read a post back
```

Drop `--dry-run` to post for real. `--dry-run` renders the exact JSON payload, resolves the canonical URL and thumbnail file, makes **zero** API calls, and writes nothing to the ledger — always dry-run first.

## Commands

| Command | Purpose |
| --- | --- |
| `post-article <ref>` | Share a post as an article card. `<ref>` = `section/YYYY-MM-DD-slug`, a path, or a slug. Commentary defaults to the post's sub-title + hashtags; override with `--commentary` / `--commentary-file`. |
| `post-text` | Standalone update. `--message` or `--message-file`. |
| `from-drafts` | Publish every `status: pending` file in `drafts/linkedin/`, then flip it to `published`. This is the Model-B (merge = approval) path. |
| `refresh-token` | Exchange the refresh token for a new 60-day access token; `--write-env` updates local `.env`. |
| `check-token` | Cheap authenticated ping; exit 1 when the token is rejected or within `--warn-days` (default 7) of expiry. |
| `verify --urn` | `GET /rest/posts/{urn}` (needs `r_organization_social`). |
| `self-test` | Offline assertions on payload shape, canonical URL, hashtags, brand guard. |

## Secrets & config

Secrets come from the environment **only** — local `.env` (gitignored) for dev, GitHub Actions secrets in CI. Never committed, never logged, never on a command line. See `.env.example`.

| Variable | Kind | Notes |
| --- | --- | --- |
| `LINKEDIN_ACCESS_TOKEN` | secret | 60-day token from the [token generator](https://www.linkedin.com/developers/tools/oauth/token-generator), scopes `w_organization_social r_organization_social`. |
| `LINKEDIN_REFRESH_TOKEN` | secret | optional; only issued to approved partners. Enables `refresh-token`. |
| `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` | secret | needed for refresh. |
| `LINKEDIN_ORG_URN` | var | defaults to `urn:li:organization:64517157`. Public, not a secret. |
| `LINKEDIN_BASE_URL` | var | defaults to `https://bash-365.com` (the canonical host and CNAME). |
| `LINKEDIN_API_VERSION` | var | `LinkedIn-Version`, `YYYYMM`; defaults to a recent value and expires ~yearly. |

## Idempotency

Every published share is recorded in `.github/linkedin-log.json`, keyed by canonical URL. A source already in the ledger is skipped (pass `--force` to override). The ledger lives under `.github/` so writing it never triggers a Jekyll rebuild.

## Layout

`config.py` settings · `net.py` HTTP + retry · `auth.py` token resolve/refresh · `images.py` thumbnail upload · `posts.py` payloads + create/get · `content.py` frontmatter → payload (reuses `content_lint.py`'s reader + banned-phrase list) · `ledger.py` idempotency · `__main__.py` CLI.

> Articles here are **link-shares** to site posts. The LinkedIn API cannot
> publish native long-form LinkedIn Articles.
