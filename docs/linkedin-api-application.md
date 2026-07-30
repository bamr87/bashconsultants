# LinkedIn Community Management API — application answers

The text we submit for the LinkedIn Developer application. The form asks two things: one description of the business and product, then a per-use-case description for each capability we request.

> *Tell us about your business and the product that will leverage Community
> Management API access. Please provide a detailed description otherwise your
> application will be rejected.*

> *For each use case below, please provide a detailed description. What use case
> does your organization plan to enable with the Community Management APIs?*
> **Page management** — create and manage company posts, comments, and reactions,
> and monitor engagement. **Profile management** — the same, on behalf of
> individual profiles. **Page analytics** — track post analytics and performance.

> *Please provide a screen recording of the application for this submission.*

The app under review is **zer0-CMS**, a headless content management system. The component that talks to LinkedIn is its distribution lane, [`prototype/zer0-distribute/`](../prototype/zer0-distribute/). Architecture: [`zer0-cms-convergence.md`](./zer0-cms-convergence.md). Recording: [`prototype/zer0-distribute/demo/`](../prototype/zer0-distribute/demo/).

**Read this before editing.** The product's users are the people who own the content — a business publishing to its own page, an individual publishing to their own profile — so **both Page management and Profile management are primary**, and the analytics use case is what closes the loop between them. Four things carry the application, and weakening any one turns it into a request LinkedIn refuses: every post is approved by whoever's name goes on it; each account is authorized by its own owner's consent; the audience someone writes for is **declared by them, never derived from LinkedIn data**; and everything read back is the author's **own aggregate** numbers. Keep present-tense claims and roadmap separate — the prototype is honest about what does not exist yet.

## Business and product (paste as plain text)

**Our business.** BASH Consulting LLC is a Denver, Colorado software and information technology (IT) consultancy serving small and medium-sized businesses. We build and run the systems a business depends on — cloud infrastructure, Enterprise Resource Planning (ERP) and accounting platforms, data architecture, and automation with an artificial intelligence (AI) overlay — and we build content tooling alongside the client work, in the open, at https://bash-365.com. The practice is owner-operated by Amr Abdel-Motaleb.

**The product: zer0-CMS, a headless content management system.** It manages a site's content as files in the owner's own repository rather than rows in someone else's database, and it covers the whole loop a publisher actually has: write, publish, engage, and decide what to write next from how the audience responded. It is assembled from four open-source components we develop — a content engine that indexes and scores every page, an editing surface built on Front Matter CMS, an image pipeline that produces social and preview art, and a Jekyll theme that renders the site. LinkedIn is where its distribution layer sends content.

**Who it is for.** Any business or individual with something worth reading and no publishing operation to push it out: a consultancy sharing what it has learned, a small business owner explaining their trade, a developer building a portfolio from shipped work, a team whose release notes deserve an audience, someone teaching what they just figured out. It deliberately does not assume a marketing department, because the people who need it most do not have one. It assumes someone who writes and would rather not also become a publisher.

**The problem it solves.** People who make things produce a great deal of writing as a byproduct: documentation, release notes, guides, explanations, answers to a question a customer asked twice. Almost none of it reaches anyone, because "write a LinkedIn post" is a separate task with a blank page and an unfamiliar register. So it stays on the site, or in the repository, and the person has nothing public to show when they need it — looking for clients, for a role, for collaborators, for contributors. And when they do post, they have no idea which subjects landed, so the next choice is a guess.

**How it works, concretely.** The engine indexes the site and scores every page for completeness and freshness. The distribution lane reads that index — the same one the editor reads, so there is one definition of a page — and lists what is fit to publish: nothing that is a draft, generated, structural, or scoring below a health floor. The author picks a piece and an audience they defined themselves, and the tool composes a post from the page's own opening and the audience's tone. They review it in a dashboard, beside the exact API request it would become and the point where LinkedIn truncates it, and approve it. Approving is what publishes it. The post's preview image is the one the image pipeline already made for the page, not a new one.

**The loop closes with analytics.** The lane reads back the aggregate performance of the author's own posts and writes it into the CMS as a worklist of what to write next, in four lanes: content that scores well and has never been published (real work on day one, before any audience data exists); subjects that earned attention; subjects that consistently did not; and content that performed and has since gone stale, where refreshing beats starting over. The content engine can already say a page is thin or out of date, because that is in the file. It cannot say which subject an audience cares about. That is the gap this closes, and it is the reason the analytics use case matters as much as the publishing ones.

