"""Config, frontmatter, and on-disk state for shiplog.

Everything shiplog knows lives in files inside the user's own repository:
config in `shiplog.toml`, pending drafts in `.shiplog/queue/`, and the
published record in `.shiplog/ledger.json`. There is no server and no account,
so there is nothing to sign into and nothing to migrate off.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

QUEUE_DIRNAME = "queue"
STATE_DIRNAME = ".shiplog"
CONFIG_NAME = "shiplog.toml"

# A draft moves pending -> approved -> published. `publish` only ever reads
# `approved`, which is the whole point: the gate is a state a person sets.
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_PUBLISHED = "published"
STATUS_ORDER = [STATUS_PENDING, STATUS_APPROVED, STATUS_PUBLISHED]

STARTER_CONFIG = '''\
# shiplog — publish what you ship.
# Everything here is yours to edit; nothing is inferred from LinkedIn.

[author]
# Which identity posts. "member" is your own profile, "organization" is a page.
kind = "member"
# Filled in by the OAuth flow. Placeholder until then.
member_urn = "urn:li:person:REPLACE_ME"
organization_urn = ""
name = "Your Name"
headline = "What you want to be known for"

[sources]
# Where publishable material lives in this repository.
changelog = "CHANGELOG.md"
posts = ["docs/**/*.md"]
include_tags = true
include_commits = true
commit_types = ["feat", "fix", "perf"]

# Audience profiles are DECLARED, not derived. shiplog never reads your
# connections or anyone's profile to guess who you are writing for.
[[audience]]
id = "backend-hiring"
label = "Engineering managers hiring backend developers"
reads_for = "evidence someone can ship and explain their work"
tone = "plain, specific, no hype"
hashtags = ["Backend", "SoftwareEngineering"]

[[audience]]
id = "peer-devs"
label = "Other developers working on similar problems"
reads_for = "the technical detail and the trade-off you actually made"
tone = "practitioner to practitioner"
hashtags = ["DevTools", "OpenSource"]
'''


@dataclass
class Audience:
    """A reader the developer has decided to write for."""

    id: str
    label: str
    reads_for: str = ""
    tone: str = ""
    hashtags: list[str] = field(default_factory=list)


@dataclass
class Config:
    root: Path
    author_kind: str = "member"
    member_urn: str = ""
    organization_urn: str = ""
    name: str = ""
    headline: str = ""
    changelog: str = "CHANGELOG.md"
    posts: list[str] = field(default_factory=list)
    include_tags: bool = True
    include_commits: bool = True
    commit_types: list[str] = field(default_factory=lambda: ["feat", "fix", "perf"])
    audiences: list[Audience] = field(default_factory=list)

    @property
    def state_dir(self) -> Path:
        return self.root / STATE_DIRNAME

    @property
    def queue_dir(self) -> Path:
        return self.state_dir / QUEUE_DIRNAME

    @property
    def ledger_path(self) -> Path:
        return self.state_dir / "ledger.json"

    def author_urn(self) -> str:
        """The URN a post is authored by — a person or an organization."""
        if self.author_kind == "organization":
            return self.organization_urn
        return self.member_urn

    def audience(self, audience_id: str) -> Audience | None:
        for aud in self.audiences:
            if aud.id == audience_id:
                return aud
        return None


def load_config(root: Path) -> Config:
    """Read `shiplog.toml`. A missing file yields usable defaults, so every
    command works in a repository that has not run `init` yet."""
    cfg = Config(root=root)
    path = root / CONFIG_NAME
    if not path.exists():
        return cfg
    with path.open("rb") as handle:
        raw = tomllib.load(handle)

    author = raw.get("author", {})
    cfg.author_kind = str(author.get("kind", "member"))
    cfg.member_urn = str(author.get("member_urn", ""))
    cfg.organization_urn = str(author.get("organization_urn", ""))
    cfg.name = str(author.get("name", ""))
    cfg.headline = str(author.get("headline", ""))

    sources = raw.get("sources", {})
    cfg.changelog = str(sources.get("changelog", "CHANGELOG.md"))
    cfg.posts = list(sources.get("posts", []))
    cfg.include_tags = bool(sources.get("include_tags", True))
    cfg.include_commits = bool(sources.get("include_commits", True))
    cfg.commit_types = list(sources.get("commit_types", ["feat", "fix", "perf"]))

    for entry in raw.get("audience", []):
        cfg.audiences.append(
            Audience(
                id=str(entry.get("id", "")),
                label=str(entry.get("label", "")),
                reads_for=str(entry.get("reads_for", "")),
                tone=str(entry.get("tone", "")),
                hashtags=list(entry.get("hashtags", [])),
            )
        )
    return cfg


# ---------------------------------------------------------------------------
# Frontmatter drafts
# ---------------------------------------------------------------------------

def parse_draft(text: str) -> tuple[dict, str]:
    """Split `---\\nkey: value\\n---\\nbody` into (metadata, body).

    Deliberately small: draft frontmatter is flat strings, so a full YAML
    parser would be a dependency bought for nothing.
    """
    if not text.startswith("---"):
        return {}, text.strip()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text.strip()
    meta: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta, parts[2].strip()


def render_draft(meta: dict, body: str) -> str:
    lines = ["---"]
    for key, value in meta.items():
        text = str(value)
        lines.append(f'{key}: "{text}"' if ": " in text or "#" in text else f"{key}: {text}")
    lines.append("---")
    lines.append(body.strip())
    return "\n".join(lines) + "\n"


@dataclass
class Draft:
    path: Path
    meta: dict
    body: str

    @property
    def id(self) -> str:
        return self.path.stem

    @property
    def status(self) -> str:
        return str(self.meta.get("status", STATUS_PENDING)).lower()

    @property
    def audience_id(self) -> str:
        return str(self.meta.get("audience", ""))

    @property
    def title(self) -> str:
        return str(self.meta.get("title", self.id))


def read_draft(path: Path) -> Draft:
    meta, body = parse_draft(path.read_text(encoding="utf-8"))
    return Draft(path=path, meta=meta, body=body)


def write_draft(draft: Draft) -> None:
    draft.path.parent.mkdir(parents=True, exist_ok=True)
    draft.path.write_text(render_draft(draft.meta, draft.body), encoding="utf-8")


def load_queue(cfg: Config) -> list[Draft]:
    if not cfg.queue_dir.exists():
        return []
    return [read_draft(p) for p in sorted(cfg.queue_dir.glob("*.md"))]


def find_draft(cfg: Config, draft_id: str) -> Draft | None:
    for draft in load_queue(cfg):
        if draft.id == draft_id or draft.id.endswith(draft_id):
            return draft
    return None


# ---------------------------------------------------------------------------
# Ledger — the published record, and the portfolio's source of truth
# ---------------------------------------------------------------------------

def load_ledger(cfg: Config) -> list[dict]:
    if not cfg.ledger_path.exists():
        return []
    try:
        data = json.loads(cfg.ledger_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data.get("published", []) if isinstance(data, dict) else []


def append_ledger(cfg: Config, entry: dict) -> None:
    entries = load_ledger(cfg)
    entries.append(entry)
    cfg.ledger_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.ledger_path.write_text(
        json.dumps({"published": entries}, indent=2) + "\n", encoding="utf-8"
    )


def already_published(cfg: Config, source_id: str) -> bool:
    """Idempotency: one source, one post. Re-running `publish` is safe."""
    return any(e.get("source") == source_id for e in load_ledger(cfg))
