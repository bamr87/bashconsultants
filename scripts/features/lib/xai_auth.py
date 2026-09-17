#!/usr/bin/env python3
"""xAI OAuth credentials for the preview-image generator: acquisition, storage, rotation.

Ported from bamr87/law-ai ``backend/law_ai/core/xai_oauth.py`` (spec 050, ADR 0007),
which itself ports the flow Kilo Code ships in the open. xAI documents only an
API key for ``https://api.x.ai/v1``; the subscription OAuth flow below reuses
the public Grok-CLI desktop client that xAI's auth server allowlists.

Two grants, one credential store:

* **Device code** (RFC 8628) is the default. It needs no inbound path to this
  process, so it works from a laptop, a VPS, or a container alike.
* **Loopback PKCE** is the opt-in for a host with a browser. The redirect URI is
  part of the client registration (``127.0.0.1:56121``) and cannot be moved.

``resolve()`` is what the generator calls. It walks the credential chain and
stops at the first hit:

1. ``XAI_OAUTH_TOKEN``
2. This repo's store (``.xai/credentials.json``, written by
   ``scripts/features/xai-login``), refreshed under a cross-process lock when
   the access token is due; ``XAI_REFRESH_TOKEN`` seeds it when no file exists
3. The Grok CLI store (``~/.grok/auth.json`` from ``grok login``)
4. Kilo's xAI login (``~/.local/share/kilo/auth.json``), refreshed when expired
5. ``XAI_API_KEY``, pay-per-use, last

Nothing here logs a token: error messages carry status codes and server error
bodies only, the callback server's access log is silenced, and the store is
written atomically at mode 0600. Standard library only, so it runs wherever
the generator runs.

Command line (used by the bash generator)::

    python3 scripts/features/lib/xai_auth.py resolve [--force-refresh]
    python3 scripts/features/lib/xai_auth.py status
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import json
import math
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Optional

try:  # POSIX only; the lock degrades to best effort elsewhere
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[3]

#: Public Grok-CLI desktop client. xAI's auth server rejects this flow from
#: non-allowlisted clients, so, like every other open implementation, we reuse
#: the client id xAI ships for desktop OAuth rather than registering our own.
#: xAI can revoke it at any time; that degrades to an ordinary provider failure.
CLIENT_ID = "b1a00492-073a-47ea-816f-4c329264a828"
SCOPE = "openid profile email offline_access grok-cli:access api:access"

DEVICE_CODE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"

#: The loopback redirect is part of the client's registration, so the host and
#: port are not ours to choose.
OAUTH_HOST = "127.0.0.1"
OAUTH_PORT = 56121
OAUTH_REDIRECT_PATH = "/callback"
REDIRECT_URI = f"http://{OAUTH_HOST}:{OAUTH_PORT}{OAUTH_REDIRECT_PATH}"

#: Refresh a little before the token actually dies so a long image request does
#: not have to recover from a mid-flight 401.
ACCESS_TOKEN_REFRESH_SKEW_S = 120.0

# Device-code polling bounds (RFC 8628 section 3.5).
DEVICE_DEFAULT_INTERVAL_S = 5.0
DEVICE_MIN_INTERVAL_S = 1.0
DEVICE_SLOW_DOWN_INCREMENT_S = 5.0
DEVICE_DEFAULT_EXPIRES_S = 300.0

TOKEN_REQUEST_TIMEOUT_S = 30.0
LOOPBACK_TIMEOUT_S = 300.0

USER_AGENT = "bash-365-preview-images"
REFERRER = "bash-365"

DEFAULT_AUTH_BASE_URL = "https://auth.x.ai"
DEFAULT_API_BASE_URL = "https://api.x.ai/v1"
DEFAULT_CREDENTIALS_PATH = REPO_ROOT / ".xai" / "credentials.json"

NO_CREDENTIAL_MESSAGE = (
    "no xAI credential. Run scripts/features/xai-login, set XAI_OAUTH_TOKEN, "
    "or set XAI_API_KEY"
)


class XaiAuthError(RuntimeError):
    """Raised when no usable xAI credential can be obtained. Never carries a token."""


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


def load_dotenv(path: Optional[Path] = None) -> None:
    """Load ``KEY=value`` lines from the repo's ``.env`` into the environment.

    Explicit environment variables win: a key that is already set is left
    alone. Quotes around a value are stripped, comments and blank lines skipped.
    """
    file = path or (REPO_ROOT / ".env")
    try:
        lines = file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[key] = value


def auth_base_url() -> str:
    return (os.environ.get("XAI_AUTH_BASE_URL") or DEFAULT_AUTH_BASE_URL).rstrip("/")


def api_base_url() -> str:
    return (os.environ.get("XAI_BASE_URL") or DEFAULT_API_BASE_URL).rstrip("/")


def authorize_url() -> str:
    return f"{auth_base_url()}/oauth2/authorize"


def token_url() -> str:
    return f"{auth_base_url()}/oauth2/token"


def legacy_token_url() -> str:
    """The pre-``oauth2`` path some clients still hit; tried only on a 404."""
    return f"{auth_base_url()}/oauth/token"


def device_authorization_url() -> str:
    return f"{auth_base_url()}/oauth2/device/code"


def _form_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }


# ---------------------------------------------------------------------------
# HTTP (one seam, so the tests never touch the network)
# ---------------------------------------------------------------------------


def _http_post_form(
    url: str, data: dict[str, str], timeout: float = TOKEN_REQUEST_TIMEOUT_S
) -> tuple[int, str]:
    """POST a form body and return ``(status, text)``; HTTP errors are returned, not raised."""
    body = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers=_form_headers())
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return int(err.code), err.read().decode("utf-8", "replace")
    except urllib.error.URLError as err:
        raise XaiAuthError(f"cannot reach {url}: {err.reason}") from err


def _http_get(url: str, token: str, timeout: float = TOKEN_REQUEST_TIMEOUT_S) -> tuple[int, str]:
    """GET with a bearer token and return ``(status, text)``."""
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status), response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return int(err.code), err.read().decode("utf-8", "replace")
    except urllib.error.URLError as err:
        raise XaiAuthError(f"cannot reach {url}: {err.reason}") from err


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        body = json.loads(text) if text else {}
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


# ---------------------------------------------------------------------------
# JWT helper: scheduling only, never a trust decision
# ---------------------------------------------------------------------------


def jwt_claims(token: str) -> Optional[dict[str, Any]]:
    """Decode a JWT payload **without** verifying the signature.

    The only thing these claims decide is whether to refresh early; someone
    able to forge them wins nothing but an unnecessary token request.
    """
    parts = str(token or "").split(".")
    if len(parts) < 2:
        return None
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        claims = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except Exception:
        return None
    return claims if isinstance(claims, dict) else None


def jwt_is_expiring(token: str, skew_s: float = ACCESS_TOKEN_REFRESH_SKEW_S) -> bool:
    """True iff *token* is a JWT whose ``exp`` falls inside the skew window."""
    claims = jwt_claims(token)
    exp = claims.get("exp") if claims else None
    if not isinstance(exp, (int, float)):
        return False
    return float(exp) <= time.time() + max(0.0, skew_s)


def positive_seconds(value: Any, default: float) -> float:
    """Normalize a server-supplied seconds value, rejecting NaN, None, and negatives.

    Without this a NaN interval slips through ``or default`` (NaN is a float),
    reaches ``sleep(NaN)``, and busy-loops until the hard deadline.
    """
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(seconds) or seconds <= 0:
        return default
    return seconds


# ---------------------------------------------------------------------------
# Credential store
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Credentials:
    """One xAI OAuth credential set. ``expires_at`` is a Unix timestamp."""

    access: str
    refresh: str
    expires_at: float

    def is_expiring(self, skew_s: float = ACCESS_TOKEN_REFRESH_SKEW_S) -> bool:
        """True when this credential should be refreshed before the next call.

        Two independent signals, because neither is reliable alone: the stored
        deadline (xAI does not always return ``expires_in``) and the access
        token's own ``exp`` claim (absent on opaque tokens).
        """
        if self.expires_at <= time.time() + max(0.0, skew_s):
            return True
        return jwt_is_expiring(self.access, skew_s)


def credentials_path() -> Path:
    """Where the rotating credential set lives (``XAI_CREDENTIALS_PATH``).

    A relative override resolves against the repo root, so the same value
    works from any working directory.
    """
    configured = (os.environ.get("XAI_CREDENTIALS_PATH") or "").strip()
    if not configured:
        return DEFAULT_CREDENTIALS_PATH
    path = Path(configured).expanduser()
    return path if path.is_absolute() else REPO_ROOT / path


def _env_seed() -> Optional[Credentials]:
    """Credentials supplied by the environment, for hosts without a file.

    The file, once written, wins: it is the one that stays current as xAI
    rotates the refresh token. A seeded pair carries no deadline, so the first
    use refreshes and writes a real file with a real expiry.
    """
    refresh = (os.environ.get("XAI_REFRESH_TOKEN") or "").strip()
    if not refresh:
        return None
    access = (os.environ.get("XAI_ACCESS_TOKEN") or "").strip()
    return Credentials(access=access, refresh=refresh, expires_at=0.0)


def load_credentials() -> Optional[Credentials]:
    """Read the stored credential set, falling back to the environment seed."""
    try:
        raw = json.loads(credentials_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _env_seed()
    if not isinstance(raw, dict):
        return _env_seed()
    refresh = str(raw.get("refresh") or "")
    if not refresh:
        return _env_seed()
    try:
        expires_at = float(raw.get("expires_at") or 0.0)
    except (TypeError, ValueError):
        expires_at = 0.0
    return Credentials(access=str(raw.get("access") or ""), refresh=refresh, expires_at=expires_at)


def save_credentials(creds: Credentials) -> Path:
    """Persist *creds* atomically at mode 0600.

    Written to a temp file in the same directory and ``os.replace``d, so a
    crash mid-write can never leave a half-token behind for another process.
    """
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    payload = {"access": creds.access, "refresh": creds.refresh, "expires_at": creds.expires_at}
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path


def delete_credentials() -> bool:
    """Remove the store. Returns True when a file was deleted."""
    path = credentials_path()
    try:
        path.unlink()
    except FileNotFoundError:
        return False
    with contextlib.suppress(OSError):
        _lock_path().unlink()
    return True


def is_configured() -> bool:
    return load_credentials() is not None


def unconfigured_reason() -> Optional[str]:
    if is_configured():
        return None
    return "no stored xAI credentials (run scripts/features/xai-login, or set XAI_REFRESH_TOKEN)"


# ---------------------------------------------------------------------------
# Token responses and refresh (cross-process single-flight)
# ---------------------------------------------------------------------------


def _post_token(data: dict[str, str]) -> dict[str, Any]:
    """POST the token endpoint and return the parsed body.

    Error bodies are surfaced without the request form, so a refresh token can
    never reach a log line through an exception message.
    """
    status, text = _http_post_form(token_url(), data)
    if status == 404:
        status, text = _http_post_form(legacy_token_url(), data)
    if status >= 400:
        detail = text[:200] if text else ""
        raise XaiAuthError(
            f"xAI token request failed ({status})" + (f": {detail}" if detail else "")
        )
    body = _parse_json_object(text)
    if not body:
        raise XaiAuthError("xAI token response was not a JSON object")
    return body


def _credentials_from_token_response(
    body: dict[str, Any], *, previous_refresh: str = ""
) -> Credentials:
    """Build a credential set from a token response, keeping the old refresh
    token when xAI did not rotate one in."""
    access = str(body.get("access_token") or "")
    if not access:
        raise XaiAuthError("xAI token response carried no access_token")
    refresh = str(body.get("refresh_token") or "") or previous_refresh
    if not refresh:
        raise XaiAuthError("xAI token response carried no refresh_token")
    expires_in = positive_seconds(body.get("expires_in"), 3600.0)
    return Credentials(access=access, refresh=refresh, expires_at=time.time() + expires_in)


def _lock_path() -> Path:
    # A sibling lock file, never the credentials file itself: save_credentials
    # replaces that path, so a lock held on its inode would guard nothing.
    path = credentials_path()
    return path.with_name(f"{path.name}.lock")


def _acquire_lock() -> Any:
    """Take the exclusive cross-process refresh lock (blocking)."""
    lock_file = _lock_path()
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_file, "a+")  # noqa: SIM115 - released by _release_lock
    if fcntl is not None:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except OSError:
            handle.close()
            raise
    return handle


def _release_lock(handle: Any) -> None:
    if fcntl is not None:
        with contextlib.suppress(OSError):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    with contextlib.suppress(OSError):
        handle.close()


def refresh_credentials(
    current: Credentials, *, stale_access: Optional[str] = None
) -> Credentials:
    """Exchange the refresh token for a new pair and persist the result.

    xAI **rotates** the refresh token on every use, so the old one is dead the
    moment this returns. The exclusive file lock is what stops two generator
    workers from each spending the same token and invalidating the other;
    whoever loses the race re-reads under the lock and takes the winner's
    fresh credential instead of replaying a consumed one.

    ``stale_access`` names a token the caller has just seen rejected (a 401).
    That is the case where "the stored credential still looks valid" is
    exactly wrong, so the freshness shortcut becomes "did somebody else already
    replace *this* token?" rather than "does the stored one look unexpired?".
    """
    handle = _acquire_lock()
    try:
        stored = load_credentials()
        if stored is not None:
            if stale_access is not None:
                if stored.access and stored.access != stale_access:
                    return stored  # another process rotated after our 401
            elif not stored.is_expiring():
                return stored  # another process refreshed while we waited
        source = stored or current
        body = _post_token(
            {
                "grant_type": "refresh_token",
                "refresh_token": source.refresh,
                "client_id": CLIENT_ID,
            }
        )
        refreshed = _credentials_from_token_response(body, previous_refresh=source.refresh)
        save_credentials(refreshed)
        return refreshed
    finally:
        _release_lock(handle)


def access_token(*, stale_access: Optional[str] = None) -> str:
    """Return a usable access token from the repo store, refreshing when due."""
    creds = load_credentials()
    if creds is None:
        raise XaiAuthError(unconfigured_reason() or "no stored xAI credentials")
    if stale_access is not None or creds.is_expiring():
        creds = refresh_credentials(creds, stale_access=stale_access)
    if not creds.access:
        raise XaiAuthError("xAI credential has no access token")
    return creds.access


# ---------------------------------------------------------------------------
# Device-code grant (RFC 8628): the default
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeviceCode:
    """The device-authorization response the operator acts on."""

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: Optional[str] = None
    expires_in: Any = None
    interval: Any = None

    @property
    def browser_url(self) -> str:
        """The URL to open: the pre-filled one when xAI supplied it."""
        return self.verification_uri_complete or self.verification_uri


def request_device_code() -> DeviceCode:
    """Start the device-authorization grant."""
    status, text = _http_post_form(
        device_authorization_url(), {"client_id": CLIENT_ID, "scope": SCOPE}
    )
    if status >= 400:
        raise XaiAuthError(
            f"xAI device code request failed ({status})" + (f": {text[:200]}" if text else "")
        )
    body = _parse_json_object(text)
    if not body:
        raise XaiAuthError("xAI device code response was not a JSON object")
    missing = [key for key in ("device_code", "user_code", "verification_uri") if not body.get(key)]
    if missing:
        raise XaiAuthError("xAI device code response is missing " + ", ".join(sorted(missing)))
    return DeviceCode(
        device_code=str(body["device_code"]),
        user_code=str(body["user_code"]),
        verification_uri=str(body["verification_uri"]),
        verification_uri_complete=(
            str(body["verification_uri_complete"]) if body.get("verification_uri_complete") else None
        ),
        expires_in=body.get("expires_in"),
        interval=body.get("interval"),
    )


def poll_device_token(
    device: DeviceCode,
    *,
    sleep: Optional[Callable[[float], None]] = None,
    now: Optional[Callable[[], float]] = None,
) -> Credentials:
    """Poll the token endpoint until the operator approves (RFC 8628 section 3.5).

    ``authorization_pending`` keeps the current interval, ``slow_down`` widens
    it, and everything else is terminal. ``sleep`` and ``now`` are injectable
    so the tests exercise every branch without real waits.
    """
    _sleep = sleep or time.sleep
    _now = now or time.monotonic
    deadline = _now() + positive_seconds(device.expires_in, DEVICE_DEFAULT_EXPIRES_S)
    interval = max(positive_seconds(device.interval, DEVICE_DEFAULT_INTERVAL_S), DEVICE_MIN_INTERVAL_S)

    while _now() < deadline:
        status, text = _http_post_form(
            token_url(),
            {
                "grant_type": DEVICE_CODE_GRANT_TYPE,
                "client_id": CLIENT_ID,
                "device_code": device.device_code,
            },
        )
        if status < 400:
            creds = _credentials_from_token_response(_parse_json_object(text))
            save_credentials(creds)
            return creds

        error_body = _parse_json_object(text)
        error = str(error_body.get("error") or "")
        if error == "authorization_pending":
            _sleep(min(interval, max(0.0, deadline - _now())))
            continue
        if error == "slow_down":
            interval += DEVICE_SLOW_DOWN_INCREMENT_S
            _sleep(min(interval, max(0.0, deadline - _now())))
            continue
        if error in {"access_denied", "authorization_denied"}:
            raise XaiAuthError("xAI device authorization was denied")
        if error == "expired_token":
            raise XaiAuthError("xAI device code expired; run the login again")
        detail = str(error_body.get("error_description") or error or "")
        raise XaiAuthError(
            f"xAI device token exchange failed ({status})" + (f": {detail}" if detail else "")
        )

    raise XaiAuthError("xAI device authorization timed out")


# ---------------------------------------------------------------------------
# Loopback PKCE grant: opt-in, for a host with a browser
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Pkce:
    verifier: str
    challenge: str


def generate_pkce() -> Pkce:
    verifier = secrets.token_urlsafe(64)[:64]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return Pkce(verifier=verifier, challenge=challenge)


def build_authorize_url(pkce: Pkce, state: str, nonce: str) -> str:
    """Assemble the consent URL.

    ``plan=generic`` opts the consent screen into xAI's generic OAuth plan
    tier; without it the auth server rejects loopback OAuth from this client.
    ``referrer`` is best-effort attribution in xAI's own logs.
    """
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "code_challenge": pkce.challenge,
        "code_challenge_method": "S256",
        "state": state,
        "nonce": nonce,
        "plan": "generic",
        "referrer": REFERRER,
    }
    return f"{authorize_url()}?{urllib.parse.urlencode(params)}"


class _CallbackHandler(BaseHTTPRequestHandler):
    """Captures ``?code=&state=`` on the redirect path and closes the page."""

    code: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    #: True once a request actually reached the redirect path, so a stray hit
    #: on another path cannot be mistaken for the callback we are waiting on.
    received: bool = False

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != OAUTH_REDIRECT_PATH:
            self.send_response(404)
            self.end_headers()
            return
        _CallbackHandler.received = True
        query = urllib.parse.parse_qs(parsed.query)

        def first(key: str) -> Optional[str]:
            values = query.get(key)
            return values[0] if values else None

        _CallbackHandler.code = first("code")
        _CallbackHandler.state = first("state")
        _CallbackHandler.error = first("error")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<!doctype html><title>BASH preview images</title>"
            b"<p>xAI authorization received. You can close this window.</p>"
        )

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Silence the default stderr access log: the query string carries the
        # authorization code.
        return


def _serve_one_callback(
    timeout_s: float, *, port: Optional[int] = None
) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Serve the loopback port until the OAuth callback arrives, or time out.

    Not literally one request: a stray hit on another path (a browser
    prefetch, a favicon fetch) answers 404 and must not consume the slot the
    login is waiting on, so the loop keeps serving until a request actually
    reaches the redirect path.
    """
    _CallbackHandler.code = None
    _CallbackHandler.state = None
    _CallbackHandler.error = None
    _CallbackHandler.received = False
    address = (OAUTH_HOST, OAUTH_PORT if port is None else port)
    server = HTTPServer(address, _CallbackHandler)
    deadline = time.monotonic() + timeout_s
    try:
        while not _CallbackHandler.received:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            server.timeout = remaining
            server.handle_request()
    finally:
        server.server_close()
    return _CallbackHandler.code, _CallbackHandler.state, _CallbackHandler.error


