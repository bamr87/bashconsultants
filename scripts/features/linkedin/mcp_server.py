#!/usr/bin/env python3
"""A Model Context Protocol (MCP) server for the BASH LinkedIn company page.

This is the Claude-native front end to the deterministic publisher in this same
package. It exposes the publisher's capabilities as MCP tools so an assistant
(Claude Code, or any MCP client) can inspect the page, preview a post, stage a
governed draft, and — behind an explicit opt-in — publish to the company page.

Design choices, and why they differ from LinkedIn's reference server
(fredericbarthelet/linkedin-mcp-server, the "Develop with MCP" sample):

  * LinkedIn's sample is a REMOTE, multi-user server (HTTP+SSE) that runs the
    MCP third-party OAuth flow to mint each visitor's token on the fly. This one
    is a LOCAL, single-operator server (stdio) that reuses the token already in
    `.env` — no network-exposed surface, no OAuth dance. The remote/OAuth model
    is the future path if the publisher is ever hosted for many users.
  * LinkedIn's sample exposes `user-info` + `create-post`. This one keeps that
    spirit but wraps `create-post` in the repo's governance: reads and previews
    are always available; `linkedin_publish` is OFF by default and requires the
    env opt-in LINKEDIN_MCP_ALLOW_PUBLISH plus a per-call confirm. `linkedin_draft`
    is the doctrine-preferred path — the AI drafts, the human merge approves.

Transport: newline-delimited JSON-RPC 2.0 on stdin/stdout (the MCP stdio
transport). Stdlib only, matching the rest of scripts/features/linkedin/.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --- Protect the protocol channel ------------------------------------------
# stdout is the JSON-RPC channel; a stray print() from any imported module would
# corrupt it. Capture the real stdout once, then point sys.stdout at stderr so
# every incidental print lands on the (client-ignored) log stream instead.
_PROTOCOL_OUT = sys.stdout
sys.stdout = sys.stderr

# The package modules use flat imports; ensure our own directory is importable
# whether launched as a script or a module.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import auth  # noqa: E402
import content  # noqa: E402
import ledger  # noqa: E402
import posts  # noqa: E402
from config import (  # noqa: E402
    Config,
    OAUTH_TOKEN_URL,
    QUEUE_DIR,
    REPO_ROOT,
    TOKEN_GENERATOR_URL,
)
from net import LinkedInHTTPError, linkedin_headers, request  # noqa: E402

SERVER_NAME = "bash-linkedin"
SERVER_VERSION = "1.0.0"
# The protocol version we implement; we echo the client's if it sends a known one.
DEFAULT_PROTOCOL = "2025-06-18"
SUPPORTED_PROTOCOLS = {"2024-11-05", "2025-03-26", "2025-06-18"}

PUBLISH_ENABLED = os.environ.get("LINKEDIN_MCP_ALLOW_PUBLISH", "").strip().lower() in (
    "1", "true", "yes", "on",
)


# ---------------------------------------------------------------------------
# .env loading (local dev convenience; secrets never come from the repo)
# ---------------------------------------------------------------------------

def _load_dotenv():
    """Load repo-root .env into os.environ for keys not already set.

    Minimal KEY=VALUE parser (stdlib only). Existing environment wins, so CI —
    which sets real secrets in the environment — is unaffected.
    """
    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Tool implementations — each returns a human-readable string
# ---------------------------------------------------------------------------

def _cfg():
    return Config()


def tool_whoami(_args):
    """Token status, granted scopes and expiry — LinkedIn's `user-info`, adapted.

    Prefers OAuth token introspection (needs client id/secret); otherwise does a
    cheap authenticated read to confirm the token at least works.
    """
    cfg = _cfg()
    try:
        token = auth.resolve_token(cfg, verbose=False)
    except RuntimeError as exc:
        return f"No usable token. {exc}"

    lines = [f"organization: {cfg.org_urn}", f"api version : {cfg.api_version}"]

    if cfg.client_id and cfg.client_secret:
        body = urllib.parse.urlencode({
            "client_id": cfg.client_id,
            "client_secret": cfg.client_secret,
            "token": token,
        }).encode()
        req = urllib.request.Request(
            "https://www.linkedin.com/oauth/v2/introspectToken",
            data=body, method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            return "\n".join(lines + [f"introspection failed: HTTP {exc.code}"])
        active = data.get("active")
        scopes = sorted(s.strip() for s in (data.get("scope") or "").split(",") if s.strip())
        lines.append(f"token active: {active}")
        if data.get("expires_at"):
            import datetime
            exp = datetime.datetime.fromtimestamp(int(data["expires_at"]), datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            lines.append(f"expires     : {exp.strftime('%Y-%m-%d %H:%M UTC')} "
                         f"(~{(exp - now).days} days)")
        lines.append("scopes      : " + (", ".join(scopes) or "(none)"))
        can_post = "w_organization_social" in scopes
        can_read = "r_organization_social" in scopes
        lines.append(f"can post to page (w_organization_social): {can_post}")
        lines.append(f"can read page    (r_organization_social): {can_read}")
        if not active:
            lines.append("NOTE: token is not active — regenerate at " + TOKEN_GENERATOR_URL)
    else:
        # No client creds: fall back to a cheap read to prove the token works.
        author = urllib.parse.quote(cfg.org_urn, safe="")
        url = f"{cfg.rest_base}/posts?author={author}&q=author&count=1"
        try:
            request("GET", url, headers=linkedin_headers(
                token, cfg.api_version, extra={"X-RestLi-Method": "FINDER"}))
            lines.append("token: valid (authenticated read succeeded)")
        except LinkedInHTTPError as exc:
            lines.append(f"token check returned HTTP {exc.status}: {exc}")
    lines.append(f"publish tool enabled: {PUBLISH_ENABLED} "
                 f"(set LINKEDIN_MCP_ALLOW_PUBLISH=1 to enable)")
    return "\n".join(lines)


def tool_list_posts(args):
    """List the organization's recent posts (needs r_organization_social)."""
    cfg = _cfg()
    count = int(args.get("count", 5) or 5)
    count = max(1, min(count, 20))
    token = auth.resolve_token(cfg, verbose=False)
    author = urllib.parse.quote(cfg.org_urn, safe="")
    url = f"{cfg.rest_base}/posts?author={author}&q=author&count={count}"
    try:
        _, _, data = request("GET", url, headers=linkedin_headers(
            token, cfg.api_version, extra={"X-RestLi-Method": "FINDER"}))
    except LinkedInHTTPError as exc:
        return f"list failed: HTTP {exc.status}: {exc}"
    els = data.get("elements", [])
    total = (data.get("paging") or {}).get("total")
    out = [f"{len(els)} of {total if total is not None else '?'} post(s) on the page:"]
    for el in els:
        urn = el.get("id", "?")
        text = (el.get("commentary") or "").replace("\n", " ")
        out.append(f"  - {urn}\n    {text[:100]}")
        out.append(f"    {posts.feed_url(urn)}")
    return "\n".join(out)


