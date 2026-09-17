"""Tests for the xAI credential lifecycle behind ``--provider xai``.

Standard library only, no network: every token call goes through the
``_http_post_form`` seam. Run from the repo root::

    python3 -m unittest scripts/features/lib/test_xai_auth.py

What matters here is the credential contract ported from law-ai spec 050: the
RFC 8628 polling branches, atomic 0600 storage, the resolve chain order, and
the one that bites in production, that a rotated refresh token is persisted
and never replayed.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import stat
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import xai_auth  # noqa: E402


def _jwt(exp: float) -> str:
    """A JWT-shaped token with the given ``exp``; the signature is junk."""
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode()
    return f"header.{payload.rstrip('=')}.signature"


class _Clock:
    """Monotonic stand-in that only advances when the polled sleep is called."""

    def __init__(self) -> None:
        self.t = 0.0
        self.slept: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.t += max(seconds, 0.001)


def _responses(*items: tuple[int, dict[str, Any]]) -> Callable[..., tuple[int, str]]:
    queue = list(items)

    def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
        status, body = queue.pop(0)
        return status, json.dumps(body)

    return handler


class _StoreCase(unittest.TestCase):
    """Every test gets an isolated store and a scrubbed environment."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = Path(self._tmp.name) / "xai" / "credentials.json"
        self._env = mock.patch.dict(
            os.environ,
            {
                "XAI_CREDENTIALS_PATH": str(self.store),
                "XAI_OAUTH_TOKEN": "",
                "XAI_API_KEY": "",
                "XAI_ACCESS_TOKEN": "",
                "XAI_REFRESH_TOKEN": "",
                "GROK_AUTH_PATH": str(Path(self._tmp.name) / "grok.json"),
                "KILO_AUTH_PATH": str(Path(self._tmp.name) / "kilo.json"),
                "XAI_AUTH_BASE_URL": "https://auth.test",
            },
        )
        self._env.start()

    def tearDown(self) -> None:
        self._env.stop()
        self._tmp.cleanup()


# ---------------------------------------------------------------------------
# Credential store
# ---------------------------------------------------------------------------


class TestCredentialStore(_StoreCase):
    def test_round_trip(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("a", "r", time.time() + 3600))
        loaded = xai_auth.load_credentials()
        assert loaded is not None
        self.assertEqual((loaded.access, loaded.refresh), ("a", "r"))

    def test_file_is_owner_only(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("a", "r", 0.0))
        self.assertEqual(stat.S_IMODE(self.store.stat().st_mode), 0o600)

    def test_missing_file_is_unconfigured(self) -> None:
        self.assertIsNone(xai_auth.load_credentials())
        self.assertFalse(xai_auth.is_configured())
        self.assertIn("xai-login", xai_auth.unconfigured_reason() or "")

    def test_environment_seed_is_used_when_no_file(self) -> None:
        with mock.patch.dict(os.environ, {"XAI_REFRESH_TOKEN": "seeded"}):
            loaded = xai_auth.load_credentials()
        assert loaded is not None
        self.assertEqual(loaded.refresh, "seeded")
        # A seeded pair carries no deadline, so it must refresh before first use.
        self.assertTrue(loaded.is_expiring())

    def test_corrupt_file_falls_back_to_seed(self) -> None:
        self.store.parent.mkdir(parents=True)
        self.store.write_text("{not json", encoding="utf-8")
        with mock.patch.dict(os.environ, {"XAI_REFRESH_TOKEN": "seeded"}):
            loaded = xai_auth.load_credentials()
        assert loaded is not None
        self.assertEqual(loaded.refresh, "seeded")

    def test_relative_path_resolves_against_the_repo_root(self) -> None:
        with mock.patch.dict(os.environ, {"XAI_CREDENTIALS_PATH": ".xai/creds.json"}):
            self.assertEqual(xai_auth.credentials_path(), xai_auth.REPO_ROOT / ".xai" / "creds.json")

    def test_logout_removes_the_store(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("a", "r", 0.0))
        self.assertTrue(xai_auth.delete_credentials())
        self.assertFalse(self.store.exists())
        self.assertFalse(xai_auth.delete_credentials())


