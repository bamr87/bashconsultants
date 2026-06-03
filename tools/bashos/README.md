# bashos — BASH OS AI engine CLI

Runs the versioned prompt library (`.github/prompts/`) against the working tree
with Claude, using cached instruction context and gated by the blast-radius
[autonomy policy](../../docs/ai-framework/AUTONOMY-POLICY.md). One of the two AI
execution surfaces in [BASH OS](../../docs/ai-framework/PLAN.md) (the other is the
VS Code extension); CI agents invoke this same CLI headless.

## Setup

```bash
cd tools/bashos
npm install
npm run build          # tsc → dist/
npm link               # optional: makes `bashos` available globally
export ANTHROPIC_API_KEY=sk-...   # required for `run`; not for classify/prompts
```

## Commands

```bash
bashos prompts                       # list available prompts
bashos classify [--json]             # blast-radius verdict for the working tree
bashos run <prompt> <file> [opts]    # run a prompt against a file with Claude
bashos content <verb> ...            # Content Studio pipeline (see below)
```

### Content Studio (`bashos content`)

The idea→publish pipeline. Stages and prompt mappings live in [`_data/pipeline.yml`](../../_data/pipeline.yml).

```bash
bashos content board                              # status of every post by stage (no API key)
bashos content new -s tech -T "My title"          # scaffold a post at stage:idea, published:false
bashos content outline <file> --write             # run the outline prompt (Claude)
bashos content draft   <file> --write             # flesh out the draft (article-write)
bashos content review  <file>                     # editorial/voice review
bashos content seo     <file>                     # SEO + metadata pass
bashos content stage   <file> <stage>             # move a post to a stage (sets published flag)
```

**Safety:** pre-publish posts carry `published: false` — Jekyll-native build exclusion, so they are **not live** even on `main` (unlike the decorative `draft:` field). Promoting to `published` is a 🟡 Yellow action and must go through human PR review; the board flags any post that is `published: true` while still in a pre-publish stage.

`run` options:

| Flag | Default | Meaning |
|---|---|---|
| `-t, --tier <opus\|sonnet\|haiku>` | `opus` | model tier (cost vs. capability) |
| `-w, --write` | off | write result back to the file (default: print to stdout) |
| `--max-tokens <n>` | 4096 | max output tokens |

### Examples

```bash
bashos run article-review pages/_posts/tech/2025-11-19-prompts-are-the-new-command-line.md
bashos run article-write pages/_posts/muses/2026-06-02-new-idea.md --write --tier sonnet
bashos classify                      # what could the AI auto-commit right now?
```

## Safety model

- `run` **never commits**. It prints or writes a file, then reports the autonomy
  class. Committing is gated behind the policy and added in a later phase.
- `classify` exits non-zero (code 2) when the changeset is **not** auto-committable,
  so CI can branch on it (Green → auto-merge; Yellow → PR; Red → fail).
- Prompt caching marks the large, stable instruction + prompt context as cacheable;
  only the variable file content is billed at full input price on repeat runs.

## Layout

```
tools/bashos/
├─ src/
│  ├─ index.ts            # CLI entry (commander)
│  ├─ commands/           # run, classify
│  └─ lib/                # claude (cached) · prompts · policy · repo · audit
├─ policy/blast-radius.yml   # the autonomy policy config
└─ evals/validate-prompts.mjs # dependency-free prompt schema eval (CI)
```