def tool_get_post(args):
    """Fetch one post back by URN."""
    urn = (args.get("urn") or "").strip()
    if not urn:
        return "error: 'urn' is required"
    cfg = _cfg()
    token = auth.resolve_token(cfg, verbose=False)
    try:
        data = posts.get_post(cfg, token, urn)
    except LinkedInHTTPError as exc:
        return f"get failed: HTTP {exc.status}: {exc}"
    keep = {k: data.get(k) for k in
            ("id", "author", "lifecycleState", "visibility", "commentary", "content")
            if k in data}
    return json.dumps(keep, indent=2, ensure_ascii=False)


def _build_preview(cfg, args):
    """Shared payload builder for preview + publish. Returns (payload, notes)."""
    kind = (args.get("type") or "article").lower()
    notes = []
    if kind in ("text", "update"):
        message = (args.get("message") or args.get("commentary") or "").strip()
        if not message:
            raise ValueError("a text post needs 'message'")
        notes += [f"{lvl}: {msg}" for lvl, msg in content.guard_commentary(message)]
        return posts.build_text_payload(cfg, message), notes, "text", None, None
    if kind != "article":
        raise ValueError(f"unknown type '{kind}' (use 'article' or 'text')")

    ref = (args.get("ref") or "").strip()
    if not ref:
        raise ValueError("an article post needs 'ref' (section/YYYY-MM-DD-slug)")
    post = content.load_post(ref)
    url = content.canonical_url(cfg, post.path)
    title, description = post.title, post.description
    if not title or not description:
        raise ValueError(f"post is missing title/description ({post.path})")
    commentary = (args.get("commentary") or "").strip() or content.default_commentary(cfg, post)
    notes += [f"{lvl}: {msg}" for lvl, msg in content.guard_commentary(commentary)]
    payload = posts.build_article_payload(
        cfg, url=url, title=title, description=description,
        commentary=commentary, thumbnail_urn=None)
    thumb = content.resolve_thumbnail(post.get("preview"))
    return payload, notes, "article", url, (post, thumb)