class TestExpiry(unittest.TestCase):
    def test_stored_deadline_drives_refresh(self) -> None:
        self.assertTrue(xai_auth.Credentials("a", "r", time.time() + 5).is_expiring())
        self.assertFalse(xai_auth.Credentials("a", "r", time.time() + 9999).is_expiring())

    def test_jwt_exp_wins_over_an_optimistic_deadline(self) -> None:
        creds = xai_auth.Credentials(_jwt(time.time() + 5), "r", time.time() + 9999)
        self.assertTrue(creds.is_expiring())

    def test_opaque_token_defers_to_stored_deadline(self) -> None:
        self.assertFalse(xai_auth.Credentials("not-a-jwt", "r", time.time() + 9999).is_expiring())

    def test_garbage_seconds_fall_back_to_the_default(self) -> None:
        self.assertEqual(xai_auth.positive_seconds(float("nan"), 5.0), 5.0)
        self.assertEqual(xai_auth.positive_seconds(None, 5.0), 5.0)
        self.assertEqual(xai_auth.positive_seconds(-1, 5.0), 5.0)
        self.assertEqual(xai_auth.positive_seconds("7", 5.0), 7.0)


# ---------------------------------------------------------------------------
# Refresh and rotation
# ---------------------------------------------------------------------------


class TestRefresh(_StoreCase):
    def test_rotated_refresh_token_is_persisted(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("old", "r1", 0.0))
        seen: list[dict[str, str]] = []

        def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
            seen.append(dict(data))
            return 200, json.dumps({"access_token": "new", "refresh_token": "r2", "expires_in": 3600})

        with mock.patch.object(xai_auth, "_http_post_form", handler):
            token = xai_auth.access_token()

        self.assertEqual(token, "new")
        self.assertEqual(seen[0]["refresh_token"], "r1")
        self.assertEqual(seen[0]["client_id"], xai_auth.CLIENT_ID)
        stored = xai_auth.load_credentials()
        assert stored is not None
        self.assertEqual(stored.refresh, "r2")

    def test_response_without_rotation_keeps_old_refresh(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("old", "r1", 0.0))
        with mock.patch.object(
            xai_auth, "_http_post_form", _responses((200, {"access_token": "new", "expires_in": 60}))
        ):
            xai_auth.access_token()
        stored = xai_auth.load_credentials()
        assert stored is not None
        self.assertEqual(stored.refresh, "r1")

    def test_second_refresh_reuses_the_first_result(self) -> None:
        """The lock must collapse a concurrent refresh, not replay a dead token."""
        xai_auth.save_credentials(xai_auth.Credentials("old", "r1", 0.0))
        calls = 0

        def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
            nonlocal calls
            calls += 1
            return 200, json.dumps({"access_token": "new", "refresh_token": "r2", "expires_in": 3600})

        stale = xai_auth.Credentials("old", "r1", 0.0)
        with mock.patch.object(xai_auth, "_http_post_form", handler):
            xai_auth.refresh_credentials(stale)
            xai_auth.refresh_credentials(stale)
        self.assertEqual(calls, 1)

    def test_a_401_refreshes_past_a_credential_that_looks_valid(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("rejected", "r1", time.time() + 9999))
        with mock.patch.object(
            xai_auth,
            "_http_post_form",
            _responses((200, {"access_token": "new", "refresh_token": "r2", "expires_in": 3600})),
        ):
            token = xai_auth.access_token(stale_access="rejected")
        self.assertEqual(token, "new")

    def test_a_401_takes_another_process_rotation_without_spending_ours(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("theirs", "r9", time.time() + 9999))
        stale = xai_auth.Credentials("rejected", "r1", time.time() + 9999)
        with mock.patch.object(xai_auth, "_http_post_form", side_effect=AssertionError("no network")):
            fresh = xai_auth.refresh_credentials(stale, stale_access="rejected")
        self.assertEqual(fresh.access, "theirs")

    def test_rejected_refresh_raises_without_the_form(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("old", "dead-refresh-token", 0.0))
        with mock.patch.object(xai_auth, "_http_post_form", _responses((400, {"error": "invalid_grant"}))):
            with self.assertRaises(xai_auth.XaiAuthError) as ctx:
                xai_auth.access_token()
        self.assertIn("400", str(ctx.exception))
        self.assertNotIn("dead-refresh-token", str(ctx.exception))

    def test_a_404_falls_back_to_the_legacy_token_path(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("old", "r1", 0.0))
        urls: list[str] = []

        def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
            urls.append(url)
            if url.endswith("/oauth2/token"):
                return 404, ""
            return 200, json.dumps({"access_token": "new", "refresh_token": "r2", "expires_in": 60})

        with mock.patch.object(xai_auth, "_http_post_form", handler):
            xai_auth.access_token()
        self.assertEqual(urls, ["https://auth.test/oauth2/token", "https://auth.test/oauth/token"])

    def test_unconfigured_raises_rather_than_calling_out(self) -> None:
        with mock.patch.object(xai_auth, "_http_post_form", side_effect=AssertionError("no network")):
            with self.assertRaises(xai_auth.XaiAuthError):
                xai_auth.access_token()


