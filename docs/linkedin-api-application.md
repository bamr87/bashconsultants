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

The app under review is **shiplog** ([`prototype/shiplog/`](../prototype/shiplog/)), a publishing tool for developers. The recording and how to reproduce it: [`prototype/shiplog/demo/`](../prototype/shiplog/demo/).

**Read this before editing.** The application is for a product with individual developers as its users, so **Profile management is the primary use case** — a developer publishing to their own profile. That is a larger ask than a company posting to its own page, and it will be read more carefully. Three things carry the application, and weakening any of them turns it into the kind of request LinkedIn refuses: every post is approved by the person whose name goes on it, each developer authorizes their own account through their own consent, and the audience a developer writes for is **declared by them, never derived from LinkedIn data**. Keep present-tense claims and roadmap separate; the prototype is honest about what does not exist yet.

## Business and product (paste as plain text)

**Our business.** BASH Consulting LLC is a Denver, Colorado software and information technology (IT) consultancy serving small and medium-sized businesses. We build and run the systems a business depends on — cloud infrastructure, Enterprise Resource Planning (ERP) and accounting platforms, data architecture, and automation with an artificial intelligence (AI) overlay — and we build developer tooling alongside the client work, in the open, at https://bash-365.com. The practice is owner-operated by Amr Abdel-Motaleb.

**The product: shiplog, a publishing tool for developers.** Developers produce a great deal of writing as a byproduct of doing their job: commit messages, release notes, changelog entries, architecture decisions, postmortems, internal docs. Almost none of it reaches anyone outside the repository. The obstacle is not time or modesty — it is that "write a LinkedIn post" is a different task from "write a release note," with a blank page and an unfamiliar register, so the work stays private. The cost lands later, when that developer is looking for a role, a client, a collaborator, or contributors to a project, and has no public record of what they can actually do.

shiplog starts from work that is already finished. It reads the developer's own repository — git tags, conventional commits, `CHANGELOG.md`, markdown docs — and composes a LinkedIn post from a chosen piece of it. The developer picks who they are writing for from audience profiles they defined themselves, reviews the draft in a local dashboard next to the exact API request it would become, edits it, and approves it. Approving is what publishes it. Over time the tool keeps a record of what was published, so a developer can see their own cadence, topics, and track record instead of guessing.

**Concretely, the flow is four steps.** `sources` lists what is publishable in this repository. `draft <source>` composes a post for a declared audience and puts it in a queue at status `pending`. `serve` opens a local review dashboard where the developer reads the draft, the character count, where LinkedIn will truncate it, and the full outgoing payload. `publish` sends only what a human moved to `approved`.

**Who uses it.** Individual developers, publishing to their own LinkedIn profiles, each authorizing their own account through their own OAuth consent and able to revoke it at any time. A team or an open-source project can additionally connect a page they administer, so a release can go out under the project's name as well as the maintainer's. There is no version of shiplog that posts as a member who has not personally authorized it.

**Status, stated plainly.** shiplog is a working prototype. Source discovery, composition, the audience profiles, the review dashboard, the approval gate, the payload builder, the portfolio view, and an offline test suite all exist and run end to end with no network access. The one thing that does not exist is the live call to LinkedIn: the app has no API access yet, which is what this application is for, so `publish` renders the request and stops. We chose not to stub a fake success — a tool that lies to its user about having posted is worse than one that plainly cannot yet.

**Volume.** Low by design and by nature. This is a tool for publishing considered posts about real work, not a scheduler: on the order of a few posts per developer per month. Nothing in the product rewards or enables volume, and there is no bulk, queue-ahead, or timed-release mode.

**Our privacy policy is at https://bash-365.com/privacy/.**

## Use-case answers (paste as plain text, one per box)

### Profile management — our primary use case

A developer publishing their own work to their own LinkedIn profile, with their explicit approval on every post. This is the centre of the product; the other two use cases support it.

What we do with it. Create a text post on the authenticated member's own profile via POST /rest/posts with author urn:li:person:{id}, from a draft that member has read and approved in the review dashboard. Read that same member's own posts back to confirm publication and to show them how their own posts performed.

Scope requested: w_member_social to publish, and member read access limited to the authenticated member's own content.

Consent. Each developer connects their own account through their own three-legged OAuth consent, and can revoke it from LinkedIn at any time without asking us. We hold no credential that lets us act as a member who has not personally authorized us, and there is no administrative path, impersonation mode, or shared token that would produce one.

The approval gate, which is the part we would ask a reviewer to look at first. A draft is created with status pending and is inert. It becomes eligible to publish only when the member moves it to approved — a click in the dashboard or an explicit command. `publish` reads nothing else. There is no scheduler, no queue-ahead, no timed release, and no unattended mode anywhere in the product. The screen recording shows this: a draft sitting pending, the payload it would become, and a person clicking Approve.

Comments and reactions on the member's own posts. We want a developer to be able to answer the replies their own post attracts, from the same place they wrote it, rather than losing the thread. Same gate: a reply is drafted, the member reads it, the member sends it. No automated replying.

What we will not do, and have not built. We will not post, comment, or react as any member who has not personally authorized it. We will not read other members' profiles, connections, followers, or feeds. There is no automated engagement of any kind — no auto-liking, auto-commenting, auto-following, auto-connecting, and no messaging or InMail. We do not scrape LinkedIn. Member data is not sold, shared, or used to train a model.

