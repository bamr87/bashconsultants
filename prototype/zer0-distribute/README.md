# zer0-distribute — the distribution lane of zer0-CMS

The CMS engine indexes and scores your content. The authoring surface edits it. The theme renders it. This lane carries it **off** the site — to LinkedIn today — and brings the audience's response **back**, so the next thing you write is chosen on evidence rather than instinct.

```
write ──▶ publish ──▶ engage ──▶ cater ──▶ write
  │           │          │          │
authoring  this lane  this lane  .cms/distribution/worklists/
```

Full design, and how the four repositories fit together: [`docs/zer0-cms-convergence.md`](../../docs/zer0-cms-convergence.md).

```bash
python3 prototype/zer0-distribute cms                    # what the .cms/ contract says
python3 prototype/zer0-distribute sources                # what is publishable
python3 prototype/zer0-distribute draft content:my-post --audience practitioners
python3 prototype/zer0-distribute serve                  # review + approve in a dashboard
python3 prototype/zer0-distribute publish                # sends what you approved
python3 prototype/zer0-distribute analytics --ingest stats.json
python3 prototype/zer0-distribute cater                  # what to write next
```

**Status: prototype.** Everything above runs end to end offline. The two live LinkedIn calls — one write, one statistics read — are not implemented, because the app has not been granted Community Management API access. `publish` renders the exact request and stops; `analytics` prints the reads it would make. A stub that faked success would put invented numbers into the catering worklist, which is worse than an empty one.

## It plugs into the contract, it does not replace it

With a `.cms/` index present, publishable material is whatever the index says is publishable — the same rows the authoring surface renders, with the same health scores and freshness bands. A page qualifies when the engine already judged it fit: not a draft, not generated, not structural, scoring at or above the health floor. Content below the floor is not a distribution problem; it is already on the engine's own worklist.

Without a `.cms/`, discovery falls back to reading git and the filesystem — tags, conventional commits, changelog sections, markdown docs — so the tool is useful on a repository that has never run the engine.

What it writes back:

```
.cms/distribution/
  performance.json               aggregate engagement, keyed by content path
  worklists/<date>-catering.md   what to write next, in the engine's own format
```

## Design commitments

The load-bearing ones. They are why the tool is shaped this way.

1. **Nothing publishes without a person.** Every draft lands `pending` and is inert. It becomes eligible only when a human moves it to `approved` — a click in the dashboard or an explicit command — and `publish` reads nothing else. No scheduler, no queue-ahead, no timed release, no unattended mode.
2. **Audience is declared, never derived.** You describe who you write for in `zer0-distribute.toml`. Nothing reads your connections, your followers, or anyone's profile to infer an audience. Topic grouping uses your own collections, not clustering. See `compose.py` and `catering.py`.
3. **Aggregate only, one hop from you.** The analytics read surface is short enough to print — run `analytics` and it does. Everything on it returns your own content. Catering consumes only what that module produces, so the boundary holds for the whole loop by construction.
4. **Deterministic first, model second.** Discovery, composition, payload building, and catering are plain code. A draft exists with no API key and no model in the path. A model improves a draft a human is already reading; it is never required to produce one, and it never publishes.
5. **Your data stays yours.** Drafts, the ledger, and the worklists are files in your repository. There is no server and no account.

## Commands

| Command | What it does |
| --- | --- |
| `init` | Write a starter `zer0-distribute.toml` and create the queue. |
| `cms` | What the `.cms/` contract says, and what this lane has added to it. |
| `sources` | Publishable material — the index first, git and the filesystem as fallback. |
| `audience` | The audience profiles you declared. |
| `draft <source-id>` | Compose a draft into the queue at `pending`. |
| `queue` | Drafts and their status. |
| `preview [id]` | The exact LinkedIn payload. Zero network calls. |
| `approve <id>` | Mark a draft approved. The gate. |
| `publish` | Send every `approved` draft. `--dry-run` to rehearse. |
| `record <id>` | Record a published post in the ledger. |
| `media [path]` | Which preview image each page would share with. |
| `analytics` | The read surface; `--ingest <file>` to load statistics. |
| `cater` | The catering worklist. `--print` to see it without writing. |
| `portfolio` | Your published track record. |
| `serve` | The review dashboard on `http://127.0.0.1:8765`. |
| `self-test` | Offline assertions across the whole lane. |

## Where the LinkedIn API comes in

Two author identities, one payload shape:

- **An individual's own profile** — `w_member_social`, author `urn:li:person:{id}`. Each person authorizes their own account through their own consent.
- **An organization page** — `w_organization_social`, author `urn:li:organization:{id}`, for a page the authenticated user administers.

Read access is used for exactly two things: confirming a post published, and reading back the aggregate performance of the author's **own** posts to build the portfolio and the catering worklist.

## Media

A LinkedIn share wants the same social image the site already has. `media.py` finds it — from the page's `preview:` frontmatter, or the conventional `assets/images/previews/<slug>.*` path — and when there is none, emits the brief that zer0-image-generator's analyze stage takes. Rendering stays in the generator, where the provider matrix, the review stage, and the credential chain already live.

## Layout

`core.py` config, frontmatter, queue, ledger · `contract.py` the `.cms/` bus, read and write · `sources.py` discovery, index-first · `compose.py` audiences and composition · `payload.py` LinkedIn payloads · `media.py` the image handoff · `analytics.py` the read surface and ingest · `catering.py` what to write next · `portfolio.py` the track record · `server.py` the review dashboard · `selftest.py` offline assertions · `__main__.py` the CLI.

Standard library only, Python 3.11+. No dependencies, no network except the publish and statistics calls themselves.
