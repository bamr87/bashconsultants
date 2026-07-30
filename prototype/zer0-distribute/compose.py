"""Turn a source into a LinkedIn draft, written for a declared audience.

**Audience is declared, never derived.** The profiles used here come from the
developer's own `zer0-distribute.toml`. zer0-distribute does not read connections, followers,
or anyone's profile to infer who the reader is — there is no code path that
requests member data, and adding one would be a change to this contract, not
an implementation detail.

Composition is deterministic: a template per source kind, shaped by the
audience's tone and hashtags. That means a draft exists with no API key and no
model in the path. A model's job is to improve the draft a human is already
looking at, never to be the only way to get one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from core import Audience, Config, Draft, STATUS_PENDING
from sources import Source

# LinkedIn truncates the visible post with "…see more" at roughly this point,
# so the reason to keep reading has to land before it.
FOLD = 140
MAX_LEN = 3000

# Copy that reads as marketing filler to a developer audience. A draft that
# trips one of these is flagged for the human, not silently rewritten.
FILLER = [
    (re.compile(r"\bgame[- ]chang(?:er|ing)\b", re.I), "game-changer"),
    (re.compile(r"\bcutting[- ]edge\b", re.I), "cutting-edge"),
    (re.compile(r"\bnext[- ]generation\b", re.I), "next-generation"),
    (re.compile(r"\brevolutionar(?:y|ies)\b", re.I), "revolutionary"),
    (re.compile(r"\bexcited to announce\b", re.I), "excited to announce"),
    (re.compile(r"\bthrilled to\b", re.I), "thrilled to"),
    (re.compile(r"\bhumbled\b", re.I), "humbled"),
    (re.compile(r"\bsynerg\w*", re.I), "synergy"),
    (re.compile(r"!{1,}"), "exclamation mark"),
]


@dataclass
class Composed:
    body: str
    warnings: list[str]

    @property
    def hook(self) -> str:
        """What a reader sees before the fold."""
        return self.body[:FOLD]


def _hashtags(audience: Audience | None, source: Source) -> str:
    tags = list(audience.hashtags) if audience else []
    if source.kind == "tag" and "Release" not in tags:
        tags.append("Release")
    if not tags:
        tags = ["SoftwareEngineering"]
    return " ".join(f"#{t.lstrip('#')}" for t in tags[:3])


def _closing(audience: Audience | None, source: Source) -> str:
    """One call to action, in the reader's own terms.

    The audience's `reads_for` is a note to the writer, not copy — splicing it
    into a sentence produces the kind of line nobody says out loud.
    """
    if source.kind == "content":
        return "Full piece is linked — happy to talk through any of it."
    if source.kind == "tag":
        return f"Code and changelog are public if you want the detail on {source.ref}."
    if source.kind == "changelog":
        return "The full list is in the changelog."
    if source.kind == "commits":
        return "It is all in the commit history if you want specifics."
    return "Happy to go deeper on any of this if it is useful."


def _template(source: Source, audience: Audience | None) -> str:
    """A hook that earns the click, the substance, then one ask."""
    who = f" for {audience.label.lower()}" if audience and audience.label else ""

    # A page out of the CMS index: the commentary is the hook above the link
    # card, so it must not restate the title the card already shows.
    if source.kind == "content":
        return (
            f"{source.detail}\n\n"
            f"{_closing(audience, source)}"
        )

    if source.kind == "tag":
        return (
            f"{source.title.replace('Released', 'Shipped')}. {source.detail}\n\n"
            "The part worth writing down is not the version number, it is what it "
            "changed for the person using it.\n\n"
            f"{_closing(audience, source)}"
        )
    if source.kind == "changelog":
        return (
            f"{source.title}, in plain terms:\n\n{source.detail}\n\n"
            "Each of those started as a real problem someone hit. That is usually "
            "the more interesting half of a release note.\n\n"
            f"{_closing(audience, source)}"
        )
    if source.kind == "commits":
        return (
            f"A week of work, written out{who}:\n\n{source.detail}\n\n"
            "None of it is dramatic on its own. Together it is the difference "
            "between a thing that demos and a thing that runs.\n\n"
            f"{_closing(audience, source)}"
        )
    # For a post, lead with the substance. A bare title on line one spends the
    # whole pre-fold budget saying nothing, which the hook check will flag.
    return (
        f"{source.detail}\n\n"
        f'Wrote that up properly as "{source.title}".\n\n'
        f"{_closing(audience, source)}"
    )


def check(body: str) -> list[str]:
    """Warn about filler and length. Advisory — the human decides."""
    warnings: list[str] = []
    for pattern, name in FILLER:
        if pattern.search(body):
            warnings.append(f"reads as filler: {name}")
    if len(body) > MAX_LEN:
        warnings.append(f"{len(body)} characters, over LinkedIn's {MAX_LEN} limit")
    first = body[:FOLD]
    if "\n" in first and len(first.split("\n")[0]) < 40:
        warnings.append("weak hook: the first line ends before it says anything")
    return warnings


def compose(cfg: Config, source: Source, audience_id: str = "") -> Composed:
    audience = cfg.audience(audience_id) if audience_id else None
    body = _template(source, audience)
    tags = _hashtags(audience, source)
    body = f"{body}\n\n{tags}"
    return Composed(body=body.strip(), warnings=check(body))


def draft_for(cfg: Config, source: Source, audience_id: str = "") -> Draft:
    """A pending draft on disk. It publishes only after a person approves it."""
    composed = compose(cfg, source, audience_id)
    slug = re.sub(r"[^a-z0-9]+", "-", source.id.lower()).strip("-")
    meta = {
        "source": source.id,
        "kind": source.kind,
        "title": source.title,
        "audience": audience_id,
        "author": cfg.author_urn(),
        "status": STATUS_PENDING,
    }
    # The join key for the whole feedback loop: engagement comes back keyed by
    # post URN, and this is what lets it land on the page that earned it.
    if source.content_path:
        meta["content_path"] = source.content_path
        meta["collection"] = source.collection
    return Draft(path=cfg.queue_dir / f"{slug}.md", meta=meta, body=composed.body)
