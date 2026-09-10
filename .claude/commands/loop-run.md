---
description: Run one cycle of the content loop — plan from recent work, write one piece or one improvement, open one PR
argument-hint: "[new|improve] [corp|erp|muses|tech] (default: let the planner decide)"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3 scripts/loop/plan.py:*), Bash(python3 scripts/loop/signals.py:*), Bash(python3 scripts/loop/ledger.py:*), Bash(python3 scripts/content_lint.py:*), Bash(python3 scripts/doctrine_check.py:*), Bash(python3 scripts/content_inventory.py:*), Bash(python3 tools/unwrap-prose.py:*), Bash(git:*), Bash(gh pr create:*), Bash(gh pr list:*), Bash(gh pr view:*), Bash(date:*), Bash(ls:*)
---

Run one cycle of the **content loop** (`docs/content-loop.md`) by following the **`content-loop`** skill exactly. Arguments: `$ARGUMENTS` — an optional mode (`new` | `improve`) and an optional section to put first in the ring.

**Do this:**

1. Plan deterministically — never decide the mode by hand:
   ```bash
   python3 scripts/loop/plan.py --out .loop [--mode <new|improve>] [--section <section>] [--no-remote]
   ```
   Read `.loop/plan.md` and `.loop/digest.md`. If the decision is `IDLE`, report the reason and stop.
2. Follow the skill: read the chosen story's commits for real, translate it for the section's reader in the section's voice (or expand the first improve candidate from the same work), gate it with the scripts, record the run with `scripts/loop/ledger.py --record`, and open ONE pull request on a `loop/<run-id>` branch. Never push to `main`, never merge.
3. Report a short table: mode → section → story spent → file → PR URL, plus anything you left in the story for a later run.

If there is no honest lesson in the offered work, say so and open nothing.
