"""Offline summary-adapter integration with the real pinned v2 host gate.

Only the transport and time sources are fake. Both independent fetchers keep
separate response/robots caches, and share only real HostRequestGate files in
this test's temporary directory. No live protocol directory is opened.
"""
import contextlib
import datetime as dt
import email.utils
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import local_lab_summary_gaps as gaps


COLLECTOR_SHA = "baa97a1a8b71216c76a3d125a17d25058c36fb509b8a19c7bf62e97ef507c253"
GATE_SHA = "3cec5f78dff65ff19fe49e5f2e394bf98c12c6a843e3e4fecd102c176894938c"
CURRENT_COLLECTOR_SHA = "aee6c49634e619c2e7f3f6369dee843604b71647e6a20ec77130e0bac7fcc11c"
# Keep the complete resumed collector receipt pinned independently of its live
# process.json. Order also records the dependency compilation boundary.
CURRENT_SOURCE_PINS = (
    ("lab_destinations.py", "d5c0578a3135e344ec59391468d8511f1fe1ef549f2f0ff2462ec70ddfb5aecd"),
    ("refresh_labs.py", "cdbd7832f6d6e7baeb1988da0535b85c8abcd7e06a6b62d740b81dc670237ead"),
    ("refresh_faculty_directories.py", "012184fb455602fc21d57fad477487dc4f815ba75888806c8d37e69e3199a8f8"),
    ("collection_lock.py", "06b3b4968f62e32f259c723c02637c701261b778814e387e5ad810b7afc72056"),
    ("collection_scope.py", "6f589d2673f44c5cbbe7681b60655c460b4f196bd8decf47373b452a44483029"),
    ("network_coordination.py", GATE_SHA),
    ("collect_ucsd_coverage.py", CURRENT_COLLECTOR_SHA),
)
LATEST_COLLECTOR_SHA = "edaacebf859c73b14b76b41673b4c30089b65c987c41baf2d4294015bae9d439"
LATEST_SOURCE_PINS = tuple((name, LATEST_COLLECTOR_SHA if name == "collect_ucsd_coverage.py" else digest)
                           for name, digest in CURRENT_SOURCE_PINS)
COLLECTOR_6A5D_SHA = "6a5d3c3b8739ad4ae2b9abeaaaa0c9e545bd677f680779691c44e94fa8e0aa82"
SOURCE_PINS_6A5D = tuple((name, {
    "collect_ucsd_coverage.py": COLLECTOR_6A5D_SHA,
    "refresh_faculty_directories.py": "29757f294a7b8cc576d211c4dd3089c17b64553189c4e5cb4956d9d959c36896",
}.get(name, digest)) for name, digest in LATEST_SOURCE_PINS)
COLLECTOR_22AD_SHA = "22ad544185024a96f0bde83a7f43b275c2424b4cafbf157327bfb9677b398d9c"
SOURCE_PINS_22AD = tuple((name, COLLECTOR_22AD_SHA if name == "collect_ucsd_coverage.py" else digest)
                        for name, digest in SOURCE_PINS_6A5D)
COLLECTOR_A071_SHA = "a07158ed32b17f11819f1ae468d7e63c459ca6bc2cc923c2ba4f27497c30360b"
SOURCE_PINS_A071 = tuple((name, {
    "collect_ucsd_coverage.py": COLLECTOR_A071_SHA,
    "refresh_labs.py": "063ae6effe54c5a6543c09a952800cbc859461bc897a19ef0e66e4aaf5eaa59b",
}.get(name, digest)) for name, digest in SOURCE_PINS_22AD)
ORIGIN = "https://adapter-source.example.test"


class FakeClock:
    def __init__(self):
        self.epoch = 1_800_000_000.0
        self.ticks = 1_000.0
        self.sleeps = []

    def time(self):
        return self.epoch

    def monotonic(self):
        return self.ticks

    def sleep(self, seconds):
        if seconds <= 0:
            raise AssertionError("gate must only sleep for a positive duration")
        self.sleeps.append(seconds)
        self.epoch += seconds
        self.ticks += seconds

    def iso(self):
        return dt.datetime.fromtimestamp(self.epoch, dt.timezone.utc).isoformat()


class SharedCooldownAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load exactly the historical v2 source snapshots, without consulting a PID
        # or changing collector/shared-network state. Source identity is part of
        # the integration boundary, not a mocked replacement gate.
        hashes = {
            "collectorCodeSha256": COLLECTOR_SHA,
            "coordinationCodeSha256": GATE_SHA,
        }
        for stem, digest in [("collect_ucsd_coverage", COLLECTOR_SHA),
                             ("network_coordination", GATE_SHA)]:
            source = gaps.OUT / "network-adapter-sources" / (stem + "-" + digest + ".py")
            if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                raise AssertionError("pinned integration source hash changed")
        with patch.object(gaps, "read", return_value={"networkCoordination": hashes}):
            cls.module = gaps.load_fetcher()
        cls.real_gate = cls.module.HostRequestGate
        cls.public_fetcher = cls.module.PublicFetcher

    @contextlib.contextmanager
    def adapter(self, transport):
        module = self.module
        with tempfile.TemporaryDirectory(prefix="cooldown-integration-", dir=gaps.OUT) as temp:
            root = Path(temp)
            collector = root / "readonly-collector-view"
            collector.mkdir()
            (collector / "queue.json").write_text(json.dumps({"items": {}}))
            clock = FakeClock()
            calls, gates = [], []
            original_init = self.public_fetcher.__init__

            def gate_factory():
                gate = self.real_gate(root / "shared-host-state", clock=clock.time,
                                      monotonic=clock.monotonic, sleep=clock.sleep)
                gates.append(gate)
                return gate

            def init(fetcher, cache, *args, **kwargs):
                kwargs.setdefault("clock", clock.time)
                kwargs.setdefault("sleep", clock.sleep)
                original_init(fetcher, cache, *args, **kwargs)

            def fake_transport(fetcher, url, max_bytes):
                # This is the only wire boundary. The real gate and real
                # PublicFetcher._wire/_rules/fetch paths remain untouched.
                calls.append({"owner": fetcher.cache.name, "url": url,
                              "startedEpoch": clock.time()})
                return transport(fetcher, url, max_bytes, clock)

            ledger = {"items": {}, "wireEvents": [], "wireRequestsTotal": 0}
            with contextlib.ExitStack() as stack:
                stack.enter_context(patch.object(gaps, "OUT", root))
                stack.enter_context(patch.object(gaps, "CACHE", collector))
                stack.enter_context(patch.object(gaps.time, "time", clock.time))
                stack.enter_context(patch.object(gaps, "now", clock.iso))
                stack.enter_context(patch.object(module, "HostRequestGate", gate_factory))
                stack.enter_context(patch.object(self.public_fetcher, "__init__", init))
                stack.enter_context(patch.object(self.public_fetcher, "_transport", fake_transport))
                stack.enter_context(patch.object(module.subprocess, "run", side_effect=
                                                AssertionError("offline test attempted a subprocess")))
                first = gaps.instrumented_fetcher(module, root / "summary-cache", ledger)

                def independent_consumer():
                    # A collector-style consumer has no summary retry ledger
                    # and cannot inherit first's in-memory robots or locks.
                    return self.public_fetcher(root / "observer-cache")

                def state(url):
                    _, _, path = first.network_gate.paths(url)
                    return self.real_gate.read(path)

                yield SimpleNamespace(first=first, independent=independent_consumer,
                                      clock=clock, calls=calls, ledger=ledger,
                                      gates=gates, state=state, root=root)
                self.assertTrue(gates)
                self.assertTrue(all(gate.directory.is_relative_to(root) for gate in gates))

    @staticmethod
    def failure_transport(status, headers=None, error="", raises=False):
        def transport(fetcher, url, max_bytes, clock):
            if url.endswith("/robots.txt"):
                return 404, {}, "", ""
            if fetcher.cache.name == "summary-cache":
                if raises:
                    raise RuntimeError("simulated transport exception")
                return status, headers or {}, "", error
            return 200, {"content-type": "text/html"}, "<h1>Observer Lab</h1>", ""
        return transport

    def assert_independent_consumer_waits(self, env, deadline):
        observer = env.independent()
        self.assertIsNot(observer.network_gate, env.first.network_gate)
        self.assertIsInstance(observer.network_gate, self.real_gate)
        self.assertEqual(observer.robots, {})
        meta, body = observer.fetch(ORIGIN + "/independent-lab")
        self.assertEqual(meta["status"], "ok")
        self.assertIn("Observer Lab", body)
        observed = [call for call in env.calls if call["owner"] == "observer-cache"]
        self.assertEqual([call["url"] for call in observed],
                         [ORIGIN + "/robots.txt", ORIGIN + "/independent-lab"])
        self.assertGreaterEqual(observed[0]["startedEpoch"], deadline)
        self.assertGreaterEqual(observed[1]["startedEpoch"], deadline + 1)
        self.assertTrue(env.clock.sleeps)
        # Only the summary's own two wires belong in its private ledger.
        self.assertEqual(len(env.ledger["wireEvents"]), 2)

    def test_page_429_retry_after_reaches_an_independent_consumer(self):
        with self.adapter(self.failure_transport(429, {"retry-after": "180"})) as env:
            meta, _ = env.first.fetch(ORIGIN + "/lab")
            state = env.state(ORIGIN)
            deadline = env.calls[-1]["startedEpoch"] + 180
            self.assertEqual(meta["status"], "http_error")
            self.assertEqual(state["lastResponseStatus"], 429)
            self.assertEqual(state["protocolVersion"], "fcntl-host-clock-v2")
            self.assertEqual(state["notBeforeEpoch"], deadline)
            self.assertEqual(meta["retryAfterEpoch"], deadline)
            self.assertEqual(env.ledger["hostRetryAfter"]["adapter-source.example.test"], deadline)
            self.assert_independent_consumer_waits(env, deadline)

    def test_all_5xx_default_cooldowns_survive_the_summary_adapter(self):
        # 501/599 are intentionally outside the adapter's older local pause
        # list: passing requires the real v2 shared response policy to survive.
        for status in [500, 501, 502, 503, 504, 599]:
            with self.subTest(status=status):
                with self.adapter(self.failure_transport(status)) as env:
                    meta, _ = env.first.fetch(ORIGIN + "/lab")
                    state = env.state(ORIGIN)
                    deadline = env.calls[-1]["startedEpoch"] + 60
                    self.assertEqual(meta["status"], "http_error")
                    self.assertEqual(state["lastResponseStatus"], status)
                    self.assertEqual(state["cooldownReason"], "transient_default_backoff")
                    self.assertEqual(state["notBeforeEpoch"], deadline)
                    self.assertEqual(meta["retryAfterEpoch"], deadline)
                    self.assert_independent_consumer_waits(env, deadline)

    def test_returned_transport_error_sets_shared_cooldown(self):
        with self.adapter(self.failure_transport(0, error="simulated_timeout")) as env:
            meta, _ = env.first.fetch(ORIGIN + "/lab")
            state = env.state(ORIGIN)
            deadline = env.calls[-1]["startedEpoch"] + 60
            self.assertEqual(meta["status"], "fetch_error")
            self.assertEqual(state["lastResponseStatus"], 0)
            self.assertEqual(meta["retryAfterEpoch"], deadline)
            self.assert_independent_consumer_waits(env, deadline)

    def test_raised_transport_error_is_persisted_before_another_consumer(self):
        with self.adapter(self.failure_transport(0, raises=True)) as env:
            with self.assertRaisesRegex(RuntimeError, "simulated transport exception"):
                env.first.fetch(ORIGIN + "/lab")
            state = env.state(ORIGIN)
            deadline = env.calls[-1]["startedEpoch"] + 60
            self.assertEqual(state["lastResponseStatus"], 0)
            self.assertEqual(state["notBeforeEpoch"], deadline)
            self.assert_independent_consumer_waits(env, deadline)

    def test_robots_http_date_retry_after_is_shared_without_a_page_wire(self):
        deadline = 1_800_000_240.0
        retry_date = email.utils.formatdate(deadline, usegmt=True)

        def transport(fetcher, url, max_bytes, clock):
            if fetcher.cache.name == "summary-cache":
                self.assertTrue(url.endswith("/robots.txt"))
                return 429, {"retry-after": retry_date}, "", ""
            if url.endswith("/robots.txt"):
                return 404, {}, "", ""
            return 200, {"content-type": "text/html"}, "<h1>Observer Lab</h1>", ""

        with self.adapter(transport) as env:
            meta, _ = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(meta["status"], "robots_unavailable")
            self.assertEqual(env.state(ORIGIN)["notBeforeEpoch"], deadline)
            self.assertEqual(len(env.ledger["wireEvents"]), 1)
            observer = env.independent()
            result, _ = observer.fetch(ORIGIN + "/independent-lab")
            self.assertEqual(result["status"], "ok")
            observed = [call for call in env.calls if call["owner"] == "observer-cache"]
            self.assertGreaterEqual(observed[0]["startedEpoch"], deadline)
            self.assertEqual(len(env.ledger["wireEvents"]), 1)

    def test_page_redirect_retry_after_reaches_target_before_robots_and_page(self):
        destination = "https://profiles.ucsd.edu/adapter-test-lab"
        target_deadline = []

        def transport(fetcher, url, max_bytes, clock):
            if url == ORIGIN + "/lab":
                target_deadline.append(clock.time() + 150)
                return 302, {"location": destination, "retry-after": "150"}, "", ""
            if urllib.parse.urlsplit(url).hostname == "profiles.ucsd.edu":
                state = env.state(destination)
                self.assertEqual(state["cooldownReason"], "redirect_retry_after")
                self.assertGreaterEqual(clock.time(), target_deadline[0])
            if url.endswith("/robots.txt"):
                return 404, {}, "", ""
            return 200, {"content-type": "text/html"}, "<h1>Redirected Lab</h1>", ""

        with self.adapter(transport) as env:
            meta, _ = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(meta["status"], "ok")
            target_calls = [call for call in env.calls if "profiles.ucsd.edu" in call["url"]]
            self.assertEqual([call["url"] for call in target_calls],
                             ["https://profiles.ucsd.edu/robots.txt", destination])
            self.assertEqual(target_calls[0]["startedEpoch"], target_deadline[0])
            self.assertGreaterEqual(target_calls[1]["startedEpoch"], target_deadline[0] + 10)
            self.assertEqual(meta["redirects"][0]["retryAfterEpoch"], target_deadline[0])
            self.assertEqual(env.ledger["wireRequestsTotal"], 4)

    def test_robots_redirect_retry_after_reaches_target_before_robots(self):
        target_robots = "https://adapter-robots.example.test/robots.txt"
        target_deadline = []

        def transport(fetcher, url, max_bytes, clock):
            if url == ORIGIN + "/robots.txt":
                target_deadline.append(clock.time() + 120)
                return 302, {"location": target_robots, "retry-after": "120"}, "", ""
            if url == target_robots:
                state = env.state(target_robots)
                self.assertEqual(state["cooldownReason"], "redirect_retry_after")
                self.assertGreaterEqual(clock.time(), target_deadline[0])
                return 404, {}, "", ""
            return 200, {"content-type": "text/html"}, "<h1>Original Lab</h1>", ""

        with self.adapter(transport) as env:
            meta, _ = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(meta["status"], "ok")
            self.assertEqual([call["url"] for call in env.calls],
                             [ORIGIN + "/robots.txt", target_robots, ORIGIN + "/lab"])
            self.assertEqual(env.calls[1]["startedEpoch"], target_deadline[0])
            self.assertEqual(meta["robots"]["redirects"][0]["retryAfterEpoch"], target_deadline[0])
            self.assertEqual(env.ledger["wireRequestsTotal"], 3)