def loopback_login(
    *,
    open_browser: Optional[Callable[[str], Any]] = None,
    port: Optional[int] = None,
    timeout_s: Optional[float] = None,
) -> tuple[str, Credentials]:
    """Run the loopback PKCE grant, returning the consent URL and the tokens.

    The URL is returned as well as opened so a caller can print it: the whole
    point of this path is that the operator may be looking at a different
    screen than the one this process can reach.
    """
    pkce = generate_pkce()
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    url = build_authorize_url(pkce, state, nonce)

    if open_browser is not None:
        open_browser(url)

    code, returned_state, error = _serve_one_callback(
        LOOPBACK_TIMEOUT_S if timeout_s is None else timeout_s, port=port
    )
    if error:
        raise XaiAuthError(f"xAI authorization failed: {error}")
    if not code:
        raise XaiAuthError("xAI authorization timed out waiting for the callback")
    if returned_state != state:
        # A mismatched state means the callback did not come from the request
        # we started; treating it as ours would be the CSRF this check exists
        # to prevent.
        raise XaiAuthError("xAI authorization state mismatch; refusing the callback")

    body = _post_token(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "code_verifier": pkce.verifier,
        }
    )
    creds = _credentials_from_token_response(body)
    save_credentials(creds)
    return url, creds


# ---------------------------------------------------------------------------
# Other people's stores: the Grok CLI and Kilo
# ---------------------------------------------------------------------------


