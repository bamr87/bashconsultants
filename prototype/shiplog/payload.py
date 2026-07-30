"""Draft -> LinkedIn Posts API payload.

One function, no side effects, no network. `preview` prints exactly what
`publish` would send, which is what makes the tool auditable: a developer can
read the request before granting it, and a reviewer can read it without
running anything.

Author identity is the only structural difference between the two cases the
tool supports:

- a developer's own profile — `urn:li:person:{id}`, scope `w_member_social`
- an organization page      — `urn:li:organization:{id}`, scope `w_organization_social`
"""

from __future__ import annotations

from core import Config, Draft

API_PATH = "/rest/posts"


def scope_for(cfg: Config) -> str:
    return (
        "w_organization_social"
        if cfg.author_kind == "organization"
        else "w_member_social"
    )


def build(cfg: Config, draft: Draft) -> dict:
    """The exact JSON body of the POST that publishes this draft."""
    author = str(draft.meta.get("author") or cfg.author_urn())
    return {
        "author": author,
        "commentary": draft.body,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }


def describe(cfg: Config, draft: Draft) -> str:
    """A one-line summary of the call, for logs and the dashboard."""
    return f"POST {API_PATH} as {draft.meta.get('author') or cfg.author_urn()} ({scope_for(cfg)})"
