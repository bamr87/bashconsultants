# LinkedIn Community Management API — application answer

The text we submit for the LinkedIn Developer application question:

> *Tell us about your business and the product that will leverage Community
> Management API access. Please provide a detailed description otherwise your
> application will be rejected.*

Access to that API is the prerequisite for everything in [`automation.md`](./automation.md#workflow-linkedin-publishing) — the publisher cannot post without the `w_organization_social` + `r_organization_social` scopes. Keep this answer factual and in step with what `scripts/features/linkedin/` actually does; reviewers reject vague submissions, and a claim we cannot back is worse than a short answer. `docs/` is excluded from the Jekyll build, so this never ships as a page.

**Why the roadmap is in the answer.** Managing a page we do not own is a different kind of access than publishing to our own, and LinkedIn reviews it separately. Disclosing the intent up front — with the boundary stated plainly — is better than having a multi-organization product surface later against a grant that was approved as first-party. The present-tense claims and the forward-looking ones are kept in separate sections on purpose; do not blur them when editing.

## The answer (paste as plain text)

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
`/linkedin-draft` command and `linkedin-share` skill, the merge-is-approval workflow, the token-health check, and the `extension/` Prompt Orchestrator that runs the prompt and review-agent library. Planned, and not to be described as built: the multi-organization CMS extension, the sentiment and engagement analysis, and industry-news sourcing. Keep that line in any answer we give — an overstated capability is the fastest way to lose the grant.