def _read_store(path: Path) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _expiry_seconds(value: Any, claims: Optional[dict[str, Any]]) -> float:
    """Stores keep ``expires`` in seconds or milliseconds; JWTs keep ``exp``."""
    if isinstance(value, (int, float)) and value:
        return float(value) / 1000 if value > 1e12 else float(value)
    exp = (claims or {}).get("exp")
    return float(exp) if isinstance(exp, (int, float)) else 0.0


def grok_store_path() -> Path:
    return Path(os.environ.get("GROK_AUTH_PATH") or Path.home() / ".grok" / "auth.json")


def kilo_store_path() -> Path:
    if os.environ.get("KILO_AUTH_PATH"):
        return Path(os.environ["KILO_AUTH_PATH"])
    xdg = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(xdg) / "kilo" / "auth.json"


def grok_store_token() -> Optional[str]:
    """The official Grok CLI store: ``{"https://auth.x.ai::<client>": {"key": ...}}``."""
    store = _read_store(grok_store_path())
    if not store:
        return None
    rows = list(store.items())
    hit = next((r for r in rows if "auth.x.ai" in r[0]), None) or next(
        (r for r in rows if "accounts.x.ai" in r[0]), None
    )
    if not hit:
        return None
    _scope, value = hit
    record = value if isinstance(value, dict) else {"key": value}
    access = record.get("key") or record.get("access") or record.get("access_token")
    if not access:
        return None
    exp = _expiry_seconds(record.get("expires"), jwt_claims(str(access)))
    if not exp or exp - 60 > time.time():
        return str(access)
    return None


