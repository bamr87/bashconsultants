# Preacher findings — week of 2026-09-05

Deterministic gates: `python3 scripts/doctrine_check.py` → **PASS** (0 errors, 0 warnings, 1 registered check over 82 files). `python3 scripts/content_lint.py --warn-only` → **PASS** (0 errors, 13 pre-existing warnings, none introduced this window). Judgment pass covered the diff since `870aa71` (2026-08-29 → 2026-09-05: the content-loop launch, the constellation particle engine, and the ERP Survivor episode 2 post).

## DFF (design for failure) — 3 violations, one principle, recurring

The same failure mode last week's run (`docs/preacher-findings.md` on the merged `Preacher: 1 doctrine violation(s) — week of 2026-08-29` PR, #41) flagged is still live and has now recurred a third time.

- `pages/_posts/muses/2026-08-15-your-best-programmer-thinks-theyre-just-good-at-excel.md:13` — `preview: /images/previews/your-best-programmer-thinks-they-re-just-good-at-e.png` still does not exist on disk. `draft: false`, live since 2026-08-15 — **21 days** with a broken preview/Open Graph image in production. Unresolved from last week's finding.
- `pages/_posts/muses/2026-08-19-best-practice-is-the-interest-of-the-stronger.md:12` — `preview: /images/previews/best-practice-is-the-interest-of-the-stronger.png` still does not exist. `draft: false`, live since 2026-08-19 — **17 days**. Unresolved from last week's finding.
- `pages/_posts/erp/2026-09-03-erp-survivor-episode-2-the-great-chart-of-accounts.md:11` — `preview: /images/previews/erp-survivor-episode-2-the-great-chart-of-accounts.png` does not exist either. `draft: false`, live since 2026-09-03. **New this window** — the identical mistake, committed two days after last week's finding was merged (`49c9395`, opened by the automated content-gardener workflow, PR #44). Worse than the first two: the post body itself carries the unresolved marker in production source — `pages/_posts/erp/2026-09-03-erp-survivor-episode-2-the-great-chart-of-accounts.md:15`: `<!-- TODO: add preview image at /images/previews/erp-survivor-episode-2-the-great-chart-of-accounts.png (1200x630) -->` — an admission of incomplete work shipped and merged as `draft: false`, with no mechanism catching it.
- Fix: `./scripts/generate-preview-images.sh --file <post>` for each of the three posts (per `docs/preview-images.md`), then delete the leftover TODO comment from the ERP post body.

## Mechanization candidate — now urgent, not hypothetical

Last week's finding already named this: `content_lint.py:368-373` checks that `preview:` is *shaped* correctly but never checks the file exists on disk. That was proposed as a candidate for the next clean run. It is no longer hypothetical — the exact same gap produced a third violation within the week, through an unrelated automated workflow (the gardener, not a human), proving the pattern repeats across authors and will keep repeating until it is a gate.

Proposed check for `scripts/doctrine_check.py` (or `content_lint.py`, whichever the next run judges the better home): for every post with `draft: false`, resolve `preview:` against `assets/images/` and fail if the file is missing. Self-test: a fixture post with `draft: false` pointing at a real file (pass), one pointing at a missing file (fail), and one with `draft: true` pointing at a missing file (pass — drafts are exempt). This should be the mechanization the *next* clean preacher run picks up, ahead of any other candidate, given it has now cost three live production incidents.

Full findings: this file, on this branch.
