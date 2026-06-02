---
name: content-article
description: Draft a new bashconsultants.com blog post end-to-end — route the subfolder, scaffold frontmatter, and write to house voice. Use when the user wants a new article, post, or muse drafted.
---

# Content — Draft Article

Wraps the canonical prompt: [`.github/prompts/article-write.prompt.md`](../../../.github/prompts/article-write.prompt.md).

Read that prompt and follow it verbatim — it owns the inputs, subfolder routing, frontmatter schema, and workflow. This skill exists only so the workflow is discoverable as a Claude skill.

## Guardrails

- Obey [`content-style.instructions.md`](../../../.github/instructions/content-style.instructions.md) and [`posts.instructions.md`](../../../.github/instructions/posts.instructions.md).
- New posts are written with `draft: true` — a **Green / low-risk** action under the autonomy policy ([`docs/ai-framework/AUTONOMY-POLICY.md`](../../../docs/ai-framework/AUTONOMY-POLICY.md)). Promoting to `draft: false` (publish) is **Yellow** and requires human review.
- Never invent client names, testimonials, metrics, or pricing.