def kilo_store_token() -> tuple[Optional[str], str]:
    """Kilo's ``{"xai": {"access", "refresh", "expires", "client_id"}}`` slot.

    Returns ``(token, source)``; refreshes and rewrites the store when the
    access token has expired and a refresh token is present.
    """
    path = kilo_store_path()
    store = _read_store(path)
    slot = store.get("xai") if store else None
    if not isinstance(slot, dict) or not (slot.get("access") or slot.get("refresh")):
        return None, ""
    claims = jwt_claims(str(slot.get("access") or ""))
    exp = _expiry_seconds(slot.get("expires"), claims)
    if slot.get("access") and exp - 60 > time.time():
        return str(slot["access"]), "kilo-auth"
    if not slot.get("refresh"):
        raise XaiAuthError("the xAI token in the Kilo store is expired and has no refresh token; re-login via Kilo")
    client_id = slot.get("client_id") or (claims or {}).get("client_id") or (claims or {}).get("aud")
    if isinstance(client_id, list):
        client_id = client_id[0] if client_id else None
    if not client_id:
        raise XaiAuthError("the xAI token in the Kilo store is expired and carries no client_id to refresh with; re-login via Kilo")
    body = _post_token(
        {"grant_type": "refresh_token", "refresh_token": str(slot["refresh"]), "client_id": str(client_id)}
    )
    if not body.get("access_token"):
        raise XaiAuthError("xAI OAuth refresh returned no access_token")
    ttl = positive_seconds(body.get("expires_in"), 3600.0)
    renewed = dict(slot)
    renewed.update(
        {
            "type": "oauth",
            "access": body["access_token"],
            "refresh": body.get("refresh_token") or slot["refresh"],
            "expires": int((time.time() + ttl) * 1000),
            "client_id": client_id,
        }
    )
    assert store is not None
    store["xai"] = renewed
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return str(renewed["access"]), "kilo-auth-refresh"


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------


