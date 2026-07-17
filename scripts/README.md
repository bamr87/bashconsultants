# Scripts

Utility scripts for developing and maintaining bashconsultants.com. Everything listed here exists in this directory; if a script isn't listed, it was retired.

## Content quality

### `content_lint.py`

Mechanically enforces the editorial contract from `.github/instructions/content-style.instructions.md` and `posts.instructions.md` across reader-facing Markdown (posts, services, root pages): required post frontmatter, description length, banned marketing phrases, draft flags, filename/date agreement, flow-style category/tag lists, and exclamation marks in titles or descriptions.

```bash
python3 scripts/content_lint.py             # lint the repo, exit 1 on errors
python3 scripts/content_lint.py --warn-only # report but always exit 0
python3 scripts/content_lint.py --self-test # run inline fixtures
```

### `doctrine_check.py`

The deterministic half of "practice what we preach" — structural doctrine checks (DRY, single-source-of-truth) that complement `content_lint.py`'s editorial focus. An extensible registry of `@check` functions; the [preacher](../docs/the-preacher.md) grows it by mechanizing recurring AI-review burdens. The seed check, `DRY-CONTACT`, flags hardcoded contact values in content that should read from `_data/entity/info.yml`.

```bash
python3 scripts/doctrine_check.py             # run all checks, exit 1 on any violation
python3 scripts/doctrine_check.py --warn-only # report but always exit 0
python3 scripts/doctrine_check.py --list      # list the registered checks
python3 scripts/doctrine_check.py --self-test # run inline fixtures
```

### `content_inventory.py`

The deterministic seed for the weekly content review — lists every reader-facing content page with its word count, last-modified date, and age, and flags the thin and the stale. The [content curator](../.claude/agents/content-curator.md) starts from this instead of re-reading the whole corpus every week (structural pages — index stubs, landing loops — are skipped).

```bash
python3 scripts/content_inventory.py          # full table, most-neglected first
python3 scripts/content_inventory.py --focus  # the thin/stale shortlist for a weekly run
python3 scripts/content_inventory.py --json   # machine-readable (for the curator)
```

### `generate_playbook_data.py`

Generates `_data/playbook.yml` from `.github/prompts/*.prompt.md` and `.github/instructions/*.instructions.md` so Jekyll pages can loop over the prompt library. Standard library only, deterministic output.

```bash
python3 scripts/generate_playbook_data.py          # write _data/playbook.yml
python3 scripts/generate_playbook_data.py --check  # exit 1 if the file is stale
```

## Preview images

### `features/generate-preview-images` (canonical)

AI preview image generator for posts and configured collections. Reads defaults from the `preview_images` section of `_config.yml` (provider `openai`, model `gpt-image-2`, size `1536x1024`, quality `high`), detects content missing a `preview:` image, generates images via the OpenAI Images API (Stability AI and a `local` placeholder provider are also supported), and writes them to `assets/images/previews/`.

Requires `OPENAI_API_KEY` (or `STABILITY_API_KEY`) — see `.env.example`. API keys are passed to `curl` via mode-600 config files, never on the command line.

```bash
./scripts/features/generate-preview-images --list-missing        # no API calls
./scripts/features/generate-preview-images --dry-run --verbose   # show prompts
./scripts/features/generate-preview-images --collection posts    # generate
```

### `generate-preview-images.sh`

Backward-compatibility wrapper that forwards all arguments to `features/generate-preview-images`. The VS Code tasks in `.vscode/tasks.json` call this wrapper.

Related: `_plugins/preview_image_generator.rb` provides the Jekyll side (Liquid filters/tags and a build-time report of missing previews). Its defaults are kept in sync with `_config.yml` and the script above.

## Setup helpers

### `setup-admin-settings.sh`

Creates the admin/settings content pages for a site using the zer0-mistakes theme (the layouts, includes, and assets ship with the theme itself). Supports `--dry-run` and `--force`.

### `setup-git.sh`

Interactive helper for global Git configuration (user.name, user.email, editor, optional GitHub CLI wiring and SSH key upload). Dry-run by default; pass `--apply` to make changes.

```bash
bash scripts/setup-git.sh --name "Your Name" --email you@example.com          # dry-run
bash scripts/setup-git.sh --apply --name "Your Name" --email you@example.com  # apply
```

## Legacy

### `routine-maintenance.sh`

Clipboard-era helper that assembles prompts from `.github/prompts/` for manual pasting into VS Code Chat. Superseded by the Prompt Orchestrator extension in `extension/`, which runs the same workflows natively. The file is kept because the extension's code and docs reference it as the canonical command-to-prompt alias map:

| Alias | Prompt file |
|---|---|
| `refactor` | `code-refactoring.prompt.md` |
| `test` | `test-generation.prompt.md` |
| `docs` | `documentation.prompt.md` |
| `debug` | `debugging.prompt.md` |
| `analyze` | `requirements-analysis.prompt.md` |
| `design` | `system-design.prompt.md` |
| `implement` | `code-implementation.prompt.md` |
| `review` | `article-review.prompt.md` |

Prefer the extension for new work.
