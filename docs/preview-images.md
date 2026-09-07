# Preview image pipeline

How the AI-generated banner images for posts and section pages work, and the rules that keep frontmatter, filenames, and the generator in sync.

## The facts

| Item | Value |
|---|---|
| Generator | `scripts/features/generate-preview-images` (wrapper: `scripts/generate-preview-images.sh`) |
| Jekyll integration | `_plugins/preview_image_generator.rb` (Liquid tags, path normalization, missing-preview detection) |
| Provider / model | OpenAI `gpt-image-2` by default (the `preview_images` block of `_config.yml`; DALL-E 3 is retired on this account). `--provider xai` paints with xAI Imagine (`grok-imagine-image-2.0`) instead — see [xAI Imagine provider](#xai-imagine-provider-oauth-first) |
| Size / quality | `1536x1024` landscape, `high` |
| Style | Retro pixel art, 8-bit video game aesthetic — the `style` and `style_modifiers` keys in `_config.yml` are the single source of truth for the look |
| Output directory | `assets/images/previews/` |
| Credentials | `OPENAI_API_KEY`, loaded from `.env` at the repo root (never committed). For xAI: OAuth first (`XAI_OAUTH_TOKEN`, the Grok CLI store, Kilo's xAI login), `XAI_API_KEY` last |
| Cost | Roughly $0.15–0.20 per image at current pricing — cheap for one post, real money for a `--force` run across the whole site |

## Filename rule

The image filename is derived from the post's `title:`, not its file path:

1. Lowercase the title.
2. Replace every run of non-alphanumeric characters with a single `-`.
3. Strip leading and trailing `-`.
4. Truncate to 50 characters (a trailing `-` left by truncation is kept).

Example: `"bashos: the new command-line operating system"` → `bashos-the-new-command-line-operating-system.png`.

Because the filename comes from the title, **changing a title orphans its image**. Regenerate previews only after titles are final, and if you retitle a published piece, regenerate (or rename) its preview in the same change.

## Frontmatter path rule

Use the short form in frontmatter:

```yaml
preview: /images/previews/<slug>.png
```

The build auto-prefixes `/assets` (the `assets_prefix` / `auto_prefix` keys in `_config.yml`), so `/images/previews/foo.png` resolves to `assets/images/previews/foo.png`. Do not write `/assets/images/previews/...` in frontmatter — both work at render time, but the short form is the house convention and what the generator writes back.

## Running the generator

```bash
# See what's missing without spending anything
./scripts/generate-preview-images.sh --dry-run
./scripts/generate-preview-images.sh --list-missing

# Generate for everything that lacks a preview
./scripts/generate-preview-images.sh --collection posts

# Regenerate one post's image after a title change
./scripts/generate-preview-images.sh --force --file pages/_posts/tech/2026-07-06-my-post.md
```

`--force` regenerates even when an image already exists — pair it with `--file` for a single post rather than running it site-wide.

## xAI Imagine provider (OAuth first)

`--provider xai` paints the same house-style prompt with xAI Imagine instead of OpenAI. The wiring is ported from the lifehacker.dev preview pipeline: a subscription (OAuth) token wins over a metered API key, and the key is never sent when OAuth is present. The generator resolves a credential in this order and stops at the first hit:

1. `XAI_OAUTH_TOKEN` (environment or `.env`)
2. The official Grok CLI store, `~/.grok/auth.json`, written by `grok login`
3. Kilo's local xAI login, `~/.local/share/kilo/auth.json`, refreshed against `auth.x.ai` when the access token has expired
4. `XAI_API_KEY`, pay-per-use, last

`GROK_AUTH_PATH` and `KILO_AUTH_PATH` override the store locations. Nothing logs a token; the bearer header travels in a mode-600 curl config, exactly like the OpenAI key.

Model, aspect ratio, resolution, and quality come from `_config.yml` (`xai_model`, `xai_aspect_ratio`, `xai_resolution`, `xai_quality`; defaults `grok-imagine-image-2.0`, `3:2`, `1k`, `medium`) or the matching `XAI_IMAGE_MODEL`, `XAI_IMAGE_ASPECT`, `XAI_IMAGE_RESOLUTION`, and `XAI_IMAGE_QUALITY` environment variables. Imagine returns JPEG; the generator converts it to a real PNG (sips on macOS, ImageMagick or Pillow elsewhere) so `<slug>.png` stays an honest filename and nothing downstream changes.

```bash
# Mint an OAuth token once (SuperGrok / X Premium); the generator reads the store directly
curl -fsSL https://x.ai/cli/install.sh | bash
export PATH="$HOME/.grok/bin:$PATH"
grok login

./scripts/generate-preview-images.sh --provider xai --collection posts
./scripts/generate-preview-images.sh --provider xai --force --file pages/_posts/tech/2026-07-06-my-post.md
```

Where the process cannot see the store (CI, Docker, another machine), copy the access token into `.env` as `XAI_OAUTH_TOKEN`; it is a short-lived JWT, so re-copy it after the next `grok login`. Without a subscription, an API key from [console.x.ai](https://console.x.ai/) as `XAI_API_KEY` is the documented fallback. `--enhance` stays an OpenAI-only feature.

## House rule: the final review pass

The last polish pass over any content batch is always run by the strongest available model at the top level (currently Opus-class) — not delegated to a subagent. That pass confirms titles are final *before* previews are generated, and checks that no reader-facing text names a piece's creative device. Order of operations: write → review → finalize titles → generate previews.
