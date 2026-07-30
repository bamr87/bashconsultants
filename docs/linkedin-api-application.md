# LinkedIn Community Management API — application answers

The text we submit for the LinkedIn Developer application. The form asks two things: one description of the business and product, then a per-use-case description for each capability we request.

> *Tell us about your business and the product that will leverage Community
> Management API access. Please provide a detailed description otherwise your
> application will be rejected.*

> *For each use case below, please provide a detailed description. What use case
> does your organization plan to enable with the Community Management APIs?*
> **Page management** — create and manage company posts, comments, and reactions,
> and monitor engagement. **Page analytics** — track post analytics and
> performance. **Profile management** — create and manage posts, comments, and
> reactions, and monitor engagement, on behalf of individual profiles.

Access to that API is the prerequisite for everything in [`automation.md`](./automation.md#workflow-linkedin-publishing) — the publisher cannot post without the `w_organization_social` + `r_organization_social` scopes. Keep this answer factual and in step with what `scripts/features/linkedin/` actually does; reviewers reject vague submissions, and a claim we cannot back is worse than a short answer. `docs/` is excluded from the Jekyll build, so this never ships as a page.

**Why the roadmap is in the answer.** Managing a page we do not own is a different kind of access than publishing to our own, and LinkedIn reviews it separately. Disclosing the intent up front — with the boundary stated plainly — is better than having a multi-organization product surface later against a grant that was approved as first-party. The present-tense claims and the forward-looking ones are kept in separate sections on purpose; do not blur them when editing.

## Business and product (paste as plain text)

**Our business.** BASH Consulting LLC is a Denver, Colorado information technology (IT) consultancy serving small and medium-sized businesses. We design, implement, and support the systems a business runs on: cloud infrastructure, Enterprise Resource Planning (ERP) and accounting platforms, data architecture, and automation with an artificial intelligence (AI) overlay. Alongside client work we build and publish our own tooling — a governed content pipeline, a Visual Studio Code extension (Prompt Orchestrator) that runs a versioned library of AI prompts and review agents, and the publishing tool described below. The practice is owner-operated by Amr Abdel-Motaleb and develops in the open at https://bash-365.com.

**What we are requesting access for today.** Our own website's publishing pipeline. The site is a static Jekyll site whose source lives in a GitHub repository; inside it we maintain a small, dependency-free Python publisher that shares our newly published articles and short practice updates to our own LinkedIn company page, BASH Consulting (urn:li:organization:64517157). The current implementation is first-party: one application, one organization page, administered by us. There are no third-party users, customer accounts, or sign-ups today.

Scopes and endpoints in use today:

- w_organization_social — create posts on our own page via POST /rest/posts. Two kinds only: an article link-share pointing at a post on our site, and a plain text update.
- r_organization_social — read a post back via GET /rest/posts/{urn} to confirm it published, and validate access-token health with one inexpensive authenticated call.
- Images API — upload the article's existing preview image as the share's thumbnail.

**Data handling today.** We do not access member profiles, connections, or private messages. We store no LinkedIn data beyond the post URN returned to us, which we keep in a version-controlled ledger so a given article can never be posted twice. No LinkedIn data is sold, shared with anyone, or used to train a model.

**Approval before anything publishes.** An AI agent drafts the commentary into a file and opens a pull request; a person edits and merges it, and that merge is the approval that triggers publication. A dry-run mode renders the exact request payload with zero API calls, and an automated check rejects copy that fails our editorial standards. Current volume is low — on the order of one to four posts a month, tied to our own publishing cadence.

**Where the product is going.** We are building this pipeline out into a content management system (CMS) extension and distribution app that other organizations will be able to run against their own pages, with AI agents doing the drafting and analysis a small marketing team has no time for. The intent, plainly:

- Distribution from the CMS. Publish from where the content is already authored — a git-based or headless CMS — rather than copying text into a browser tab. Write once, review it in the same pull request as the article, publish to the page on merge, and keep the audit trail of who approved what.
- AI agents in the review loop. Extend the review agents we already run: draft the commentary, critique it against the organization's own editorial and brand rules before anyone sees it, and flag copy that should not go out. The agents draft and analyze; a named person still approves.
- Analysis and sentiment on an organization's own content. Read back the comments and reactions on the organization's own posts to report which topics and formats earn engagement, and summarize the tone of the discussion for the page owner, so the next post is informed by the last one instead of guesswork.
- Relevant industry news. Give an operator something worth posting by surfacing current, on-topic developments in their industry, drawn from public feeds and publications outside LinkedIn. This is a content-sourcing feature, not a LinkedIn data feature.

The aim throughout is better engagement through better and more consistent posting — organizations publishing relevant, timely, human-approved content on a steady cadence, rather than volume for its own sake. We are not building an automation tool that posts without a person's approval, and the human gate stays in the product.

**Boundaries we will hold to.** The access we are requesting now covers our own page, and we will use it only for that. When the app is ready to manage a page we do not own, each organization will authorize its own page through its own administrator's consent, and we will apply to LinkedIn separately for whatever review or partnership that use requires rather than treating this grant as covering it. Analysis will stay scoped to a page's own content and reported in aggregate to that page's owner — we will not build member profiles, resell LinkedIn data, or train models on it. News discovery reads public sources outside LinkedIn; we do not scrape LinkedIn or read member feeds.

Our privacy policy is at https://bash-365.com/privacy/.

## Use-case answers (paste as plain text, one per box)

**Which to request.** Page management and Page analytics are both real and both belong to the product as described above — request them. Profile management is a decision: it is not implemented, it is the use case most likely to draw scrutiny, and requesting a capability we are not using is a common rejection reason. Request it only if founder-profile publishing is something we actually want in the near term; otherwise use the decline text below. Nothing in the other two use cases depends on it.

**If we do request Profile management, the business-and-product answer above needs one line**, or a reviewer reading both will find the main description silent on member posting. Add to the roadmap list: *"Publishing from a consultant's own profile. The same article, drafted and reviewed the same way, posted by the individual to their own profile under their own consent — never on behalf of a member who has not authorized it."* Leave the "Data handling today" paragraph alone; it is scoped to today and stays true either way.

### Page management

This is our primary use case and the one already built. We publish and manage the content on our own LinkedIn company page, BASH Consulting (urn:li:organization:64517157), from the same repository that holds our website.

Posts. When we publish an article at https://bash-365.com, our publisher creates the matching share on our page via POST /rest/posts — either an article link-share carrying that article's own preview image as the card thumbnail, or a plain text update for practice news. We read the post back with GET /rest/posts/{urn} to confirm it published, and we record the returned URN in a version-controlled ledger so the same article can never be posted twice.

Comments and reactions. We want to hold the conversation our own posts start: read the comments on our page's posts, reply from the page to the ones that deserve an answer, and react where a reply is not needed. For a consultancy this is where the value is — an owner asking what a system like this costs for a twenty-person shop deserves an answer rather than silence. We also want to moderate our own page's threads, hiding or removing spam and abuse.

Engagement monitoring. We track which of our own posts drew comments and reactions, so the next one is informed by the last.

Governance. Everything that publishes — an original post or a reply to a comment — is drafted by an AI agent into a file, opened as a pull request, and published only when a person merges it. There is no auto-reply and no unattended posting. A dry-run mode renders the exact request payload with zero API calls, and an automated check rejects copy that fails our editorial standards.

Scopes: w_organization_social and r_organization_social, on pages we administer. Volume is low — currently on the order of one to four posts a month plus replies, tied to our own publishing cadence.

### Page analytics

We want to know whether the content is working, and to report that back in plain terms to whoever owns the page.

What we would read. Aggregate statistics for our own organization's posts and page: impressions, clicks, reactions, comments, shares, and engagement rate per post, plus page-level follower and visitor counts over time. Read-only, through the Community Management API's organization share statistics and page statistics endpoints under r_organization_social.

What we would do with it. Three things, all editorial rather than advertising. First, decide what to publish next — which topics, formats, and lengths earn attention from small-business owners and finance leads, and which do not. Second, decide when — what cadence actually correlates with engagement for our audience, instead of guessing. Third, close the loop on our own writing: our content pipeline already flags which articles on the site are thin or stale, and post performance is a second signal for which subjects deserve a deeper piece.

Sentiment. Alongside the counts we want to summarize the tone and the recurring themes in the comments on our own posts — what readers ask, push back on, or raise repeatedly — so the page owner reads one honest summary instead of scrolling threads. This is analysis of the conversation on our own content, reported in aggregate to that content's owner.

Boundaries. Metrics stay aggregate and stay scoped to pages we administer. We do not build profiles of individual members, do not attempt to re-identify anyone inside an aggregate count, and do not join LinkedIn metrics to any other dataset about a person. Nothing is sold or shared with a third party, and no LinkedIn data trains a model. We retain only what a trend line needs.

### Profile management — requesting it

We would use this narrowly: for the profile of the person who authorizes it, and never for anyone else's.

Today. Not implemented. Nothing in our current code touches a member profile.

Why we would want it. BASH Consulting is an owner-operated practice, so the founder's own profile is where most of the audience actually is and the company page is the smaller channel. The intent is that when we publish an article, the founder can also post it from his own profile — the same article, drafted and reviewed through the same pull-request gate, published under his own explicit consent — rather than retyping it into a browser. As the product opens to other organizations, an individual consultant would be able to do the same for their own profile, each authorizing their own account through their own OAuth consent and revoking it whenever they choose.

What we would use. The member-level posting scope (w_member_social) to create a post on the authenticated member's own profile, and read-back of that member's own posts to confirm publication and report to that same member how the post performed.

What we would not do. We would not post, comment, or react as any member who has not personally authorized it. We would not read other members' profiles, connections, or feeds. There is no automated engagement of any kind — no auto-liking, auto-commenting, auto-following, auto-connecting, and no scraping. Every post is drafted by an agent and published only when the member approves it. Member data is not sold, shared, or used to train a model.

If this use case is not granted, nothing in our page management or page analytics use cases is affected.

### Profile management — declining it

Not requested. Our product manages organization pages, not individual profiles. We do not post, comment, or react on behalf of any member, and we do not read member profiles, connections, or feeds. If we later add profile-level publishing, we will apply for it separately, with each member authorizing their own account through their own consent.

## If we are asked for more

Answers we can give without inventing anything:

- **Who authorizes the token.** A page administrator (the founder) authorizes it
  through LinkedIn's token generator; there is no third-party OAuth flow because there are no third-party users yet. A multi-organization version would use a standard three-legged OAuth consent per organization admin.
- **Where credentials live.** Environment only — a gitignored local `.env` for
development and GitHub Actions secrets in continuous integration. Never committed, never logged, never passed on a command line. See `.env.example`.
- **Rate limiting.** Volume is bounded by our own publishing cadence and by the
idempotency ledger (`.github/linkedin-log.json`); a source already in the ledger is skipped rather than retried.
- **The code.** `scripts/features/linkedin/` — standard-library Python, readable
  in full, documented in its own [README](../scripts/features/linkedin/README.md).
- **What exists vs. what is planned.** Shipping today: the publisher, the
`/linkedin-draft` command and `linkedin-share` skill, the merge-is-approval workflow, the token-health check, and the `extension/` Prompt Orchestrator that runs the prompt and review-agent library. Planned, and not to be described as built: the multi-organization CMS extension, comment replies and moderation, the analytics and sentiment reporting, industry-news sourcing, and any profile-level publishing. Keep that line in any answer we give — an overstated capability is the fastest way to lose the grant.
