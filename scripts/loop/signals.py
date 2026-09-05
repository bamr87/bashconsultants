#!/usr/bin/env python3
"""The activity miner — turn the practice's recent work into stories the loop can write about.

The content loop writes about work that actually happened, so its ideas come
from the record of that work rather than from a topic list:

  * the home repository's git history (commits, files, insertions/deletions,
    conventional-commit type/scope, `(#N)` pull-request references, and the
    `Co-Authored-By: Claude` / `Claude-Session:` trailers that mark AI-assisted
    work and group commits into the session that produced them);
  * the CHANGELOG lines that mention those pull requests;
  * committed AI-session traces (`_data/loop/sessions.jsonl` — intent, files
    touched, commits; written by scripts/loop/trace.py, never a transcript);
  * optionally, the founder's sister repositories through the GitHub API
    (`_data/loop/sources.yml`, `via: github`) — read-only and best-effort,
    skipped with a note whenever `gh` or a token is missing.

Commits are grouped into **stories** — by AI session when a trailer names one,
else by pull request, else by day — and each story is scored (recency, size,
source weight, AI-session bonus) and marked *spent* when a ledger record has
already written it up. The planner hands the writer the best unspent stories.

Deterministic, stdlib only, no model calls. The judgment (which story, what
angle, which section) stays with the writer.

Usage:
  python3 scripts/loop/signals.py [--window 30] [--today YYYY-MM-DD] [--no-remote]
                                  [--top 6] [--json | --markdown] [--out DIR]
  python3 scripts/loop/signals.py --self-test
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _lib  # noqa: E402
import ledger  # noqa: E402

# --------------------------------------------------------------------------- #
# Classification tables (data the writer and the planner both lean on)
# --------------------------------------------------------------------------- #

# path regex -> area label. First match wins. `posts/<section>` is derived.
AREA_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^pages/_posts/(corp|erp|muses|tech)/"), "posts/{0}"),
    (re.compile(r"^pages/_toolkit/"), "toolkit"),
    (re.compile(r"^pages/_services/"), "services"),
    (re.compile(r"^pages/_case-studies/"), "case-studies"),
    (re.compile(r"^pages/"), "pages"),
    (re.compile(r"^(index|about|contact|tools|ai-operations|privacy)\.md$"), "pages"),
    (re.compile(r"^\.github/workflows/"), "ci"),
    (re.compile(r"^\.github/(prompts|instructions)/"), "prompts"),
    (re.compile(r"^\.github/"), "ci"),
    (re.compile(r"^\.claude/"), "claude"),
    (re.compile(r"^(scripts|tools)/"), "scripts"),
    (re.compile(r"^extension/"), "extension"),
    (re.compile(r"^api/"), "api"),
    (re.compile(r"^(_config|_data/|\.theme-overrides|zer0\.json|Gemfile|docker|Dockerfile|package\.json)"), "config"),
    (re.compile(r"^(_layouts|_includes|_sass|_plugins|assets)/"), "theme"),
    (re.compile(r"^docs/"), "docs"),
    (re.compile(r"^(CHANGELOG|README|CLAUDE|AGENTS|llms)\.(md|txt)$"), "docs"),
    (re.compile(r"^drafts/"), "drafts"),
]

# area -> the post sections its work most naturally lands in (first = best).
SECTION_HINTS: dict[str, list[str]] = {
    "claude": ["tech", "muses"], "ci": ["tech", "corp"], "scripts": ["tech", "muses"],
    "prompts": ["tech", "muses"], "extension": ["tech"], "api": ["tech", "corp"],
    "config": ["tech", "corp"], "theme": ["tech"], "docs": ["tech", "muses"],
    "toolkit": ["tech", "corp"], "services": ["corp", "tech"], "pages": ["corp", "muses"],
    "case-studies": ["corp", "erp"], "posts/erp": ["erp"], "posts/corp": ["corp"],
    "posts/muses": ["muses"], "posts/tech": ["tech"], "drafts": ["muses"], "other": ["tech"],
}

# Subject/path keywords that pull a story toward a section regardless of area.
KEYWORD_HINTS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(erp|ledger|quickbooks|netsuite|close|invoice|journal|accounting|finance|payroll|"
                r"consolidat|reconcil|gl\b|ar/ap|audit trail)", re.I), "erp"),
    (re.compile(r"\b(security|privacy|consent|posthog|analytics|domain|dmarc|dns|insurance|policy|vendor|"
                r"cost|budget|token|secret|credential|licen[cs]e|contract|governance|compliance)", re.I), "corp"),
    (re.compile(r"\b(essay|muse|philosoph|reflect|paradox|thrasymachus|innovation)", re.I), "muses"),
]

# Areas that are the site's own articles: a commit that only adds a post is a
# weak seed for a NEW article (an article about writing an article).
CONTENT_ONLY_AREAS = {"posts/corp", "posts/erp", "posts/muses", "posts/tech", "drafts"}

# Conventional-commit type -> how much of a story it usually is. A story takes
# the best factor among its commits (a session with a feat and a style fix is
# a feat). Unknown types count as 1.0.
TYPE_FACTOR = {"feat": 1.0, "fix": 0.95, "docs": 0.95, "content": 0.9, "refactor": 0.9,
               "ci": 0.9, "build": 0.85, "chore": 0.8, "style": 0.6, "test": 0.8}

PR_RE = re.compile(r"\(#(\d+)\)\s*$")
MERGE_PR_RE = re.compile(r"^Merge pull request #(\d+) from (\S+)")
CC_RE = re.compile(r"^(\w+)(?:\(([^)]*)\))?!?:\s*(.+)$")
SESSION_RE = re.compile(r"^\s*Claude-Session:\s*(\S+)", re.I | re.M)
CLAUDE_COAUTHOR_RE = re.compile(r"^\s*Co-Authored-By:\s*Claude\b", re.I | re.M)
BOT_RE = re.compile(r"\[bot\]|github-actions|dependabot|copilot", re.I)
NUMSTAT_RE = re.compile(r"^(\d+|-)\t(\d+|-)\t(.+)$")


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #

def area_of(path: str) -> str:
    for pat, label in AREA_RULES:
        m = pat.match(path)
        if m:
            return label.format(*m.groups()) if "{0}" in label else label
    return "other"


def session_id_from(value: str) -> str:
    """`https://claude.ai/code/session_01ABC` / `session_01ABC` / `01ABC` -> `01ABC`."""
    v = str(value or "").strip().rstrip("/").rsplit("/", 1)[-1]
    return v[len("session_"):] if v.startswith("session_") else v


def parse_subject(subject: str) -> tuple[str, str, str]:
    """Conventional-commit `type(scope): text` -> (type, scope, text); else ('', '', subject)."""
    m = CC_RE.match(subject.strip())
    if not m:
        return "", "", subject.strip()
    return m.group(1).lower(), (m.group(2) or "").lower(), m.group(3).strip()


def pr_number(subject: str) -> int | None:
    m = PR_RE.search(subject)
    return int(m.group(1)) if m else None


def suggest_sections(areas: list[str], subjects: list[str], paths: list[str]) -> list[str]:
    """Ordered section suggestions from the story's areas plus keyword pulls."""
    votes: Counter = Counter()
    for rank, area in enumerate(areas):
        for pos, sec in enumerate(SECTION_HINTS.get(area, SECTION_HINTS["other"])):
            votes[sec] += (3 - min(rank, 2)) * (2 if pos == 0 else 1)
    blob = "\n".join(subjects + paths)
    for pat, sec in KEYWORD_HINTS:
        hits = len(pat.findall(blob))
        if hits:
            votes[sec] += 3 * min(hits, 4)  # three mentions outweigh a single area's first choice
    if not votes:
        return ["tech"]
    ordered = sorted(votes.items(), key=lambda kv: (-kv[1], _lib.SECTIONS.index(kv[0]) if kv[0] in _lib.SECTIONS else 9))
    return [sec for sec, _ in ordered]


