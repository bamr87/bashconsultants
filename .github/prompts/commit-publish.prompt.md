---
mode: agent
description: "Review changes, validate the Jekyll build, update CHANGELOG, then commit and push to main (direct-to-main workflow)"
date: 2026-05-18T12:00:00.000Z
lastmod: 2026-05-18T12:00:00.000Z
---

# Commit & Publish — BASH Consultants

When invoked with `/commit-publish`, walk through the publish workflow: review → validate → document → commit → push. This repo deploys to GitHub Pages on push to `main` (no PR gate).

## Steps

### 1. Review Changes

```bash
git status --short
git diff --stat
```

Classify each changed file: `post | page | service | config | extension | ci | docs`.
Refuse to proceed if any file contains literal secret prefixes (`ghp_…`, `sk-…`, `AKIA…`). Surface unexpected items: generated `_site/`, large binaries, `Gemfile.lock` deletions.

### 2. Validate

For Jekyll changes (`_*.yml`, `_includes/**`, `_layouts/**`, `pages/**`, `*.md`):

```bash
docker-compose up -d jekyll
docker-compose exec -T jekyll bundle exec jekyll build \
  --config '_config.yml,_config_dev.yml'
```

For `extension/` changes:

```bash
cd extension && npm run lint && npm run compile
```

Stop on failure.

### 3. Update Documentation

Update `README.md` in any touched directory. Update root `README.md` only for user-visible changes. Add entry to `CHANGELOG.md` under `## [Unreleased]`:

```markdown
### Added | Changed | Fixed | Removed
- **<area>**: <one-line summary>
```

### 4. Commit

```bash
git add -A
git commit -m "<type>(<scope>): <imperative subject>

<body explaining why>"
```

Types: `feat fix docs refactor chore ci`. Scopes: `posts pages services config extension prompts docs`.

### 5. Push

```bash
git pull --rebase origin main
git push origin main
```

GitHub Pages auto-deploys on push.

### 6. Verify

```bash
sleep 60
curl -sI https://bash-365.com/ | head -1   # expect HTTP/2 200
```

## Output to User

```markdown
## Release Summary — <YYYY-MM-DD>

### Changes
- <bullet>

### Validation
| Check | Result |
|---|---|
| Jekyll build | ✅ |
| Extension lint+compile | ✅ / N/A |
| Secret scan | ✅ |

### Commit
- SHA: <sha>
- Pushed: ✅
- Deployment: pending Pages build (~1-2 min)
```

## Hard Rules

- Never commit `_site/`, `node_modules/`, or `vendor/`.
- Never push tags before the commit.
- Never force-push to `main`.
- Roll forward, never rewrite history.