def resolve(*, force_refresh: bool = False, warn: Optional[Callable[[str], None]] = None) -> dict[str, str]:
    """Walk the credential chain and return ``{"token", "source", "mode"}``.

    ``force_refresh`` is the post-401 path: the repo store's access token is
    treated as stale even when its deadline says otherwise. A repo store whose
    refresh fails is reported through ``warn`` and the chain continues, so a
    revoked subscription token never hides a working API key.
    """
    _warn = warn or (lambda message: print(f"[xai-auth] {message}", file=sys.stderr))

    explicit = (os.environ.get("XAI_OAUTH_TOKEN") or "").strip()
    if explicit:
        return {"token": explicit, "source": "XAI_OAUTH_TOKEN", "mode": "oauth"}

    creds = load_credentials()
    if creds is not None:
        try:
            if force_refresh or creds.is_expiring():
                creds = refresh_credentials(creds, stale_access=creds.access if force_refresh else None)
            if creds.access:
                return {"token": creds.access, "source": "xai-login", "mode": "oauth"}
        except XaiAuthError as err:
            _warn(f"stored xAI credential could not be refreshed ({err}); trying other sources")

    grok = grok_store_token()
    if grok:
        return {"token": grok, "source": "grok-auth", "mode": "oauth"}

    kilo, source = kilo_store_token()
    if kilo:
        return {"token": kilo, "source": source, "mode": "oauth"}

    key = (os.environ.get("XAI_API_KEY") or "").strip()
    if key:
        return {"token": key, "source": "XAI_API_KEY", "mode": "api_key"}

    raise XaiAuthError(NO_CREDENTIAL_MESSAGE)