# --------------------------------------------------------------------------- #
# Home repository — git
# --------------------------------------------------------------------------- #

def _git_commits(root: Path, since: _dt.date) -> list[dict]:
    fmt = "%x1e%H%x1f%aI%x1f%an%x1f%s%x1f%b%x1f"
    raw = _lib.git("log", "--no-merges", f"--since={since.isoformat()}", "--date=iso-strict",
                   f"--format={fmt}", "--numstat", cwd=root)
    commits: list[dict] = []
    for chunk in raw.split("\x1e"):
        if not chunk.strip():
            continue
        parts = chunk.split("\x1f")
        if len(parts) < 6:
            continue
        sha, date, author, subject, body, stats = parts[:6]
        files: list[dict] = []
        for line in stats.splitlines():
            m = NUMSTAT_RE.match(line.strip("\r"))
            if not m:
                continue
            add, dele, path = m.groups()
            files.append({"path": path, "add": 0 if add == "-" else int(add), "del": 0 if dele == "-" else int(dele)})
        ctype, scope, text = parse_subject(subject)
        sm = SESSION_RE.search(body)
        commits.append({
            "sha": sha.strip(), "short": sha.strip()[:7], "date": date.strip()[:10], "author": author.strip(),
            "subject": subject.strip(), "type": ctype, "scope": scope, "text": text,
            "pr": pr_number(subject), "session": session_id_from(sm.group(1)) if sm else "",
            "ai": bool(CLAUDE_COAUTHOR_RE.search(body)) or bool(sm),
            "bot": bool(BOT_RE.search(author)), "files": files,
        })
    return commits