On audience targeting, because the words invite a wrong reading. shiplog helps a developer write *for* an audience they have described in their own configuration file — "engineering managers hiring backend developers," in their words, with the tone and hashtags they chose. It does not identify, enumerate, segment, or target individual members, and it derives nothing from their connections or followers. There is no code path that requests member data for this, and adding one would be a change to a published design commitment rather than an implementation detail.

### Page management

The same publishing flow, for a page the developer administers: a team's page, a product's page, or an open-source project's page. A maintainer usually wants a release to be visible under both their own name and the project's.

What we do with it. Create posts on a page the authenticated user administers via POST /rest/posts with author urn:li:organization:{id}, from the same reviewed-and-approved draft queue — the only structural difference from a profile post is the author URN. Read the post back to confirm it published. Read and reply to comments on the page's own posts so a maintainer can answer questions about their own release, and moderate spam and abuse in those threads.

Scope requested: w_organization_social and r_organization_social, only for pages the authenticated user administers, verified through LinkedIn rather than asserted by us.

Same gate, same refusals. Every page post is a draft a person approved. No automated posting or replying, no acting on a page whose administrator has not connected it.

Our own use, for what it is worth as evidence. BASH Consulting's website repository already publishes its articles to our own company page (urn:li:organization:64517157) through the same draft-then-approve pipeline, gated on a human merging the draft. That code is in the open and is where shiplog started; we are the first user of the thing we are describing.

### Page analytics

So a developer can tell whether any of this is working, and see a track record accumulate.

What we would read. Aggregate statistics for the author's own posts and, where a page is connected, their own page: impressions, clicks, reactions, comments, shares, engagement rate per post, and follower and visitor counts over time. Read-only, through the organization share and page statistics endpoints under r_organization_social, and the equivalent own-post statistics for a member.

What the developer gets. Three plain answers. Which of their own topics and formats people actually read, so the next post is chosen on evidence. What cadence they are really keeping, against what they think they are keeping. A portfolio view — volume, streak, subjects, the work each post came from — which is the honest version of a personal brand: a record of what someone shipped and explained, rather than a claim about themselves.

Boundaries. Statistics stay aggregate and belong to the author whose content produced them. We do not build profiles of individual members, do not attempt to identify anyone inside an aggregate count, do not join LinkedIn metrics to any other dataset about a person, and do not expose one developer's numbers to another. Nothing is sold or shared with a third party, and no LinkedIn data trains a model. Retention is limited to what a trend line needs.

## Screen recording (what we submit and what it shows)

`prototype/shiplog/demo/recording/shiplog-review-gate.mp4` — 33 seconds, 1280×800, H.264. A live capture of the prototype's review dashboard, ending with a person approving a draft.

In order: the queue as a developer opens it · a draft composed from the demo repository's own v0.6.0 release tag, with the marker showing where LinkedIn truncates the post · the exact POST /rest/posts payload that draft becomes, with the member author URN and the w_member_social scope named · the developer's accumulated track record · the audience profiles the copy was written for, with the note that they are declared and not derived · a person clicking Approve, and the pending counter dropping to zero.

**It does not show a post reaching LinkedIn, and it says so.** The app has no API access, so `publish` renders the payload and stops. Recording a fabricated success would misrepresent the app to the reviewer assessing it. If LinkedIn would like to see the live call, we will record it the day the grant lands.

Everything in it is live: the dashboard is served from files on disk, the drafts were composed by shiplog from the demo repository's real git history, and the Approve click rewrites the draft — verifiable with `queue` before and after. [`demo/README.md`](../prototype/shiplog/demo/README.md) reproduces the whole thing from scratch, and carries the narration script if we add a voice-over.

## If we are asked for more

Answers we can give without inventing anything:

- **What exists vs. what is planned.** Running now: source discovery from git
tags, conventional commits, changelog sections and markdown docs; audience profiles; deterministic draft composition; the filler-and-length guard; the pending/approved/published queue; the review dashboard; the payload builder for both member and organization authors; the portfolio view; the local ledger; and an offline self-test covering all of it. Not built, and not to be described as built: the live LinkedIn call, comment reading and replying, analytics ingestion, and any multi-developer hosted service. Keep that line in every answer — an overstated capability is the fastest way to lose a grant after it is issued.
- **Why a dashboard for a command-line tool.** Approving copy is reading, and a
browser is where reading is comfortable. Every dashboard action exists as a command too, and the dashboard holds no state of its own — it reads and writes the same files. It exists so the decision that matters happens somewhere legible.
- **No model is required.** Draft composition is a deterministic template per
source kind. A language model can improve a draft the developer is already looking at; it is never the only way to get one, and it never publishes.
- **Where credentials live.** Environment variables only — a gitignored local
`.env` in development, secrets storage in continuous integration. Never committed, never logged, never passed on a command line. A hosted version would hold each developer's token encrypted and scoped to that developer alone.
- **Idempotency and rate.** One source produces one post: the local ledger is
keyed by source, and a source already in it is skipped rather than retried. Volume is bounded by how often a developer ships and chooses to write about it.
- **The code.** [`prototype/shiplog/`](../prototype/shiplog/) — standard-library
Python, no dependencies, readable in full. `python3 prototype/shiplog self-test` runs the assertions offline, including the ones that fail if `publish` ever picks up a draft a human did not approve.