# ---------------------------------------------------------------------------
# Device-code grant (RFC 8628 section 3.5)
# ---------------------------------------------------------------------------


def _device(**kw: Any) -> xai_auth.DeviceCode:
    return xai_auth.DeviceCode(
        device_code=kw.get("device_code", "dc"),
        user_code=kw.get("user_code", "ABCD-1234"),
        verification_uri=kw.get("verification_uri", "https://x.ai/device"),
        verification_uri_complete=kw.get("verification_uri_complete"),
        expires_in=kw.get("expires_in", 60),
        interval=kw.get("interval", 5),
    )


class TestDeviceCode(_StoreCase):
    def test_request_returns_the_operator_facing_fields(self) -> None:
        seen: list[dict[str, str]] = []

        def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
            seen.append(dict(data))
            return 200, json.dumps(
                {
                    "device_code": "dc",
                    "user_code": "WXYZ-9999",
                    "verification_uri": "https://x.ai/device",
                    "verification_uri_complete": "https://x.ai/device?code=WXYZ-9999",
                    "expires_in": 600,
                    "interval": 5,
                }
            )

        with mock.patch.object(xai_auth, "_http_post_form", handler):
            device = xai_auth.request_device_code()
        self.assertEqual(device.user_code, "WXYZ-9999")
        self.assertTrue(device.browser_url.endswith("?code=WXYZ-9999"))
        self.assertEqual(seen[0]["scope"], xai_auth.SCOPE)

    def test_request_reports_missing_fields(self) -> None:
        with mock.patch.object(xai_auth, "_http_post_form", _responses((200, {"device_code": "dc"}))):
            with self.assertRaises(xai_auth.XaiAuthError) as ctx:
                xai_auth.request_device_code()
        self.assertIn("user_code", str(ctx.exception))

    def test_pending_then_success_writes_the_store(self) -> None:
        clock = _Clock()
        handler = _responses(
            (400, {"error": "authorization_pending"}),
            (200, {"access_token": "a", "refresh_token": "r", "expires_in": 3600}),
        )
        with mock.patch.object(xai_auth, "_http_post_form", handler):
            creds = xai_auth.poll_device_token(_device(), sleep=clock.sleep, now=clock.now)
        self.assertEqual(creds.access, "a")
        stored = xai_auth.load_credentials()
        assert stored is not None
        self.assertEqual(stored.refresh, "r")

    def test_slow_down_widens_the_interval(self) -> None:
        clock = _Clock()
        handler = _responses(
            (400, {"error": "slow_down"}),
            (400, {"error": "authorization_pending"}),
            (200, {"access_token": "a", "refresh_token": "r", "expires_in": 60}),
        )
        with mock.patch.object(xai_auth, "_http_post_form", handler):
            xai_auth.poll_device_token(_device(interval=5), sleep=clock.sleep, now=clock.now)
        self.assertAlmostEqual(clock.slept[0], 10.0)  # 5 plus the 5s increment
        self.assertAlmostEqual(clock.slept[1], 10.0)  # stays widened

    def test_terminal_errors_raise(self) -> None:
        for error, message in (
            ("access_denied", "denied"),
            ("authorization_denied", "denied"),
            ("expired_token", "expired"),
        ):
            with self.subTest(error=error):
                clock = _Clock()
                with mock.patch.object(xai_auth, "_http_post_form", _responses((400, {"error": error}))):
                    with self.assertRaisesRegex(xai_auth.XaiAuthError, message):
                        xai_auth.poll_device_token(_device(), sleep=clock.sleep, now=clock.now)

    def test_deadline_gives_up(self) -> None:
        clock = _Clock()

        def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
            return 400, json.dumps({"error": "authorization_pending"})

        with mock.patch.object(xai_auth, "_http_post_form", handler):
            with self.assertRaisesRegex(xai_auth.XaiAuthError, "timed out"):
                xai_auth.poll_device_token(_device(expires_in=12, interval=5), sleep=clock.sleep, now=clock.now)

    def test_garbage_interval_does_not_busy_loop(self) -> None:
        clock = _Clock()
        handler = _responses(
            (400, {"error": "authorization_pending"}),
            (200, {"access_token": "a", "refresh_token": "r", "expires_in": 60}),
        )
        with mock.patch.object(xai_auth, "_http_post_form", handler):
            xai_auth.poll_device_token(_device(interval=float("nan")), sleep=clock.sleep, now=clock.now)
        self.assertGreaterEqual(clock.slept[0], 1.0)


