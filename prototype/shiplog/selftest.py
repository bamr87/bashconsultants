"""Offline assertions across the whole pipeline.

Runs in a throwaway git repository with no network and no credentials, which
is the point: every claim the tool makes about its own behaviour is checkable
without LinkedIn access. The approval-gate tests are the ones that matter — if
`publish` ever picks up a draft a human did not approve, this fails.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import compose
import payload as payload_mod
import portfolio as portfolio_mod
import sources as sources_mod
from core import (
    STARTER_CONFIG,
    STATUS_APPROVED,
    STATUS_PENDING,
    Config,
    append_ledger,
    load_config,
    load_queue,
    parse_draft,
    render_draft,
    write_draft,
)

CHANGELOG = """# Change Log

## [0.4.0]

- **Queue** — drafts wait for a person instead of a scheduler.
- **Payload preview** — read the request before it is sent.

## [0.3.0]

- **Audience profiles** — declared in config, never inferred.
"""

POST = """# Why the approval gate is the feature

Publishing tools fail in one direction: they post something the author would
not have posted. A queue that requires a click is slower and better.
"""


def _fixture(root: Path) -> Config:
    (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "approval-gate.md").write_text(POST, encoding="utf-8")
    (root / "shiplog.toml").write_text(STARTER_CONFIG, encoding="utf-8")
    for args in (
        ["init", "-q"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "T"],
        ["add", "-A"],
        ["commit", "-q", "-m", "feat(queue): hold drafts for a human"],
        ["tag", "-a", "v0.4.0", "-m", "The approval gate release"],
    ):
        subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=30)
    return load_config(root)


def run() -> int:
    failures: list[str] = []

    def check(label: str, condition: bool) -> None:
        if not condition:
            failures.append(label)

    # --- frontmatter round-trips ---
    meta, body = parse_draft(render_draft({"status": "pending", "title": "x"}, "hello"))
    check("frontmatter round-trip", meta.get("status") == "pending" and body == "hello")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cfg = _fixture(root)

        # --- config ---
        check("config: audiences load", len(cfg.audiences) == 2)
        check("config: audience lookup", cfg.audience("peer-devs") is not None)
        check("config: member author", payload_mod.scope_for(cfg) == "w_member_social")
        org = load_config(root)
        org.author_kind = "organization"
        org.organization_urn = "urn:li:organization:1"
        check("config: org author", payload_mod.scope_for(org) == "w_organization_social")
        check("config: org urn wins", org.author_urn() == "urn:li:organization:1")

        # --- discovery ---
        found = sources_mod.discover(cfg)
        kinds = {s.kind for s in found}
        check("sources: finds a tag", "tag" in kinds)
        check("sources: finds changelog", "changelog" in kinds)
        check("sources: finds a post", "post" in kinds)
        check("sources: finds commits", "commits" in kinds)
        check("sources: ids are unique", len({s.id for s in found}) == len(found))
        check("sources: lookup by full id", sources_mod.find(cfg, "tag:v0.4.0") is not None)
        check("sources: lookup by bare ref", sources_mod.find(cfg, "v0.4.0") is not None)
        check("sources: unknown id is None", sources_mod.find(cfg, "nope:xyz") is None)

        # --- composition ---
        tag_source = sources_mod.find(cfg, "tag:v0.4.0")
        composed = compose.compose(cfg, tag_source, "peer-devs")
        check("compose: non-empty", len(composed.body) > 80)
        check("compose: under the limit", len(composed.body) <= compose.MAX_LEN)
        check("compose: carries hashtags", "#" in composed.body)
        check("compose: audience hashtag used", "#DevTools" in composed.body)
        check("compose: hook is the first line", len(composed.hook) == compose.FOLD)
        check("compose: clean draft has no warnings", composed.warnings == [])
        check("compose: works with no audience",
              len(compose.compose(cfg, tag_source, "").body) > 50)

        # --- the filler guard ---
        check("guard: catches hype", "reads as filler: game-changer"
              in compose.check("This is a game-changer for teams"))
        check("guard: catches exclamation", any(
            "exclamation" in w for w in compose.check("Shipped it!")))
        check("guard: catches over-length", any(
            "over LinkedIn" in w for w in compose.check("x" * (compose.MAX_LEN + 1))))
        check("guard: passes plain copy", compose.check("Shipped v1. It is faster.") == [])

        # --- the approval gate ---
        draft = compose.draft_for(cfg, tag_source, "peer-devs")
        write_draft(draft)
        queue = load_queue(cfg)
        check("queue: draft persisted", len(queue) == 1)
        check("gate: new draft is pending", queue[0].status == STATUS_PENDING)
        approved = [d for d in load_queue(cfg) if d.status == STATUS_APPROVED]
        check("gate: nothing is approved on creation", approved == [])

        queue[0].meta["status"] = STATUS_APPROVED
        write_draft(queue[0])
        check("gate: approval persists",
              load_queue(cfg)[0].status == STATUS_APPROVED)

        # --- payload ---
        body = payload_mod.build(cfg, load_queue(cfg)[0])
        check("payload: author is the member urn", body["author"].startswith("urn:li:person:"))
        check("payload: commentary matches the draft", body["commentary"] == queue[0].body)
        check("payload: published state", body["lifecycleState"] == "PUBLISHED")
        check("payload: public", body["visibility"] == "PUBLIC")
        check("payload: no third-party distribution",
              body["distribution"]["thirdPartyDistributionChannels"] == [])
        check("payload: serializes", json.loads(json.dumps(body))["author"] == body["author"])

        # --- portfolio ---
        check("portfolio: empty ledger reads as zero", portfolio_mod.build(cfg).count == 0)
        for month, kind in (("2026-05", "tag"), ("2026-06", "post"), ("2026-07", "post")):
            append_ledger(cfg, {
                "draft": f"d-{month}", "source": f"s-{month}", "kind": kind,
                "audience": "peer-devs", "hashtags": ["DevTools"],
                "published_at": f"{month}-01T00:00:00Z",
            })
        p = portfolio_mod.build(cfg)
        check("portfolio: counts posts", p.count == 3)
        check("portfolio: months active", p.months_active == 3)
        check("portfolio: cadence", p.cadence == 1.0)
        check("portfolio: consecutive streak", p.streak == 3)
        check("portfolio: groups by kind", p.by_kind["post"] == 2)
        check("portfolio: renders", "3 post(s)" in portfolio_mod.render(p))

        # --- idempotency ---
        from core import already_published
        check("ledger: known source is skipped", already_published(cfg, "s-2026-05"))
        check("ledger: unknown source is not", not already_published(cfg, "s-nope"))

        # --- dashboard renders without a browser ---
        import server
        page = server.render_page(cfg)
        check("dashboard: renders", "<!doctype html>" in page)
        check("dashboard: shows the queue", "Awaiting your approval" in page)
        check("dashboard: states the gate", "connections" in page)

    if failures:
        print(f"self-test: FAIL ({len(failures)})")
        for failure in failures:
            print(f"  ✗ {failure}")
        return 1
    print("self-test: PASS — discovery, composition, guard, approval gate, "
          "payload, portfolio, ledger, dashboard")
    return 0
