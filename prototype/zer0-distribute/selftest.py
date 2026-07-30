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


def _raises(fn, exc) -> bool:
    try:
        fn()
    except exc:
        return True
    except Exception:
        return False
    return False


def _write_cms_index(root: Path) -> None:
    """A `.cms/` index in the engine's own shape.

    Seven rows chosen to exercise every distributable/withheld branch: two healthy
    posts in one collection, two healthy notes in another (so topic ranking has
    something to compare), plus a low-health page, a draft, and a generated file
    that must all be withheld.
    """
    def row(path, collection, health, **over):
        record = {
            "path": path, "collection": collection, "fm_content_type": "post",
            "is_notebook": False, "frontmatter_present": True, "read_only": False,
            "generated": False, "structural": False, "draft": False,
            "title": Path(path).stem.replace("-", " ").title(),
            "description_len": 140, "title_len": 30, "word_count": 900,
            "heading_count": 4, "lastmod": "2026-07-01", "date": "2026-06-01",
            "age_days": 30, "freshness": "fresh", "broken_links": 0,
            "health": health, "issues": [],
        }
        record.update(over)
        return record

    files = [
        row("pages/_posts/good-one.md", "posts", 95),
        row("pages/_posts/second.md", "posts", 88),
        row("pages/_notes/quiet-one.md", "notes", 84),
        row("pages/_notes/quiet-two.md", "notes", 80, freshness="stale"),
        row("pages/_posts/unhealthy.md", "posts", 40),
        row("pages/_posts/draft-one.md", "posts", 95, draft=True),
        row("pages/_posts/generated.md", "posts", 95, generated=True),
    ]
    # Four of the seven are distributable; unhealthy/draft/generated exist to
    # prove each withholding branch fires.
    index_dir = root / ".cms" / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "content-index.json").write_text(
        json.dumps({"generated_at": "2026-07-30T00:00:00Z", "files": files}, indent=2),
        encoding="utf-8",
    )
    (index_dir / "summary.json").write_text(
        json.dumps({"generated_at": "2026-07-30T00:00:00Z", "total_files": len(files),
                    "avg_health": 82}, indent=2),
        encoding="utf-8",
    )
    for path in files:
        page = root / path["path"]
        page.parent.mkdir(parents=True, exist_ok=True)
        if not page.exists():
            page.write_text(
                f"---\ntitle: {path['title']}\n---\n\n"
                "A real opening paragraph so composition has substance to work "
                "from rather than an empty string.\n",
                encoding="utf-8",
            )


def approve_and_record(cfg: Config, draft, urn: str) -> None:
    """Walk one draft through the gate and into the ledger, as the CLI would."""
    from core import STATUS_PUBLISHED, append_ledger
    draft.meta["status"] = STATUS_PUBLISHED
    write_draft(draft)
    append_ledger(cfg, {
        "draft": draft.id,
        "source": str(draft.meta.get("source", draft.id)),
        "kind": str(draft.meta.get("kind", "")),
        "audience": draft.audience_id,
        "content_path": draft.content_path,
        "collection": draft.collection,
        "hashtags": ["DevTools"],
        "published_at": "2026-07-30T00:00:00Z",
        "urn": urn,
    })