# ---------------------------------------------------------------------------
# Loopback PKCE grant
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _callback_get(port: int, query: str, path: str = "/callback") -> int:
    """GET the loopback server, retrying until it is bound. Returns the status."""
    url = f"http://127.0.0.1:{port}{path}?{query}"
    deadline = time.monotonic() + 5
    while True:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return int(response.status)
        except urllib.error.HTTPError as err:
            code = int(err.code)
            err.close()
            return code
        except OSError:
            if time.monotonic() > deadline:
                raise
            time.sleep(0.02)


def _in_thread(fn: Callable[[], Any]) -> threading.Thread:
    # loopback_login calls open_browser before it binds the socket, so a
    # callback fired synchronously from open_browser would deadlock the very
    # server it is waiting on.
    thread = threading.Thread(target=fn, daemon=True)
    thread.start()
    return thread


def _state_of(url: str) -> str:
    return str(urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["state"][0])


class TestAuthorizeUrl(unittest.TestCase):
    def test_carries_pkce_and_the_generic_plan(self) -> None:
        pkce = xai_auth.generate_pkce()
        url = xai_auth.build_authorize_url(pkce, "state123", "nonce123")
        self.assertIn("code_challenge_method=S256", url)
        self.assertIn(f"code_challenge={pkce.challenge}", url)
        self.assertIn("plan=generic", url)
        self.assertIn("state=state123", url)
        self.assertIn(xai_auth.CLIENT_ID, url)

    def test_redirect_uri_is_the_registered_one(self) -> None:
        self.assertEqual(xai_auth.REDIRECT_URI, "http://127.0.0.1:56121/callback")


