"""Find the things in a repository that are worth telling someone about.

Two tiers, and the order matters.

**The CMS index first.** When a site has a `.cms/` contract, publishable
material is whatever the content index says is publishable — the same rows the
authoring surface renders, with the same health scores and freshness bands. One
index, many outputs: the alternative is a second definition of "a page" that
drifts from the first.

**The repository second.** With no `.cms/` present, discovery falls back to
reading git and the filesystem directly: tags, conventional commits, changelog
sections, markdown docs. That keeps the tool useful for an individual with a
repo and no CMS, which is most people on their first day.

Everything here is read-only and local: git plumbing and file reads. No network,
and nothing is sent anywhere.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import contract as contract_mod
from core import Config


@dataclass
class Source:
    """One publishable thing, with a stable id you can pass to `draft`."""

    id: str
    kind: str          # content | tag | changelog | post | commits
    title: str
    detail: str = ""   # the body the draft composes from
    ref: str = ""      # file path or git ref this came from
    # Set only for `content` sources, i.e. those that came from the CMS index.
    # Carrying them lets the draft record which page it distributes, which is
    # what lets analytics join engagement back onto content.
    content_path: str = ""
    collection: str = ""
    health: int = -1
    freshness: str = ""

    @property
    def short(self) -> str:
        text = " ".join(self.detail.split())
        return text[:96] + "…" if len(text) > 96 else text

    @property
    def from_cms(self) -> bool:
        return bool(self.content_path)


def _git(root: Path, *args: str) -> str:
    """Run git, returning empty on any failure — a repo without tags, or no
    git at all, is a normal state and not an error worth raising."""
    try:
        out = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def _tags(cfg: Config, limit: int = 3) -> list[Source]:
    raw = _git(cfg.root, "tag", "--sort=-creatordate", "--format=%(refname:short)%09%(contents:subject)")
    found: list[Source] = []
    for line in raw.splitlines()[:limit]:
        name, _, subject = line.partition("\t")
        name = name.strip()
        if not name:
            continue
        found.append(
            Source(
                id=f"tag:{name}",
                kind="tag",
                title=f"Released {name}",
                detail=subject.strip() or f"Tagged {name}.",
                ref=name,
            )
        )
    return found


def _changelog(cfg: Config, limit: int = 2) -> list[Source]:
    """Pull the bullet list out of each `## [version]` section."""
    path = cfg.root / cfg.changelog
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = re.split(r"^##\s+", text, flags=re.M)[1:]
    found: list[Source] = []
    for section in sections[:limit]:
        heading, _, body = section.partition("\n")
        heading = heading.strip().strip("[]")
        bullets = [
            re.sub(r"\*\*(.+?)\*\*", r"\1", line.strip()[2:]).strip()
            for line in body.splitlines()
            if line.strip().startswith("- ")
        ]
        if not bullets:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-") or "unversioned"
        found.append(
            Source(
                id=f"changelog:{slug}",
                kind="changelog",
                title=f"What changed in {heading}",
                detail="\n".join(f"- {b}" for b in bullets[:6]),
                ref=cfg.changelog,
            )
        )
    return found


def _posts(cfg: Config, limit: int = 4) -> list[Source]:
    """Markdown the developer wrote, matched by the globs in config."""
    found: list[Source] = []
    seen: set[Path] = set()
    for pattern in cfg.posts:
        for path in sorted(cfg.root.glob(pattern)):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8", errors="replace")
            title = ""
            para: list[str] = []
            # Take the first whole paragraph, not the first N lines — markdown
            # is usually hard-wrapped, so a line count cuts mid-sentence.
            for line in text.splitlines():
                stripped = line.strip()
                if not title and stripped.startswith("# "):
                    title = stripped[2:].strip()
                    continue
                if not title:
                    continue
                if not stripped:
                    if para:
                        break
                    continue
                if stripped.startswith(("#", ">", "|", "-", "*", "`")):
                    if para:
                        break
                    continue
                para.append(stripped)
            if not title:
                continue
            summary = [" ".join(para)] if para else []
            found.append(
                Source(
                    id=f"post:{path.stem}",
                    kind="post",
                    title=title,
                    detail=" ".join(summary),
                    ref=str(path.relative_to(cfg.root)),
                )
            )
            if len(found) >= limit:
                return found
    return found


def _commits(cfg: Config, limit: int = 12) -> list[Source]:
    """Group recent conventional commits into one 'here is what I shipped'."""
    raw = _git(cfg.root, "log", f"-{limit * 3}", "--no-merges", "--format=%s")
    if not raw:
        return []
    wanted = tuple(f"{t}" for t in cfg.commit_types)
    subjects: list[str] = []
    for line in raw.splitlines():
        match = re.match(r"^(\w+)(\([^)]*\))?!?:\s*(.+)$", line.strip())
        if match and match.group(1) in wanted:
            subjects.append(match.group(3).strip())
        if len(subjects) >= limit:
            break
    if not subjects:
        return []
    return [
        Source(
            id="commits:recent",
            kind="commits",
            title=f"Recent work — {len(subjects)} changes",
            detail="\n".join(f"- {s}" for s in subjects[:6]),
            ref="git log",
        )
    ]


# Real pages open with more than prose: inline <style> blocks, Liquid tags, HTML
# wrappers, tables. Anything with these in it is markup, not a sentence.
_NOT_PROSE = ("{", "}", ";", "<", ">", "|", "=")

_BLOCK_OPEN = ("<style", "<script", "<svg")
_BLOCK_CLOSE = ("</style>", "</script>", "</svg>")


def _looks_like_prose(line: str) -> bool:
    """Whether a line is a sentence a human wrote, rather than markup.

    Cheap and strict on purpose: a false negative costs one skipped line, while a
    false positive puts a CSS rule in a LinkedIn post.
    """
    if any(ch in line for ch in _NOT_PROSE):
        return False
    if line.startswith(("#", "!", "[", "*", "-", "`", ":", ".", "%", "@")):
        return False
    return len(line.split()) >= 3


def _first_paragraph(root: Path, content_path: str) -> str:
    """The opening paragraph of a page, for the draft to compose from.

    The index carries metadata, not prose, so the body still comes from the file
    — but only for the one page being drafted, not the whole corpus.
    """
    page = root / content_path
    if not page.exists():
        return ""
    try:
        text = page.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) >= 3 else text

    para: list[str] = []
    in_block = False
    for raw in text.splitlines():
        stripped = raw.strip()
        lowered = stripped.lower()

        # Walk over embedded style/script/svg blocks entirely.
        if in_block:
            if any(close in lowered for close in _BLOCK_CLOSE):
                in_block = False
            continue
        if any(lowered.startswith(open_) for open_ in _BLOCK_OPEN):
            in_block = not any(close in lowered for close in _BLOCK_CLOSE)
            continue

        if not stripped:
            if para:
                break
            continue
        if not _looks_like_prose(stripped):
            if para:
                break
            continue
        para.append(stripped)
        # Two lines of a hard-wrapped paragraph is enough for a hook; more just
        # pushes the call to action past what anyone reads.
        if len(" ".join(para)) > 320:
            break
    return " ".join(para)


def _from_contract(cfg: Config, contract: contract_mod.Contract, limit: int = 25) -> list[Source]:
    """Publishable content, straight off the CMS index."""
    found: list[Source] = []
    for record in contract.distributable()[:limit]:
        found.append(
            Source(
                id=f"content:{record.slug}",
                kind="content",
                title=record.title or record.slug,
                detail=_first_paragraph(cfg.root, record.path),
                ref=record.path,
                content_path=record.path,
                collection=record.collection,
                health=record.health,
                freshness=record.freshness,
            )
        )
    return found


def discover(cfg: Config, contract: contract_mod.Contract | None = None) -> list[Source]:
    """All publishable material, most authoritative first.

    With a `.cms/` contract present, its content index is the answer and the
    repository heuristics are additive — a release tag is still worth posting
    about, and the index has no row for it.
    """
    if contract is None:
        contract = contract_mod.load(cfg.root)

    found: list[Source] = []
    if contract.present:
        found.extend(_from_contract(cfg, contract))
    if cfg.include_tags:
        found.extend(_tags(cfg))
    found.extend(_changelog(cfg))
    if not contract.present:
        # With no index, markdown docs are the only content signal there is.
        found.extend(_posts(cfg))
    if cfg.include_commits:
        found.extend(_commits(cfg))
    return found


def find(cfg: Config, source_id: str, contract: contract_mod.Contract | None = None) -> Source | None:
    found = discover(cfg, contract)
    for source in found:
        if source.id == source_id:
            return source
    # Allow the bare half of an id, so `draft v0.4.0` finds `tag:v0.4.0`.
    for source in found:
        if source.id.partition(":")[2] == source_id:
            return source
    return None