def status() -> dict[str, Any]:
    """Describe the repo store without exposing token values."""
    path = credentials_path()
    creds = load_credentials()
    report: dict[str, Any] = {
        "path": str(path),
        "file_present": path.is_file(),
        "configured": creds is not None,
    }
    if creds is None:
        report["reason"] = unconfigured_reason()
        return report
    report["access_present"] = bool(creds.access)
    report["expires_in_s"] = int(creds.expires_at - time.time())
    report["refresh_due"] = creds.is_expiring()
    return report


def probe_models(token: str) -> dict[str, Any]:
    """List the model ids the credential can see, for a post-login check.

    Both listing endpoints are tried; either may be allowlisted per account, so
    a failure on one is informational and never fatal.
    """
    report: dict[str, Any] = {}
    for name, path in (("models", "/models"), ("image_models", "/image-generation-models")):
        try:
            code, text = _http_get(f"{api_base_url()}{path}", token)
        except XaiAuthError as err:
            report[name] = {"status": None, "error": str(err)}
            continue
        body = _parse_json_object(text)
        rows = body.get("data") if isinstance(body.get("data"), list) else body.get("models")
        ids = [str(row.get("id")) for row in rows if isinstance(row, dict) and row.get("id")] if isinstance(rows, list) else []
        report[name] = {"status": code, "ids": ids}
    return report