class ResumedCollectorSharedCooldownAdapterTests(SharedCooldownAdapterTests):
    """Run every real-gate scenario against the resumed seven-source collector."""

    collector_sha = CURRENT_COLLECTOR_SHA
    source_pins = CURRENT_SOURCE_PINS

    @classmethod
    def setUpClass(cls):
        required = dict(cls.source_pins)
        hashes = {
            "collectorCodeSha256": cls.collector_sha,
            "coordinationCodeSha256": GATE_SHA,
            "scopePolicyCodeSha256": required["collection_scope.py"],
        }
        state = dict(hashes, requiredSourceFiles=required)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(gaps, "read", return_value={"networkCoordination": state}))
            verified = stack.enter_context(patch.object(gaps, "verified_source", wraps=gaps.verified_source))
            stack.enter_context(patch.object(gaps.subprocess, "run", side_effect=
                                             AssertionError("pinned-source test attempted a subprocess")))
            cls.module = gaps.load_fetcher(expected_hashes=hashes, expected_sources=required)
        cls.loaded_source_pins = tuple((Path(call.args[0]).name, call.args[1])
                                      for call in verified.call_args_list)
        cls.real_gate = cls.module.HostRequestGate
        cls.public_fetcher = cls.module.PublicFetcher

    def test_current_collector_uses_all_seven_exact_pinned_sources(self):
        self.assertEqual(self.loaded_source_pins, self.source_pins)
        self.assertNotEqual(self.collector_sha, COLLECTOR_SHA)
        for filename, digest in self.source_pins:
            with self.subTest(source=filename):
                snapshot = gaps.OUT / "network-adapter-sources" / (Path(filename).stem + "-" + digest + ".py")
                self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), digest)


