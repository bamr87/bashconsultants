"""The `.cms/` contract — the bus this lane plugs into.

`.cms/` is the machine-readable view of a site's whole content set, produced by
the CMS engine (`scripts/cms/cms.py` in IT-Journey) and already consumed by the
authoring surface (zer0-CMS reads it through `src/zer0/cms-contract.ts`). It
carries an index of every file with a health score, freshness band, and
lane-classified issues, plus a dated worklist of what to fix next.

Distribution is the lane that was missing from it. This module does two things:

**Reads** `.cms/index/content-index.json` so publishable material is the same
content the authoring surface sees — one index, many outputs. No parallel
content model, no second definition of "a page."

**Writes** `.cms/distribution/`, which extends the contract with what the
engine cannot know on its own: what has been published off-site, how the
audience responded, and — in `worklists/<date>-catering.md` — what to write
next based on that response. That file is the mirror image of the engine's own
worklist: same shape, evidence from readers instead of from linting.

The reader degrades on purpose. A repository with no `.cms/` still works;
`sources.py` falls back to reading git and the filesystem directly, so the tool
is useful before a site adopts the CMS engine and better after.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

CMS_DIRNAME = ".cms"
DISTRIBUTION_DIRNAME = "distribution"

# Health at or above this is worth putting in front of an audience. Below it,
# the honest move is to fix the page first — which is the engine's own worklist,
# not ours.
PUBLISHABLE_HEALTH = 70

# Freshness bands the engine assigns. Stale content can still be distributed,
# but the catering worklist says so rather than quietly promoting it.
FRESH_BANDS = ("fresh", "aging")


@dataclass
class ContentRecord:
    """One row of the CMS index, narrowed to what distribution needs."""

    path: str
    collection: str = ""
    title: str = ""
    description_len: int = 0
    word_count: int = 0
    health: int = -1
    freshness: str = "unknown"
    draft: bool | None = None
    generated: bool = False
    structural: bool = False
    read_only: bool = False
    date: str | None = None
    lastmod: str | None = None
    issues: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return Path(self.path).stem

    @property
    def distributable(self) -> bool:
        """Whether it is honest to put this in front of an audience.

        Drafts, generated files, and structural pages (indexes, redirects) are
        not content anyone wants in a feed. A low health score means the page
        has known problems — distributing it spends attention on work that is
        not ready.
        """
        if self.draft or self.generated or self.structural:
            return False
        if self.health >= 0 and self.health < PUBLISHABLE_HEALTH:
            return False
        return bool(self.title)


@dataclass
class Contract:
    """A resolved view of `.cms/` for one repository."""

    root: Path
    present: bool = False
    generated_at: str = ""
    records: list[ContentRecord] = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    @property
    def cms_dir(self) -> Path:
        return self.root / CMS_DIRNAME

    @property
    def distribution_dir(self) -> Path:
        return self.cms_dir / DISTRIBUTION_DIRNAME

    def distributable(self) -> list[ContentRecord]:
        """Publishable content, best-scored first."""
        ready = [r for r in self.records if r.distributable]
        ready.sort(key=lambda r: (-(r.health if r.health >= 0 else 0), r.path))
        return ready

    def by_path(self, path: str) -> ContentRecord | None:
        for record in self.records:
            if record.path == path or record.slug == path:
                return record
        return None


def _issue_kinds(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    kinds = []
    for issue in raw:
        if isinstance(issue, dict) and issue.get("kind"):
            kinds.append(str(issue["kind"]))
    return kinds


def load(root: Path) -> Contract:
    """Read `.cms/` if a site has one. Absence is a normal state, not an error."""
    contract = Contract(root=root)
    index_path = contract.cms_dir / "index" / "content-index.json"
    summary_path = contract.cms_dir / "index" / "summary.json"

    if summary_path.exists():
        try:
            contract.summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            contract.summary = {}

    if not index_path.exists():
        return contract

    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return contract

    contract.present = True
    contract.generated_at = str(raw.get("generated_at", ""))
    for entry in raw.get("files", []):
        if not isinstance(entry, dict):
            continue
        contract.records.append(
            ContentRecord(
                path=str(entry.get("path", "")),
                collection=str(entry.get("collection", "")),
                title=str(entry.get("title") or ""),
                description_len=int(entry.get("description_len") or 0),
                word_count=int(entry.get("word_count") or 0),
                health=int(entry.get("health") if entry.get("health") is not None else -1),
                freshness=str(entry.get("freshness") or "unknown"),
                draft=entry.get("draft"),
                generated=bool(entry.get("generated")),
                structural=bool(entry.get("structural")),
                read_only=bool(entry.get("read_only")),
                date=entry.get("date"),
                lastmod=entry.get("lastmod"),
                issues=_issue_kinds(entry.get("issues")),
            )
        )
    return contract


# ---------------------------------------------------------------------------
# Writing the distribution lane back into the contract
# ---------------------------------------------------------------------------

def performance_path(contract: Contract) -> Path:
    return contract.distribution_dir / "performance.json"


def load_performance(contract: Contract) -> dict:
    """Per-content engagement, keyed by content path.

    Populated from the author's own post statistics once the app has read
    access. Until then it is empty and every consumer treats that as "no
    evidence yet" rather than as zero engagement.
    """
    path = performance_path(contract)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data.get("content", {}) if isinstance(data, dict) else {}


def write_performance(contract: Contract, content: dict) -> Path:
    path = performance_path(contract)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Aggregate statistics for the author's own posts. No member-level data.",
        "content": content,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_worklist(contract: Contract, date: str, body: str) -> Path:
    """Write `.cms/distribution/worklists/<date>-catering.md`.

    Deliberately the same shape as the engine's own worklist so the authoring
    surface can render both in one list, and a human reads one format.
    """
    path = contract.distribution_dir / "worklists" / f"{date}-catering.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path
