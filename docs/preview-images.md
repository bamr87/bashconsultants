# Preview image pipeline

How the AI-generated banner images for posts and section pages work, and the rules that keep frontmatter, filenames, and the generator in sync.

This is the operator's runbook — the facts, the commands, and the traps. The **full reference** — every configuration key, how the prompt is assembled, the styling levers, the render and social-card path, the CMS surface, and where this sits relative to `zer0-image-generator` — is the published partner doc at [`pages/_toolkit/preview-image-pipeline.md`](../pages/_toolkit/preview-image-pipeline.md) (`/tools/partners/preview-image-pipeline/`). Change a behavior and both files need the update.

## The facts

| Item | Value |
|---|---|
| Generator | `scripts/features/generate-preview-images` (wrapper: `scripts/generate-preview-images.sh`) |
| Engine (zer0 stack) | The `zer0-image-generator` gem in the root `Gemfile` — `bundle exec jekyll preview-images --list-missing` inside the dev container reports what lacks a banner, from the same `preview_images` block. It replaced the vendored `_plugins/preview_image_generator.rb`, whose Liquid filters and tags nothing rendered |
| Provider / model | OpenAI `gpt-image-2` by default (configured in the `preview_images` block of `_config.yml`; DALL-E 3 is retired on this account). **xAI Grok Imagine** (`grok-imagine-image-2.0`) is the second option, on a Grok OAuth token — see below |
| Size / quality | `1536x1024` landscape, `high` |
| Style | Two looks. **Posts:** retro pixel art, 8-bit video game aesthetic (`style` + `style_modifiers`). **Services, toolkit, about:** a professional IT look — isometric enterprise systems, technical blueprints, and operations consoles in teal and slate navy with one crimson accent, no people (`collection_styles`). The `preview_images` block in `_config.yml` is the single source of truth for both |
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

The extension is the image's real format: OpenAI renders are `.png`, xAI Grok Imagine renders are `.jpg`. The generator writes whichever it saved into front matter.

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

The business-facing sections use the gem, because the shell script only knows the global retro style and would ignore `collection_styles`. They are not in `collections:`, so name them:

```bash
# Services, toolkit, and about pages — the professional look
bundle exec jekyll preview-images --collection toolkit --dry-run
bundle exec jekyll preview-images --collection services --force
bundle exec jekyll preview-images -f pages/_toolkit/my-new-doc.md
```

Outside the dev container, the gem's engine runs the same way as a bare script from the repo root: `python3 "$(gem contents zer0-image-generator | grep preview_generator.py)" --collection about`.

## The xAI option: Grok Imagine on a Kilo Code login

A second renderer that runs on the Grok subscription instead of OpenAI billing. Grok also writes each image prompt and reviews the render, so no Claude token is needed either. Only the gem engine has it; the shell script stays OpenAI-only. The services, toolkit, and about banners were made this way.

```bash
KILO_AUTH_PATH="$HOME/.local/share/kilo/auth.json" XAI_AUTH=oauth \
  bundle exec jekyll preview-images --collection toolkit -j 6 \
  --provider xai --model grok-imagine-image-2.0 --prompt-engine xai --review xai
```

- **Credential.** The engine reads the Grok OAuth token from Kilo Code's store (`KILO_AUTH_PATH`; the default path is already on its search list). `XAI_OAUTH_TOKEN` or `~/.grok/auth.json` work too, and `XAI_API_KEY` is the paid fallback. `XAI_AUTH=oauth` pins the subscription token so a stale login fails loudly instead of billing the key.
- **Expiry.** Kilo's access token is short-lived. When it has expired, the engine refreshes it at `auth.x.ai` with the refresh token Kilo saved and writes the new pair back into Kilo's store, so Kilo keeps working too. Only a failed refresh (`invalid_grant`) means signing in to Grok in Kilo Code again.
- **One run at a time.** Parallel workers inside one run share a single refresh. Two runs started side by side can each refresh, and the second can spend a refresh token the first just rotated. Run collections one after another and use `-j` for speed.
- **Output.** Imagine answers JPEG at 1248×832 (3:2), about 200 KB. The file is saved as `<slug>.jpg`.
- **Engine version.** Kilo's store and Grok art direction need zer0-image-generator PR #23. The token refresh, the 3:2 shape, `.jpg` naming, and the Cloudflare-safe `User-Agent` are on the `feat/xai-imagine-kilo-refresh` branch on top of it. None of that is in the published gem (0.6.0) yet. Until it is, run that checkout's engine directly: `python3 ../zer0-image-generator/lib/zer0_image_generator/preview_generator.py` with the same flags.
- **Settings that carry over.** `collection_styles`, `size` (sent as the nearest Imagine aspect ratio, so `1536x1024` becomes `3:2`), and the front-matter path rules apply unchanged. The `gpt-image-2` model and `quality` do not; the `--model` flag replaces them for the run.
## Per-section styles

