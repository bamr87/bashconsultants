# Claude Skills — bashconsultants

Claude-native [Agent Skills](https://docs.claude.com/en/docs/agents/skills) for this repo. Each skill is a thin wrapper that points Claude at an existing prompt in [`.github/prompts/`](../../.github/prompts/) — **the prompt files stay the single source of truth**; skills add discoverability and progressive disclosure without duplicating the prompt body (same anti-drift principle as `CLAUDE.md` symlinking `AGENTS.md`).

## Convention

```
.claude/skills/<skill-name>/SKILL.md
```

`SKILL.md` frontmatter:

```yaml
---
name: <skill-name>
description: <one sentence — WHEN Claude should reach for this skill>
---
```

The body says what the skill does and **links** to the canonical prompt; it must not copy the prompt's instructions.

## Skills

| Skill | Wraps | Use when |
|---|---|---|
| `content-article` | `.github/prompts/article-write.prompt.md` | Drafting a new blog post end-to-end |
| `content-review` | `.github/prompts/article-review.prompt.md` | Reviewing a post for structure / voice / SEO |

## Adding a skill

1. Create `.claude/skills/<slug>/SKILL.md` with the frontmatter above.
2. Point its body at the canonical prompt in `.github/prompts/`.
3. Keep it ≤ 1 screen; detail lives in the prompt, not here.
4. Add a row to the table above.