def tool_preview(args):
    """Render the exact /rest/posts payload without posting (dry-run)."""
    cfg = _cfg()
    try:
        payload, notes, _kind, url, _extra = _build_preview(cfg, args)
    except (ValueError, FileNotFoundError) as exc:
        return f"error: {exc}"
    out = ["dry-run — this is the exact body that WOULD POST to /rest/posts:",
           json.dumps(payload, indent=2, ensure_ascii=False)]
    if url:
        out.append(f"canonical url: {url}")
    if notes:
        out.append("brand guard:")
        out += [f"  {n}" for n in notes]
    else:
        out.append("brand guard: clean")
    return "\n".join(out)


def tool_draft(args):
    """Stage a governed draft in drafts/linkedin/ (status: pending).

    The doctrine-preferred path: the AI drafts here, a human reviews and merges,
    and the merge is the approval. Nothing is published.
    """
    cfg = _cfg()
    kind = (args.get("type") or "article").lower()
    try:
        if kind in ("text", "update"):
            message = (args.get("message") or args.get("commentary") or "").strip()
            if not message:
                return "error: a text draft needs 'message'"
            slug = (args.get("slug") or "update").strip()
            fm = {"type": "update", "status": "pending"}
            body = message
        else:
            ref = (args.get("ref") or "").strip()
            if not ref:
                return "error: an article draft needs 'ref' (section/YYYY-MM-DD-slug)"
            post = content.load_post(ref)
            url = content.canonical_url(cfg, post.path)
            commentary = (args.get("commentary") or "").strip() or content.default_commentary(cfg, post)
            slug = (args.get("slug") or content.FILENAME_DATE_RE.sub("", post.path.stem)).strip()
            fm = {
                "type": "article",
                "status": "pending",
                "source": str(post.path.relative_to(REPO_ROOT)),
                "title": post.title,
                "description": post.description,
                "link": url,
            }
            body = commentary
    except (ValueError, FileNotFoundError) as exc:
        return f"error: {exc}"

    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    dest = QUEUE_DIR / f"{slug}.md"
    n = 2
    while dest.exists():
        dest = QUEUE_DIR / f"{slug}-{n}.md"
        n += 1
    fm_lines = ["---"]
    for k, v in fm.items():
        val = str(v).replace('"', '\\"')
        fm_lines.append(f'{k}: "{val}"' if k in ("title", "description", "link", "source") else f"{k}: {v}")
    fm_lines.append("---")
    dest.write_text("\n".join(fm_lines) + "\n\n" + body.strip() + "\n", encoding="utf-8")

    guard = content.guard_commentary(body)
    rel = dest.relative_to(REPO_ROOT)
    out = [f"drafted: {rel}", f"type: {fm['type']}  status: pending"]
    if guard:
        out.append("brand guard:")
        out += [f"  {lvl}: {msg}" for lvl, msg in guard]
    out.append("Review, edit, and merge the draft PR to approve; then publish "
               "with `from-drafts` or the linkedin_publish tool.")
    return "\n".join(out)


