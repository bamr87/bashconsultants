# shiplog — publish what you ship

A developer's publishing tool. It turns the work you already wrote down — commits, tags, changelog entries, blog posts, docs — into LinkedIn posts, so a track record accumulates in public instead of dying in a private repository.

The problem it solves is not writing. Developers write constantly. The problem is that none of it reaches the place where opportunities, collaborators, and clients actually look, because "write a LinkedIn post" is a different task with a different tone and a blank page in front of it. shiplog starts from something you already finished.

```
$ python3 prototype/shiplog sources
$ python3 prototype/shiplog draft tag:v0.4.0 --audience backend-hiring
$ python3 prototype/shiplog serve          # review + approve in a local dashboard
$ python3 prototype/shiplog publish        # posts what you approved
```

**Status: prototype.** The pipeline is real and runs end to end offline. The final call to LinkedIn is stubbed behind `--dry-run` until the app is granted Community Management API access; `preview` renders the exact payload that call will carry.

## Design commitments

These are the load-bearing ones. They are why the tool is shaped the way it is.

1. **Nothing publishes without a person.** Every draft lands in a queue at `status: pending` and stays there. Approval is an explicit act — a click in the local dashboard or a git merge — and `publish` only ever touches drafts a human marked `approved`. There is no scheduler, no auto-post, and no unattended mode.
2. **Deterministic first, model second.** Source discovery, payload construction, and the portfolio view are plain code with no model in the path. Drafting uses a template per source kind and can run with no API key at all. A model improves a draft; it is never required to produce one.
3. **Audience is declared, never derived.** You describe who you are writing for in `shiplog.toml`. The tool does not read your connections, your followers, or anyone's profile to infer an audience. See `compose.py`.
4. **Your data stays yours.** Drafts and the published ledger are files in your repository. There is no shiplog server and no account.

## Commands

| Command | What it does |
| --- | --- |
| `init` | Write a starter `shiplog.toml` and create `.shiplog/`. |
| `sources` | Discover publishable material in this repository. Each gets a stable id. |
| `audience` | List the audience profiles declared in config. |
| `draft <source-id>` | Compose a draft for one source into the queue at `status: pending`. |
| `queue` | List drafts and their status. |
| `preview [id]` | Render the exact LinkedIn API payload. Zero network calls. |
| `approve <id>` | Mark a draft approved (what the dashboard button calls). |
| `publish` | Publish every `approved` draft, then record it in the ledger. `--dry-run` to rehearse. |
| `portfolio` | Your published track record: volume, cadence, topics, streak. |
| `serve` | Local review dashboard on `http://127.0.0.1:8765`. |
| `self-test` | Offline assertions across the whole pipeline. |

## Where the LinkedIn API comes in

Two author identities, same Posts API shape:

- **A developer's own profile** — the primary case. `w_member_social`, author `urn:li:person:{id}`. This is where a developer's portfolio and reputation actually live.
- **An organization page** — for a team, a product, or an open-source project. `w_organization_social`, author `urn:li:organization:{id}`.

Read access (`r_member_social` / `r_organization_social`) is used for two things only: confirming a post published, and reading back the performance of the author's **own** posts to build the portfolio view.

## Layout

`core.py` config, frontmatter, queue and ledger I/O · `sources.py` repository discovery · `compose.py` audience profiles and draft composition · `payload.py` LinkedIn payloads · `portfolio.py` track-record statistics · `server.py` the review dashboard · `selftest.py` offline assertions · `__main__.py` CLI.

Standard library only, Python 3.11+. No `pip install`, no dependencies, no network except the publish call itself.
