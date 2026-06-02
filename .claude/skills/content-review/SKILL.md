---
name: content-review
description: Review a blog post for frontmatter validity, structure, voice, and SEO, and suggest concrete expansions. Use when the user wants an article reviewed, edited, or SEO-checked.
---

# Content — Review Article

Wraps the canonical prompt: [`.github/prompts/article-review.prompt.md`](../../../.github/prompts/article-review.prompt.md).

Read that prompt and follow it verbatim — it owns the review checklist and output format. This skill exists only so the workflow is discoverable as a Claude skill.

## Guardrails

- Judge voice and structure against [`content-style.instructions.md`](../../../.github/instructions/content-style.instructions.md).
- Producing a review report or editing a `draft: true` post is **Green / low-risk**. Any edit that changes a *published* post's customer-facing copy is **Yellow** — propose it, don't auto-commit it (see [`docs/ai-framework/AUTONOMY-POLICY.md`](../../../docs/ai-framework/AUTONOMY-POLICY.md)).
