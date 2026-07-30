"""Reading back how the author's own posts performed.

One boundary governs this whole module, and it is worth stating before any code:
**everything here is the author's own aggregate numbers.** Impressions, clicks,
reactions, comments, shares — counts attached to a post the author published.
Nothing identifies who engaged. There is no per-member record, no attempt to
resolve a reaction to a profile, and no join against any other dataset about a
person. `catering.py` consumes only what this module produces, so that boundary
holds for the whole feedback loop by construction.

Two entry points:

- `ingest` maps aggregate statistics onto content paths and stores them in the
  contract, so the catering worklist has evidence to rank on.
- `plan` describes the read calls that would fetch them. It exists so the
  request surface is auditable before any credential is granted — the same
  reason `payload.py` renders writes without sending them.

The live calls are not implemented. The app has no LinkedIn read access yet, and
a stub returning invented numbers would poison the catering worklist with
fabricated evidence, which is worse than an empty one.
"""

from __future__ import annotations

from dataclasses import dataclass

from contract import Contract, load_performance, write_performance
from core import Config, load_ledger

# The aggregate fields the loop uses. Anything not on this list is not read.
METRICS = ("impressions", "clicks", "reactions", "comments", "shares")


@dataclass
class ReadPlan:
    """One read the app would make, described rather than made."""

    what: str
    endpoint: str
    scope: str
    returns: str


def plan(cfg: Config) -> list[ReadPlan]:
    """The complete read surface of the analytics lane.

    Deliberately short. If this list ever grows a call that returns anything
    about another member, that is a change to the product's boundary and not an
    implementation detail.
    """
    if cfg.author_kind == "organization":
        return [
            ReadPlan(
                what="confirm a post published",
                endpoint="GET /rest/posts/{urn}",
                scope="r_organization_social",
                returns="the app's own post, as created",
            ),
            ReadPlan(
                what="aggregate statistics for the page's own posts",
                endpoint="GET /rest/organizationalEntityShareStatistics",
                scope="r_organization_social",
                returns="impressions, clicks, reactions, comments, shares per post",
            ),
            ReadPlan(
                what="page follower and visitor trend",
                endpoint="GET /rest/organizationPageStatistics",
                scope="r_organization_social",
                returns="aggregate counts over time",
            ),
        ]
    return [
        ReadPlan(
            what="confirm a post published",
            endpoint="GET /rest/posts/{urn}",
            scope="member read, own content",
            returns="the member's own post, as created",
        ),
        ReadPlan(
            what="aggregate statistics for the member's own posts",
            endpoint="GET /rest/posts (own) + statistics",
            scope="member read, own content",
            returns="impressions, clicks, reactions, comments, shares per post",
        ),
    ]


def describe_plan(cfg: Config) -> str:
    lines = ["Reads this lane would make, and nothing else:", ""]
    for item in plan(cfg):
        lines.append(f"  {item.endpoint}")
        lines.append(f"    to        {item.what}")
        lines.append(f"    scope     {item.scope}")
        lines.append(f"    returns   {item.returns}")
        lines.append("")
    lines.append("No member profiles, connections, followers, or feeds. No per-member")
    lines.append("records of who engaged — aggregate counts only.")
    return "\n".join(lines)


def _engagements(stats: dict) -> int:
    """Reactions, comments, and shares — the deliberate actions. Impressions are
    the denominator, and clicks measure something different (reading), so
    neither belongs in this total."""
    return sum(int(stats.get(k) or 0) for k in ("reactions", "comments", "shares"))


def normalise(raw: dict) -> dict:
    """Keep only the aggregate metrics, coerce to integers, add the derived
    total. Anything unexpected in the input is dropped rather than stored."""
    clean = {k: int(raw.get(k) or 0) for k in METRICS}
    clean["engagements"] = _engagements(clean)
    return clean


def ingest(cfg: Config, contract: Contract, stats_by_urn: dict) -> tuple[dict, int]:
    """Join post statistics onto content paths via the publish ledger.

    The ledger is what knows which post came from which page, so statistics
    arrive keyed by post URN and leave keyed by content path — the key the
    content index and the catering worklist both use.
    """
    by_urn: dict[str, str] = {}
    for entry in load_ledger(cfg):
        urn = str(entry.get("urn") or "")
        source = str(entry.get("content_path") or entry.get("source") or "")
        if urn and source:
            by_urn[urn] = source

    merged = load_performance(contract)
    matched = 0
    for urn, raw in stats_by_urn.items():
        path = by_urn.get(str(urn))
        if not path or not isinstance(raw, dict):
            continue
        merged[path] = normalise(raw)
        matched += 1

    write_performance(contract, merged)
    return merged, matched


def fetch(cfg: Config) -> dict:
    """Live statistics. Not implemented — see the module docstring.

    Raising is the right behaviour: a caller that wanted real numbers must not
    silently receive an empty set and treat it as "nothing engaged."
    """
    raise NotImplementedError(
        "Reading post statistics needs LinkedIn read access, which this app has "
        "not been granted. `plan` describes the calls; `ingest` accepts them from "
        "a file so the loop can be exercised without inventing numbers."
    )
