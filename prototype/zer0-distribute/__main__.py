"""zer0-distribute — the distribution lane of zer0-CMS.

    python3 prototype/zer0-distribute <command> [options]

The CMS engine indexes and scores content. The authoring surface edits it. The
theme renders it. This lane carries it off the site — to LinkedIn today — and
brings the audience's response back into `.cms/` so the next thing written is
chosen on evidence instead of instinct.

The loop, end to end:

    write ──▶ publish ──▶ engage ──▶ cater ──▶ write
      │          │           │         │
   authoring  this lane   this lane  catering worklist
   (zer0-CMS)                        (.cms/distribution/worklists/)

Standard library only, so there is nothing to install.

The gate that matters: a draft is created `pending`, a person moves it to
`approved`, and only then will `publish` send it. There is no scheduler and no
unattended path — see `approve` and `cmd_publish` below.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import analytics as analytics_mod                         # noqa: E402
import catering as catering_mod                           # noqa: E402
import compose                                            # noqa: E402
import contract as contract_mod                           # noqa: E402
import media as media_mod                                 # noqa: E402
import payload as payload_mod                             # noqa: E402
import portfolio as portfolio_mod                         # noqa: E402
import sources as sources_mod                             # noqa: E402
from core import (                                        # noqa: E402
    CONFIG_NAME,
    STARTER_CONFIG,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_PUBLISHED,
    Config,
    append_ledger,
    already_published,
    find_draft,
    load_config,
    load_ledger,
    load_queue,
    write_draft,
)

BULLET = "  •"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hashtags(body: str) -> list[str]:
    return [w.lstrip("#") for w in body.split() if w.startswith("#")]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init(cfg: Config, args) -> int:
    path = cfg.root / CONFIG_NAME
    if path.exists() and not args.force:
        print(f"{CONFIG_NAME} already exists — pass --force to overwrite")
        return 1
    path.write_text(STARTER_CONFIG, encoding="utf-8")
    cfg.queue_dir.mkdir(parents=True, exist_ok=True)
    print(f"wrote {CONFIG_NAME}")
    print(f"created {cfg.queue_dir.relative_to(cfg.root)}/")
    print("\nNext: edit the author URN and audience profiles, then run `sources`.")
    return 0


def cmd_sources(cfg: Config, args) -> int:
    contract = contract_mod.load(cfg.root)
    found = sources_mod.discover(cfg, contract)
    if not found:
        print("no publishable sources found — check [sources] in zer0-distribute.toml")
        return 0
    if contract.present:
        print(f"CMS index: {len(contract.records)} file(s), "
              f"{len(contract.distributable())} distributable "
              f"(indexed {contract.generated_at or 'unknown'})")
    else:
        print("no .cms/ contract — falling back to git and the filesystem")
    print(f"\n{len(found)} publishable source(s) in {cfg.root.name}:\n")
    for source in found:
        print(f"  {source.id}")
        badge = f"health {source.health} · {source.freshness}" if source.from_cms else source.kind
        print(f"    {badge}")
        print(f"    {source.title}")
        if source.short:
            print(f"    {source.short}")
        print()
    print("Compose one:  draft <source-id> --audience <audience-id>")
    return 0


def cmd_cms(cfg: Config, args) -> int:
    """What the contract says, and what this lane adds to it."""
    contract = contract_mod.load(cfg.root)
    if not contract.present:
        print(f"no .cms/ contract at {contract.cms_dir}")
        print("\nThis lane works without one — `sources` falls back to git and the")
        print("filesystem. With one, publishable content comes from the same index")
        print("the authoring surface reads. Build it with: cms.py index")
        return 0
    summary = contract.summary
    print(f".cms/ contract  (indexed {contract.generated_at or 'unknown'})")
    print(f"  files           {len(contract.records)}")
    print(f"  distributable   {len(contract.distributable())} "
          f"(health >= {contract_mod.PUBLISHABLE_HEALTH}, not draft/generated/structural)")
    if summary.get("avg_health") is not None:
        print(f"  avg health      {summary['avg_health']}")
    by_collection = {}
    for record in contract.distributable():
        by_collection[record.collection] = by_collection.get(record.collection, 0) + 1
    if by_collection:
        pairs = ", ".join(f"{k} {v}" for k, v in sorted(by_collection.items(), key=lambda kv: -kv[1]))
        print(f"  by collection   {pairs}")
    perf = contract_mod.load_performance(contract)
    print(f"\n  distribution lane -> {contract.distribution_dir}")
    print(f"  performance     {len(perf)} page(s) with audience data")
    published = {d.content_path for d in load_queue(cfg) if d.content_path}
    print(f"  distributed     {len(published)} page(s) drafted or published")
    return 0


def cmd_media(cfg: Config, args) -> int:
    """Which image a page would share with — reused from the site, not made here."""
    contract = contract_mod.load(cfg.root)
    records = contract.distributable()
    if args.content:
        record = contract.by_path(args.content)
        records = [record] if record else []
        if not records:
            print(f"no indexed content matches '{args.content}'")
            return 1
    if not records:
        print("no distributable content to check")
        return 0
    missing = 0
    for record in records[:20]:
        found = media_mod.resolve(cfg.root, record)
        mark = "ok  " if found.found else "MISS"
        print(f"  [{mark}] {record.path}")
        print(f"          {found.describe()}")
        if not found.found:
            missing += 1
    if missing:
        print(f"\n{missing} page(s) have no preview image. zer0-image-generator makes them;")
        print("this lane only reuses what it produced.")
    return 0


def cmd_analytics(cfg: Config, args) -> int:
    """Show the read surface, or ingest statistics from a file."""
    contract = contract_mod.load(cfg.root)
    if not args.ingest:
        print(analytics_mod.describe_plan(cfg))
        perf = contract_mod.load_performance(contract)
        print(f"\nStored: {len(perf)} page(s) with audience data"
              f" ({contract_mod.performance_path(contract)})")
        if not perf:
            print("Ingest some: analytics --ingest <file.json>   (keyed by post URN)")
        return 0

    path = Path(args.ingest)
    if not path.exists():
        print(f"no such file: {path}")
        return 1
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        print(f"could not parse {path}: {err}")
        return 1
    stats = raw.get("posts", raw) if isinstance(raw, dict) else {}
    if not isinstance(stats, dict):
        print("expected an object keyed by post URN")
        return 1
    merged, matched = analytics_mod.ingest(cfg, contract, stats)
    print(f"ingested {matched} of {len(stats)} post(s) -> "
          f"{contract_mod.performance_path(contract)}")
    if matched < len(stats):
        print("Unmatched URNs have no ledger entry, so there is no page to attribute them to.")
    print(f"{len(merged)} page(s) now carry audience data. Next: cater")
    return 0


def cmd_cater(cfg: Config, args) -> int:
    """What to write next, from how the audience responded."""
    contract = contract_mod.load(cfg.root)
    performance = contract_mod.load_performance(contract)
    published = {
        str(e.get("content_path") or "")
        for e in load_ledger(cfg)
        if e.get("content_path")
    }
    plan = catering_mod.build(contract, performance, published)
    date = args.date or _now()[:10]
    body = catering_mod.render(plan, date)

    if args.print:
        print(body)
        return 0
    if not contract.present:
        print("no .cms/ contract — nothing to write a worklist into.")
        print("Run with --print to see it anyway.")
        return 1
    path = contract_mod.write_worklist(contract, date, body)
    print(f"wrote {path}")
    print(f"  Lane A  {len(plan.undistributed)} strong page(s) never distributed")
    if plan.has_evidence:
        print(f"  Lane B  {len(plan.proven)} topic(s) at or above median engagement")
        print(f"  Lane C  {len(plan.quiet)} topic(s) below it")
        print(f"  Lane D  {len(plan.refresh)} page(s) that worked and went stale")
    else:
        print("  Lanes B-D  no audience data yet — rankings left empty, not guessed")
    return 0


def cmd_audience(cfg: Config, args) -> int:
    if not cfg.audiences:
        print("no audience profiles declared — add [[audience]] blocks to zer0-distribute.toml")
        return 0
    print(f"{len(cfg.audiences)} declared audience profile(s):\n")
    for aud in cfg.audiences:
        print(f"  {aud.id}")
        print(f"    who:      {aud.label}")
        if aud.reads_for:
            print(f"    wants:    {aud.reads_for}")
        if aud.tone:
            print(f"    tone:     {aud.tone}")
        if aud.hashtags:
            print(f"    hashtags: {' '.join('#' + t for t in aud.hashtags)}")
        print()
    print("Declared by you in config. zer0-distribute never reads your connections to guess.")
    return 0


def cmd_draft(cfg: Config, args) -> int:
    source = sources_mod.find(cfg, args.source)
    if source is None:
        print(f"no source matches '{args.source}' — run `sources` to list them")
        return 1
    if args.audience and cfg.audience(args.audience) is None:
        print(f"unknown audience '{args.audience}' — run `audience` to list them")
        return 1
    draft = compose.draft_for(cfg, source, args.audience or "")
    write_draft(draft)
    rel = draft.path.relative_to(cfg.root)
    print(f"drafted {rel}  (status: {STATUS_PENDING})\n")
    print(draft.body)
    warnings = compose.check(draft.body)
    if warnings:
        print("\nflagged for your review:")
        for warning in warnings:
            print(f"{BULLET} {warning}")
    print(f"\nNothing is sent. Review it, then: approve {draft.id}")
    return 0


def cmd_queue(cfg: Config, args) -> int:
    drafts = load_queue(cfg)
    if not drafts:
        print("queue is empty — run `sources` then `draft <source-id>`")
        return 0
    print(f"{len(drafts)} draft(s) in the queue:\n")
    for draft in drafts:
        marker = {
            STATUS_PENDING: "waiting on you",
            STATUS_APPROVED: "approved, ready to publish",
            STATUS_PUBLISHED: "published",
        }.get(draft.status, draft.status)
        print(f"  [{draft.status:<9}] {draft.id}")
        print(f"              {draft.title}  — {marker}")
    pending = sum(1 for d in drafts if d.status == STATUS_PENDING)
    if pending:
        print(f"\n{pending} draft(s) need a human. Nothing publishes until they get one.")
    return 0


def cmd_preview(cfg: Config, args) -> int:
    drafts = load_queue(cfg)
    if args.draft:
        found = find_draft(cfg, args.draft)
        drafts = [found] if found else []
        if not drafts:
            print(f"no draft matches '{args.draft}'")
            return 1
    if not drafts:
        print("queue is empty — nothing to preview")
        return 0
    for draft in drafts:
        body = payload_mod.build(cfg, draft)
        print(f"--- {draft.id} ({draft.status}) ---")
        print(payload_mod.describe(cfg, draft))
        print(json.dumps(body, indent=2, ensure_ascii=False))
        print("no request was made: preview is offline\n")
    return 0


def cmd_approve(cfg: Config, args) -> int:
    """The gate. A person runs this, or clicks the button that calls it."""
    draft = find_draft(cfg, args.draft)
    if draft is None:
        print(f"no draft matches '{args.draft}'")
        return 1
    if draft.status == STATUS_PUBLISHED:
        print(f"{draft.id} is already published")
        return 0
    draft.meta["status"] = STATUS_APPROVED
    draft.meta["approved_at"] = _now()
    write_draft(draft)
    print(f"approved {draft.id} — `publish` will send it")
    return 0


def cmd_publish(cfg: Config, args) -> int:
    drafts = [d for d in load_queue(cfg) if d.status == STATUS_APPROVED]
    if not drafts:
        pending = [d for d in load_queue(cfg) if d.status == STATUS_PENDING]
        if pending:
            print(f"nothing approved. {len(pending)} draft(s) are pending — approve one first.")
        else:
            print("nothing approved to publish")
        return 0

    for draft in drafts:
        source_id = str(draft.meta.get("source", draft.id))
        if already_published(cfg, source_id) and not args.force:
            print(f"skip {draft.id}: {source_id} is already in the ledger")
            continue
        body = payload_mod.build(cfg, draft)
        print(f"--- {draft.id} ---")
        print(payload_mod.describe(cfg, draft))
        if args.dry_run:
            print(json.dumps(body, indent=2, ensure_ascii=False))
            print("dry-run: no request made, ledger untouched\n")
            continue
        # The live call goes here. It is deliberately not implemented in the
        # prototype: the app has not been granted Community Management API
        # access yet, and a stub that pretends to succeed would make the tool
        # lie to its user. Until the grant lands, publish is dry-run only.
        print("publish is stubbed pending LinkedIn API access — re-run with --dry-run")
        return 2
    return 0


def cmd_record(cfg: Config, args) -> int:
    """Record an already-published post in the ledger.

    Separate from `publish` so the portfolio view can be demonstrated, and
    populated, before the live API call exists.
    """
    draft = find_draft(cfg, args.draft)
    if draft is None:
        print(f"no draft matches '{args.draft}'")
        return 1
    entry = {
        "draft": draft.id,
        "source": str(draft.meta.get("source", draft.id)),
        "kind": str(draft.meta.get("kind", "")),
        "audience": draft.audience_id,
        "title": draft.title,
        "hashtags": _hashtags(draft.body),
        "published_at": args.at or _now(),
        "urn": args.urn or "",
        # Carried so analytics can join engagement back onto the page.
        "content_path": draft.content_path,
        "collection": draft.collection,
    }
    append_ledger(cfg, entry)
    draft.meta["status"] = STATUS_PUBLISHED
    write_draft(draft)
    print(f"recorded {draft.id} in the ledger")
    return 0


def cmd_portfolio(cfg: Config, args) -> int:
    print(portfolio_mod.render(portfolio_mod.build(cfg)))
    return 0


def cmd_serve(cfg: Config, args) -> int:
    import server
    return server.serve(cfg, host=args.host, port=args.port, open_once=args.once)


def cmd_self_test(cfg: Config, args) -> int:
    import selftest
    return selftest.run()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zer0-distribute",
        description="The distribution lane of zer0-CMS: publish, engage, cater.",
    )
    parser.add_argument("--root", default=".", help="repository root (default: cwd)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="write a starter zer0-distribute.toml")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    sub.add_parser("sources", help="discover publishable material").set_defaults(func=cmd_sources)
    sub.add_parser("audience", help="list declared audience profiles").set_defaults(func=cmd_audience)

    p = sub.add_parser("draft", help="compose a draft for one source")
    p.add_argument("source")
    p.add_argument("--audience", default="")
    p.set_defaults(func=cmd_draft)

    sub.add_parser("queue", help="list drafts and their status").set_defaults(func=cmd_queue)

    p = sub.add_parser("preview", help="render the exact API payload, offline")
    p.add_argument("draft", nargs="?", default="")
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("approve", help="mark a draft approved")
    p.add_argument("draft")
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("publish", help="publish approved drafts")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("record", help="record a published post in the ledger")
    p.add_argument("draft")
    p.add_argument("--urn", default="")
    p.add_argument("--at", default="")
    p.set_defaults(func=cmd_record)

    sub.add_parser("portfolio", help="your published track record").set_defaults(func=cmd_portfolio)

    sub.add_parser("cms", help="what the .cms/ contract says").set_defaults(func=cmd_cms)

    p = sub.add_parser("media", help="which preview image each page would share with")
    p.add_argument("content", nargs="?", default="")
    p.set_defaults(func=cmd_media)

    p = sub.add_parser("analytics", help="the read surface, or ingest statistics")
    p.add_argument("--ingest", default="", help="JSON keyed by post URN")
    p.set_defaults(func=cmd_analytics)

    p = sub.add_parser("cater", help="what to write next, from audience response")
    p.add_argument("--print", action="store_true", help="print instead of writing")
    p.add_argument("--date", default="", help="worklist date (default: today)")
    p.set_defaults(func=cmd_cater)

    p = sub.add_parser("serve", help="local review dashboard")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--once", action="store_true", help="serve one request and exit")
    p.set_defaults(func=cmd_serve)

    sub.add_parser("self-test", help="offline assertions").set_defaults(func=cmd_self_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config(Path(args.root).resolve())
    return args.func(cfg, args)


if __name__ == "__main__":
    raise SystemExit(main())
