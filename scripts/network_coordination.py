#!/usr/bin/env python3
"""Cross-process host request slots; coordination state only, no response cache.

Every network consumer must hold request_slot across the actual wire operation.
Robots and redirect hops each need their own slot. Callers supply their robots
delay; the strongest interval already observed for that host is retained. This
module does not grant robots permission or permit authenticated access.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import email.utils
import fcntl
import hashlib
import json
import math
import os
import tempfile
import time
import urllib.parse
import urllib.robotparser
from pathlib import Path

PROTOCOL_VERSION = 'fcntl-host-clock-v2'
DEFAULT_DIRECTORY = Path('/tmp/ucsd-research-network-20261016')
TRANSIENT_STATUSES = {0, 408, 429, *range(500, 600)}


def retry_after_seconds(value, current_time):
    try:
        seconds = float(value)
    except (ValueError, TypeError):
        try:
            parsed = email.utils.parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            seconds = parsed.timestamp() - current_time
        except (ValueError, TypeError, OverflowError, AttributeError):
            return None
    return max(0, seconds) if math.isfinite(seconds) else None


class RequestSlot(dict):
    def __init__(self, state, record):
        super().__init__(state)
        self._record = record

    def record_response(self, status, headers):
        """Must be called inside the slot, before releasing its host lock."""
        result = self._record(status, headers)
        self.update(result)
        return result


def host_name(url_or_host):
    value = url_or_host if '://' in url_or_host else 'https://' + url_or_host
    host = urllib.parse.urlsplit(value).hostname
    if not host:
        raise ValueError('missing_coordination_host')
    return host.rstrip('.').encode('idna').decode('ascii').lower()


def atomic_state(path, value):
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class HostRequestGate:
    def __init__(self, directory=DEFAULT_DIRECTORY, *, clock=time.time, monotonic=time.monotonic, sleep=time.sleep):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.clock, self.monotonic, self.sleep = clock, monotonic, sleep

    def paths(self, url_or_host):
        host = host_name(url_or_host)
        stem = 'host-' + hashlib.sha256(host.encode()).hexdigest()
        return host, self.directory / (stem + '.lock'), self.directory / (stem + '.json')

    @staticmethod
    def read(path):
        try:
            value = json.loads(path.read_text())
            if not isinstance(value, dict):
                raise ValueError('invalid_shared_host_clock')
            return value
        except FileNotFoundError:
            return {}

    @contextlib.contextmanager
    def request_slot(self, url, minimum_interval=1):
        host, lock_path, state_path = self.paths(url)
        # The lock inode is never replaced; only the separate JSON clock is.
        with lock_path.open('a+') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                state = self.read(state_path)
                interval = max(1.0, float(minimum_interval), float(state.get('minimumIntervalSeconds', 0)),
                               10.0 if host == 'profiles.ucsd.edu' or host.endswith('.profiles.ucsd.edu') else 0)
                while True:
                    remaining = max(float(state.get('lastRequestAt', 0)) + interval,
                                    float(state.get('notBeforeEpoch', 0))) - self.clock()
                    previous_mono = state.get('lastRequestMonotonic')
                    current_mono = self.monotonic()
                    if previous_mono is not None and 0 <= float(previous_mono) <= current_mono:
                        remaining = max(remaining, float(previous_mono) + interval - current_mono)
                    cooldown_mono = state.get('notBeforeMonotonic')
                    if cooldown_mono is not None and state.get('cooldownSetMonotonic', 0) <= current_mono:
                        remaining = max(remaining, float(cooldown_mono) - current_mono)
                    if remaining <= 0:
                        break
                    self.sleep(min(remaining, 30))
                started = self.clock()
                state.update(protocolVersion=PROTOCOL_VERSION, host=host,
                             lastRequestAt=started, lastRequestMonotonic=self.monotonic(),
                             minimumIntervalSeconds=interval, ownerPid=os.getpid())
                atomic_state(state_path, state)
                active = [True]

                def record(status, headers):
                    if not active[0]:
                        raise RuntimeError('Response policy must be recorded before releasing the host lock')
                    headers = {k.lower(): v for k, v in headers.items()}
                    raw = headers.get('retry-after')
                    transient = status in TRANSIENT_STATUSES
                    failures = int(state.get('consecutiveTransientFailures', 0)) + 1 if transient else 0
                    state.update(lastResponseAt=self.clock(), lastResponseStatus=status,
                                 consecutiveTransientFailures=failures, responseCooldownSet=False)
                    if transient or raw is not None:
                        default = min(3600, 60 * 2 ** min(max(failures - 1, 0), 6))
                        parsed = retry_after_seconds(raw, self.clock()) if raw is not None else None
                        delay = max(default, parsed or 0)
                        deadline = max(float(state.get('notBeforeEpoch', 0)), self.clock() + delay)
                        state.update(notBeforeEpoch=deadline,
                                     notBeforeMonotonic=self.monotonic() + max(0, deadline - self.clock()),
                                     cooldownSetMonotonic=self.monotonic(), responseCooldownSet=True,
                                     cooldownReason='retry_after' if raw is not None else 'transient_default_backoff')
                    atomic_state(state_path, state)
                    return state.copy()

                # Keep flock held until the caller's GET/HEAD has finished.
                try:
                    yield RequestSlot(state.copy(), record)
                finally:
                    active[0] = False
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def defer(self, url_or_host, not_before_epoch, reason='imported_cooldown'):
        """Preserve a known server deadline without changing request timestamps."""
        deadline = float(not_before_epoch)
        if not math.isfinite(deadline):
            raise ValueError('Invalid cooldown deadline')
        host, lock_path, state_path = self.paths(url_or_host)
        with lock_path.open('a+') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                state = self.read(state_path)
                if deadline > float(state.get('notBeforeEpoch', 0)):
                    state.update(notBeforeEpoch=deadline, cooldownReason=reason,
                                 notBeforeMonotonic=self.monotonic() + max(0, deadline - self.clock()),
                                 cooldownSetMonotonic=self.monotonic())
                state.update(protocolVersion=PROTOCOL_VERSION, host=host)
                atomic_state(state_path, state)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def seed(self, url_or_host, last_request_at, minimum_interval=1):
        """Import a previous clock at an exclusive, stopped-worker boundary."""
        host, lock_path, state_path = self.paths(url_or_host)
        with lock_path.open('a+') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            try:
                state = self.read(state_path)
                prior = float(state.get('lastRequestAt', 0))
                incoming = float(last_request_at)
                if incoming > prior:
                    state['lastRequestAt'] = incoming
                    state.pop('lastRequestMonotonic', None)
                state.update(protocolVersion=PROTOCOL_VERSION, host=host,
                             minimumIntervalSeconds=max(1.0, float(minimum_interval), float(state.get('minimumIntervalSeconds', 0)), 10.0 if host == 'profiles.ucsd.edu' else 0))
                atomic_state(state_path, state)
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def migrate_legacy_clocks(cache, urls, gate, user_agent, observations=()):
    """Read old clocks/robots; write only gate coordination state, never caches."""
    cache = Path(cache)
    netlocs, origins = set(), set()
    for url in urls:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme in {'http', 'https'} and parsed.hostname:
            netlocs.add(parsed.netloc.lower())
            origins.add(f'{parsed.scheme}://{parsed.netloc.lower()}')
    intervals = {}
    for origin in origins:
        robot_url = origin + '/robots.txt'
        stem = 'robots-' + hashlib.sha256(robot_url.encode()).hexdigest()
        meta_path, body_path = cache / (stem + '.json'), cache / (stem + '.html')
        if not meta_path.exists() or not body_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        if meta.get('status') != 'checked':
            continue
        rules = urllib.robotparser.RobotFileParser(robot_url)
        rules.parse(body_path.read_text().splitlines())
        delay = rules.crawl_delay(user_agent) or rules.crawl_delay('*') or 0
        host = host_name(origin)
        intervals[host] = max(intervals.get(host, 1), delay)
    imported = 0
    for netloc in netlocs:
        path = cache / ('clock-' + hashlib.sha256(netloc.encode()).hexdigest() + '.json')
        if path.exists():
            previous = json.loads(path.read_text())
            gate.seed(netloc, previous['lastRequestAt'], intervals.get(host_name(netloc), 1))
            imported += 1
    cooldowns = {}
    records = []
    for path in cache.glob('*.json'):
        if path.name.startswith('clock-'):
            continue
        records.append(json.loads(path.read_text()))
    for item in observations:
        records.append({**item.get('fetch', {}), 'sourceUrl': item.get('fetch', {}).get('sourceUrl') or item.get('url'),
                        'retryAfterEpoch': max(item.get('retryAt', 0), item.get('fetch', {}).get('retryAfterEpoch', 0))})
    for record in records:
        for meta in [record, record.get('robots', {})]:
            target = meta.get('finalUrl') or meta.get('blockedUrl') or meta.get('sourceUrl')
            deadline = meta.get('retryAfterEpoch', 0)
            if not deadline and meta.get('httpStatus') in TRANSIENT_STATUSES:
                deadline = meta.get('retrievedEpoch', 0) + 60
            if target and deadline > gate.clock():
                cooldowns[(target, deadline)] = True
            for step in meta.get('redirects', []):
                if step.get('retryAfterEpoch', 0) > gate.clock():
                    for target in [step['from'], step['to']]:
                        if target:
                            cooldowns[(target, step['retryAfterEpoch'])] = True
    for target, deadline in cooldowns:
        gate.defer(target, deadline, 'legacy_response_cooldown')
    return {'protocolVersion': PROTOCOL_VERSION, 'directory': str(gate.directory),
            'legacyClocksImported': imported, 'legacyCooldownsImported': len(cooldowns),
            'cacheObservationTimestampsModified': False}
