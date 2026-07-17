# `features/posthog` — server-side PostHog integration

Talks to the PostHog REST API with the **personal API key** (`POSTHOG_API_KEY`, prefix `phx_`) held in `.env` / Actions secrets — distinct from the public project (write) key the site ships in `_config.yml` (`posthog.api_key`, prefix `phc_`, used client-side to send events). Stdlib-only Python, same discipline as `scripts/content_lint.py`.

## Run it

```bash
python3 scripts/features/posthog verify     # is the site wired to the right project? settings drift?
python3 scripts/features/posthog settings   # print the project's privacy-relevant settings
python3 scripts/features/posthog annotate --content "Deployed <sha>" [--dry-run]
```

## Commands

| Command | Purpose |
| --- | --- |
| `verify` | Fetches the project and confirms `posthog.api_key` in `_config.yml` matches the live project's token (so events actually reach it), then reports the privacy posture — IP anonymization, session-recording opt-in, event retention. Exits non-zero on a key mismatch. Good as a CI health check. |
| `settings` | Prints the project's privacy-relevant settings. |
| `annotate` | Posts a project annotation (a dated marker) — wire it into a deploy step so releases line up with the analytics. `--dry-run` renders without posting. |

## Config

Non-secret values come from `_config.yml`'s `posthog:` block (`api_key`, `project_id`, `api_region`) so there is one source of truth; override with `POSTHOG_PROJECT_ID` / `POSTHOG_API_REGION` / `POSTHOG_PROJECT_KEY`. The secret personal key comes only from `POSTHOG_API_KEY` in the environment — never a tracked file, never logged. Create one at
<https://us.posthog.com/settings/user-api-keys>.

## Notes

- **Region:** US project — REST API host is `https://us.posthog.com`; event
  ingestion (client) is `https://us.i.posthog.com`.
- **Event retention** is plan-controlled on PostHog Cloud and is not settable
  through the project API; `verify` reports the current value for visibility.
- The site's tracking was previously pointed at the zer0-mistakes theme's demo
  key; `verify` guards against that regressing.
