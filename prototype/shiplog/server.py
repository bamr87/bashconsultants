"""The local review dashboard — where a person approves a post.

Runs on the developer's own machine, serves one page, and holds no state of
its own: every action writes to the same files the CLI reads. Standard library
`http.server`, because a review UI for one local user does not need a
framework.

This screen is the product's answer to "what stops it posting something bad."
A draft sits here until someone reads it and clicks Approve.
"""

from __future__ import annotations

import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import compose
import payload as payload_mod
import portfolio as portfolio_mod
from core import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_PUBLISHED,
    Config,
    find_draft,
    load_queue,
    write_draft,
)

STYLE = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#e6edf3;font:15px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;padding:0 0 64px}
code,pre,.mono{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,monospace}
header{border-bottom:1px solid #21262d;background:#010409;padding:20px 32px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
header h1{font-size:19px;font-weight:650;letter-spacing:-.2px}
header h1 .p{color:#2f81f7}
header .sub{color:#7d8590;font-size:13px}
header .id{margin-left:auto;text-align:right;font-size:12px;color:#7d8590}
header .id b{color:#e6edf3;font-weight:550;display:block;font-size:13px}
main{max-width:1180px;margin:0 auto;padding:28px 32px;display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:28px;align-items:start}
@media (max-width:980px){main{grid-template-columns:1fr}}
section{margin-bottom:28px}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:#7d8590;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:8px}
h2 .n{background:#21262d;color:#e6edf3;border-radius:20px;padding:1px 8px;font-size:11px;letter-spacing:0}
.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px 18px;margin-bottom:14px}
.card.pending{border-left:3px solid #d29922}
.card.approved{border-left:3px solid #3fb950}
.card.published{border-left:3px solid #58a6ff;opacity:.72}
.row{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.pill{font-size:11px;padding:2px 9px;border-radius:20px;font-weight:600;letter-spacing:.03em;text-transform:uppercase}
.pill.pending{background:#3d2f0f;color:#e3b341}
.pill.approved{background:#12331c;color:#56d364}
.pill.published{background:#0d2d4e;color:#79c0ff}
.title{font-weight:600;font-size:15px}
.meta{color:#7d8590;font-size:12px}
.meta b{color:#a8b3bf;font-weight:550}
.body{white-space:pre-wrap;background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:13px 15px;font-size:13.5px;color:#c9d1d9;margin:10px 0}
.fold{border-top:1px dashed #d2992255;position:relative;margin:9px 0 3px;height:0}
.fold span{position:absolute;right:0;top:-9px;background:#161b22;color:#d29922;font-size:10px;padding:0 6px;letter-spacing:.05em}
.warn{background:#2d1e07;border:1px solid #9e6a03;color:#e3b341;border-radius:7px;padding:9px 12px;font-size:12.5px;margin:9px 0}
.warn b{display:block;margin-bottom:2px;color:#f0c674}
button{background:#238636;border:1px solid #2ea043;color:#fff;font:inherit;font-size:13px;font-weight:600;padding:6px 15px;border-radius:7px;cursor:pointer}
button:hover{background:#2ea043}
button.ghost{background:#21262d;border-color:#30363d;color:#c9d1d9}
button.ghost:hover{background:#30363d}
form{display:inline}
.actions{display:flex;gap:8px;align-items:center;margin-top:12px}
.gate{color:#7d8590;font-size:12px;margin-left:auto;font-style:italic}
pre.json{background:#0d1117;border:1px solid #21262d;border-radius:8px;padding:13px 15px;font-size:12.5px;color:#a5d6ff;line-height:1.55;white-space:pre-wrap;word-break:break-word}
.call{font-size:12px;color:#7d8590;margin-bottom:8px;word-break:break-all}
.call b{color:#79c0ff;font-weight:600}
.note{color:#7d8590;font-size:12px;border-left:2px solid #30363d;padding-left:11px;margin-top:10px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px}
.stat{background:#161b22;border:1px solid #30363d;border-radius:9px;padding:12px 13px}
.stat .v{font-size:22px;font-weight:650;letter-spacing:-.5px}
.stat .k{font-size:11px;color:#7d8590;text-transform:uppercase;letter-spacing:.06em;margin-top:1px}
.aud{background:#161b22;border:1px solid #30363d;border-radius:9px;padding:12px 14px;margin-bottom:10px}
.aud .i{font-family:ui-monospace,monospace;font-size:12px;color:#79c0ff;margin-bottom:3px}
.aud .l{font-size:13.5px;margin-bottom:4px}
.aud .w{font-size:12px;color:#7d8590}
.tags{margin-top:7px}
.tag{display:inline-block;background:#0d2d4e;color:#79c0ff;font-size:11px;padding:1px 8px;border-radius:20px;margin-right:5px}
.empty{color:#7d8590;font-size:13px;background:#161b22;border:1px dashed #30363d;border-radius:9px;padding:18px;text-align:center}
"""


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _draft_card(cfg: Config, draft) -> str:
    warnings = compose.check(draft.body)
    body = _esc(draft.body)
    # Show where LinkedIn truncates, so the reviewer sees what a reader sees.
    fold = ""
    if len(draft.body) > compose.FOLD:
        cut = len(_esc(draft.body[: compose.FOLD]))
        body = f'{body[:cut]}<div class="fold"><span>…see more</span></div>{body[cut:]}'
        fold = ""
    aud = draft.audience_id or "none"
    warn_html = ""
    if warnings:
        items = "<br>".join(_esc(w) for w in warnings)
        warn_html = f'<div class="warn"><b>Flagged for you</b>{items}</div>'
    action = ""
    if draft.status == STATUS_PENDING:
        action = (
            f'<div class="actions">'
            f'<form method="post" action="/approve">'
            f'<input type="hidden" name="id" value="{_esc(draft.id)}">'
            f'<button type="submit">Approve</button></form>'
            f'<span class="gate">Nothing is sent until you click this.</span>'
            f"</div>"
        )
    elif draft.status == STATUS_APPROVED:
        action = (
            f'<div class="actions"><span class="meta">Approved — '
            f'<span class="mono">publish</span> will send it.</span></div>'
        )
    return f"""
    <div class="card {_esc(draft.status)}">
      <div class="row">
        <span class="pill {_esc(draft.status)}">{_esc(draft.status)}</span>
        <span class="title">{_esc(draft.title)}</span>
      </div>
      <div class="meta"><b>source</b> {_esc(draft.meta.get('source', ''))} &nbsp;·&nbsp;
        <b>written for</b> {_esc(aud)} &nbsp;·&nbsp;
        <b>{len(draft.body)}</b> chars</div>
      <div class="body">{body}</div>{fold}
      {warn_html}{action}
    </div>"""


def _payload_panel(cfg: Config, drafts) -> str:
    target = next((d for d in drafts if d.status == STATUS_PENDING), None)
    if target is None:
        target = next((d for d in drafts if d.status != STATUS_PUBLISHED), None)
    if target is None:
        return '<div class="empty">Nothing queued to preview.</div>'
    body = json.dumps(payload_mod.build(cfg, target), indent=2, ensure_ascii=False)
    scope = payload_mod.scope_for(cfg)
    return f"""
    <div class="card">
      <div class="call">What <b>{_esc(target.title)}</b> becomes:<br>
        <b>POST</b> https://api.linkedin.com/rest/posts &nbsp;·&nbsp; scope <b>{_esc(scope)}</b></div>
      <pre class="json">{_esc(body)}</pre>
      <div class="note">Rendered locally. No request has been made — the payload is
      built from the file on disk so you can read it before anything is sent.</div>
    </div>"""


def _portfolio_panel(cfg: Config) -> str:
    p = portfolio_mod.build(cfg)
    if not p.count:
        return (
            '<div class="empty">No published posts yet.<br>'
            "The track record starts at one.</div>"
        )
    topics = "".join(
        f'<span class="tag">#{_esc(t)}</span>' for t, _ in p.topics.most_common(5)
    )
    return f"""
    <div class="stats">
      <div class="stat"><div class="v">{p.count}</div><div class="k">Published</div></div>
      <div class="stat"><div class="v">{p.cadence}</div><div class="k">Per month</div></div>
      <div class="stat"><div class="v">{p.streak}</div><div class="k">Month streak</div></div>
    </div>
    <div class="card"><div class="meta"><b>built from</b>
      {_esc(', '.join(f'{k} {v}' for k, v in p.by_kind.most_common()))}</div>
      <div class="tags">{topics}</div></div>"""


def _audience_panel(cfg: Config) -> str:
    if not cfg.audiences:
        return '<div class="empty">No audience profiles declared.</div>'
    cards = "".join(
        f"""<div class="aud"><div class="i">{_esc(a.id)}</div>
        <div class="l">{_esc(a.label)}</div>
        <div class="w">Reads for {_esc(a.reads_for)}</div>
        <div class="tags">{''.join(f'<span class="tag">#{_esc(t)}</span>' for t in a.hashtags)}</div>
        </div>"""
        for a in cfg.audiences
    )
    return cards + (
        '<div class="note">You declared these. shiplog does not read your '
        "connections or anyone's profile to infer an audience.</div>"
    )


def render_page(cfg: Config) -> str:
    drafts = load_queue(cfg)
    pending = sum(1 for d in drafts if d.status == STATUS_PENDING)
    queue_html = (
        "".join(_draft_card(cfg, d) for d in drafts)
        if drafts
        else '<div class="empty">Queue is empty. Run <span class="mono">draft &lt;source-id&gt;</span>.</div>'
    )
    identity = cfg.name or "unconfigured"
    urn = cfg.author_urn() or "no author URN set"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>shiplog — review</title><style>{STYLE}</style></head><body>
<header>
  <h1><span class="p">$</span> shiplog</h1>
  <span class="sub">publish what you ship</span>
  <div class="id"><b>{_esc(identity)}</b>{_esc(urn)}</div>
</header>
<main>
  <div>
    <section>
      <h2>Awaiting your approval <span class="n">{pending}</span></h2>
      {queue_html}
    </section>
  </div>
  <div>
    <section><h2>Outgoing request</h2>{_payload_panel(cfg, drafts)}</section>
    <section><h2>Your track record</h2>{_portfolio_panel(cfg)}</section>
    <section><h2>Writing for</h2>{_audience_panel(cfg)}</section>
  </div>
</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    cfg: Config
    server_version = "shiplog"

    def log_message(self, fmt, *args):  # quieter terminal during a demo
        return

    def _send(self, status: int, body: bytes, ctype="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route = urlparse(self.path).path
        if route in ("/", "/index.html"):
            self._send(200, render_page(self.cfg).encode("utf-8"))
        elif route == "/health":
            self._send(200, b'{"ok":true}', "application/json")
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):
        if urlparse(self.path).path != "/approve":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        fields = parse_qs(self.rfile.read(length).decode("utf-8"))
        draft_id = (fields.get("id") or [""])[0]
        draft = find_draft(self.cfg, draft_id)
        if draft is not None and draft.status == STATUS_PENDING:
            draft.meta["status"] = STATUS_APPROVED
            write_draft(draft)
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()


def serve(cfg: Config, host="127.0.0.1", port=8765, open_once=False) -> int:
    Handler.cfg = cfg
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"shiplog review dashboard: http://{host}:{port}")
    print("Approve a draft there, then run `publish`. Ctrl-C to stop.")
    try:
        if open_once:
            httpd.handle_request()
        else:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
    return 0