**Status, stated plainly.** The engine, the editing surface, the image pipeline, and the theme are all in use on live sites today. The distribution lane is a working prototype: the contract reader, discovery, composition, the audience profiles, the approval queue, the review dashboard, the payload builder, the image handoff, the analytics ingest, the catering worklist, and an offline test suite all run end to end with no network access. It has been validated against a real 380-page content index. What does not exist is the pair of live LinkedIn calls — one write, one statistics read — which is what this application is for. We chose not to stub them: a tool that reports a post it never sent is bad, and invented engagement numbers would poison the worklist that decides what gets written.

**Volume.** Low by design. This publishes considered posts about real work — a few per author per month. There is no scheduler, no bulk mode, and no timed release anywhere in the product, so nothing in it rewards or enables volume.

**Our privacy policy is at https://bash-365.com/privacy/.**

## Use-case answers (paste as plain text, one per box)

### Page management

A business publishing its own content to its own LinkedIn page, with a named person approving every post.

What we do with it. Create posts on a page the authenticated user administers via POST /rest/posts with author urn:li:organization:{id}. The content comes from that organization's own site: a page out of the CMS index, shared with the preview image the image pipeline already produced for it. We read the post back with GET /rest/posts/{urn} to confirm it published, and record the returned URN in a ledger keyed by content path, so the same page is never posted twice and its later performance can be attributed to it.

Comments and reactions. We want a business to answer the replies its own posts attract, from the same place the post was written, rather than losing the thread. A reply is drafted, a person reads it, a person sends it. We also want to moderate the organization's own threads — hiding or removing spam and abuse. There is no automated replying.

Scopes requested: w_organization_social and r_organization_social, only for pages the authenticated user administers, verified through LinkedIn rather than asserted by us.

The approval gate, which is the part we would ask a reviewer to look at first. A draft is created with status pending and is inert. It becomes eligible to publish only when a person moves it to approved — a click in the review dashboard or an explicit command — and the publish step reads nothing else. There is no scheduler, no queue-ahead, no timed release, and no unattended mode anywhere in the product. The screen recording shows this: a draft sitting pending, the payload it would become, and a person clicking Approve.

Our own use, as evidence. BASH Consulting's website repository already publishes its articles to our own company page (urn:li:organization:64517157) through this pipeline's ancestor, gated on a human merging the draft. That code is in the open, and we are the first user of what we are describing.

### Profile management

An individual publishing their own work to their own LinkedIn profile, with their explicit approval on every post. For a sole trader, a consultant, or a developer, the profile is where their audience actually is — the page is the smaller channel, and often there is no page at all.

What we do with it. Create a post on the authenticated member's own profile via POST /rest/posts with author urn:li:person:{id}, from a draft that member has read and approved. Read that same member's own posts back to confirm publication and to show them how their own posts performed.

Scope requested: w_member_social to publish, and member read access limited to the authenticated member's own content.

Consent. Each person connects their own account through their own three-legged OAuth consent, and can revoke it from LinkedIn at any time without involving us. We hold no credential that lets us act as a member who has not personally authorized it, and there is no administrative path, impersonation mode, or shared token that could produce one.

Comments on their own posts. Same as the page case and the same gate: a reply is drafted, the member reads it, the member sends it. No automated replying, liking, or reacting.

What we will not do, and have not built. We will not post, comment, or react as any member who has not personally authorized it. We will not read other members' profiles, connections, followers, or feeds. There is no automated engagement of any kind — no auto-liking, auto-commenting, auto-following, auto-connecting — and no messaging or InMail. We do not scrape LinkedIn. Member data is not sold, shared, or used to train a model.

On audience targeting, because the words invite a wrong reading. Our tool helps someone write *for* an audience they described in their own configuration file — "engineering managers hiring backend developers," in their words, with the tone and hashtags they chose. It does not identify, enumerate, segment, or target individual members, and it derives nothing from connections or followers. Even the topic grouping in our analytics uses the author's own content categories rather than clustering anything about people. There is no code path in the product that requests member data for this, and adding one would be a change to a published design commitment rather than an implementation detail.

### Page analytics

This is what closes the loop, and it is the reason the product exists rather than a reporting add-on.