class TestLoopbackLogin(_StoreCase):
    def setUp(self) -> None:
        super().setUp()
        self.port = _free_port()

    @staticmethod
    def _token_ok(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
        return 200, json.dumps({"access_token": "a", "refresh_token": "r", "expires_in": 3600})

    def test_grant_exchanges_the_code_with_the_pkce_verifier(self) -> None:
        seen: dict[str, Any] = {}
        pkce: dict[str, Any] = {}
        real_generate = xai_auth.generate_pkce

        def spy() -> xai_auth.Pkce:
            pkce["value"] = real_generate()
            return pkce["value"]

        def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
            seen["form"] = dict(data)
            return self._token_ok(url, data)

        def open_browser(url: str) -> None:
            query = urllib.parse.urlencode({"code": "abc", "state": _state_of(url)})
            _in_thread(lambda: _callback_get(self.port, query))

        with mock.patch.object(xai_auth, "generate_pkce", spy), mock.patch.object(
            xai_auth, "_http_post_form", handler
        ):
            url, creds = xai_auth.loopback_login(open_browser=open_browser, port=self.port, timeout_s=5.0)

        self.assertTrue(url.startswith(xai_auth.authorize_url()))
        self.assertEqual(seen["form"]["grant_type"], "authorization_code")
        self.assertEqual(seen["form"]["code"], "abc")
        self.assertEqual(seen["form"]["code_verifier"], pkce["value"].verifier)
        self.assertEqual(creds.access, "a")
        self.assertEqual(stat.S_IMODE(self.store.stat().st_mode), 0o600)

    def test_state_mismatch_is_refused_without_spending_the_code(self) -> None:
        calls = 0

        def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
            nonlocal calls
            calls += 1
            return self._token_ok(url, data)

        def open_browser(url: str) -> None:
            query = urllib.parse.urlencode({"code": "abc", "state": "not-the-state"})
            _in_thread(lambda: _callback_get(self.port, query))

        with mock.patch.object(xai_auth, "_http_post_form", handler):
            with self.assertRaisesRegex(xai_auth.XaiAuthError, "state mismatch"):
                xai_auth.loopback_login(open_browser=open_browser, port=self.port, timeout_s=5.0)
        self.assertEqual(calls, 0)
        self.assertIsNone(xai_auth.load_credentials())

    def test_a_denied_consent_is_reported(self) -> None:
        def open_browser(url: str) -> None:
            _in_thread(lambda: _callback_get(self.port, urllib.parse.urlencode({"error": "access_denied"})))

        with mock.patch.object(xai_auth, "_http_post_form", self._token_ok):
            with self.assertRaisesRegex(xai_auth.XaiAuthError, "authorization failed"):
                xai_auth.loopback_login(open_browser=open_browser, port=self.port, timeout_s=5.0)

    def test_a_stray_request_does_not_consume_the_callback_slot(self) -> None:
        stray: list[int] = []

        def open_browser(url: str) -> None:
            query = urllib.parse.urlencode({"code": "abc", "state": _state_of(url)})

            def sequence() -> None:
                stray.append(_callback_get(self.port, "", path="/favicon.ico"))
                _callback_get(self.port, query)

            _in_thread(sequence)

        with mock.patch.object(xai_auth, "_http_post_form", self._token_ok):
            _url, creds = xai_auth.loopback_login(open_browser=open_browser, port=self.port, timeout_s=5.0)
        self.assertEqual(stray, [404])
        self.assertEqual(creds.access, "a")

    def test_no_callback_at_all_times_out(self) -> None:
        with self.assertRaisesRegex(xai_auth.XaiAuthError, "timed out"):
            xai_auth.loopback_login(port=self.port, timeout_s=0.3)


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------


class TestResolveChain(_StoreCase):
    def test_explicit_environment_token_wins(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("stored", "r", time.time() + 9999))
        with mock.patch.dict(os.environ, {"XAI_OAUTH_TOKEN": "explicit"}):
            info = xai_auth.resolve()
        self.assertEqual((info["token"], info["source"], info["mode"]), ("explicit", "XAI_OAUTH_TOKEN", "oauth"))

    def test_repo_store_comes_next_and_refreshes_when_due(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("old", "r1", 0.0))
        with mock.patch.object(
            xai_auth,
            "_http_post_form",
            _responses((200, {"access_token": "new", "refresh_token": "r2", "expires_in": 3600})),
        ):
            info = xai_auth.resolve()
        self.assertEqual((info["token"], info["source"]), ("new", "xai-login"))

    def test_force_refresh_rotates_a_token_that_looks_valid(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("rejected", "r1", time.time() + 9999))
        with mock.patch.object(
            xai_auth,
            "_http_post_form",
            _responses((200, {"access_token": "new", "refresh_token": "r2", "expires_in": 3600})),
        ):
            info = xai_auth.resolve(force_refresh=True)
        self.assertEqual(info["token"], "new")

    def test_a_dead_repo_store_falls_through_to_the_api_key(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("old", "dead", 0.0))
        warnings: list[str] = []
        with mock.patch.dict(os.environ, {"XAI_API_KEY": "key"}), mock.patch.object(
            xai_auth, "_http_post_form", _responses((400, {"error": "invalid_grant"}))
        ):
            info = xai_auth.resolve(warn=warnings.append)
        self.assertEqual((info["token"], info["mode"]), ("key", "api_key"))
        self.assertTrue(warnings and "refreshed" in warnings[0])

    def test_grok_store_is_read_when_the_repo_store_is_empty(self) -> None:
        Path(os.environ["GROK_AUTH_PATH"]).write_text(
            json.dumps({"https://auth.x.ai::client": {"key": _jwt(time.time() + 9999)}}), encoding="utf-8"
        )
        info = xai_auth.resolve()
        self.assertEqual(info["source"], "grok-auth")

    def test_expired_grok_store_is_skipped(self) -> None:
        Path(os.environ["GROK_AUTH_PATH"]).write_text(
            json.dumps({"https://auth.x.ai::client": {"key": _jwt(time.time() - 10)}}), encoding="utf-8"
        )
        with mock.patch.dict(os.environ, {"XAI_API_KEY": "key"}):
            info = xai_auth.resolve()
        self.assertEqual(info["source"], "XAI_API_KEY")

    def test_kilo_store_is_refreshed_and_rewritten_when_expired(self) -> None:
        kilo = Path(os.environ["KILO_AUTH_PATH"])
        kilo.write_text(
            json.dumps({"xai": {"access": "old", "refresh": "kr1", "expires": 1, "client_id": "cid"}}),
            encoding="utf-8",
        )
        seen: list[dict[str, str]] = []

        def handler(url: str, data: dict[str, str], timeout: float = 0) -> tuple[int, str]:
            seen.append(dict(data))
            return 200, json.dumps({"access_token": "kilo-new", "refresh_token": "kr2", "expires_in": 3600})

        with mock.patch.object(xai_auth, "_http_post_form", handler):
            info = xai_auth.resolve()
        self.assertEqual((info["token"], info["source"]), ("kilo-new", "kilo-auth-refresh"))
        self.assertEqual(seen[0]["client_id"], "cid")
        rewritten = json.loads(kilo.read_text(encoding="utf-8"))
        self.assertEqual(rewritten["xai"]["refresh"], "kr2")
        self.assertEqual(stat.S_IMODE(kilo.stat().st_mode), 0o600)

    def test_api_key_is_last(self) -> None:
        with mock.patch.dict(os.environ, {"XAI_API_KEY": "key"}):
            info = xai_auth.resolve()
        self.assertEqual((info["source"], info["mode"]), ("XAI_API_KEY", "api_key"))

    def test_nothing_configured_raises_with_guidance(self) -> None:
        with self.assertRaisesRegex(xai_auth.XaiAuthError, "xai-login"):
            xai_auth.resolve()

    def test_status_never_carries_token_values(self) -> None:
        xai_auth.save_credentials(xai_auth.Credentials("secret-access", "secret-refresh", time.time() + 600))
        report = json.dumps(xai_auth.status())
        self.assertNotIn("secret", report)
        self.assertIn('"configured": true', report)

    def test_cli_resolve_prints_json_and_exits_3_without_a_credential(self) -> None:
        import io

        with mock.patch("sys.stdout", new_callable=io.StringIO) as out, mock.patch.dict(
            os.environ, {"XAI_API_KEY": "key"}
        ):
            self.assertEqual(xai_auth.main(["resolve"]), 0)
        self.assertEqual(json.loads(out.getvalue())["source"], "XAI_API_KEY")
        with mock.patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(xai_auth.main(["resolve"]), 3)


if __name__ == "__main__":
    unittest.main()