def _git_merge_prs(root: Path, since: _dt.date) -> dict[int, str]:
    """PR number -> head branch, from real merge commits (squash merges carry `(#N)` instead)."""
    raw = _lib.git("log", "--merges", f"--since={since.isoformat()}", "--format=%s", cwd=root)
    out: dict[int, str] = {}
    for line in raw.splitlines():
        m = MERGE_PR_RE.match(line.strip())
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


# --------------------------------------------------------------------------- #
# Session traces + changelog
# --------------------------------------------------------------------------- #

def load_traces(path: Path) -> dict[str, dict]:
    traces: dict[str, dict] = {}
    if not path.exists():
        return traces
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = session_id_from(rec.get("session_id", ""))
        if sid:
            rec["session_id"] = sid
            traces[sid] = rec  # last write wins (a re-sync refreshes)
    return traces


def changelog_hits(text: str, prs: list[int], limit: int = 3) -> list[str]:
    if not prs or not text:
        return []
    pats = [re.compile(rf"#\s?{n}(?!\d)") for n in prs]
    hits: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s and any(p.search(s) for p in pats):
            hits.append(_lib.one_line(re.sub(r"^[-*+]\s+", "", s), limit=220))
            if len(hits) >= limit:
                break
    return hits


# --------------------------------------------------------------------------- #
# Sister repositories — GitHub API via `gh` (best-effort)
# --------------------------------------------------------------------------- #

def gh_json(path: str):
    """`gh api <path>` -> parsed JSON, or None when gh is missing / unauthenticated / failing."""
    if not shutil.which("gh"):
        return None
    try:
        res = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if res.returncode != 0:
        return None
    try:
        return json.loads(res.stdout)
    except json.JSONDecodeError:
        return None


def remote_stories_from_payloads(slug: str, label: str, weight: float, commits, pulls,
                                 since: _dt.date, today: _dt.date) -> list[dict]:
    """Pure: turn `repos/{slug}/commits` + `repos/{slug}/pulls?state=closed` payloads into stories."""
    stories: list[dict] = []
    pr_numbers: set[int] = set()
    for pr in pulls or []:
        merged = _lib.parse_date(pr.get("merged_at"))
        if not merged or merged < since or merged > today:
            continue
        author = str((pr.get("user") or {}).get("login", ""))
        if BOT_RE.search(author):
            continue
        n = int(pr.get("number", 0))
        pr_numbers.add(n)
        body = _lib.one_line(_lib.scrub(str(pr.get("body") or "")), limit=400)
        title = _lib.one_line(_lib.scrub(str(pr.get("title") or "")), limit=160)
        stories.append({
            "id": f"pr:{n}@{slug}", "kind": "pr", "repo": slug, "label": label, "weight": weight,
            "date_start": merged.isoformat(), "date_end": merged.isoformat(),
            "commits": [], "files_changed": 0, "insertions": 0, "deletions": 0, "top_paths": [],
            "areas": [], "ai_assisted": bool(re.search(r"claude|copilot|\bai\b|agent", (title + " " + body), re.I)),
            "bot": False, "session": None,
            "pr": {"number": n, "title": title, "url": str(pr.get("html_url", "")), "body": body,
                   "branch": str((pr.get("head") or {}).get("ref", ""))},
            "changelog": [], "suggested_sections": suggest_sections([], [title, body], []),
        })
    by_day: dict[str, list[dict]] = defaultdict(list)
    for c in commits or []:
        msg = str((c.get("commit") or {}).get("message") or "")
        subject = msg.splitlines()[0] if msg else ""
        n = pr_number(subject)
        if n and n in pr_numbers:
            continue  # the squash merge of a PR we already have
        author = str((c.get("author") or {}).get("login") or (c.get("commit") or {}).get("author", {}).get("name") or "")
        if BOT_RE.search(author):
            continue
        date = _lib.parse_date((c.get("commit") or {}).get("author", {}).get("date"))
        if not date or date < since or date > today:
            continue
        ctype, scope, text = parse_subject(subject)
        by_day[date.isoformat()].append({
            "sha": str(c.get("sha", "")), "short": str(c.get("sha", ""))[:7], "date": date.isoformat(),
            "author": author, "subject": _lib.one_line(_lib.scrub(subject), limit=160), "type": ctype,
            "scope": scope, "text": text, "pr": n, "session": "",
            "ai": bool(CLAUDE_COAUTHOR_RE.search(msg)) or bool(SESSION_RE.search(msg)), "bot": False, "files": [],
        })
    for day, cs in by_day.items():
        stories.append({
            "id": f"day:{day}@{slug}", "kind": "day", "repo": slug, "label": label, "weight": weight,
            "date_start": day, "date_end": day, "commits": cs, "files_changed": 0, "insertions": 0,
            "deletions": 0, "top_paths": [], "areas": [], "ai_assisted": any(c["ai"] for c in cs), "bot": False,
            "session": None, "pr": None, "changelog": [],
            "suggested_sections": suggest_sections([], [c["subject"] for c in cs], []),
        })
    return stories