The four post sections carry four editorial voices, so they carry four visual registers. `section_styles:` in the `preview_images:` block overrides `style` and `style_modifiers` per section (`corp`, `erp`, `muses`, `tech`); `collection_styles:` does the same per collection. Resolution is global → collection → section, most specific winning key by key, in [`scripts/features/lib/preview_styles.py`](../scripts/features/lib/preview_styles.py).

**House rule: a section may change the genre, never the medium.** Everything is pixel art — that is the brand's visual identity — but each section names its own pixel-art tradition: isometric strategy sim for `corp`, point-and-click adventure for `erp`, atmospheric landscape for `muses`, phosphor terminal and blueprint for `tech`. A test asserts every section style still says "pixel art". Anything outside a section (the news index, a flat post) keeps the global base.

```bash
# What overrides apply to one file, and which layer supplied them
python3 scripts/features/lib/preview_styles.py pages/_posts/erp/2026-01-31-erp-frankenstein.md

# See the resulting prompt without spending anything
./scripts/generate-preview-images.sh --dry-run --verbose --file <post>

python3 -m unittest scripts/features/lib/test_preview_styles.py
```

A style block only affects images generated **after** it, so a section adopts its look as pieces are regenerated.

## xAI Imagine provider (OAuth first)

`--provider xai` paints the same house-style prompt with xAI Imagine instead of OpenAI, authenticated by a **subscription OAuth token** rather than a metered key. xAI documents only an API key; the OAuth flow is the one Kilo Code ships in the open, ported here from [bamr87/law-ai](https://github.com/bamr87/law-ai/pull/99) (spec 050, ADR 0007). It reuses the public Grok-CLI desktop client id that xAI's auth server allowlists, which xAI can revoke at any time; that degrades to an ordinary provider failure.

### Mint the token once

```bash
scripts/features/xai-login              # device-code flow: open the URL, enter the code, approve
scripts/features/xai-login --loopback   # browser PKCE flow on 127.0.0.1:56121, for a host with a browser
scripts/features/xai-login --status     # what is stored, without printing token values
scripts/features/xai-login --check      # resolve a token and probe api.x.ai for the image models it can see
scripts/features/xai-login --refresh    # rotate the stored token now
scripts/features/xai-login --logout     # delete the store
```

Device code (RFC 8628) is the default because it needs no inbound path to this process: it works from a laptop, a VPS, or a container. The loopback grant is fixed to `127.0.0.1:56121` by the client registration and cannot be re-pointed. Either way a SuperGrok / X Premium+ subscription is required.

Tokens land in `.xai/credentials.json` (gitignored, mode 0600, written atomically). xAI **rotates the refresh token on every use**, so the generator refreshes under an exclusive lock on a sibling `.lock` file: two workers cannot both spend the same token and invalidate each other, and a 401 mid-run triggers exactly one refresh-and-retry. Keep the file; do not copy it between machines.

### The credential chain

The generator resolves a credential in this order and stops at the first hit:

1. `XAI_OAUTH_TOKEN` (environment or `.env`), an explicit override
2. The repo store above, refreshed when the access token is within two minutes of expiry; `XAI_REFRESH_TOKEN` (plus optional `XAI_ACCESS_TOKEN`) seeds it on a host with no file
3. The official Grok CLI store, `~/.grok/auth.json`, written by `grok login`
4. Kilo's local xAI login, `~/.local/share/kilo/auth.json`, refreshed against `auth.x.ai` when expired
5. `XAI_API_KEY`, pay-per-use, last

`XAI_CREDENTIALS_PATH`, `GROK_AUTH_PATH`, and `KILO_AUTH_PATH` override the store locations. Nothing logs a token: error messages carry status codes and server error bodies only, and the bearer header travels in a mode-600 curl config, exactly like the OpenAI key. The chain lives in `scripts/features/lib/xai_auth.py`; `python3 -m unittest scripts/features/lib/test_xai_auth.py` covers it with no network.

### Painting

Model, aspect ratio, resolution, and quality come from `_config.yml` (`xai_model`, `xai_aspect_ratio`, `xai_resolution`, `xai_quality`; defaults `grok-imagine-image-2.0`, `3:2`, `1k`, `medium`) or the matching `XAI_IMAGE_MODEL`, `XAI_IMAGE_ASPECT`, `XAI_IMAGE_RESOLUTION`, and `XAI_IMAGE_QUALITY` environment variables. Imagine returns JPEG; the generator converts it to a real PNG (sips on macOS, ImageMagick or Pillow elsewhere) so `<slug>.png` stays an honest filename and nothing downstream changes.

```bash
./scripts/generate-preview-images.sh --provider xai --collection posts
./scripts/generate-preview-images.sh --provider xai --force --file pages/_posts/tech/2026-07-06-my-post.md
```

Without a subscription, an API key from [console.x.ai](https://console.x.ai/) as `XAI_API_KEY` is the documented fallback. `--enhance` stays an OpenAI-only feature.

## House rule: the final review pass

The last polish pass over any content batch is always run by the strongest available model at the top level (currently Opus-class) — not delegated to a subagent. That pass confirms titles are final *before* previews are generated, and checks that no reader-facing text names a piece's creative device. Order of operations: write → review → finalize titles → generate previews.