def tool_publish(args):
    """Actually POST to the company page. OFF by default; opt-in + confirm."""
    if not PUBLISH_ENABLED:
        return ("publishing is disabled. This tool posts to the LIVE company "
                "page. To enable, set LINKEDIN_MCP_ALLOW_PUBLISH=1 in the server "
                "environment. Until then, use linkedin_preview (dry-run) or "
                "linkedin_draft (governed queue).")
    if args.get("confirm") is not True:
        return ("refused: pass confirm=true to publish to the live page. "
                "Run linkedin_preview first to see the exact payload.")
    cfg = _cfg()
    try:
        payload, notes, kind, url, extra = _build_preview(cfg, args)
    except (ValueError, FileNotFoundError) as exc:
        return f"error: {exc}"

    errors = [n for n in notes if n.startswith("error:")]
    if errors and args.get("force") is not True:
        return "blocked by brand guard (pass force=true to override):\n" + "\n".join(
            f"  {n}" for n in notes)

    if kind == "article" and url and ledger.is_posted(cfg, url) and args.get("force") is not True:
        entry = ledger.get_entry(cfg, url)
        return (f"skip: already shared as {entry.get('linkedin_urn')} on "
                f"{entry.get('posted_at')} (pass force=true to repost)")

    token = auth.resolve_token(cfg, verbose=False)
    image_urn = None
    if kind == "article" and extra:
        post, thumb = extra
        if thumb:
            try:
                import images
                image_urn = images.upload_image(cfg, token, thumb, verbose=False)
                payload["content"]["article"]["thumbnail"] = image_urn
            except Exception as exc:  # thumbnail optional
                notes.append(f"warning: thumbnail upload failed ({exc}); posting without image")
    try:
        urn = posts.create_post(cfg, token, payload)
    except LinkedInHTTPError as exc:
        return f"publish failed: HTTP {exc.status}: {exc}"

    if kind == "article" and url:
        src = str(extra[0].path.relative_to(REPO_ROOT)) if extra else None
        ledger.record(cfg, url, urn, source_file=src, image_urn=image_urn, kind="article")

    out = [f"published: {urn}", f"  {posts.feed_url(urn)}"]
    if kind == "article":
        out.append("  (recorded in the idempotency ledger)")
    return "\n".join(out)


TOOLS = [
    {
        "name": "linkedin_whoami",
        "description": ("Report the LinkedIn token's status, granted scopes, and "
                        "expiry for the BASH company page, and whether the publish "
                        "tool is enabled. Read-only. Start here."),
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_whoami,
    },
    {
        "name": "linkedin_list_posts",
        "description": ("List the company page's recent posts with their URNs and "
                        "permalinks. Read-only (needs r_organization_social)."),
        "inputSchema": {
            "type": "object",
            "properties": {"count": {"type": "integer", "minimum": 1, "maximum": 20,
                                     "description": "how many posts (default 5)"}},
        },
        "handler": tool_list_posts,
    },
    {
        "name": "linkedin_get_post",
        "description": "Fetch a single company-page post back by its URN. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {"urn": {"type": "string",
                                   "description": "e.g. urn:li:share:12345 or urn:li:ugcPost:12345"}},
            "required": ["urn"],
        },
        "handler": tool_get_post,
    },
    {
        "name": "linkedin_preview",
        "description": ("Render the EXACT /rest/posts payload that a post would "
                        "send, plus the brand-guard result — without posting "
                        "anything. Use before publishing. Read-only."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["article", "text"],
                         "description": "article link-share or standalone text update"},
                "ref": {"type": "string",
                        "description": "article only: section/YYYY-MM-DD-slug, a path, or a slug"},
                "message": {"type": "string", "description": "text only: the update body"},
                "commentary": {"type": "string",
                               "description": "article only: override the auto-derived commentary"},
            },
        },
        "handler": tool_preview,
    },
    {
        "name": "linkedin_draft",
        "description": ("Stage a governed draft in drafts/linkedin/ (status: "
                        "pending) for a human to review and merge. The "
                        "doctrine-preferred path — the AI drafts, the merge "
                        "approves. Publishes nothing."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["article", "text"]},
                "ref": {"type": "string", "description": "article only: the post reference"},
                "message": {"type": "string", "description": "text only: the update body"},
                "commentary": {"type": "string", "description": "article only: commentary override"},
                "slug": {"type": "string", "description": "optional draft filename slug"},
            },
        },
        "handler": tool_draft,
    },
    {
        "name": "linkedin_publish",
        "description": ("Publish to the LIVE company page. OFF by default: needs "
                        "LINKEDIN_MCP_ALLOW_PUBLISH=1 in the server env AND "
                        "confirm=true. Runs the brand guard and records the "
                        "idempotency ledger. Prefer linkedin_draft for the "
                        "governed flow."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["article", "text"]},
                "ref": {"type": "string", "description": "article only: the post reference"},
                "message": {"type": "string", "description": "text only: the update body"},
                "commentary": {"type": "string", "description": "article only: commentary override"},
                "confirm": {"type": "boolean", "description": "must be true to post"},
                "force": {"type": "boolean",
                          "description": "override brand-guard errors / repost a ledgered URL"},
            },
            "required": ["confirm"],
        },
        "handler": tool_publish,
    },
]

_TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}


# ---------------------------------------------------------------------------
# JSON-RPC / MCP plumbing
# ---------------------------------------------------------------------------

def _send(message):
    _PROTOCOL_OUT.write(json.dumps(message, ensure_ascii=False) + "\n")
    _PROTOCOL_OUT.flush()


def _result(req_id, result):
    _send({"jsonrpc": "2.0", "id": req_id, "result": result})


def _error(req_id, code, message):
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def _handle(msg):
    method = msg.get("method")
    req_id = msg.get("id")
    is_notification = "id" not in msg

    if method == "initialize":
        params = msg.get("params") or {}
        client_proto = params.get("protocolVersion")
        proto = client_proto if client_proto in SUPPORTED_PROTOCOLS else DEFAULT_PROTOCOL
        _result(req_id, {
            "protocolVersion": proto,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": ("Tools for the BASH LinkedIn company page. Reads and "
                             "previews are always safe; linkedin_publish posts to "
                             "the live page and is opt-in. Prefer linkedin_draft."),
        })
        return

    if is_notification:
        # notifications/initialized, notifications/cancelled, etc. — no reply.
        return

    if method == "ping":
        _result(req_id, {})
        return

    if method == "tools/list":
        _result(req_id, {"tools": [
            {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
            for t in TOOLS]})
        return

    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        tool = _TOOLS_BY_NAME.get(name)
        if not tool:
            _error(req_id, -32602, f"unknown tool: {name}")
            return
        try:
            text = tool["handler"](arguments)
            is_error = isinstance(text, str) and text.lstrip().lower().startswith(
                ("error:", "refused:", "blocked", "publishing is disabled"))
            _result(req_id, {
                "content": [{"type": "text", "text": text}],
                "isError": bool(is_error),
            })
        except Exception as exc:  # never let a tool crash the server
            _result(req_id, {
                "content": [{"type": "text", "text": f"tool error: {type(exc).__name__}: {exc}"}],
                "isError": True,
            })
        return

    _error(req_id, -32601, f"method not found: {method}")


def main():
    _load_dotenv()
    sys.stderr.write(f"[{SERVER_NAME}] ready (publish {'ENABLED' if PUBLISH_ENABLED else 'disabled'})\n")
    sys.stderr.flush()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        try:
            _handle(msg)
        except Exception as exc:  # keep the loop alive on any error
            if "id" in (msg if isinstance(msg, dict) else {}):
                _error(msg.get("id"), -32603, f"internal error: {exc}")


if __name__ == "__main__":
    main()