class LatestCollectorSharedCooldownAdapterTests(ResumedCollectorSharedCooldownAdapterTests):
    """Retain older receipts and verify the active robots-retry revision too."""

    collector_sha = LATEST_COLLECTOR_SHA
    source_pins = LATEST_SOURCE_PINS

    def test_transient_robots_waits_then_recovers_with_prior_attempt_preserved(self):
        robots_calls = []

        def transport(fetcher, url, max_bytes, clock):
            if url.endswith("/robots.txt"):
                robots_calls.append(clock.time())
                if len(robots_calls) == 1:
                    return 503, {"retry-after": "120"}, "", ""
                return 200, {}, "User-agent: *\nAllow: /\n", ""
            return 200, {"content-type": "text/html"}, "<h1>Recovered Lab</h1>", ""

        with self.adapter(transport) as env:
            first, _ = env.first.fetch(ORIGIN + "/lab")
            deadline = first["retryAfterEpoch"]
            self.assertEqual(first["status"], "robots_unavailable")
            self.assertEqual(first["robots"]["attempts"], 1)
            self.assertEqual(len(env.calls), 1)
            # Retry before the deadline reuses the unavailable robots result.
            second, _ = env.first.fetch(ORIGIN + "/another-lab")
            self.assertEqual(second["status"], "robots_unavailable")
            self.assertEqual(len(env.calls), 1)
            env.clock.sleep(deadline - env.clock.time())
            recovered, body = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(recovered["status"], "ok")
            self.assertIn("Recovered Lab", body)
            self.assertEqual(robots_calls, [deadline - 120, deadline])
            self.assertEqual(recovered["robots"]["attempts"], 2)
            self.assertEqual(recovered["robots"]["attemptHistory"], [first["robots"]])

    def test_robots_challenge_is_retained_without_retry_or_page_probe(self):
        def transport(fetcher, url, max_bytes, clock):
            self.assertTrue(url.endswith("/robots.txt"))
            return 503, {}, "Verify you are human", ""

        with self.adapter(transport) as env:
            first, _ = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(first["robots"]["error"], "access_challenge")
            self.assertFalse(self.module.retryable_fetch(first))
            env.clock.sleep(600)
            second, _ = env.first.fetch(ORIGIN + "/other-lab")
            self.assertEqual(second["status"], "robots_unavailable")
            self.assertEqual(second["robots"], first["robots"])
            self.assertEqual(len(env.calls), 1)

    def test_three_transient_robots_attempts_stop_for_the_daily_cache_period(self):
        def transport(fetcher, url, max_bytes, clock):
            self.assertTrue(url.endswith("/robots.txt"))
            return 503, {}, "", ""

        with self.adapter(transport) as env:
            for attempt in range(1, 4):
                result, _ = env.first.fetch(ORIGIN + "/lab")
                self.assertEqual(result["robots"]["attempts"], attempt)
                self.assertEqual(len(env.calls), attempt)
                if attempt < 3:
                    env.clock.sleep(result["retryAfterEpoch"] - env.clock.time())
            self.assertFalse(self.module.retryable_fetch(result))
            env.clock.sleep(600)
            final, _ = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(final["robots"], result["robots"])
            self.assertEqual(len(env.calls), 3)

    def test_robots_404_and_410_challenge_blocks_page_without_rewriting_observation(self):
        for status in (404, 410):
            with self.subTest(status=status):
                def transport(fetcher, url, max_bytes, clock):
                    self.assertTrue(url.endswith("/robots.txt"))
                    return status, {}, "Verify you are human", ""

                with self.adapter(transport) as env:
                    result, _ = env.first.fetch(ORIGIN + "/lab")
                    self.assertEqual(result["status"], "robots_unavailable")
                    self.assertEqual(result["robots"]["httpStatus"], status)
                    self.assertEqual(result["robots"]["error"], "access_challenge")
                    self.assertTrue(result["robots"]["summaryAccessBoundaryEnforced"])
                    self.assertFalse(self.module.retryable_fetch(result))
                    path, _ = env.first._paths(ORIGIN + "/robots.txt", "robots-")
                    raw = json.loads(path.read_text())
                    self.assertEqual(raw["status"], "not_found")
                    self.assertEqual(raw["observedAt"], result["robots"]["observedAt"])
                    self.assertEqual(raw["retrievedEpoch"], result["robots"]["retrievedEpoch"])
                    self.assertNotIn("summaryAccessBoundaryEnforced", raw)
                    env.clock.sleep(600)
                    repeated, _ = env.first.fetch(ORIGIN + "/other-lab")
                    self.assertEqual(repeated["status"], "robots_unavailable")
                    self.assertEqual(len(env.calls), 1)


