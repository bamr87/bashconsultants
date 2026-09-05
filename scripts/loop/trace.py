#!/usr/bin/env python3
"""The session trace — what an AI session touched, recorded without its transcript.

The content loop wants to know which work was done *with* an AI session, what
the session set out to do, and which files and commits it produced. Transcripts
are the wrong record for that: they live on one machine, they are enormous, and
they can contain secrets. So the trace is **derived metadata only**:

  session id · when it ended · the repo and branch · the first user prompt
  (scrubbed, one line, capped) as the session's intent · files touched ·
  commits that carry the session's trailer · a turn count

Two stores, on purpose (the same pattern lifehacker.dev uses for retrospectives):

  .claude/loop/sessions.jsonl   the LOCAL queue the SessionEnd hook appends to —
                                gitignored, so ending a session never dirties
                                the working tree;
  _data/loop/sessions.jsonl     the COMMITTED trace the loop reads in CI — filled
                                by `--sync`, which a human runs and commits, so a
                                person always sees what is about to be public.

Usage:
  python3 scripts/loop/trace.py append            # the hook: SessionEnd JSON on stdin; never fails
  python3 scripts/loop/trace.py --list            # local queue vs committed trace
  python3 scripts/loop/trace.py --sync            # fold the local queue into _data/loop/sessions.jsonl
  python3 scripts/loop/trace.py --add --session-id ID --intent "…" [--files a,b] [--reason manual]
  python3 scripts/loop/trace.py --self-test
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib  # noqa: E402

MAX_FILES = 20
MAX_COMMITS = 20
SESSION_TRAILER_RE = re.compile(r"^\s*Claude-Session:\s*(\S+)", re.I | re.M)


# --------------------------------------------------------------------------- #
# Reading the transcript for ONE thing: the intent
# --------------------------------------------------------------------------- #

def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def intent_from_transcript(path: str | Path, limit: int = 240) -> tuple[str, int]:
    """(first real user prompt, one line, scrubbed; number of turns). Best-effort."""
    p = Path(path) if path else None
    if not p or not p.exists():
        return "", 0
    intent = ""
    turns = 0
    try:
        with p.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                kind = rec.get("type")
                if kind not in ("user", "assistant"):
                    continue
                turns += 1
                if intent or kind != "user":
                    continue
                msg = rec.get("message") or {}
                text = _text_of(msg.get("content") if isinstance(msg, dict) else rec.get("content"))
                text = re.sub(r"<[^>]{1,60}>.*?</[^>]{1,60}>", " ", text, flags=re.S)  # drop xml-ish wrappers
                text = text.strip()
                if not text or text.startswith(("<", "/")) or "tool_result" in text[:40]:
                    continue
                intent = _lib.one_line(_lib.scrub(text), limit=limit)
    except OSError:
        return "", 0
    return intent, turns


# --------------------------------------------------------------------------- #
# Deriving the record from git
# --------------------------------------------------------------------------- #

def session_commits(sid: str, cwd: Path, hours: int = 72) -> list[dict]:
    """Recent commits whose body carries this session's trailer."""
    if not sid:
        return []
    raw = _lib.git("log", f"--since={hours} hours ago", "--format=%x1e%H%x1f%s%x1f%b", cwd=cwd)
    out = []
    for chunk in raw.split("\x1e"):
        if not chunk.strip():
            continue
        parts = chunk.split("\x1f")
        if len(parts) < 3:
            continue
        sha, subject, body = parts[0].strip(), parts[1].strip(), parts[2]
        m = SESSION_TRAILER_RE.search(body)
        if m and m.group(1).rstrip("/").endswith(sid):
            out.append({"sha": sha[:7], "subject": _lib.one_line(_lib.scrub(subject), 140)})
    return out[:MAX_COMMITS]


def touched_files(cwd: Path, shas: list[str]) -> list[str]:
    files: list[str] = []
    for line in _lib.git("status", "--porcelain", cwd=cwd).splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path and path not in files:
            files.append(path)
    for sha in shas:
        for path in _lib.git("show", "--name-only", "--format=", sha, cwd=cwd).splitlines():
            path = path.strip()
            if path and path not in files:
                files.append(path)
    return files[:MAX_FILES]


def build_record(payload: dict, *, cwd: Path | None = None, now: _dt.datetime | None = None) -> dict | None:
    sid = payload.get("session_id", "")
    sid = str(sid).strip()
    sid = sid[len("session_"):] if sid.startswith("session_") else sid
    if not sid:
        return None
    root = cwd or Path(str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or _lib.ROOT))
    intent, turns = intent_from_transcript(payload.get("transcript_path", ""))
    if payload.get("intent"):
        intent = _lib.one_line(_lib.scrub(str(payload["intent"])), 240)
    commits = session_commits(sid, root)
    files = [str(f) for f in (payload.get("files") or [])] or touched_files(root, [c["sha"] for c in commits])
    stamp = (now or _dt.datetime.now(_dt.timezone.utc)).replace(microsecond=0)
    return {
        "session_id": sid,
        "ended_at": stamp.isoformat().replace("+00:00", "Z"),
        "reason": str(payload.get("reason") or ""),
        "repo": _lib.repo_slug() if root == _lib.ROOT else (payload.get("repo") or root.name),
        "branch": _lib.git("rev-parse", "--abbrev-ref", "HEAD", cwd=root).strip(),
        "head": _lib.git("rev-parse", "--short=7", "HEAD", cwd=root).strip(),
        "intent": intent,
        "files": [_lib.scrub(f) for f in files][:MAX_FILES],
        "commits": commits,
        "turns": turns,
    }


# --------------------------------------------------------------------------- #
# The two stores
# --------------------------------------------------------------------------- #

def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict) and rec.get("session_id"):
            out.append(rec)
    return out


