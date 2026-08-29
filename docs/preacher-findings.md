# Preacher findings — week of 2026-08-29

Deterministic gates: `python3 scripts/doctrine_check.py` → **PASS** (0 errors, 0 warnings, 1 registered check over 80 files). `python3 scripts/content_lint.py --warn-only` → **PASS** (0 errors, 12 pre-existing warnings, none introduced this window). Judgment pass covered the diff since `34011a1` (2026-08-11 → 2026-08-18, the last three commits before this run).

## DFF (design for failure) — 1 violation

- `pages/_posts/muses/2026-08-15-your-best-programmer-thinks-theyre-just-good-at-excel.md:12` — `preview: /images/previews/your-best-programmer-thinks-they-re-just-good-at-e.png` does not exist. There is no file under `assets/images/previews/` matching that name (checked `your-best-programmer*`, `excel*`). The post has `draft: false` and a 2026-08-15 date, so it has been live on `bash-365.com` for two weeks with a broken preview/Open Graph image.
- `pages/_posts/muses/2026-08-19-best-practice-is-the-interest-of-the-stronger.md:9` — same problem: `preview: /images/previews/best-practice-is-the-interest-of-the-stronger.png` does not exist (checked `best-practice*`, `stronger*`, `thrasymachus*`). `draft: false`, live since 2026-08-19.
- **Root cause, in the authors' own words:** `fa255b4` (2026-08-18, "feat(posts): two muses essays") added both posts with `draft: false` and its own commit message says "Preview banners for the two posts are still to be generated"; `CHANGELOG.md` under `[Unreleased] → Added` repeats it: *"Preview banners to be generated before the posts' dates."* The banners were never generated, and because neither the deterministic gates nor a human reviewer re-checks a `changelog` TODO, the gap has now outlived the "before the posts' dates" promise by 10–14 days with no tracking mechanism (Issues are disabled here, so a changelog sentence was the only record).
- **Fix:** run `./scripts/generate-preview-images.sh --file pages/_posts/muses/2026-08-15-your-best-programmer-thinks-theyre-just-good-at-excel.md` and the same for the 2026-08-19 post (per `docs/preview-images.md`), then drop the now-resolved TODO line from `CHANGELOG.md`.

## Mechanization candidate

`content_lint.py` already checks that a post's `preview:` value is shaped correctly (`/images/previews/...`, `scripts/content_lint.py:368-373`) but never checks that the file it names actually exists on disk. A new `doctrine_check.py` (or `content_lint.py`) check — for every non-draft post, `assets/{preview value}` must resolve to a real file — would have caught this the moment `fa255b4` was written, instead of ten days after publish. High-precision and cheap: skip `draft: true` posts (drafts are allowed to ship without a banner), self-test with a fixture post pointing at a real file (pass) and one pointing at a missing file (fail).
