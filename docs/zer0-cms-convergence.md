# Converging the fleet into one CMS

Four repositories already build most of a content management system between them. None of them is the whole thing, and the seam that is actually missing is smaller than it looks. This is the design for closing it.

## What each repository already is

| Repository | What it contributes | Layer |
| --- | --- | --- |
| [`it-journey`](https://github.com/bamr87/it-journey) | `scripts/cms/cms.py` and the `.cms/` contract: a machine-readable index of every content file with a health score, freshness band, lane-classified issues, and a dated worklist | **Analysis** |
| [`zer0-CMS`](https://github.com/bamr87/zer0-cms) | A fork of Front Matter CMS — content types, taxonomy, media, snippets, data files, SEO checks, dashboard and panel — plus `src/zer0/`, which reads the `.cms/` contract and runs Claude agents behind an approve/deny diff gate | **Authoring** |
| [`zer0-image-generator`](https://github.com/bamr87/zer0-image-generator) | The three-stage image pipeline: Claude writes an art brief, an image model renders it, Claude reviews the render. Ships as a Jekyll gem, a Python engine, and a Rails control panel | **Media** |
| [`zer0-mistakes`](https://github.com/bamr87/zer0-mistakes) | The Jekyll theme and layouts; GitHub Pages delivery | **Presentation** |

Read as one system, that is: something that knows what the content *is*, something to edit it with, something to illustrate it, and something to render it. Four of the five layers a CMS needs.

## The seam

The layer nobody owns is **distribution** — carrying content off the site, and bringing the audience's response back.

That absence is not a missing feature so much as a broken circuit. The intended loop is:

```
        write ──────▶ publish ──────▶ engage ──────▶ cater ──────┐
          ▲                                                       │
          └───────────────────────────────────────────────────────┘
```

Today it runs `write → publish` and stops. `cms.py` can say a page is thin, stale, or missing a field, because those are properties of the file. It cannot say *"this subject earns attention and that one does not,"* because that evidence is not in the repository — it is in what readers did. So the arrow back into `write` has nothing on it, and what to write next is decided on instinct.

## The design: extend the bus, do not build beside it

The temptation is a separate publishing app with its own content model. That produces two definitions of "a page" which drift within a release.

`.cms/` is already a contract between two independent programs — the Python engine writes it, the TypeScript extension reads it through `src/zer0/cms-contract.ts`. It is, in effect, the fleet's message bus. So distribution becomes a **third participant on that bus**, reading the same index and extending the same directory.

```
              ┌──────────────────────────────────────────────────┐
              │            .cms/  — the contract                  │
              │  index/ · schema/ · reports/ · worklists/          │
              └───┬──────────────┬──────────────────┬─────────────┘
      writes      │              │ reads            │ reads + writes
                  │              │                  │
        ┌─────────▼──┐   ┌───────▼────────┐   ┌─────▼──────────────┐
        │  cms.py    │   │   zer0-CMS     │   │  zer0-distribute   │
        │  analysis  │   │   authoring    │   │  distribution      │
        └────────────┘   └───────┬────────┘   └─────┬──────────────┘
                                 │                   │
                     ┌───────────▼──────┐   ┌────────▼─────────┐
                     │ zer0-image-      │   │ LinkedIn         │
                     │ generator        │   │ (member + page)  │
                     └───────────┬──────┘   └────────┬─────────┘
                                 │                   │
                     ┌───────────▼───────────────────▼─────────┐
                     │  zer0-mistakes → Jekyll → GitHub Pages   │
                     └──────────────────────────────────────────┘
```

### What distribution reads

`.cms/index/content-index.json` — the same rows the authoring surface renders. A page is distributable when the engine already judged it fit: not a draft, not generated, not structural, and scoring at or above a health floor. Content below the floor is not a distribution problem; it is already on the engine's own worklist.

One index, many outputs. Nothing in the distribution lane decides what content is.

### What distribution writes

A new subtree, in the contract's own idiom:

```
.cms/distribution/
  performance.json              aggregate engagement, keyed by content path
  worklists/<date>-catering.md  what to write next
```

`performance.json` is the author's own post statistics — impressions, clicks, reactions, comments, shares — joined onto content paths through the publish ledger. Aggregate counts only; there is no per-member record anywhere in it.

`<date>-catering.md` is deliberately the same shape as the engine's `.cms/worklists/<date>.md`, so the authoring surface can render both in one list and a person reads one format. Where the engine's worklist says *what is wrong with what you have*, this one says *what to write next*, in four lanes:

| Lane | Question | Evidence |
| --- | --- | --- |
| **A** | What already scores well and has never been published? | index only — works before any analytics exist |
| **B** | Which subjects earned attention? | own aggregate engagement, grouped by the author's own collections |
| **C** | Which subjects consistently did not? | same, below the median |
| **D** | What performed and has since gone stale? | engagement × the engine's freshness band |

Lane A is the important one for a new user: it is real work, ranked, on day one, with no audience data and no writing required.

## Three design commitments

**Audience is declared, never derived.** Readers are described by the author in config — "engineering managers hiring backend developers," their words, their tone, their hashtags. Nothing reads connections, followers, or anyone's profile to infer an audience. Topic grouping uses the author's *own* collections rather than clustering, which keeps the whole loop inside data the author already owns.

**Aggregate only, one hop from the author.** The analytics lane's entire read surface is enumerable — `analytics.py` prints it — and everything on it returns the author's own content. Because catering consumes only what that module produces, the boundary holds for the loop by construction rather than by discipline.

**Nothing publishes without a person.** A draft is created `pending` and is inert. It becomes eligible only when a human moves it to `approved`. There is no scheduler, no queue-ahead, no timed release, no unattended mode. This is the same gate the authoring surface already applies to agent edits, applied to the outbound direction.

## Who it is for

Any business or individual who writes something worth reading and wants it to reach people: a consultancy publishing what it has learned, a developer building a portfolio out of shipped work, a team whose release notes deserve an audience, a person teaching what they just figured out.

The tool does not assume a marketing team, because the people who need it most do not have one. It assumes someone who writes and would rather not also become a publisher.

BASH Consulting is the first user, not the intended market. The site in this repository already publishes to its own company page through the pipeline's ancestor, which is where the design came from.

## Naming, and what happens to the existing parts

| Name | Was | Becomes |
| --- | --- | --- |
| **zer0-CMS** | the VS Code extension | the product — the CMS, of which the extension is the authoring surface |
| **zer0-distribute** | `prototype/shiplog/` in this repo | the distribution lane, a peer of the analysis engine on the `.cms/` bus |
| `scripts/features/linkedin/` | this site's company-page publisher | kept and unchanged; it is what the lane generalizes, and the workflows depend on it |

Nothing is deleted. `scripts/features/linkedin/` still publishes this site's articles, and the lane converges on the same Posts API payload shape it proved out.

## Status

Running today, offline, with no credentials — [`prototype/zer0-distribute/`](../prototype/zer0-distribute/):

- reads a real `.cms/` index (validated against it-journey's own: 380 files, 330 distributable);
- falls back to git and the filesystem when a repository has no `.cms/`, so it is useful before a site adopts the engine;
- composes drafts for declared audiences with a filler, length, and weak-hook guard;
- the `pending → approved → published` queue and the local review dashboard;
- resolves the preview image zer0-image-generator already produced, and emits the generator's brief when there is none;
- ingests aggregate post statistics and writes both `performance.json` and the catering worklist;
- an offline self-test whose assertions fail if `publish` ever picks up an unapproved draft, if the analytics read surface grows a call touching another member, or if a topic is ranked on a single observation.

Not built, and not to be described as built: the live LinkedIn write, the live statistics read, comment reading and replying, and any hosted multi-tenant service. `publish` renders its request and stops, because the app has not been granted API access — and a stub that faked success would put invented numbers into the catering worklist, which is worse than an empty one.

## The next moves, in order

1. **Fold `.cms/` generation out of it-journey into a shared engine.** Today `cms.py` lives in one site. It should be installable, the way the image generator already is, so any repository can produce the contract. Until then, distribution's fallback path carries repositories that have no engine.
2. **Render the catering worklist in the authoring surface.** `src/zer0/cms-contract.ts` already parses the engine's output; teaching it `.cms/distribution/worklists/` puts "what to write next" next to "what to fix" in the editor where writing happens.
3. **Wire the image handoff both ways.** The lane finds an existing preview today. It should be able to request one and wait, so a page with no image is not a dead end.
4. **Land the LinkedIn grant, then implement the two live calls.** One write, one read. Everything else already exists.
