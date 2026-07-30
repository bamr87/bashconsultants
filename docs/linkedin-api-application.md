# LinkedIn Community Management API — application answer

The text we submit for the LinkedIn Developer application question:

> *Tell us about your business and the product that will leverage Community
> Management API access. Please provide a detailed description otherwise your
> application will be rejected.*

Access to that API is the prerequisite for everything in [`automation.md`](./automation.md#workflow-linkedin-publishing) — the publisher cannot post without the `w_organization_social` + `r_organization_social` scopes. Keep this answer factual and in step with what `scripts/features/linkedin/` actually does; reviewers reject vague submissions, and a claim we cannot back is worse than a short answer. `docs/` is excluded from the Jekyll build, so this never ships as a page.

## The answer (paste as plain text)

BASH Consulting LLC is a Denver, Colorado information technology (IT) consultancy serving small and medium-sized businesses. We design, implement, and support the systems a business runs on: cloud infrastructure, Enterprise Resource Planning (ERP) and accounting platforms, data architecture, and automation with an artificial intelligence (AI) overlay. The practice is owner-operated by Amr Abdel-Motaleb and publishes its work in the open at https://bash-365.com.

The product is our own website's publishing pipeline, not a commercial application. Our site is a static Jekyll site whose source lives in a GitHub repository. Inside it we maintain a small, dependency-free Python publisher that shares our newly published articles and short practice updates to our own LinkedIn company page, BASH Consulting (urn:li:organization:64517157). It is first-party only: one application, one organization page, administered by us. We are not building a social media management tool, we do not act on behalf of any other organization, and there is nothing for a third party to sign up for, log into, or buy.

How it uses the API:

- w_organization_social — create posts on our own page via POST /rest/posts. Two kinds only: an article link-share pointing at a post on our site, and a plain text update.
- r_organization_social — read a post back via GET /rest/posts/{urn} to confirm it published, and validate access-token health with one inexpensive authenticated call.
- Images API — upload the article's existing preview image as the share's thumbnail.

Nothing else is requested and nothing else is read. We do not access member profiles, connections, messages, follower lists, or engagement data. We store no LinkedIn data beyond the post URN returned to us, which we keep in a version-controlled ledger so a given article can never be posted twice.

Every post is approved by a person before it exists. An AI agent drafts the commentary into a file and opens a pull request; a human edits and merges it, and that merge is the approval that triggers publication. A dry-run mode renders the exact request payload with zero API calls, and an automated check rejects copy that violates our editorial standards. Expected volume is low — on the order of one to four posts a month, tied to our own publishing cadence.

Our privacy policy is at https://bash-365.com/privacy/.

## If we are asked for more

Answers we can give without inventing anything:

- **Who authorizes the token.** A page administrator (the founder) authorizes it
  through LinkedIn's token generator; there is no third-party OAuth flow because there are no third-party users.
- **Where credentials live.** Environment only — a gitignored local `.env` for
development and GitHub Actions secrets in continuous integration. Never committed, never logged, never passed on a command line. See `.env.example`.
- **Rate limiting.** Volume is bounded by our own publishing cadence and by the
idempotency ledger (`.github/linkedin-log.json`); a source already in the ledger is skipped rather than retried.
- **The code.** `scripts/features/linkedin/` — standard-library Python, readable
  in full, documented in its own [README](../scripts/features/linkedin/README.md).