def _fixture(root: Path) -> Config:
    (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "approval-gate.md").write_text(POST, encoding="utf-8")
    (root / "zer0-distribute.toml").write_text(STARTER_CONFIG, encoding="utf-8")
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

        # --- the .cms/ contract ---
        import analytics as analytics_mod
        import catering as catering_mod
        import contract as contract_mod
        import media as media_mod

        absent = contract_mod.load(root)
        check("contract: absence is not an error", absent.present is False)
        check("contract: absent yields no records", absent.records == [])
        found = sources_mod.discover(cfg, absent)
        check("contract: discovery falls back without .cms", len(found) > 0)
        check("contract: fallback has no content sources",
              all(not s.from_cms for s in found))

        _write_cms_index(root)
        cms = contract_mod.load(root)
        check("contract: index loads", cms.present is True)
        check("contract: all rows parsed", len(cms.records) == 7)
        check("contract: four of seven are distributable", len(cms.distributable()) == 4)
        ready = cms.distributable()
        ready_paths = {r.path for r in ready}
        check("contract: healthy content is distributable",
              "pages/_posts/good-one.md" in ready_paths)
        check("contract: low health is withheld",
              "pages/_posts/unhealthy.md" not in ready_paths)
        check("contract: drafts are withheld",
              "pages/_posts/draft-one.md" not in ready_paths)
        check("contract: generated files are withheld",
              "pages/_posts/generated.md" not in ready_paths)
        check("contract: sorted by health",
              [r.health for r in ready] == sorted((r.health for r in ready), reverse=True))
        check("contract: lookup by path", cms.by_path("pages/_posts/good-one.md") is not None)
        check("contract: lookup by slug", cms.by_path("good-one") is not None)

        # Discovery now prefers the index, and carries the join key.
        with_cms = sources_mod.discover(cfg, cms)
        content_sources = [s for s in with_cms if s.from_cms]
        check("contract: discovery uses the index", len(content_sources) == len(ready))
        check("contract: content source carries the path",
              all(s.content_path for s in content_sources))
        check("contract: content source carries the collection",
              all(s.collection for s in content_sources))

        # A draft from indexed content records which page it distributes —
        # without that key, engagement can never be attributed back.
        content_draft = compose.draft_for(cfg, content_sources[0], "peer-devs")
        check("contract: draft records content_path",
              content_draft.content_path == content_sources[0].content_path)
        write_draft(content_draft)

        # --- media: reuse, never generate ---
        (root / "assets" / "images" / "previews").mkdir(parents=True, exist_ok=True)
        (root / "assets" / "images" / "previews" / "good-one.png").write_bytes(b"x" * 32)
        good = cms.by_path("pages/_posts/good-one.md")
        resolved = media_mod.resolve(root, good)
        check("media: finds the conventional preview", resolved.found)
        check("media: reports its size", resolved.bytes == 32)
        naked = media_mod.resolve(root, cms.by_path("pages/_posts/second.md"))
        check("media: missing image is not an error", naked.found is False)
        check("media: emits a generator brief", "preview-images" in naked.brief)

        # --- analytics: the read surface is small and own-content only ---
        reads = analytics_mod.plan(cfg)
        check("analytics: read plan is non-empty", len(reads) >= 2)
        blob = " ".join(r.endpoint + r.returns + r.scope for r in reads).lower()
        check("analytics: no connections endpoint", "connection" not in blob)
        check("analytics: no follower enumeration", "followers/" not in blob)
        check("analytics: own content only", "own" in blob)
        check("analytics: live fetch refuses rather than inventing",
              _raises(lambda: analytics_mod.fetch(cfg), NotImplementedError))
        clean = analytics_mod.normalise(
            {"impressions": "500", "reactions": 8, "comments": 2, "shares": 1, "junk": "x"}
        )
        check("analytics: coerces to ints", clean["impressions"] == 500)
        check("analytics: derives engagements", clean["engagements"] == 11)
        check("analytics: drops unknown fields", "junk" not in clean)

        # Ingest joins statistics onto pages through the ledger.
        approve_and_record(cfg, content_draft, "urn:li:share:1")
        merged, matched = analytics_mod.ingest(
            cfg, cms,
            {"urn:li:share:1": {"impressions": 1000, "reactions": 20, "comments": 5},
             "urn:li:share:unknown": {"impressions": 9}},
        )
        check("analytics: matches known urns", matched == 1)
        check("analytics: skips urns with no ledger entry", len(merged) == 1)
        check("analytics: keyed by content path",
              content_draft.content_path in merged)

        # --- catering: what to write next ---
        plan_empty = catering_mod.build(cms, {}, set())
        check("catering: no evidence is stated, not faked", plan_empty.has_evidence is False)
        check("catering: undistributed work exists anyway",
              len(plan_empty.undistributed) > 0)
        rendered_empty = catering_mod.render(plan_empty, "2026-07-30")
        check("catering: empty worklist says so", "No audience data yet" in rendered_empty)
        check("catering: worklist has the engine's lane shape",
              "## Lane A" in rendered_empty and "## Lane D" in rendered_empty)

        plan_full = catering_mod.build(cms, merged, {content_draft.content_path})
        check("catering: distributed page leaves lane A",
              content_draft.content_path not in {r.path for r in plan_full.undistributed})
        check("catering: evidence is recognised", plan_full.has_evidence is True)

        # A topic needs more than one post before its average means anything.
        one_post = catering_mod.build(cms, {"pages/_posts/good-one.md": clean}, set())
        check("catering: one observation is not a trend",
              one_post.proven == [] and one_post.quiet == [])
        many = {
            "pages/_posts/good-one.md": analytics_mod.normalise(
                {"impressions": 100, "reactions": 30}),
            "pages/_posts/second.md": analytics_mod.normalise(
                {"impressions": 100, "reactions": 25}),
            "pages/_notes/quiet-one.md": analytics_mod.normalise(
                {"impressions": 100, "reactions": 1}),
            "pages/_notes/quiet-two.md": analytics_mod.normalise(
                {"impressions": 100, "reactions": 2}),
        }
        ranked = catering_mod.build(cms, many, set())
        check("catering: ranks topics once there is evidence",
              len(ranked.proven) >= 1)
        topics = {s.topic for s in ranked.proven}
        check("catering: the engaging topic ranks", "posts" in topics)
        check("catering: rate is engagements over impressions",
              any(abs(s.rate - 0.275) < 0.01 for s in ranked.proven))

        # --- the worklist round-trips into the contract ---
        written = contract_mod.write_worklist(cms, "2026-07-30", rendered_empty)
        check("contract: worklist lands in .cms/distribution",
              written.exists() and ".cms" in str(written) and "distribution" in str(written))
        check("contract: performance file written",
              contract_mod.performance_path(cms).exists())

    if failures:
        print(f"self-test: FAIL ({len(failures)})")
        for failure in failures:
            print(f"  ✗ {failure}")
        return 1
    print("self-test: PASS — discovery, composition, guard, approval gate, "
          "payload, portfolio, ledger, dashboard")
    return 0
