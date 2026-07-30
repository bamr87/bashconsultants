"""Find the things in a repository that are worth telling someone about.

A developer has already written the hard part — the commit message, the
changelog entry, the release note, the doc. Discovery reads those, so
publishing starts from finished work instead of a blank page.

Everything here is read-only and local: git plumbing and file reads. No
network, and nothing is sent anywhere.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from core import Config


@dataclass
class Source:
    """One publishable thing, with a stable id you can pass to `draft`."""

    id: str
    kind: str          # tag | changelog | post | commits
    title: str
    detail: str = ""   # the body the draft composes from
    ref: str = ""      # file path or git ref this came from

    @property
    def short(self) -> str:
        text = " ".join(self.detail.split())
        return text[:96] + "…" if len(text) > 96 else text


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


def discover(cfg: Config) -> list[Source]:
    """All publishable material, newest and most concrete first."""
    found: list[Source] = []
    if cfg.include_tags:
        found.extend(_tags(cfg))
    found.extend(_changelog(cfg))
    found.extend(_posts(cfg))
    if cfg.include_commits:
        found.extend(_commits(cfg))
    return found


def find(cfg: Config, source_id: str) -> Source | None:
    for source in discover(cfg):
        if source.id == source_id:
            return source
    # Allow the bare half of an id, so `draft v0.4.0` finds `tag:v0.4.0`.
    for source in discover(cfg):
        if source.id.partition(":")[2] == source_id:
            return source
    return None