What we would read. Aggregate statistics for the author's own posts and, where a page is connected, their own page: impressions, clicks, reactions, comments, shares, engagement rate per post, and follower and visitor counts over time. Read-only, through the organization share and page statistics endpoints under r_organization_social, and the equivalent own-post statistics for a member. That list is the entire read surface — the tool prints it on request, so it can be audited before any credential is granted.

What the author gets. Their own numbers, joined back onto their own pages, turned into four plain answers. Which of their subjects people actually read, so the next piece is chosen on evidence. What cadence they are really keeping, against what they think they are keeping. Which content performed and has since gone stale, where an update beats a new post. And a track record — volume, streak, subjects, the work each post came from — which is the honest version of a personal or company brand: a record of what someone published and explained, rather than a claim about themselves.

Why it goes back into the CMS. The statistics are written into the content management system as a worklist beside the one the content engine already produces. The engine's worklist says what is wrong with the content you have; this one says what to write next. Putting them in the same format and the same place means the person doing the writing sees both without leaving the editor.

Boundaries. Statistics stay aggregate and belong to the author whose content produced them. We do not build profiles of individual members, do not attempt to identify anyone inside an aggregate count, do not join LinkedIn metrics to any other dataset about a person, and do not expose one author's numbers to another. Nothing is sold or shared with a third party, and no LinkedIn data trains a model. Retention is limited to what a trend line needs. A subject is never ranked on a single observation, so no one post's numbers become a conclusion.

## Screen recording (what we submit and what it shows)

`prototype/zer0-distribute/demo/recording/` — a live capture of the distribution lane's review dashboard, running against a real 380-page content index, ending with a person approving a post.

In order: the review queue, with posts composed from real pages in a real CMS index · a draft with the marker showing where LinkedIn truncates it · the exact POST /rest/posts payload that draft becomes, with the author URN and scope named · **what to write next**, computed from the author's own aggregate post statistics — how much content is distributable, how much has been distributed, and which subjects earned attention · the audience profiles the copy was written for, with the note that they are declared and not derived · a person clicking Approve, and the pending counter dropping to zero.

**It does not show a post reaching LinkedIn, and it says so.** The app has no API access, so publish renders the payload and stops. Recording a fabricated success would misrepresent the app to the reviewer assessing it. If LinkedIn would like to see the live call, we will record it the day the grant lands.

Everything in it is live: the dashboard is served from files on disk, the drafts were composed from a real content index, and the Approve click rewrites the draft — verifiable before and after. [`demo/README.md`](../prototype/zer0-distribute/demo/README.md) reproduces it from scratch and carries the narration script.

## If we are asked for more

Answers we can give without inventing anything:

- **What exists vs. what is planned.** Running now: the `.cms/` contract reader
(validated against a real 380-file index) with a git-and-filesystem fallback for repositories that have no engine; audience profiles; deterministic composition with a filler, length and weak-hook guard; the pending/approved/published queue; the review dashboard; the payload builder for member and organization authors; the preview-image handoff; aggregate analytics ingest; the catering worklist; the track record; and an offline self-test covering all of it. Not built, and not to be described as built: the live LinkedIn write, the live statistics read, comment reading and replying, and any hosted multi-tenant service. Keep that line in every answer — an overstated capability is the fastest way to lose a grant after it is issued.
- **How the pieces relate.** One contract directory (`.cms/`) is the interface
between the content engine, the editing surface, and the distribution lane. Three independent programs read and write it. That is why the loop can close without any component knowing about the internals of another, and why publishable content has exactly one definition.
- **No model is required anywhere in the path.** Discovery, composition, the
payload, and the analytics ranking are plain deterministic code. A language model can improve a draft the author is already looking at. It is never the only way to get one, and it never publishes.
- **Where credentials live.** Environment variables only — a gitignored local
`.env` in development, secrets storage in continuous integration. Never committed, never logged, never passed on a command line. A hosted version would hold each account's token encrypted and scoped to that account alone.
- **Idempotency and rate.** One page produces one post: the ledger is keyed by
content path, and a page already in it is skipped rather than retried. Volume is bounded by how often the author publishes and chooses to share it.
- **The code.** [`prototype/zer0-distribute/`](../prototype/zer0-distribute/) —
standard-library Python, no dependencies, readable in full. `python3 prototype/zer0-distribute self-test` runs the assertions offline, including the ones that fail if publish ever picks up a draft nobody approved, if the analytics read surface grows a call that touches another member, or if a subject is ranked on a single observation.