class Collector6A5DSharedCooldownAdapterTests(LatestCollectorSharedCooldownAdapterTests):
    """The next exact seven-source receipt retains all prior boundary checks."""

    collector_sha = COLLECTOR_6A5D_SHA
    source_pins = SOURCE_PINS_6A5D


class Collector22ADSharedCooldownAdapterTests(LatestCollectorSharedCooldownAdapterTests):
    """The exact resumed22ad receipt keeps the same real-gate12 scenarios."""

    collector_sha = COLLECTOR_22AD_SHA
    source_pins = SOURCE_PINS_22AD


class CollectorA071SharedCooldownAdapterTests(LatestCollectorSharedCooldownAdapterTests):
    """Exact A071 + literal-URI dependency, keeping all twelve real-gate cases."""

    collector_sha = COLLECTOR_A071_SHA
    source_pins = SOURCE_PINS_A071

    def test_literal_http_and_www_survive_both_loaded_normalizer_and_adapter(self):
        for url in ["http://www.jacobsschool.ucsd.edu/faculty/profile?id=64",
                    "http://www.cogsci.ucsd.edu/lab?view=1"]:
            with self.subTest(url=url):
                self.assertEqual(self.module.canonical_url(url), url)
                self.assertEqual(self.module.safe_url(url), url)
        for invalid in ["file:///tmp/private", "http://127.0.0.1/", "https://localhost/",
                        "http://name:password@example.test/", "https://example.test:8080/"]:
            with self.subTest(invalid=invalid):
                self.assertEqual(self.module.safe_url(invalid), "")
        self.assertEqual(self.module.summaryUrlPolicy,
                         "preserve_wire_uri_after_pinned_public_origin_validation")

    def test_literal_http_redirect_checks_distinct_https_robots_and_keeps_www(self):
        start = "http://www.jacobsschool.ucsd.edu/lab?view=1"
        destination = "https://www.jacobsschool.ucsd.edu/lab?view=1"

        def transport(fetcher, url, max_bytes, clock):
            if url.endswith("/robots.txt"):
                self.assertEqual(max_bytes, 300_000)
                return 404, {}, "", ""
            if url == start:
                return 301, {"location": destination}, "", ""
            self.assertEqual(url, destination)
            self.assertEqual(max_bytes, 2_000_000)
            return 200, {"content-type": "text/html"}, "<h1>Literal Lab</h1>", ""

        with self.adapter(transport) as env:
            meta, body = env.first.fetch(start)
            self.assertEqual(meta["status"], "ok")
            self.assertIn("Literal Lab", body)
            self.assertEqual(meta["sourceUrl"], start)
            self.assertEqual(meta["finalUrl"], destination)
            self.assertEqual(meta["redirects"], [{"from": start, "to": destination, "httpStatus": 301}])
            self.assertEqual([c["url"] for c in env.calls], [
                "http://www.jacobsschool.ucsd.edu/robots.txt", start,
                "https://www.jacobsschool.ucsd.edu/robots.txt", destination])
            self.assertTrue(all(b["startedEpoch"] >= a["startedEpoch"] + 1
                                for a, b in zip(env.calls, env.calls[1:])))
            self.assertEqual(env.ledger["wireRequestsTotal"], 4)

    def test_fresh_explicit_robots_denial_blocks_both_independent_consumers(self):
        def transport(fetcher, url, max_bytes, clock):
            self.assertTrue(url.endswith("/robots.txt"))
            self.assertEqual(max_bytes, 300_000)
            return 200, {}, "User-agent: *\nDisallow: /private\n", ""

        with self.adapter(transport) as env:
            first, body = env.first.fetch(ORIGIN + "/private")
            self.assertEqual((first["status"], body), ("robots_denied", ""))
            observer = env.independent()
            second, _ = observer.fetch(ORIGIN + "/private")
            self.assertEqual(second["status"], "robots_denied")
            self.assertEqual([c["url"] for c in env.calls], [ORIGIN + "/robots.txt"] * 2)
            self.assertGreaterEqual(env.calls[1]["startedEpoch"], env.calls[0]["startedEpoch"] + 1)
            self.assertEqual(env.ledger["wireRequestsTotal"], 1)

    def test_redirect_to_login_is_not_followed_with_robots_or_page_requests(self):
        login = "https://sso.ucsd.edu/login"

        def transport(fetcher, url, max_bytes, clock):
            if url.endswith("/robots.txt"):
                return 404, {}, "", ""
            self.assertEqual(url, ORIGIN + "/lab")
            return 302, {"location": login}, "", ""

        with self.adapter(transport) as env:
            meta, body = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual((meta["status"], body), ("authentication_required", ""))
            self.assertEqual(meta["blockedUrl"], login)
            self.assertEqual([c["url"] for c in env.calls], [ORIGIN + "/robots.txt", ORIGIN + "/lab"])

    def test_tls_refusal_is_not_retryable_and_shared_gate_still_observes_failure(self):
        with self.adapter(self.failure_transport(0, error="curl: (60) SSL certificate problem")) as env:
            meta, _ = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(meta["status"], "fetch_error")
            self.assertFalse(self.module.retryable_fetch(meta))
            state = env.state(ORIGIN)
            self.assertEqual(state["lastResponseStatus"], 0)
            deadline = env.calls[-1]["startedEpoch"] + 60
            self.assertEqual(state["notBeforeEpoch"], deadline)
            self.assert_independent_consumer_waits(env, deadline)

    def test_warm_page_cache_preserves_capture_without_new_gate_or_wire(self):
        def transport(fetcher, url, max_bytes, clock):
            if url.endswith("/robots.txt"):
                return 404, {}, "", ""
            return 200, {"content-type": "text/html"}, "<h1>Cached Named Lab</h1>", ""

        with self.adapter(transport) as env:
            first, body = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(first["status"], "ok")
            self.assertIn("Cached Named Lab", body)
            prior_calls = list(env.calls)
            prior_events = list(env.ledger["wireEvents"])
            env.clock.sleep(30)
            repeated, repeated_body = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(repeated, first)
            self.assertEqual(repeated_body, body)
            self.assertEqual(env.calls, prior_calls)
            self.assertEqual(env.ledger["wireEvents"], prior_events)

    def test_documented_d2_mixed_503_curl63_still_has_bounded_cache_retries(self):
        mixed = {"httpStatus": 503, "error": "curl: (63) Maximum file size exceeded"}
        # Document the unchanged upstream classification edge, not a fix:
        # the 503 branch precedes the hard-error filter.
        self.assertTrue(self.module.transient_response(mixed))

        def transport(fetcher, url, max_bytes, clock):
            self.assertTrue(url.endswith("/robots.txt"))
            self.assertEqual(max_bytes, 300_000)
            return 503, {}, "", mixed["error"]

        with self.adapter(transport) as env:
            for attempt in range(1, 4):
                result, _ = env.first.fetch(ORIGIN + "/lab")
                self.assertEqual(result["status"], "robots_unavailable")
                self.assertEqual(result["robots"]["attempts"], attempt)
                self.assertEqual(len(env.calls), attempt)
                if attempt < 3:
                    self.assertTrue(self.module.retryable_fetch(result))
                    # No automatic queue or page retry is invoked here; these
                    # are explicit test calls separated by the real gate policy.
                    again, _ = env.first.fetch(ORIGIN + "/other-lab")
                    self.assertEqual(again["robots"], result["robots"])
                    self.assertEqual(len(env.calls), attempt)
                    env.clock.sleep(result["retryAfterEpoch"] - env.clock.time())
            self.assertFalse(self.module.retryable_fetch(result))
            env.clock.sleep(600)
            final, _ = env.first.fetch(ORIGIN + "/lab")
            self.assertEqual(final["robots"], result["robots"])
            self.assertEqual(len(env.calls), 3)


if __name__ == "__main__":
    unittest.main()