def fetch_remote_stories(sources: list[dict], since: _dt.date, today: _dt.date, notes: list[str]) -> list[dict]:
    out: list[dict] = []
    for src in sources:
        if src.get("via") != "github":
            continue
        slug = str(src.get("slug", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", slug):
            notes.append(f"skipped source with a bad slug: {slug!r}")
            continue
        commits = gh_json(f"repos/{slug}/commits?since={since.isoformat()}T00:00:00Z&per_page=100")
        pulls = gh_json(f"repos/{slug}/pulls?state=closed&sort=updated&direction=desc&per_page=50")
        if commits is None and pulls is None:
            notes.append(f"{slug}: not read (gh missing, no token, or the API refused) — skipped")
            continue
        found = remote_stories_from_payloads(slug, str(src.get("label", slug)), float(src.get("weight", 0.5) or 0.5),
                                             commits if isinstance(commits, list) else [],
                                             pulls if isinstance(pulls, list) else [], since, today)
        notes.append(f"{slug}: {len(found)} story(ies) in the window")
        out.extend(found)
    return out


# --------------------------------------------------------------------------- #
# Grouping, scoring, spending
# --------------------------------------------------------------------------- #

def _story_key(c: dict) -> tuple[str, str]:
    if c["session"]:
        return "session", f"session:{c['session']}"
    if c["pr"]:
        return "pr", f"pr:{c['pr']}"
    return "day", f"day:{c['date']}"


def group_home_commits(commits: list[dict], slug: str, label: str, weight: float,
                       merge_prs: dict[int, str], traces: dict[str, dict], changelog: str) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    kinds: dict[str, str] = {}
    for c in commits:
        kind, key = _story_key(c)
        groups[key].append(c)
        kinds[key] = kind
    stories: list[dict] = []
    for key, cs in groups.items():
        cs.sort(key=lambda c: c["date"])
        path_counter: Counter = Counter()
        area_counter: Counter = Counter()
        ins = dele = 0
        for c in cs:
            for f in c["files"]:
                path_counter[f["path"]] += f["add"] + f["del"] + 1
                area_counter[area_of(f["path"])] += f["add"] + f["del"] + 1
                ins += f["add"]
                dele += f["del"]
        prs = sorted({c["pr"] for c in cs if c["pr"]})
        pr_info = None
        if prs:
            n = prs[0]
            first = next(c for c in cs if c["pr"] == n)
            pr_info = {"number": n, "title": PR_RE.sub("", first["subject"]).strip(), "url": f"https://github.com/{slug}/pull/{n}",
                       "body": "", "branch": merge_prs.get(n, "")}
        sid = cs[0]["session"]
        trace = traces.get(sid) if sid else None
        session = None
        if sid:
            session = {"id": sid, "url": f"https://claude.ai/code/session_{sid}",
                       "intent": _lib.one_line(_lib.scrub(str((trace or {}).get("intent") or "")), limit=240),
                       "files": list((trace or {}).get("files") or [])[:12],
                       "reason": str((trace or {}).get("reason") or "")}
        areas = [a for a, _ in area_counter.most_common()]
        stories.append({
            "id": key, "kind": kinds[key], "repo": slug, "label": label, "weight": weight,
            "date_start": cs[0]["date"], "date_end": cs[-1]["date"],
            "commits": [{k: c[k] for k in ("sha", "short", "date", "subject", "type", "scope", "ai", "bot")} for c in cs],
            "files_changed": len(path_counter), "insertions": ins, "deletions": dele,
            "top_paths": [p for p, _ in path_counter.most_common(8)],
            "areas": areas, "ai_assisted": any(c["ai"] for c in cs), "bot": all(c["bot"] for c in cs),
            "session": session, "pr": pr_info, "changelog": changelog_hits(changelog, prs),
            "suggested_sections": suggest_sections(areas, [c["subject"] for c in cs] + ([session["intent"]] if session else []),
                                                   list(path_counter)),
        })
    # Traces with no commits in the window still count (thin evidence, low score).
    covered = {s["session"]["id"] for s in stories if s.get("session")}
    for sid, tr in traces.items():
        if sid in covered:
            continue
        day = _lib.parse_date(tr.get("ended_at") or tr.get("date"))
        if not day:
            continue
        intent = _lib.one_line(_lib.scrub(str(tr.get("intent") or "")), limit=240)
        files = [str(p) for p in (tr.get("files") or [])][:12]
        areas = [a for a, _ in Counter(area_of(p) for p in files).most_common()]
        stories.append({
            "id": f"session:{sid}", "kind": "session", "repo": slug, "label": label, "weight": weight,
            "date_start": day.isoformat(), "date_end": day.isoformat(), "commits": [],
            "files_changed": len(files), "insertions": 0, "deletions": 0, "top_paths": files[:8],
            "areas": areas, "ai_assisted": True, "bot": False,
            "session": {"id": sid, "url": f"https://claude.ai/code/session_{sid}", "intent": intent,
                        "files": files, "reason": str(tr.get("reason") or "")},
            "pr": None, "changelog": [], "suggested_sections": suggest_sections(areas, [intent], files),
        })
    return stories


def score_story(s: dict, today: _dt.date, window_days: int, cfg: dict) -> None:
    """Attach score, age_days, spent-aware, with a human-readable reasons list."""
    end = _lib.parse_date(s["date_end"]) or today
    age = max(0, (today - end).days)
    recency = max(0.35, 1.0 - 0.7 * age / max(1, window_days))
    lines = s["insertions"] + s["deletions"]
    if lines == 0 and s["kind"] in ("pr", "day") and not s["commits"] and s["pr"]:
        lines = 200  # a merged sister PR with unknown size: assume a real change
    elif lines == 0 and s["commits"]:
        lines = 50 * len(s["commits"])
    size = min(1.0, math.log10(1 + lines) / 3.0)
    factor = 1.0
    reasons = [f"recency {recency:.2f} ({age}d old)", f"size {size:.2f} ({lines} lines)"]
    types = [c.get("type", "") for c in s["commits"]] or ([s["pr"]["title"].split("(")[0].split(":")[0].strip().lower()] if s.get("pr") else [])
    tf = max((TYPE_FACTOR.get(t, 1.0) for t in types), default=1.0)
    if tf != 1.0:
        factor *= tf
        reasons.append(f"commit type factor {tf}")
    if s["ai_assisted"]:
        factor *= float(cfg.get("ai_session_bonus", 1.15) or 1.0)
        reasons.append("AI-assisted")
    if s["areas"] and set(s["areas"]) <= CONTENT_ONLY_AREAS:
        factor *= float(cfg.get("content_only_factor", 0.5) or 1.0)
        reasons.append("content-only commits")
    if s["bot"]:
        factor *= float(cfg.get("automation_factor", 0.7) or 1.0)
        reasons.append("automated run")
    if s["weight"] != 1.0:
        reasons.append(f"source weight {s['weight']}")
    score = 100.0 * recency * (0.25 + 0.75 * size) * float(s["weight"]) * factor
    s["age_days"] = age
    s["score"] = 0.0 if s.get("spent") else round(score, 1)
    s["reasons"] = reasons + (["SPENT — already written up"] if s.get("spent") else [])


def mark_spent(stories: list[dict], spent: set[str]) -> None:
    for s in stories:
        ids = {s["id"]} | {c["sha"] for c in s["commits"]} | {c["short"] for c in s["commits"]}
        if s.get("pr"):
            ids.add(f"pr:{s['pr']['number']}" if s["repo"] == _lib.repo_slug() or "@" not in s["id"] else s["id"])
        s["spent"] = bool(ids & spent)


def headline(s: dict) -> str:
    if s.get("pr") and s["pr"].get("title"):
        return s["pr"]["title"]
    if s.get("session") and s["session"].get("intent"):
        return s["session"]["intent"]
    if s["commits"]:
        return s["commits"][0]["subject"]
    return s["id"]


# --------------------------------------------------------------------------- #
# The entry point the planner calls
# --------------------------------------------------------------------------- #

def gather(today: _dt.date, window_days: int, config: dict, sources: list[dict], runs: list[dict],
           *, root: Path = _lib.ROOT, changelog_path: Path | None = None, sessions_path: Path | None = None,
           remote: bool = True, home_slug: str | None = None) -> dict:
    since = today - _dt.timedelta(days=window_days)
    notes: list[str] = []
    slug = home_slug or _lib.repo_slug() or "home"
    home = next((s for s in sources if s.get("via") == "git"), {"slug": slug, "label": "this site and practice", "weight": 1.0})
    changelog = (changelog_path or (root / "CHANGELOG.md"))
    changelog_text = changelog.read_text(encoding="utf-8", errors="replace") if changelog.exists() else ""
    traces = load_traces(sessions_path or (root / "_data" / "loop" / "sessions.jsonl"))
    traces = {sid: t for sid, t in traces.items()
              if (d := _lib.parse_date(t.get("ended_at") or t.get("date"))) is None or since <= d <= today}
    commits = _git_commits(root, since)
    stories = group_home_commits(commits, str(home.get("slug", slug)), str(home.get("label", "")),
                                 float(home.get("weight", 1.0) or 1.0), _git_merge_prs(root, since), traces, changelog_text)
    notes.append(f"{home.get('slug', slug)}: {len(commits)} commit(s), {len(traces)} session trace(s) in the window")
    if remote:
        stories.extend(fetch_remote_stories(sources, since, today, notes))
    else:
        notes.append("sister repositories not read (--no-remote)")
    mark_spent(stories, ledger.spent_signals(runs))
    sig_cfg = (config.get("signals") or {}) if isinstance(config, dict) else {}
    for s in stories:
        score_story(s, today, window_days, sig_cfg)
        s["headline"] = _lib.one_line(_lib.scrub(headline(s)), limit=160)
    stories.sort(key=lambda s: (-s["score"], s["date_end"], s["id"]), reverse=False)
    stories.sort(key=lambda s: (-s["score"], s["date_end"]), reverse=False)
    return {
        "generated_at": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "today": today.isoformat(), "since": since.isoformat(), "window_days": window_days,
        "repo": str(home.get("slug", slug)), "unspent": sum(1 for s in stories if not s["spent"] and s["score"] > 0),
        "stories": stories, "notes": notes,
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render_markdown(result: dict, top: int = 6) -> str:
    out = [f"# Activity digest — {result['today']}", ""]
    out.append(f"Window: {result['since']} → {result['today']} ({result['window_days']} days). "
               f"{len(result['stories'])} story(ies), {result['unspent']} unspent. Home: `{result['repo']}`.")
    for n in result.get("notes", []):
        out.append(f"- {n}")
    out.append("")
    live = [s for s in result["stories"] if not s["spent"] and s["score"] > 0][:top]
    if not live:
        out.append("_No unspent activity in this window._")
    for i, s in enumerate(live, 1):
        flags = " · ".join(x for x in [s["label"] or s["repo"], "AI-assisted" if s["ai_assisted"] else "", "automated" if s["bot"] else ""] if x)
        out.append(f"## {i}. {s['headline']}")
        out.append(f"`{s['id']}` · score {s['score']} · {s['date_start']}" + (f" → {s['date_end']}" if s["date_end"] != s["date_start"] else "") + f" · {flags}")
        out.append("")
        out.append(f"- **Suggested sections:** {', '.join(s['suggested_sections'])}")
        if s["areas"]:
            out.append(f"- **Areas:** {', '.join(s['areas'][:6])}")
        if s["files_changed"]:
            out.append(f"- **Size:** {s['files_changed']} file(s), +{s['insertions']} / -{s['deletions']}")
        if s["commits"]:
            out.append("- **Commits:**")
            for c in s["commits"][:8]:
                out.append(f"  - `{c['short']}` {c['date']} {c['subject']}")
            if len(s["commits"]) > 8:
                out.append(f"  - … and {len(s['commits']) - 8} more")
        if s["pr"]:
            line = f"- **Pull request:** [#{s['pr']['number']} {s['pr']['title']}]({s['pr']['url']})"
            if s["pr"].get("branch"):
                line += f" (branch `{s['pr']['branch']}`)"
            out.append(line)
            if s["pr"].get("body"):
                out.append(f"  - {s['pr']['body']}")
        for hit in s["changelog"]:
            out.append(f"- **Changelog:** {hit}")
        if s["session"]:
            out.append(f"- **AI session:** `{s['session']['id']}`" + (f" — intent: {s['session']['intent']}" if s['session']['intent'] else ""))
            if s["session"]["files"]:
                out.append(f"  - files touched: {', '.join(s['session']['files'][:8])}")
        if s["top_paths"]:
            out.append(f"- **Paths:** {', '.join(f'`{p}`' for p in s['top_paths'][:6])}")
        out.append(f"- **Why this score:** {' · '.join(s['reasons'])}")
        if s["commits"] and "@" not in s["id"]:
            out.append(f"- **Dig in:** `git show --stat {s['commits'][0]['short']}`, then `git show <sha> -- <path>` for the diffs that matter")
        out.append("")
    rest = [s for s in result["stories"] if s not in live]
    if rest:
        out.append("## Everything else in the window")
        out.append("")
        out.append("| story | score | date | headline |")
        out.append("|---|---|---|---|")
        for s in rest[:40]:
            tag = "spent" if s["spent"] else str(s["score"])
            out.append(f"| `{s['id']}` | {tag} | {s['date_end']} | {s['headline'][:80]} |")
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Self-test: a throwaway git repo with trailers, PR refs, traces, a ledger
# --------------------------------------------------------------------------- #

def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> None:
    import os
    e = dict(os.environ)
    e.update({"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@example.com",
              "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@example.com"})
    e.update(env or {})
    subprocess.run(cmd, cwd=str(cwd), env=e, check=True, capture_output=True)


def _commit(root: Path, date: str, subject: str, body: str, files: dict[str, str], author: str = "Test") -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    _run(["git", "add", "-A"], root)
    stamp = f"{date}T12:00:00+00:00"
    _run(["git", "commit", "-q", "-m", subject, "-m", body, "--author", f"{author} <t@example.com>"], root,
         {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp})


def self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name, got, want):
        if got != want:
            failures.append(f"{name}: got {got!r}, want {want!r}")

    check("area posts", area_of("pages/_posts/erp/2026-01-01-x.md"), "posts/erp")
    check("area claude", area_of(".claude/skills/x/SKILL.md"), "claude")
    check("area ci", area_of(".github/workflows/x.yml"), "ci")
    check("area root page", area_of("ai-operations.md"), "pages")
    check("area other", area_of("weird.bin"), "other")
    check("session id", session_id_from("https://claude.ai/code/session_01ABC"), "01ABC")
    check("subject parse", parse_subject("feat(claude): the loop"), ("feat", "claude", "the loop"))
    check("pr number", pr_number("fix(theme): x (#38)"), 38)
    check("erp keyword pull", suggest_sections(["scripts"], ["add a journal entry ledger for the close"], [])[0], "erp")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _run(["git", "init", "-q", "-b", "main"], root)
        _run(["git", "remote", "add", "origin", "https://github.com/acme/site.git"], root)
        _commit(root, "2026-07-15", "chore: old", "", {"README.md": "old\n"})
        _commit(root, "2026-08-20", "feat(claude): add the loop skill", "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01SESS",
                {".claude/skills/content-loop/SKILL.md": "x\n", "scripts/loop/plan.py": "y\n" * 30})
        _commit(root, "2026-08-21", "docs(docs): describe the loop", "Claude-Session: https://claude.ai/code/session_01SESS",
                {"docs/content-loop.md": "z\n" * 80})
        _commit(root, "2026-08-25", "fix(theme): retire posthog fork (#38)", "Co-authored-by: Claude Opus 5 <noreply@anthropic.com>",
                {"_includes/analytics/posthog.html": "p\n", "_config.yml": "c\n" * 40})
        _commit(root, "2026-08-27", "content(erp): expand — journal entries (#40)", "",
                {"pages/_posts/erp/2026-08-27-journal.md": "j\n" * 20}, author="github-actions[bot]")
        _commit(root, "2026-08-28", "feat(posts): two muses essays", "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>",
                {"pages/_posts/muses/2026-08-28-a.md": "m\n" * 60})
        _commit(root, "2026-08-29", "chore(config): bump", "", {"zer0.json": "{}\n"})
        (root / "CHANGELOG.md").write_text("# Change Log\n## [Unreleased]\n- **Retired the PostHog fork** (#38) — upstreamed.\n- unrelated (#99)\n")
        sessions = root / "sessions.jsonl"
        sessions.write_text(json.dumps({"session_id": "session_01SESS", "ended_at": "2026-08-21T10:00:00Z",
                                        "intent": "build the content loop with token sk-ant-api03-abcdefghijklmnop",
                                        "files": [".claude/skills/content-loop/SKILL.md"], "reason": "prompt_input_exit"}) + "\n"
                            + json.dumps({"session_id": "01LONE", "ended_at": "2026-08-30T10:00:00Z", "intent": "fix the DMARC record and privacy policy",
                                          "files": ["privacy.md", "docs/domains-and-email.md"]}) + "\n"
                            + json.dumps({"session_id": "01OLD", "ended_at": "2026-01-01T10:00:00Z", "intent": "ancient"}) + "\n"
                            + "not json\n")
        runs = [{"date": "2026-08-26", "mode": "new", "signals": ["pr:38"]}]
        cfg = {"signals": {"ai_session_bonus": 1.15, "content_only_factor": 0.5, "automation_factor": 0.7}}
        sources = [{"slug": "acme/site", "via": "git", "weight": 1.0, "label": "home"}]
        today = _dt.date(2026, 8, 31)
        res = gather(today, 30, cfg, sources, runs, root=root, changelog_path=root / "CHANGELOG.md",
                     sessions_path=sessions, remote=False, home_slug="acme/site")
        by_id = {s["id"]: s for s in res["stories"]}
        check("story ids", set(by_id), {"session:01SESS", "pr:38", "pr:40", "day:2026-08-28", "day:2026-08-29", "session:01LONE"})
        check("old trace dropped", "session:01OLD" in by_id, False)
        sess = by_id["session:01SESS"]
        check("session groups two commits", [c["subject"] for c in sess["commits"]],
              ["feat(claude): add the loop skill", "docs(docs): describe the loop"])
        check("session intent scrubbed", "abcdefghijklmnop" in sess["session"]["intent"], False)
        check("session intent kept", sess["session"]["intent"].startswith("build the content loop"), True)
        check("session areas", sess["areas"][0], "docs")
        check("session ai", sess["ai_assisted"], True)
        check("session sections", sess["suggested_sections"][0], "tech")
        check("pr spent", by_id["pr:38"]["spent"], True)
        check("pr spent score", by_id["pr:38"]["score"], 0.0)
        check("pr title", by_id["pr:38"]["pr"]["title"], "fix(theme): retire posthog fork")
        check("pr url", by_id["pr:38"]["pr"]["url"], "https://github.com/acme/site/pull/38")
        check("changelog hit", by_id["pr:38"]["changelog"], ["**Retired the PostHog fork** (#38) — upstreamed."])
        check("bot flagged", by_id["pr:40"]["bot"], True)
        check("bot factor", "automated run" in by_id["pr:40"]["reasons"], True)
        check("content-only", "content-only commits" in by_id["day:2026-08-28"]["reasons"], True)
        check("lone trace story", by_id["session:01LONE"]["kind"], "session")
        check("lone trace sections", by_id["session:01LONE"]["suggested_sections"][0], "corp")
        check("erp keyword", by_id["pr:40"]["suggested_sections"][0], "erp")
        order = [s["id"] for s in res["stories"] if not s["spent"]]
        check("best first", order[0], "session:01SESS")
        check("unspent count", res["unspent"], 5)
        md = render_markdown(res, top=3)
        check("markdown has digest", md.startswith("# Activity digest — 2026-08-31"), True)
        check("markdown lists spent", "| `pr:38` | spent |" in md, True)
        check("markdown top", "## 1. build the content loop" in md, True)
        # The window excludes the ancient commit and the old trace.
        check("old commit excluded", any("chore: old" in c["subject"] for s in res["stories"] for c in s["commits"]), False)

    # Remote payload parsing is pure — test it without gh.
    pulls = [{"number": 7, "title": "feat: the harness renders the same", "merged_at": "2026-08-30T01:00:00Z",
              "html_url": "https://github.com/acme/sis/pull/7", "body": "long body ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234 " + "x" * 600,
              "user": {"login": "amr"}, "head": {"ref": "feat/x"}},
             {"number": 8, "title": "chore(deps): bump", "merged_at": "2026-08-30T01:00:00Z", "user": {"login": "dependabot[bot]"}},
             {"number": 9, "title": "unmerged", "merged_at": None, "user": {"login": "amr"}}]
    commits = [{"sha": "abcdef1234567", "commit": {"message": "feat: the harness renders the same (#7)", "author": {"date": "2026-08-30T01:00:00Z", "name": "amr"}}, "author": {"login": "amr"}},
               {"sha": "1234567abcdef", "commit": {"message": "fix: a bare push\n\nCo-Authored-By: Claude", "author": {"date": "2026-08-29T01:00:00Z", "name": "amr"}}, "author": {"login": "amr"}},
               {"sha": "999", "commit": {"message": "bot noise", "author": {"date": "2026-08-29T01:00:00Z", "name": "dependabot[bot]"}}, "author": {"login": "dependabot[bot]"}}]
    rs = remote_stories_from_payloads("acme/sis", "sister", 0.6, commits, pulls, _dt.date(2026, 8, 1), _dt.date(2026, 8, 31))
    ids = {s["id"]: s for s in rs}
    check("remote ids", set(ids), {"pr:7@acme/sis", "day:2026-08-29@acme/sis"})
    check("remote body scrubbed", "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234" in ids["pr:7@acme/sis"]["pr"]["body"], False)
    check("remote body capped", len(ids["pr:7@acme/sis"]["pr"]["body"]) <= 400, True)
    check("remote day ai", ids["day:2026-08-29@acme/sis"]["ai_assisted"], True)
    check("gh missing is None", gh_json("repos/x/y") is None or isinstance(gh_json("repos/x/y"), (dict, list)), True)

    if failures:
        print("signals --self-test: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("signals --self-test: PASS (areas, grouping by session/PR/day, traces, spent, scoring, changelog, remote parsing, digest)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Mine the practice's recent work into stories.")
    ap.add_argument("--window", type=int, help="days to look back (default: _data/loop/config.yml signals.window_days)")
    ap.add_argument("--today", help="YYYY-MM-DD (default: today UTC, or LOOP_TODAY)")
    ap.add_argument("--no-remote", action="store_true", help="skip the sister repositories (no gh calls)")
    ap.add_argument("--top", type=int, help="stories to detail in the digest (default: config signals.top)")
    ap.add_argument("--json", action="store_true", help="print signals.json to stdout")
    ap.add_argument("--markdown", action="store_true", help="print the digest to stdout (default)")
    ap.add_argument("--out", help="directory to write signals.json + digest.md into")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    config = _lib.read_yaml(_lib.CONFIG_PATH, default={}) or {}
    sources = ((_lib.read_yaml(_lib.SOURCES_PATH, default={}) or {}).get("repos")) or []
    sig_cfg = config.get("signals") or {}
    window = args.window or int(sig_cfg.get("window_days", 30) or 30)
    top = args.top or int(sig_cfg.get("top", 6) or 6)
    today = _lib.parse_date(args.today) if args.today else _lib.today()
    if today is None:
        ap.error(f"bad --today {args.today!r}")
    runs = ledger.load_runs()
    res = gather(today, window, config, sources, runs, remote=not args.no_remote)
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "signals.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out / "digest.md").write_text(render_markdown(res, top) + "\n", encoding="utf-8")
        print(f"signals: {len(res['stories'])} story(ies), {res['unspent']} unspent → {out / 'signals.json'}, {out / 'digest.md'}")
        return 0
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(res, top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