def configured_image_model() -> str:
    """The ``xai_model`` the generator will use, read the way the bash script reads it."""
    default = "grok-imagine-image-2.0"
    override = (os.environ.get("XAI_IMAGE_MODEL") or "").strip()
    if override:
        return override
    try:
        lines = (REPO_ROOT / "_config.yml").read_text(encoding="utf-8").splitlines()
    except OSError:
        return default
    in_section = False
    for line in lines:
        if line.startswith("preview_images:"):
            in_section = True
            continue
        if in_section and line and not line[0].isspace():
            break
        if in_section:
            stripped = line.strip()
            if stripped.startswith("xai_model"):
                _key, _sep, value = stripped.partition(":")
                value = value.split("#", 1)[0].strip().strip("'\"")
                return value or default
    return default


# ---------------------------------------------------------------------------
# Command line (what the bash generator calls)
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="xAI credential chain for the preview generator")
    sub = parser.add_subparsers(dest="command", required=True)
    resolve_cmd = sub.add_parser("resolve", help="print {token, source, mode} as JSON")
    resolve_cmd.add_argument(
        "--force-refresh",
        action="store_true",
        help="treat the stored access token as rejected (after a 401) and refresh it",
    )
    sub.add_parser("status", help="describe the repo store without printing token values")
    args = parser.parse_args(argv)
    load_dotenv()

    if args.command == "status":
        print(json.dumps(status(), indent=2))
        return 0
    try:
        print(json.dumps(resolve(force_refresh=args.force_refresh)))
    except XaiAuthError as err:
        print(str(err), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
