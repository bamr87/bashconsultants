"""The track record — what publishing actually accumulates into.

This is the reason a developer keeps using the tool. One post is a post; forty
posts tied to real shipped work is a portfolio, and it is visible to anyone
deciding whether to hire, fund, or collaborate with you.

Computed entirely from the local ledger. Once the app has read access, a
developer's own post statistics fill in the engagement column — their own
posts only, never anyone else's.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from core import Config, load_ledger


@dataclass
class Portfolio:
    count: int = 0
    by_kind: Counter = field(default_factory=Counter)
    by_audience: Counter = field(default_factory=Counter)
    by_month: Counter = field(default_factory=Counter)
    topics: Counter = field(default_factory=Counter)
    latest: str = ""

    @property
    def months_active(self) -> int:
        return len(self.by_month)

    @property
    def cadence(self) -> float:
        """Posts per active month — the number that predicts whether an
        audience actually forms."""
        return round(self.count / self.months_active, 1) if self.months_active else 0.0

    @property
    def streak(self) -> int:
        """Consecutive most-recent months with at least one post."""
        if not self.by_month:
            return 0
        months = sorted(self.by_month, reverse=True)
        streak, cursor = 0, months[0]
        for month in months:
            if month != cursor:
                break
            streak += 1
            year, mon = (int(x) for x in cursor.split("-"))
            cursor = f"{year - 1:04d}-12" if mon == 1 else f"{year:04d}-{mon - 1:02d}"
        return streak


def build(cfg: Config) -> Portfolio:
    portfolio = Portfolio()
    for entry in load_ledger(cfg):
        portfolio.count += 1
        portfolio.by_kind[str(entry.get("kind", "unknown"))] += 1
        if entry.get("audience"):
            portfolio.by_audience[str(entry["audience"])] += 1
        published = str(entry.get("published_at", ""))
        if len(published) >= 7:
            portfolio.by_month[published[:7]] += 1
        for tag in entry.get("hashtags", []):
            portfolio.topics[str(tag)] += 1
        portfolio.latest = published or portfolio.latest
    return portfolio


def render(portfolio: Portfolio) -> str:
    if not portfolio.count:
        return (
            "portfolio: nothing published yet.\n"
            "  Approve a draft and run `publish` — the track record starts at one."
        )
    lines = [
        f"portfolio: {portfolio.count} post(s) across {portfolio.months_active} month(s)",
        f"  cadence:  {portfolio.cadence} per active month",
        f"  streak:   {portfolio.streak} consecutive month(s)",
    ]
    if portfolio.by_kind:
        kinds = ", ".join(f"{k} {v}" for k, v in portfolio.by_kind.most_common())
        lines.append(f"  from:     {kinds}")
    if portfolio.by_audience:
        auds = ", ".join(f"{k} {v}" for k, v in portfolio.by_audience.most_common())
        lines.append(f"  written for: {auds}")
    if portfolio.topics:
        topics = ", ".join(f"#{k}" for k, _ in portfolio.topics.most_common(5))
        lines.append(f"  topics:   {topics}")
    if portfolio.latest:
        lines.append(f"  latest:   {portfolio.latest}")
    return "\n".join(lines)
