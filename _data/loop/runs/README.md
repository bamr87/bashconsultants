# `_data/loop/runs/` — the loop's ledger, one file per run

Every content-loop run that opened a pull request records itself here as `YYYY-MM-DD-<mode>-<slug>.yml`, written by `python3 scripts/loop/ledger.py --record …` and committed **in the same PR** as the content it describes. One file per run means two loop PRs in flight can never conflict on a shared ledger line.

Jekyll ignores this README (it only loads `.yml`/`.json`/`.csv` from `_data/`), so this directory is safe to document in place.

Shape of a record:

```yaml
id: 2026-09-07-new-gating-an-ai-loop
date: "2026-09-07"
mode: new            # new | improve
section: tech        # corp | erp | muses | tech for new; any inventory section for improve
path: pages/_posts/tech/2026-09-07-gating-an-ai-loop.md
title: "Gating an AI content loop behind one variable"
signals:             # the story ids this run spent (see scripts/loop/signals.py)
  - session:01LT7a91zWYSag4Zv5tf18Bk
  - pr:38
summary: "One line: what the piece is and which work it drew from"
pr: https://github.com/bamr87/bashconsultants/pull/42
```

What reads it: `scripts/loop/plan.py` (cadence — when the last `new`/`improve` happened; rotation — which section is most overdue; cooldown — which pages were improved recently) and `scripts/loop/signals.py` (which stories are already spent). Never edit a record by hand except to correct a mistake; never delete one — the ledger is the loop's memory.