def append_local(rec: dict, queue: Path = _lib.LOCAL_QUEUE) -> bool:
    """Append once per session id (the hook can fire more than once)."""
    queue.parent.mkdir(parents=True, exist_ok=True)
    if any(r.get("session_id") == rec["session_id"] for r in read_jsonl(queue)):
        return False
    with queue.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return True


def sync(queue: Path = _lib.LOCAL_QUEUE, committed: Path = _lib.SESSIONS_PATH) -> tuple[int, int]:
    """Fold the local queue into the committed trace. Returns (added, total)."""
    existing = read_jsonl(committed)
    by_id = {r["session_id"]: r for r in existing}
    added = 0
    for rec in read_jsonl(queue):
        if rec["session_id"] in by_id:
            continue
        clean = json.loads(_lib.scrub(json.dumps(rec, ensure_ascii=False)))
        by_id[rec["session_id"]] = clean
        added += 1
    rows = sorted(by_id.values(), key=lambda r: (str(r.get("ended_at", "")), r["session_id"]))
    committed.parent.mkdir(parents=True, exist_ok=True)
    committed.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return added, len(rows)


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #

def self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        transcript = root / "t.jsonl"
        transcript.write_text(
            json.dumps({"type": "system", "message": "boot"}) + "\n"
            + json.dumps({"type": "user", "message": {"role": "user", "content": "<system-reminder>ignore me</system-reminder>"}}) + "\n"
            + json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "x"}]}}) + "\n"
            + json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "build an AI loop\nwith token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234 please " + "x" * 300}]}}) + "\n"
            + json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "ok"}]}}) + "\n"
            + "garbage\n")
        intent, turns = intent_from_transcript(transcript)
        check("intent picks first real prompt", intent.startswith("build an AI loop with token gh*_*** please"), True)
        check("intent capped", len(intent) <= 240, True)
        check("turns", turns, 4)
        check("missing transcript", intent_from_transcript(root / "nope.jsonl"), ("", 0))

        queue = root / "q.jsonl"
        committed = root / "c.jsonl"
        rec = {"session_id": "01A", "ended_at": "2026-09-05T10:00:00Z", "intent": "one", "files": ["a.md"], "commits": [], "reason": "x"}
        check("append", append_local(rec, queue), True)
        check("append dedup", append_local(rec, queue), False)
        append_local({"session_id": "01B", "ended_at": "2026-09-04T10:00:00Z", "intent": "sk-ant-api03-abcdefghijklmnop leaked", "files": []}, queue)
        added, total = sync(queue, committed)
        check("sync added", (added, total), (2, 2))
        rows = read_jsonl(committed)
        check("sync sorted by time", [r["session_id"] for r in rows], ["01B", "01A"])
        check("sync scrubs", "abcdefghijklmnop" in rows[0]["intent"], False)
        check("sync idempotent", sync(queue, committed), (0, 2))
        check("bad payload", build_record({"session_id": ""}), None)
        r = build_record({"session_id": "session_01ZZ", "cwd": str(root), "reason": "test", "intent": "manual intent",
                          "files": ["x.md"]}, cwd=root, now=_dt.datetime(2026, 9, 5, 12, 0, tzinfo=_dt.timezone.utc))
        check("record id stripped", r["session_id"], "01ZZ")
        check("record stamp", r["ended_at"], "2026-09-05T12:00:00Z")
        check("record manual intent", r["intent"], "manual intent")
        check("record files", r["files"], ["x.md"])

    if failures:
        print("trace --self-test: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("trace --self-test: PASS (intent extraction + scrubbing, local queue dedup, sync, record shape)")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description="Record what an AI session touched (metadata only).")
    ap.add_argument("command", nargs="?", choices=["append"], help="append: the SessionEnd hook entry point (JSON on stdin)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--sync", action="store_true")
    ap.add_argument("--add", action="store_true", help="add a manual entry to the local queue")
    ap.add_argument("--session-id")
    ap.add_argument("--intent", default="")
    ap.add_argument("--files", default="", help="comma-separated paths (default: derive from git)")
    ap.add_argument("--reason", default="manual")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    if args.command == "append":
        # The hook path: swallow every error, always exit 0 — a trace must never
        # get in the way of ending a session.
        try:
            raw = sys.stdin.read()
            payload = json.loads(raw) if raw.strip() else {}
            rec = build_record(payload)
            if rec:
                append_local(rec)
        except Exception as exc:  # noqa: BLE001 — deliberately broad, see above
            print(f"[trace] skipped: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 0

    if args.add:
        if not args.session_id:
            ap.error("--add needs --session-id")
        rec = build_record({"session_id": args.session_id, "intent": args.intent, "reason": args.reason,
                            "files": [f for f in args.files.split(",") if f.strip()]})
        if rec is None:
            print("trace: nothing to add", file=sys.stderr)
            return 1
        print(("added " if append_local(rec) else "already queued ") + rec["session_id"])
        return 0

    if args.sync:
        added, total = sync()
        print(f"trace: {added} new session(s) folded into {_lib.SESSIONS_PATH.relative_to(_lib.ROOT)} ({total} total). Review the diff, then commit it.")
        return 0

    local = read_jsonl(_lib.LOCAL_QUEUE)
    committed = {r["session_id"] for r in read_jsonl(_lib.SESSIONS_PATH)}
    print(f"trace: {len(local)} local session(s) in {_lib.LOCAL_QUEUE.relative_to(_lib.ROOT)}, {len(committed)} committed")
    for r in local:
        mark = "synced " if r["session_id"] in committed else "pending"
        print(f"  {mark}  {r['session_id'][:16]:16}  {str(r.get('ended_at', ''))[:10]}  {_lib.one_line(r.get('intent', ''), 70)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
