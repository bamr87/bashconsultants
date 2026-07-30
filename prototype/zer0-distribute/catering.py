"""Catering — deciding what to write next from how the audience responded.

The CMS engine already answers "what is wrong with what I have," from linting:
missing fields, thin content, stale dates, broken links. It cannot answer "what
should I write more of," because that evidence does not live in the repository.
It lives in what readers did with what was published.

This module closes that loop. It joins three things the rest of the lane
produces — the content index (`contract.py`), the publish ledger (`core.py`),
and per-content engagement (`analytics.py`) — and emits a worklist in the same
shape the engine writes, so both land in one list in front of one person.

Four questions, in the order they are worth answering:

1. **Undistributed strength.** Content that scores well and has never been put
   in front of anyone. The cheapest win available: no writing required.
2. **Proven subjects.** Topics whose posts earned attention. Evidence to write
   more, not a guarantee.
3. **Quiet subjects.** Topics that consistently did not land. Worth saying out
   loud, because the alternative is repeating them by default.
4. **Stale but working.** Content that performed and has since gone stale —
   refresh beats writing something new from nothing.

Every ranking is computed from the author's own aggregate numbers. Nothing here
looks at who engaged, and no per-member data enters this module — see the
boundary note in `analytics.py`.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from contract import FRESH_BANDS, Contract, ContentRecord

# Below this many observations a per-topic average is noise, not a signal. The
# worklist says so rather than ranking on one lucky post.
MIN_OBSERVATIONS = 2


@dataclass
class TopicSignal:
    topic: str
    posts: int = 0
    impressions: int = 0
    engagements: int = 0

    @property
    def rate(self) -> float:
        """Engagements per impression. The only rate worth comparing across
        topics, because impression counts differ wildly by cadence."""
        return round(self.engagements / self.impressions, 4) if self.impressions else 0.0

    @property
    def confident(self) -> bool:
        return self.posts >= MIN_OBSERVATIONS and self.impressions > 0


@dataclass
class Catering:
    undistributed: list[ContentRecord] = field(default_factory=list)
    proven: list[TopicSignal] = field(default_factory=list)
    quiet: list[TopicSignal] = field(default_factory=list)
    refresh: list[ContentRecord] = field(default_factory=list)
    observations: int = 0

    @property
    def has_evidence(self) -> bool:
        """Whether any audience data exists yet. Without it the worklist still
        has work in it — the undistributed list — but says plainly that the
        topic rankings are not available rather than inventing them."""
        return self.observations > 0


def _topic_signals(performance: dict, contract: Contract) -> list[TopicSignal]:
    """Group engagement by the collection each piece of content belongs to.

    Collection is the topic axis a CMS already knows, which keeps this honest:
    no clustering, no inferred interests, just the author's own taxonomy.
    """
    grouped: dict[str, TopicSignal] = defaultdict(lambda: TopicSignal(topic=""))
    for path, stats in performance.items():
        if not isinstance(stats, dict):
            continue
        record = contract.by_path(path)
        topic = (record.collection if record else "") or "uncategorised"
        signal = grouped[topic]
        signal.topic = topic
        signal.posts += 1
        signal.impressions += int(stats.get("impressions") or 0)
        signal.engagements += int(stats.get("engagements") or 0)
    return list(grouped.values())


def build(contract: Contract, performance: dict, published_paths: set[str]) -> Catering:
    catering = Catering(observations=len(performance))

    # 1. Strong content nobody has seen. Ranked by health, best first.
    catering.undistributed = [
        r for r in contract.distributable() if r.path not in published_paths
    ][:15]

    # 2 + 3. Topics that landed, and topics that did not.
    signals = [s for s in _topic_signals(performance, contract) if s.confident]
    signals.sort(key=lambda s: -s.rate)
    if signals:
        median = signals[len(signals) // 2].rate
        catering.proven = [s for s in signals if s.rate >= median][:6]
        catering.quiet = [s for s in signals if s.rate < median][:6]

    # 4. Content that earned attention and has since gone stale.
    catering.refresh = [
        record
        for path, stats in performance.items()
        if (record := contract.by_path(path)) is not None
        and record.freshness not in FRESH_BANDS
        and int(stats.get("engagements") or 0) > 0
    ][:10]

    return catering


def render(catering: Catering, date: str) -> str:
    """The worklist, in the engine's own format so both read as one thing."""
    lines = [
        f"# Distribution worklist — {date}",
        "",
        "_Generated by `zer0-distribute cater`. The audience-evidence counterpart to "
        "`.cms/worklists/<date>.md`: that one says what is wrong with the content, this one "
        "says what to write next. Rankings use the author's own aggregate post statistics; "
        "no member-level data is read or stored._",
        "",
    ]

    lines += ["## Lane A — Distribute what already exists", ""]
    if catering.undistributed:
        lines += [
            "Content that scores well and has never been published off-site. No writing "
            "required, so this is the cheapest work on the list.",
            "",
            "| # | Health | Fresh | Collection | File |",
            "|---|---|---|---|---|",
        ]
        for i, record in enumerate(catering.undistributed, 1):
            health = record.health if record.health >= 0 else "—"
            lines.append(
                f"| {i} | {health} | {record.freshness} | {record.collection} | `{record.path}` |"
            )
    else:
        lines.append("_Everything publishable has been distributed._")
    lines.append("")

    lines += ["## Lane B — Write more of what landed", ""]
    if not catering.has_evidence:
        lines += [
            "_No audience data yet. Topic rankings need published posts with statistics "
            "read back; until then this lane is empty rather than guessed._",
            "",
        ]
    elif catering.proven:
        lines += [
            f"Topics at or above the median engagement rate, each with at least "
            f"{MIN_OBSERVATIONS} posts behind it. Evidence, not a guarantee.",
            "",
            "| Topic | Posts | Impressions | Engagement rate |",
            "|---|---|---|---|",
        ]
        for signal in catering.proven:
            lines.append(
                f"| {signal.topic} | {signal.posts} | {signal.impressions:,} | {signal.rate:.2%} |"
            )
        lines.append("")
    else:
        lines += [
            f"_Not enough observations yet — a topic needs {MIN_OBSERVATIONS} posts before "
            "its average means anything._",
            "",
        ]

    lines += ["## Lane C — Say the quiet part", ""]
    if catering.quiet:
        lines += [
            "Topics below the median. Worth naming, because the alternative is repeating "
            "them by default. Low engagement is not the same as low value — a compliance "
            "post can matter and still be unpopular.",
            "",
            "| Topic | Posts | Impressions | Engagement rate |",
            "|---|---|---|---|",
        ]
        for signal in catering.quiet:
            lines.append(
                f"| {signal.topic} | {signal.posts} | {signal.impressions:,} | {signal.rate:.2%} |"
            )
    else:
        lines.append("_Nothing to report._")
    lines.append("")

    lines += ["## Lane D — Refresh what worked", ""]
    if catering.refresh:
        lines += [
            "Content that earned engagement and has since gone stale. Updating a page that "
            "already found its readers beats starting from nothing.",
            "",
            "| Health | Fresh | File |",
            "|---|---|---|",
        ]
        for record in catering.refresh:
            health = record.health if record.health >= 0 else "—"
            lines.append(f"| {health} | {record.freshness} | `{record.path}` |")
    else:
        lines.append("_Nothing published has gone stale._")
    lines.append("")

    return "\n".join(lines)
