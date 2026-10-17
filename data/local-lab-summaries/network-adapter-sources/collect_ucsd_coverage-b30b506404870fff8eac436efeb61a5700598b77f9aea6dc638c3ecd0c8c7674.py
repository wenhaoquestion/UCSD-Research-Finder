#!/usr/bin/env python3
"""Resumable, public-only UCSD directory discovery and destination checks.

Discovery is an audit artifact, not permission to assert a PI or publish a lab.
The finite scope is the 59 saved departments, their explicitly linked faculty /
research / lab directories (two discovery hops), existing lab destinations,
prior unresolved candidates, and public person URLs in the advertised official
Profiles sitemap. Sitemap entries are candidates, not a faculty roster. Only
explicit appointment-table titles qualify new faculty. No guessed URL templates,
search forms, or login flows.
All network hops, including robots and redirects, share a host clock; Profiles
has a hard minimum of ten seconds. Redirects never bypass target robots.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import signal
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.robotparser
from collections import Counter, defaultdict
from pathlib import Path

from refresh_labs import DOM, canonical_url, clean, evidence, links, now, parse_directory, every_node
from refresh_faculty_directories import SOURCES, card_records, valid_person_name, text_name, individual_profile, appointment_status
from network_coordination import HostRequestGate, migrate_legacy_clocks, PROTOCOL_VERSION
from collection_lock import task_lease
from collection_scope import ScopePolicy

ROOT = Path(__file__).resolve().parents[1]
UA = 'ResearchAtlasEvidenceBot/2.0 (public academic directory verification)'
REDIRECTS = {301, 302, 303, 307, 308}
RETRY = {408, 429, *range(500, 600)}
DIRECTORY = re.compile(r'faculty|research|laborator|\blabs?\b|\bgroups?\b|centers?|centres?|institutes?|\bpeople\b', re.I)
EXCLUDE = re.compile(r'news|events?|seminars?|publications?|papers?|giving|donate|alumni|jobs?|careers?|admissions?|courses?|syllabus|search|login|calendar|resources|funding|awards?|safety|forms?|training|graduate|undergraduate|postdoc|staff|positions|opportunit|facilities|equipment', re.I)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def official(url):
    host = (urllib.parse.urlsplit(url).hostname or '').lower()
    return host == 'ucsd.edu' or host.endswith('.ucsd.edu')


def safe_url(raw):
    try:
        p = urllib.parse.urlsplit(canonical_url(raw))
        if p.scheme not in {'https', 'http'} or not p.hostname or p.username or p.password or p.port not in {None, 80, 443}:
            return ''
        # Fetch only public, ordinary web origins; no IP literals or local hosts.
        if '.' not in p.hostname or re.fullmatch(r'[\d.]+', p.hostname) or ':' in p.hostname or p.hostname.endswith(('.local', '.localhost')):
            return ''
        return urllib.parse.urlunsplit((p.scheme, p.netloc, urllib.parse.quote(p.path or '/', safe='/%:@-._~'), p.query, ''))
    except ValueError:
        return ''


def url_key(url):
    p = urllib.parse.urlsplit(safe_url(url))
    return urllib.parse.urlunsplit((p.scheme, p.netloc, p.path.rstrip('/') or '/', p.query, ''))


def authentication_target(url):
    p = urllib.parse.urlsplit(url)
    return bool((p.hostname or '').lower() in {'accounts.google.com', 'login.microsoftonline.com', 'sso.ucsd.edu', 'shibboleth.ucsd.edu'} or re.search(r'/(?:login|signin|sign-in|sso|saml|oauth2?|authorize|shibboleth)(?:[/.?]|$)', p.path, re.I))


def transient_response(meta):
    """Retry server/transport failures, without retrying permission or TLS refusals."""
    if meta.get('error') in {'access_challenge', 'robots_redirect_is_not_a_robots_file', 'robots_response_is_html'}:
        return False
    if meta.get('httpStatus') in RETRY:
        return True
    error = meta.get('error', '')
    if re.search(r'curl:\s*\((?:1|3|60|63|77)\)|certificate|response_exceeds_size_limit', error, re.I):
        return False
    return meta.get('httpStatus') == 0 or meta.get('status') == 'fetch_error' or bool(re.search(r'curl:\s*\(\d+\)', error))


def retryable_fetch(meta):
    if meta.get('status') == 'robots_unavailable':
        robot = meta.get('robots', {})
        return robot.get('attempts', 1) < 3 and transient_response(robot)
    if meta.get('status') in {'authentication_required', 'robots_denied', 'access_challenge'}:
        return False
    return transient_response(meta)


def robots_retry_at(meta):
    return max(meta.get('retryAfterEpoch', 0), meta.get('retrievedEpoch', 0) + 60 * 2 ** max(0, meta.get('attempts', 1) - 1))


def reusable_robots(meta, current_time):
    if not meta or current_time - meta.get('retrievedEpoch', 0) > 86400:
        return False
    if meta.get('httpStatus') in REDIRECTS and 'redirects' not in meta:
        return False
    return not (meta.get('status') == 'unavailable' and meta.get('attempts', 1) < 3
                and transient_response(meta) and current_time >= robots_retry_at(meta))


def eligible_directory(label, path):
    combined = label + ' ' + path
    if re.search(r'faculty', label, re.I):
        combined = re.sub(r'staff|graduate|undergraduate', '', combined, flags=re.I)
    if re.search(r'lab|laborator', label, re.I):
        combined = re.sub(r'facilities|equipment', '', combined, flags=re.I)
    return bool(DIRECTORY.search(label) and not EXCLUDE.search(combined))


def discovery_links(node, base):
    """Navigation can discover a URL, but is never passed to field extractors."""
    def label_text(n):
        if n.tag in {'script', 'style'}:
            return ''
        return ' '.join(label_text(c) if hasattr(c, 'tag') else c for c in n.children)
    return [(n, clean(label_text(n)) or n.attrs.get('aria-label', '') or n.attrs.get('title', ''), safe_url(urllib.parse.urljoin(base, n.attrs['href'])))
            for n in every_node(node) if n.tag == 'a' and n.attrs.get('href')]


def faculty_table_rows(department, meta, markup):
    """Only a local table row with an explicit academic title and person link."""
    rows = []
    base = meta.get('finalUrl', meta['sourceUrl'])
    for row in DOM(markup).main().walk():
        if row.tag != 'tr':
            continue
        text = row.text()
        title = re.search(r'\b(?:(?:Assistant|Associate|Adjunct|Clinical|Research|Teaching|Distinguished|Emeritus|Visiting)\s+)*(?:Professor|Lecturer)(?:\s+Emerit(?:us|a))?\b', text, re.I)
        if not title or len(text) > 1600:
            continue
        names = [(text_name(label), u) for _, label, u in links(row, base) if valid_person_name(text_name(label)) and individual_profile(u)]
        if len({name for name, _ in names}) != 1:
            continue
        name, profile = names[0]
        emails = re.findall(r'[\w.+%-]+@(?:[\w-]+\.)*ucsd\.edu', text)
        proof = evidence(meta, 'official_faculty_table_row', text)
        rows.append({'name': name, 'department': department, 'listedRole': title[0],
            'appointmentStatus': appointment_status(title[0]), 'directorySection': 'Faculty table',
            'sourceUrl': base, 'observedAt': meta['observedAt'], 'evidence': proof,
            'profileUrl': profile, 'namedLinkUrl': profile, 'email': emails[0] if len(set(emails)) == 1 else '',
            'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': []})
    return rows


def discover_math_profile_metadata(queue, item, meta, body):
    """Discover actual person links from Math's public metadata, never a roster.

    The endpoint also contains students and blank titles. Its name and location
    cannot qualify a faculty member. Only explicit relative profile links are
    followed; personal websites and arbitrary URLs in JSON are not traversed.
    """
    source = urllib.parse.urlsplit(item['url'])
    if source.hostname not in {'math.ucsd.edu', 'www.math.ucsd.edu'} or source.path.rstrip('/') != '/export/people/faculty' or source.query:
        return False
    if meta.get('status') != 'ok':
        return False
    final = urllib.parse.urlsplit(meta.get('finalUrl', ''))
    assessment = {'status': 'invalid_metadata', 'sourceUrl': meta.get('finalUrl', item['url']),
                  'observedAt': meta['observedAt'], 'bodySha256': meta.get('sha256'),
                  'profileLinks': 0, 'invalidRows': 0, 'facultyAppointmentsAsserted': 0}
    item['structuredProfileDiscovery'] = assessment
    if item['depth'] > 1 or not any(c['kind'] in {'directory', 'faculty_directory'} for c in item['contexts']):
        assessment['status'] = 'outside_directory_discovery_depth'
        return True
    if hashlib.sha256(body.encode()).hexdigest() != meta.get('sha256'):
        assessment['status'] = 'capture_hash_mismatch'
        return True
    try:
        rows = json.loads(body)
    except (ValueError, TypeError):
        return True
    if final.hostname not in {'math.ucsd.edu', 'www.math.ucsd.edu'} or final.path.rstrip('/') != '/export/people/faculty' or final.query or not isinstance(rows, list) or len(rows) > 1000:
        return True
    targets = set()
    for index, row in enumerate(rows):
        path = row.get('view_node_1', '') if isinstance(row, dict) else ''
        if not isinstance(path, str) or not re.fullmatch(r'/people/profiles/[a-zA-Z0-9_-]+', path):
            assessment['invalidRows'] += 1
            continue
        target = safe_url(urllib.parse.urljoin(meta['finalUrl'], path))
        observation = {'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'], 'bodySha256': meta.get('sha256'),
                       'jsonPointer': '/' + str(index), 'profilePathAsListed': path,
                       'recordIdAsListed': row.get('nid_1'), 'publicEmailAsListed': row.get('field_work_email', ''),
                       'titleAsListed': row.get('field_person_title', ''), 'classification': 'person_metadata_not_faculty_qualification'}
        queue.add(target, 'Mathematics', 'new_faculty_profile', meta['finalUrl'], item['depth'] + 1)
        target_item = queue.state['items'][url_key(target)]
        observations = target_item.setdefault('sourceMetadataObservations', [])
        if observation not in observations:
            observations.append(observation)
        targets.add(target)
    assessment.update(status='metadata_links_discovered', metadataRows=len(rows), profileLinks=len(targets),
                      titlesAsListed=dict(Counter(str(r.get('field_person_title', '')) for r in rows if isinstance(r, dict))))
    return True


def profiles_identity_heading(dom):
    """The production Profiles name is h2 inside pageTitle; h1 is site chrome."""
    nodes = list(dom.main().walk())
    primary = [n.text() for n in nodes if n.tag == 'h2' and n.parent and 'pageTitle' in n.parent.attrs.get('class', '').split()]
    fallback = [n.text() for n in nodes if n.tag == 'h1']
    for headings, method in [(primary, 'profiles_page_title_h2'), (fallback, 'profile_person_h1')]:
        names = list(dict.fromkeys(h for h in headings if h and len(h) < 160 and (method == 'profiles_page_title_h2' or valid_person_name(h)) and not re.search(r'\bsearch\b|\bresults\b|\babout\b|\bhelp\b|UCSD Profiles', h, re.I)))
        if names:
            return (names[0], method) if len(names) == 1 else ('', 'ambiguous_identity_headings')
    return '', 'missing_person_heading'


def profiles_appointment(meta, markup):
    """Read the explicit appointment table, never titles in a biography/nav."""
    dom = DOM(markup)
    name, heading_method = profiles_identity_heading(dom)
    values = {}
    for node in dom.main().walk():
        if node.tag != 'tr':
            continue
        cells = [c for c in node.children if hasattr(c, 'tag') and c.tag in {'th', 'td'}]
        if len(cells) == 2 and cells[0].tag == 'th':
            values.setdefault(cells[0].text(), cells[1].text())
    title, school = values.get('Title(s)', ''), values.get('School', '')
    assessment = {'nameAsDisplayed': name, 'identityHeadingMethod': heading_method, 'titleAsListed': title, 'schoolAsListed': school,
                  'sourceUrl': meta.get('finalUrl', meta['sourceUrl']), 'observedAt': meta['observedAt']}
    if not name or not title:
        return {**assessment, 'status': 'missing_identity_or_appointment_table'}, None
    if not valid_person_name(name):
        return {**assessment, 'status': 'profile_identity_heading_requires_review'}, None
    if not academic_title_clause(title):
        return {**assessment, 'status': 'academic_title_clause_requires_review' if re.search(r'\bprofessor\b|\bprof\b|\blecturer\b', title, re.I) else 'no_explicit_faculty_title_captured'}, None
    if not (school.lower().startswith('vc-') or re.search(r'UC\s*San\s*Diego|University of California.{0,15}San Diego|School of|Jacobs|Academic Affairs', school, re.I)):
        return {**assessment, 'status': 'academic_title_ucsd_unit_unconfirmed'}, None
    unit = title.split(',', 1)[1].strip() if ',' in title else ''
    unit = re.split(r'\b(?:(?:Assistant|Associate|Adjunct|Clinical|Teaching|Research)\s+)*(?:Professor|Lecturer)\b', unit, flags=re.I)[0].strip(' ,;')
    unit = re.sub(r'^Department of\s+', '', unit, flags=re.I)
    if not unit and re.search(r'\bof\s+', title):
        unit = re.split(r'\bof\s+', title, maxsplit=1, flags=re.I)[1].split(',')[0].strip()
    def dept_key(value):
        return clean(re.sub(r'\band\b', '', clean(value).lower().replace('&', ' ')))
    department = next((d['name'] for d in json.loads((ROOT / 'data/ucsd/departments.json').read_text())['departments'] if dept_key(d['name']) == dept_key(unit)), 'Unknown')
    if department == 'Unknown' and re.search(r'Salk|Scripps Research|Burnham|Sanford|University of (?!California)|Harvard|Stanford', title, re.I):
        return {**assessment, 'status': 'partner_institution_appointment_requires_review'}, None
    proof = evidence(meta, 'official_profiles_explicit_appointment_table', f'{name} | Title(s): {title} | School: {school}')
    assessment.update(status='explicit_faculty_appointment_as_listed', departmentAsListed=unit, mappedDepartment=department)
    return assessment, {'name': name, 'department': department, 'departmentExplicitlyListed': bool(unit),
        'departmentAsListed': unit, 'departmentMappingStatus': 'matched_saved_department' if department != 'Unknown' else 'explicit_unit_unmapped' if unit else 'unit_not_stated',
        'profileDiscovery': True, 'discoveryId': 'ucsd-profile-faculty-' + hashlib.sha256(canonical_url(proof['sourceUrl']).encode()).hexdigest()[:14], 'listedRole': title, 'appointmentStatus': appointment_status(title),
        'directorySection': 'UCSD Profiles explicit appointment table', 'sourceUrl': proof['sourceUrl'],
        'observedAt': meta['observedAt'], 'evidence': proof, 'profileUrl': proof['sourceUrl'],
        'namedLinkUrl': proof['sourceUrl'], 'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': []}


def academic_title_clause(title):
    return bool(re.search(r'(?:^|[,;|])\s*(?:(?:Department\s+)?(?:Chair|Dean|Director)\s+(?:and|&)\s+)?(?:(?:Assistant|Associate|Adjunct|Clinical|Research|Teaching|Distinguished|Emeritus|Visiting|Acting|Senior|HS|Health Sciences|Asst\.?|Assoc\.?)\s+)*(?:Professor|Prof|Lecturer)\b\.?', title, re.I))


class WireHeaders(dict):
    def __init__(self, headers, network_policy):
        super().__init__(headers)
        self.network_policy = network_policy


class PublicFetcher:
    """One bounded request per host at a time, TLS checked by system curl."""
    def __init__(self, cache, timeout=18, delay=1, clock=time.time, sleep=time.sleep):
        self.cache = Path(cache)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.timeout, self.delay, self.clock, self.sleep = timeout, max(1, delay), clock, sleep
        self.lock = threading.RLock()
        self.host_locks = defaultdict(threading.RLock)
        self.robot_locks = defaultdict(threading.RLock)
        self.last = {}
        self.robots = {}
        self.wire_requests = 0
        self.network_gate = HostRequestGate()

    def _paths(self, url, prefix=''):
        key = prefix + hashlib.sha256(url.encode()).hexdigest()
        return self.cache / (key + '.json'), self.cache / (key + '.html')

    def _load(self, path):
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None

    def _wire(self, url, minimum=1, max_bytes=2_000_000):
        host = urllib.parse.urlsplit(url).netloc
        stamp, _ = self._paths(host, 'clock-')
        with self.host_locks[host]:
            minimum = max(minimum, 10 if host == 'profiles.ucsd.edu' else self.delay)
            with self.network_gate.request_slot(url, minimum) as slot:
                self.last[host] = slot['lastRequestAt']
                # This is only a compatibility clock, never a cache observedAt.
                atomic_json(stamp, {'lastRequestAt': slot['lastRequestAt']})
                self.wire_requests += 1
                try:
                    code, headers, body, error = self._transport(url, max_bytes)
                except Exception:
                    slot.record_response(0, {})
                    raise
                policy = slot.record_response(code, headers)
                return code, WireHeaders(headers, policy), body, error

    def _transport(self, url, max_bytes):
        with tempfile.TemporaryDirectory() as tmp:
            body, headers = Path(tmp) / 'body', Path(tmp) / 'headers'
            result = subprocess.run([
                'curl', '--silent', '--show-error', '--proto', '=http,https',
                '--max-time', str(self.timeout), '--connect-timeout', '10',
                '--max-filesize', str(max_bytes), '--user-agent', UA,
                '--header', 'Accept: text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.1',
                '--dump-header', str(headers), '--output', str(body),
                '--write-out', '%{http_code}', url,
            ], capture_output=True, timeout=self.timeout + 5)
            content = body.read_bytes() if body.exists() else b''
            if len(content) > max_bytes:
                return 0, {}, '', 'response_exceeds_size_limit'
            # Skip proxy CONNECT and 1xx headers; use the last response block.
            raw = headers.read_text(errors='replace') if headers.exists() else ''
            blocks = re.split(r'\r?\n\r?\n', raw.strip())
            header = {}
            for line in blocks[-1].splitlines() if blocks else []:
                if ':' in line:
                    k, v = line.split(':', 1)
                    header[k.lower()] = v.strip()
            code = int(result.stdout or b'0')
            return code, header, content.decode('utf-8', 'replace'), clean(result.stderr.decode())[:220] if result.returncode else ''

    def _rules(self, url):
        p = urllib.parse.urlsplit(url)
        origin = f'{p.scheme}://{p.netloc}'
        with self.robot_locks[origin]:
            if origin in self.robots:
                if reusable_robots(self.robots[origin][1], self.clock()):
                    return self.robots[origin]
                del self.robots[origin]
            robots_url = origin + '/robots.txt'
            path, body_path = self._paths(robots_url, 'robots-')
            meta = self._load(path)
            body = body_path.read_text() if body_path.exists() else ''
            if not reusable_robots(meta, self.clock()):
                previous = meta
                attempts = (previous.get('attempts', 1) if previous and self.clock() - previous.get('retrievedEpoch', 0) <= 86400 else 0) + 1
                current, redirects = robots_url, []
                for _ in range(6):
                    code, headers, body, error = self._wire(current, max_bytes=300_000)
                    if code not in REDIRECTS:
                        break
                    target = safe_url(urllib.parse.urljoin(current, headers.get('location', '')))
                    if not target or not urllib.parse.urlsplit(target).path.endswith('/robots.txt'):
                        error = 'robots_redirect_is_not_a_robots_file'
                        break
                    redirects.append({'from': current, 'to': target, 'httpStatus': code})
                    policy = getattr(headers, 'network_policy', {})
                    if policy.get('responseCooldownSet'):
                        redirects[-1]['retryAfterEpoch'] = policy['notBeforeEpoch']
                        self.network_gate.defer(target, policy['notBeforeEpoch'], 'redirect_retry_after')
                    current = target
                if code == 200 and body.lstrip().startswith('<'):
                    error = 'robots_response_is_html'
                if re.search(r'just a moment|verify you are human|access denied|attention required.{0,40}cloudflare', body[:15000], re.I):
                    error = 'access_challenge'
                meta = {'sourceUrl': robots_url, 'observedAt': now(), 'httpStatus': code,
                        'retrievedEpoch': self.clock(), 'error': error, 'redirects': redirects,
                        'attempts': attempts,
                        'status': 'checked' if code == 200 and not error else 'not_found' if code in {404, 410} else 'unavailable'}
                if previous:
                    meta['attemptHistory'] = previous.get('attemptHistory', []) + [{k: v for k, v in previous.items() if k != 'attemptHistory'}]
                if getattr(headers, 'network_policy', {}).get('responseCooldownSet'):
                    meta['retryAfterEpoch'] = headers.network_policy['notBeforeEpoch']
                body_path.write_text(body)
                atomic_json(path, meta)
            rp = None
            if meta['status'] == 'checked':
                rp = urllib.robotparser.RobotFileParser(robots_url)
                rp.parse(body.splitlines())
            self.robots[origin] = (rp, meta)
            return rp, meta

    def fetch(self, raw):
        url = safe_url(raw)
        meta_path, body_path = self._paths(url)
        old = self._load(meta_path)
        if old and old.get('status') == 'ok' and authentication_target(old.get('finalUrl', '')):
            old.update(status='authentication_required', blockedUrl=old['finalUrl'], contentAssessmentAt=now())
            atomic_json(meta_path, old)
        if old and old.get('status') == 'ok' and body_path.exists() and self.clock() - old.get('retrievedEpoch', 0) < 30 * 86400:
            return old, body_path.read_text()
        meta = {'sourceUrl': url, 'observedAt': now(), 'status': 'error', 'redirects': []}
        current, body = url, ''
        for _ in range(7):
            if not current:
                meta.update(status='invalid_url')
                break
            if authentication_target(current):
                meta.update(status='authentication_required', blockedUrl=current, reason='public_source_redirects_to_login; no_login_attempted')
                break
            rp, robot_meta = self._rules(current)
            meta['robots'] = robot_meta
            if robot_meta['status'] == 'unavailable':
                meta.update(status='robots_unavailable', blockedUrl=current)
                if retryable_fetch(meta):
                    meta['retryAfterEpoch'] = robots_retry_at(robot_meta)
                break
            if rp and not rp.can_fetch(UA, current):
                meta.update(status='robots_denied', blockedUrl=current)
                break
            delay = max(self.delay, (rp.crawl_delay(UA) or rp.crawl_delay('*') or 0) if rp else 0)
            code, headers, body, error = self._wire(current, delay)
            if code in REDIRECTS:
                target = safe_url(urllib.parse.urljoin(current, headers.get('location', '')))
                meta['redirects'].append({'from': current, 'to': target, 'httpStatus': code})
                policy = getattr(headers, 'network_policy', {})
                if policy.get('responseCooldownSet'):
                    meta['redirects'][-1]['retryAfterEpoch'] = policy['notBeforeEpoch']
                    if target:
                        self.network_gate.defer(target, policy['notBeforeEpoch'], 'redirect_retry_after')
                current = target
                continue
            meta.update(httpStatus=code, finalUrl=current, contentType=headers.get('content-type', ''), error=error)
            if error:
                meta['status'] = 'fetch_error'
            elif code != 200:
                meta['status'] = 'http_error'
            elif not any(t in meta['contentType'].lower() for t in ['html', 'text/plain', 'json', 'xml']):
                meta['status'] = 'unsupported_content'
            elif re.search(r'just a moment|verify you are human|access denied|attention required.{0,40}cloudflare', body[:15000], re.I):
                meta['status'] = 'access_challenge'
            else:
                meta['status'] = 'ok'
                meta['sha256'] = hashlib.sha256(body.encode()).hexdigest()
            if getattr(headers, 'network_policy', {}).get('responseCooldownSet'):
                meta['retryAfterEpoch'] = headers.network_policy['notBeforeEpoch']
            elif code in RETRY:
                value = headers.get('retry-after', '')
                try:
                    retry = float(value)
                except ValueError:
                    try:
                        import email.utils
                        retry = email.utils.parsedate_to_datetime(value).timestamp() - self.clock()
                    except (ValueError, TypeError):
                        retry = 60
                meta['retryAfterEpoch'] = self.clock() + max(60, retry)
            break
        else:
            meta.update(status='redirect_limit', blockedUrl=current)
        meta.update(observedAt=now(), retrievedEpoch=self.clock())
        if meta['status'] == 'ok':
            temp = body_path.with_suffix('.html.tmp')
            temp.write_text(body)
            os.replace(temp, body_path)
        atomic_json(meta_path, meta)
        return meta, body if meta['status'] == 'ok' else ''


class Queue:
    def __init__(self, path):
        self.path = path
        self.state = json.loads(path.read_text()) if path.exists() else {'schemaVersion': 1, 'startedAt': now(), 'items': {}, 'labCandidates': {}, 'centers': {}, 'facultyListings': [], 'sources': {}}
        for item in self.state['items'].values():
            if item['state'] == 'running':
                item['state'] = 'pending'
            if item.get('fetch', {}).get('status') == 'ok' and authentication_target(item['fetch'].get('finalUrl', '')):
                item['fetch'].update(status='authentication_required', contentAssessmentAt=now(), reason='response_is_a_login_page; no_credentials_or_forms_submitted')
                item['state'] = 'unresolved'
            meta = item.get('fetch', {})
            if item['state'] == 'unresolved' and item.get('attempts', 0) < 3 and retryable_fetch(meta):
                if meta.get('status') == 'robots_unavailable':
                    # Migrate old receipts without changing their source observation.
                    deadline = robots_retry_at(meta['robots'])
                else:
                    deadline = meta.get('retryAfterEpoch', 0)
                item.update(state='pending', retryAt=max(deadline, time.time() + 30 * 2 ** item.get('attempts', 0)))
            if item['state'] == 'unresolved' and item.get('fetch', {}).get('status') == 'robots_unavailable' and item.get('fetch', {}).get('robots', {}).get('httpStatus') in REDIRECTS and 'redirects' not in item['fetch']['robots']:
                item['state'] = 'pending'

    def add(self, url, department, kind, source='', depth=0, candidate_id='', professor_id='', identity_depth=None):
        url = safe_url(url)
        if not url or re.search(r'\.(?:pdf|zip|png|jpe?g|gif|xlsx?|docx?|pptx?|bib|mp4)(?:$|\?)', url, re.I):
            return
        key = url_key(url)
        entry = self.state['items'].setdefault(key, {'url': url, 'state': 'pending', 'attempts': 0, 'depth': depth, 'contexts': []})
        entry['depth'] = min(depth, entry['depth'])
        context = {'department': department, 'kind': kind, 'sourceUrl': source, 'candidateId': candidate_id, 'professorId': professor_id}
        if identity_depth is not None:
            context['identityDepth'] = identity_depth
        if context not in entry['contexts']:
            entry['contexts'].append(context)
        if kind == 'profile_identity_review' and entry['state'] == 'retained_prior_evidence':
            # A specific identity/field review requires its actual response.
            # Preserve the older retention receipt and reuse a fresh imported
            # capture through the ordinary fetch/cache path under the lease.
            previous = entry.pop('retainedEvidence', None)
            if previous:
                entry.setdefault('retainedEvidenceHistory', []).append(previous)
            entry.update(state='pending', identityReviewRequestedAt=now())

    def seed(self, atlas):
        for d in json.loads((ROOT / 'data/ucsd/departments.json').read_text())['departments']:
            self.add(d['homepage'], d['name'], 'department')
        for d in json.loads((ROOT / 'data/ucsd/source-candidates.json').read_text())['departments']:
            for c in d['candidates']:
                if c.get('discovered') and eligible_directory(c.get('linkText', ''), urllib.parse.urlsplit(c['url']).path):
                    self.add(c['url'], d['department'], 'directory', c.get('sourceUrl', ''))
        for source in SOURCES:
            self.add(source[2], source[1], 'faculty_directory')
        for lab in atlas['labs']:
            self.add(lab['labWebsiteUrl'], lab['department'], 'lab_destination')
            for url in lab.get('sourceUrls', []):
                if official(url) and DIRECTORY.search(urllib.parse.urlsplit(url).path) and not EXCLUDE.search(urllib.parse.urlsplit(url).path):
                    self.add(url, lab['department'], 'directory')
        candidates = json.loads((ROOT / 'data/ucsd/lab-expansion-candidates.json').read_text())['candidates']
        for c in candidates:
            if c['status'] != 'unverified':
                continue
            for url in [c.get('labWebsiteUrl', ''), c.get('officialAffiliationSourceUrl', '')] + c.get('sourceUrls', []):
                self.add(url, c['department'], 'unresolved_candidate', candidate_id=c['candidate_id'])
        capture = json.loads((ROOT / 'data/ucsd/lab-evidence.json').read_text())
        for p in atlas['professors']:
            if 'catalog.ucsd.edu' in p['officialProfileUrl']:
                continue
            status = capture.get('byProfessorId', {}).get(p['id'], {}).get('verification', {}).get('status')
            if status not in {'verified', 'catalog_only'}:
                self.add(p['officialProfileUrl'], p['department'], 'profile', professor_id=p['id'])
        for u in [
            'https://research.ucsd.edu/ORU/index.html',
            'https://medschool.ucsd.edu/research/centers/index.html',
            'https://vchs.ucsd.edu/institutes-centers/index.html',
            'https://jacobsschool.ucsd.edu/research/centers-institutes',
            'https://bioinformatics.ucsd.edu/about/departments',
            'https://inc.ucsd.edu/research/centers_labs.php',
            'https://cse.ucsd.edu/research/associated-centers-and-research-units',
            'https://psychiatry.ucsd.edu/research/programs-centers/index.html',
        ]:
            self.add(u, 'Interdisciplinary', 'institute_directory')
        extra = ROOT / 'data/ucsd/coverage-20261016-additional-sources.json'
        if extra.exists():
            for source in json.loads(extra.read_text())['sources']:
                self.add(source['url'], source['department'], source.get('kind', 'directory'), source.get('sourceUrl', ''), depth=source.get('depth', 0), candidate_id=source.get('candidateId', ''), professor_id=source.get('professorId', ''), identity_depth=source.get('identityDepth'))
        sitemap = ROOT / 'data/ucsd/profile-sitemap-20261016.json'
        if sitemap.exists():
            for url in json.loads(sitemap.read_text()).get('urls', []):
                p = urllib.parse.urlsplit(url)
                if p.hostname == 'profiles.ucsd.edu' and p.path.count('/') == 1 and p.path.strip('/').lower() not in {'', 'search', 'about', 'login', 'error', 'profile', 'display', 'activity', 'orng', 'shindigorng', 'sparql'} and not p.path.lower().endswith(('.aspx', '.xml', '.txt', '.ashx', '.asmx')):
                    self.add(url, 'Unknown', 'profile_discovery', 'https://profiles.ucsd.edu/sitemap.xml')

    def save(self):
        self.state['updatedAt'] = now()
        self.state['counts'] = dict(Counter(x['state'] for x in self.state['items'].values()))
        self.state['collectionState'] = 'in_progress' if any(x['state'] in {'pending', 'running'} for x in self.state['items'].values()) else 'completed'
        atomic_json(self.path, self.state)

    def retain_recent_profiles(self, atlas):
        if not hasattr(self, '_verified_profiles'):
            capture = json.loads((ROOT / 'data/ucsd/lab-evidence.json').read_text())
            verified = {}
            for p in atlas['professors']:
                patch = capture.get('byProfessorId', {}).get(p['id'], {})
                v = patch.get('verification', {})
                if v.get('status') != 'verified' or not v.get('identityMatched'):
                    continue
                try:
                    age = dt.datetime.now(dt.UTC) - dt.datetime.fromisoformat(v['observedAt'])
                except (ValueError, KeyError, TypeError):
                    continue
                if dt.timedelta(0) <= age <= dt.timedelta(days=30):
                    for u in [p['officialProfileUrl'], v.get('sourceUrl', '')]:
                        verified[url_key(u)] = {'professorId': p['id'], 'verification': v}
            self._verified_profiles = verified
        verified = self._verified_profiles
        for key, item in self.state['items'].items():
            if item['state'] == 'pending' and all(c['kind'] in {'new_faculty_profile', 'profile', 'profile_discovery'} for c in item['contexts']) and key in verified:
                item.update(state='retained_prior_evidence', retainedEvidence=verified[key])


def discover_lab_identity_pages(queue, item, meta, dom):
    """Identity depth starts at the lab, independent of directory depth."""
    base = meta.get('finalUrl', item['url'])
    if urllib.parse.urlsplit(base).hostname == 'profiles.ucsd.edu':
        return
    policy = getattr(queue, 'scope_policy', None)
    if policy and not policy.can_expand(item):
        return
    if not policy and not official(base):
        return
    for context in list(item['contexts']):
        kind = context['kind']
        if kind == 'identity_page':
            depth = context.get('identityDepth', 1)
        elif kind in {'unresolved_candidate', 'discovered_lab', 'lab_destination', 'lab_link_candidate'}:
            depth = 0
        else:
            continue
        if depth >= 2:
            continue
        for _, label, url in discovery_links(dom.root, base):
            if urllib.parse.urlsplit(url).netloc != urllib.parse.urlsplit(base).netloc or url_key(url) == url_key(base):
                continue
            named = re.fullmatch(r'home|about(?: us| the lab)?|(?:our |meet our |lab |group )?(?:people|team|members)|leadership|contact(?: us)?|principal investigator|our lab|research group', label, re.I)
            image_home = not label and urllib.parse.urlsplit(url).path.rstrip('/') == '/home'
            if named or image_home:
                queue.add(url, context['department'], 'identity_page', base, 2, context.get('candidateId', ''), identity_depth=depth + 1)


def replay_identity_discovery(queue, cache):
    if queue.state.get('identityDiscoveryVersion', 0) >= 2:
        return
    # Two passes allow newly recognized cached first-hop pages to contribute
    # a second identity hop. No transport or fact extraction occurs here.
    before = len(queue.state['items'])
    for _ in range(2):
        for item in list(queue.state['items'].values()):
            if item['state'] != 'done' or item.get('fetch', {}).get('status') != 'ok':
                continue
            if not any(c['kind'] in {'unresolved_candidate', 'discovered_lab', 'lab_destination', 'lab_link_candidate', 'identity_page'} for c in item['contexts']):
                continue
            path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
            if path.exists():
                discover_lab_identity_pages(queue, item, item['fetch'], DOM(path.read_text()))
    queue.state.update(identityDiscoveryVersion=2, identityDiscoveryReplay={'version': 2, 'at': now(), 'newQueueUrls': len(queue.state['items']) - before, 'sourceObservationDatesPreserved': True, 'wireRequests': 0})
    queue.save()


def mark_scope_excluded(item, reason):
    if item['state'] == 'scope_excluded' and item.get('scopeAssessment', {}).get('reason') != reason:
        old = item['scopeAssessment']
        item.setdefault('scopeAssessmentHistory', []).append(old)
        item['scopeAssessment'] = {**old, 'reason': reason, 'reviewedAt': now()}
    elif item['state'] != 'scope_excluded':
        item['scopeAssessment'] = {'status': 'excluded', 'reason': reason, 'reviewedAt': now(),
                                   'previousQueueState': item['state'], 'sourceObservationsPreserved': True,
                                   'policyVersion': 1}
        item['state'] = 'scope_excluded'


def audit_queue_scope(queue, *, save=True):
    policy = queue.scope_policy
    restored = []
    for item in queue.state['items'].values():
        reason = policy.request_reason(item)
        if not reason and item.get('fetch', {}).get('status') == 'ok':
            reason = policy.destination_reason(item)
        if reason:
            mark_scope_excluded(item, reason)
        elif item['state'] == 'scope_excluded':
            # New, specific source association or explicit review can admit a
            # previously held candidate without losing its earlier disposition.
            old = item.pop('scopeAssessment')
            item.setdefault('scopeAssessmentHistory', []).append(old)
            previous = old.get('previousQueueState', 'pending')
            item['state'] = 'pending' if previous in {'pending', 'running'} else previous
            restored.append(item)
    queue.state['scopePolicyVersion'] = 1
    if save:
        queue.save()
    return restored


def reassess_scope(queue, cache):
    """Checkpoint new associations and their cached navigation together."""
    before = len(queue.state['items'])
    restored = audit_queue_scope(queue, save=False)
    skipped = []
    for item in restored:
        if item['state'] != 'done' or item.get('fetch', {}).get('status') != 'ok':
            continue
        path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
        if path.exists():
            discover_lab_identity_pages(queue, item, item['fetch'], DOM(path.read_text()))
        else:
            skipped.append({'url': item['url'], 'reason': 'captured_body_missing_for_identity_navigation'})
    stamp = now()
    if restored:
        queue.state.setdefault('scopeReassessmentHistory', []).append({'at': stamp, 'restoredUrls': [item['url'] for item in restored],
            'newQueueUrls': len(queue.state['items']) - before, 'navigationSkipped': skipped,
            'wireRequests': 0, 'sourceObservationDatesPreserved': True})
    queue.state['scopeLastReassessedAt'] = stamp
    queue.save()


def analyze_profile_appointment(queue, item, meta, body, dom=None):
    dom = dom or DOM(body)
    base = meta.get('finalUrl', meta['sourceUrl'])
    assessment, row = profiles_appointment(meta, body)
    old = item.get('profileEligibility')
    if old and old != assessment:
        item.setdefault('profileEligibilityHistory', []).append(old)
    item['profileEligibility'] = assessment
    if row and row not in queue.state['facultyListings']:
        queue.state['facultyListings'].append(row)
    discover_profile_websites(queue, meta, dom, row)


def discover_profile_websites(queue, meta, dom, row, only_targets=None):
    base = meta.get('finalUrl', meta['sourceUrl'])
    for _, label, url in links(dom.main(), base):
        if only_targets is not None and url not in only_targets:
            continue
        explicit_lab = bool(re.fullmatch(r'(?:my |our |visit )?(?:lab(?:oratory)?|research group)(?: web ?site| site| home ?page)?', label, re.I))
        personal = row and re.fullmatch(r'(?:my |personal |research |faculty |visit )?(?:web ?site|home ?page)', label, re.I)
        if url and (explicit_lab or personal) and urllib.parse.urlsplit(url).hostname != 'profiles.ucsd.edu':
            queue.add(url, row['department'] if row else 'Unknown', 'lab_link_candidate', base, 1)
            target = queue.state['items'].get(url_key(url))
            if target:
                proof = evidence(meta, 'official_profile_website_link_discovery_only', label + ' → ' + url)
                observed = target.setdefault('discoveryEvidence', [])
                if proof not in observed:
                    observed.append(proof)


def replay_profile_qualifications(queue, cache):
    if queue.state.get('profileQualificationVersion', 0) >= 2:
        return
    initial_rows, initial_urls = len(queue.state['facultyListings']), len(queue.state['items'])
    captures = 0
    for item in list(queue.state['items'].values()):
        meta = item.get('fetch', {})
        if meta.get('status') != 'ok' or urllib.parse.urlsplit(meta.get('finalUrl', '')).hostname != 'profiles.ucsd.edu':
            continue
        path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
        if path.exists():
            analyze_profile_appointment(queue, item, meta, path.read_text())
            captures += 1
    queue.state.update(profileQualificationVersion=2, profileQualificationReplay={'version': 2, 'at': now(), 'capturesRead': captures,
        'newFacultyRows': len(queue.state['facultyListings']) - initial_rows, 'newQueueUrls': len(queue.state['items']) - initial_urls,
        'wireRequests': 0, 'sourceObservationsPreserved': True})
    queue.save()


def replay_literal_uri_discovery(queue, cache, atlas):
    """Replay only captures containing links the old transport normalizer changed.

    Original observations and metadata remain untouched. New literal URI leads
    still require their own robots, transport and identity checks under the lease.
    """
    if queue.state.get('literalUriDiscoveryVersion', 0) >= 1:
        return
    kinds = {'department', 'directory', 'faculty_directory', 'institute_directory',
             'profile', 'new_faculty_profile', 'profile_discovery', 'profile_identity_review',
             'lab_destination', 'lab_link_candidate', 'discovered_lab', 'identity_page'}
    selected = []
    changed_links = set()
    for item in list(queue.state['items'].values()):
        meta = item.get('fetch', {})
        if item['state'] != 'done' or meta.get('status') != 'ok' or not any(c['kind'] in kinds for c in item['contexts']):
            continue
        path = Path(cache) / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != meta.get('sha256'):
            raise ValueError('Literal URI replay requires the unchanged original capture: ' + item['url'])
        body = path.read_text()
        affected = set()
        dom = DOM(body)
        discovery_root = dom.main() if urllib.parse.urlsplit(meta.get('finalUrl', item['url'])).hostname == 'profiles.ucsd.edu' else dom.root
        for _, _, target in discovery_links(discovery_root, meta.get('finalUrl', item['url'])):
            parsed = urllib.parse.urlsplit(target)
            if (parsed.scheme == 'http' and (parsed.hostname or '').endswith('ucsd.edu')) or parsed.netloc in {'www.cogsci.ucsd.edu', 'www.jacobsschool.ucsd.edu'}:
                affected.add(target)
        if affected:
            selected.append((item, meta, body, affected))
            changed_links.update(affected)
    before_urls, before_labs, before_rows = len(queue.state['items']), len(queue.state['labCandidates']), len(queue.state['facultyListings'])
    by_department, by_profile = defaultdict(list), defaultdict(list)
    for person in atlas['professors']:
        by_department[person['department']].append(person)
        by_profile[canonical_url(person['officialProfileUrl'])].append(person)
    for item, meta, body, affected in selected:
        if urllib.parse.urlsplit(meta.get('finalUrl', item['url'])).hostname == 'profiles.ucsd.edu':
            dom = DOM(body)
            assessment = item.get('profileEligibility')
            if not assessment or assessment.get('observedAt') != meta['observedAt']:
                assessment, _ = profiles_appointment(meta, body)
            row = {'department': assessment.get('mappedDepartment', 'Unknown')} if assessment.get('status') == 'explicit_faculty_appointment_as_listed' else None
            discover_profile_websites(queue, meta, dom, row, affected)
            # Retain any separately named lab lead that the old general
            # directory parser found in a biography, without inferred PI links.
            if any(url in affected and re.search(r'lab|laborator|research group', label, re.I) for _, label, url in links(dom.main(), meta['finalUrl'])):
                for lab in parse_directory(row['department'] if row else 'Unknown', meta, body, []):
                    if lab['labWebsiteUrl'] not in affected:
                        continue
                    key = url_key(lab['labWebsiteUrl'])
                    proof = {'department': lab['department'], 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'], 'label': lab['labName'], 'fieldEvidence': lab['fieldEvidence'], 'professorIds': []}
                    candidate = queue.state['labCandidates'].setdefault(key, {'record': lab, 'observations': [], 'state': 'needs_identity_review'})
                    if proof not in candidate['observations']:
                        candidate['observations'].append(proof)
                    queue.add(lab['labWebsiteUrl'], lab['department'], 'discovered_lab', meta['finalUrl'], 1)
            continue
        # parse_directory can associate a professor only through a direct
        # profile link or an exact name in the source department. Keep both
        # sets; avoid rebuilding/scanning the entire roster for every card.
        people = {p['id']: p for c in item['contexts'] for p in by_department[c['department']]}
        for _, _, target in links(DOM(body).main(), meta.get('finalUrl', item['url'])):
            people.update({p['id']: p for p in by_profile.get(canonical_url(target), [])})
        narrowed = {**atlas, 'professors': list(people.values())}
        analyze(queue, item, meta, body, narrowed)
    queue.state.update(literalUriDiscoveryVersion=1, literalUriDiscoveryReplay={
        'at': now(), 'version': 1, 'capturesRead': len(selected), 'changedLiteralLinks': len(changed_links),
        'newQueueUrls': len(queue.state['items']) - before_urls,
        'newLabCandidates': len(queue.state['labCandidates']) - before_labs,
        'newFacultyListingObservations': len(queue.state['facultyListings']) - before_rows,
        'wireRequests': 0, 'sourceObservationsPreserved': True})
    queue.save()


def analyze(queue, item, meta, body, atlas):
    if not body or meta['status'] != 'ok':
        return
    if discover_math_profile_metadata(queue, item, meta, body):
        return
    dom = DOM(body)
    main = dom.main()
    base = meta.get('finalUrl', meta['sourceUrl'])
    headings = [n.text() for n in main.walk() if n.tag in {'h1', 'h2', 'h3'} and len(n.text()) < 250]
    title = next((n.text() for n in dom.root.walk() if n.tag == 'title'), '')
    item['page'] = {'title': title, 'headings': headings[:30], 'mainTextExcerpt': main.text()[:800]}
    if getattr(queue, 'scope_policy', None):
        queue.scope_policy.observe(item)
        reason = queue.scope_policy.destination_reason(item)
        if reason:
            mark_scope_excluded(item, reason)
            return
    if urllib.parse.urlsplit(base).hostname == 'profiles.ucsd.edu':
        analyze_profile_appointment(queue, item, meta, body, dom)
    contexts = list(item['contexts'])
    for context in contexts:
        dept, kind = context['department'], context['kind']
        if official(base) and kind not in {'lab_destination', 'profile', 'identity_page', 'profile_identity_review'} and item['depth'] <= 2:
            # Reuse only proven explicit local directory records; never infer PIs.
            for lab in parse_directory(dept, meta, body, atlas['professors']):
                lab['principalInvestigator'] = lab['principalInvestigatorProfileUrl'] = 'Not found'
                lab.get('fieldEvidence', {}).pop('principalInvestigator', None)
                lab['relationshipType'] = 'official_directory_same_record'
                key = url_key(lab['labWebsiteUrl'])
                old = queue.state['labCandidates'].get(key)
                proof = {'department': dept, 'sourceUrl': base, 'observedAt': meta['observedAt'], 'label': lab['labName'], 'fieldEvidence': lab['fieldEvidence'], 'professorIds': lab.get('professorIds', [])}
                if not old:
                    queue.state['labCandidates'][key] = {'record': lab, 'observations': [proof], 'state': 'needs_identity_review'}
                elif proof not in old['observations']:
                    old['observations'].append(proof)
                queue.add(lab['labWebsiteUrl'], dept, 'discovered_lab', base, item['depth'] + 1)
            # Campus card template is used only on faculty-labelled sources.
            if re.search(r'faculty|professors|emerit', base + ' ' + title, re.I):
                adapter = next((s for s in SOURCES if url_key(s[2]) == url_key(item['url'])), None)
                adapter = adapter or ('coverage-' + dept, dept, base, 'profile-listing-card', 'cascade')
                rows = card_records(adapter, meta, body) + faculty_table_rows(dept, meta, body)
                queue.state['facultyListings'].extend(r for r in rows if r not in queue.state['facultyListings'])
                for row in rows:
                    if row['profileUrl']:
                        queue.add(row['profileUrl'], dept, 'new_faculty_profile', base, item['depth'] + 1)
            if item['depth'] < 2:
                # Navigation may discover a queue target, but supplies no facts.
                for _, label, url in discovery_links(dom.root, base):
                    if not official(url) or not label or len(label) > 130:
                        continue
                    path = urllib.parse.urlsplit(url).path
                    if eligible_directory(label, path):
                        queue.add(url, dept, 'directory', base, item['depth'] + 1)
        if official(base):
            for node, label, url in links(main, base):
                if not url or not re.search(r'\b(?:center|centre|institute)\b', label, re.I) or len(label) > 160:
                    continue
                if EXCLUDE.search(label) or re.fullmatch(r'(?:Research )?(?:Centers?|Institutes?)(?: and Institutes)?', label, re.I):
                    continue
                key = url_key(url)
                proof = evidence(meta, 'official_directory_explicit_center_link', label + ' → ' + url)
                entity = queue.state['centers'].setdefault(key, {'id': 'ucsd-center-' + hashlib.sha256(key.encode()).hexdigest()[:14], 'entityType': 'center_or_institute', 'name': label, 'url': url, 'observations': []})
                observation = {'department': dept, 'evidence': proof}
                if observation not in entity['observations']:
                    entity['observations'].append(observation)
    discover_lab_identity_pages(queue, item, meta, dom)


def write_report(queue, path):
    by_dept = defaultdict(Counter)
    for item in queue.state['items'].values():
        for dept in {c['department'] for c in item['contexts']}:
            by_dept[dept][item['state']] += 1
    report = {'schemaVersion': 1, 'generatedAt': now(), 'scope': __doc__, 'counts': queue.state.get('counts', {}),
              'sourceStatuses': dict(Counter(x.get('fetch', {}).get('status', x['state']) for x in queue.state['items'].values() if x['state'] != 'scope_excluded')),
              'scopeExcludedTransportStatuses': dict(Counter(x.get('fetch', {}).get('status', 'not_requested') for x in queue.state['items'].values() if x['state'] == 'scope_excluded')),
              'labCandidates': len(queue.state['labCandidates']), 'centersAndInstitutes': len(queue.state['centers']),
              'facultyListings': len(queue.state['facultyListings']), 'departments': {k: dict(v) for k, v in sorted(by_dept.items())},
              'structuredPersonDiscovery': [item['structuredProfileDiscovery'] for item in queue.state['items'].values() if item.get('structuredProfileDiscovery')],
              'profileEligibilityStatuses': dict(Counter(x.get('profileEligibility', {}).get('status', x['state']) for x in queue.state['items'].values() if any(c['kind'] == 'profile_discovery' for c in x['contexts']))),
              'blocked': [{'url': x['url'], 'status': x['fetch']['status'], 'httpStatus': x['fetch'].get('httpStatus'), 'error': x['fetch'].get('error'), 'blockedUrl': x['fetch'].get('blockedUrl')} for x in queue.state['items'].values() if x['state'] == 'unresolved']}
    atomic_json(path, report)
    excluded = [{'url': item['url'], 'scopeAssessment': item['scopeAssessment'], 'contexts': item['contexts'],
                 'fetch': item.get('fetch'), 'discoveryEvidence': item.get('discoveryEvidence', []),
                 'rootSources': [{'requestedUrl': r['url'], 'observedFinalUrl': r.get('fetch', {}).get('finalUrl'),
                                  'sourceContexts': r['contexts'], 'sourceTitle': r.get('page', {}).get('title')}
                                 for r in queue.scope_policy.roots(item)] if getattr(queue, 'scope_policy', None) else [],
                 'labDiscoveryObservations': queue.state['labCandidates'].get(url_key(item['url']), {}).get('observations', [])}
                for item in queue.state['items'].values() if item['state'] == 'scope_excluded']
    atomic_json(ROOT / 'data/ucsd/coverage-20261016-scope-exclusions.json', {'schemaVersion': 1, 'generatedAt': now(),
                'count': len(excluded), 'items': excluded,
                'policy': 'Scope dispositions are terminal queue states, not closure/absence claims. Original discovery contexts, captures and source times remain intact. New specific UCSD association evidence can make a held candidate eligible again.'})
    progress = ROOT / 'docs/operations/PROGRESS-20261016.md'
    old = progress.read_text() if progress.exists() else ''
    marker = '\n<!-- coverage-queue -->\n'
    old = old.split(marker)[0]
    text = f'\n## Public collection queue (updated {now()})\n\n'
    text += f'- Queue: {len(queue.state["items"])} unique URLs; states {queue.state.get("counts", {})}.\n'
    text += f'- Discovery: {report["labCandidates"]} lab candidates; {report["centersAndInstitutes"]} separate center/institute destinations; {report["facultyListings"]} explicit faculty cards. Discovery counts are not accepted additions.\n'
    text += '- Requests use system TLS validation, target robots checks at every redirect, one request per host at a time, >=1 second between requests, and >=10 seconds for UCSD Profiles. HTTP 403/challenges and robots refusals remain unresolved; they never imply closure.\n'
    text += '- Cache, host clocks, atomic queue checkpoints and response hashes: `.cache/coverage-20261016/`. Re-running the command resumes pending URLs and bounded transient retries without replacing observations.\n'
    text += '- Command: `python3 scripts/collect_ucsd_coverage.py --workers 8`; machine coverage: `data/ucsd/coverage-20261016-report.json`.\n'
    text += '- Next: finish eligible queue, review identity/dedup evidence, merge accepted additions with stable baseline IDs, validate data/references and static site.\n'
    progress.write_text(old + marker + text)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--cache', type=Path, default=ROOT / '.cache/coverage-20261016')
    cli.add_argument('--workers', type=int, default=8)
    cli.add_argument('--max-pages', type=int, default=0, help='0 drains the eligible queue')
    cli.add_argument('--timeout', type=float, default=18)
    cli.add_argument('--reparse-cached', action='store_true', help='Replay successful saved pages through current discovery rules; keeps original observation times')
    cli.add_argument('--reparse-profile-appointments', action='store_true', help='Replay only saved successful Profiles pages through the explicit appointment-table reader')
    args = cli.parse_args()
    with task_lease(args.cache / 'collector.lock'):
        collect(args)


def collect(args):
    atlas = json.loads((ROOT / 'data/research-atlas.json').read_text())
    queue = Queue(args.cache / 'queue.json')
    atomic_json(args.cache / 'process.json', {'pid': os.getpid(), 'startedAt': now()})
    queue.seed(atlas)
    queue.retain_recent_profiles(atlas)
    def optional_json(name):
        path = ROOT / 'data/ucsd' / name
        return json.loads(path.read_text()) if path.exists() else {}
    queue.scope_policy = ScopePolicy(queue.state, atlas, optional_json('coverage-20261016-decisions.json'), optional_json('legacy-lab-identity-review-20261016.json'), optional_json('lab-expansion-candidates.json'), optional_json('coverage-20261016-original-candidate-reviews.json'))
    reassess_scope(queue, args.cache)
    fetcher = PublicFetcher(args.cache / 'responses', args.timeout)
    clock_urls = []
    for item in queue.state['items'].values():
        clock_urls.append(item['url'])
        meta = item.get('fetch', {})
        clock_urls += [meta.get('finalUrl', ''), meta.get('robots', {}).get('sourceUrl', '')]
        for redirect in meta.get('redirects', []) + meta.get('robots', {}).get('redirects', []):
            clock_urls += [redirect.get('from', ''), redirect.get('to', '')]
    coordination = migrate_legacy_clocks(args.cache / 'responses', clock_urls, fetcher.network_gate, UA, queue.state['items'].values())
    coordination.update(state='active', activatedAt=now(), robotsAndRedirectsIncluded=True, profilesMinimumSeconds=10,
                        collectorCodeSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        coordinationCodeSha256=hashlib.sha256((Path(__file__).parent / 'network_coordination.py').read_bytes()).hexdigest(),
                        scopePolicyCodeSha256=hashlib.sha256((Path(__file__).parent / 'collection_scope.py').read_bytes()).hexdigest(),
                        requiredSourceFiles={name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                            for name in ['collect_ucsd_coverage.py', 'network_coordination.py', 'collection_lock.py', 'collection_scope.py', 'refresh_labs.py', 'refresh_faculty_directories.py', 'lab_destinations.py']})
    atomic_json(args.cache / 'process.json', {'pid': os.getpid(), 'startedAt': now(), 'networkCoordination': coordination})
    print(json.dumps({'at': now(), 'networkCoordination': coordination, 'pid': os.getpid()}), flush=True)
    replay_identity_discovery(queue, args.cache)
    replay_profile_qualifications(queue, args.cache)
    replay_literal_uri_discovery(queue, args.cache, atlas)
    if args.reparse_cached or args.reparse_profile_appointments:
        for index, item in enumerate(list(queue.state['items'].values()), 1):
            if item['state'] != 'done' or item.get('fetch', {}).get('status') != 'ok':
                continue
            if args.reparse_profile_appointments and not args.reparse_cached and urllib.parse.urlsplit(item['fetch'].get('finalUrl', '')).hostname != 'profiles.ucsd.edu':
                continue
            path = args.cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
            if path.exists():
                analyze(queue, item, item['fetch'], path.read_text(), atlas)
            if index % 100 == 0:
                queue.save()
                print(json.dumps({'at': now(), 'cachedReplayPosition': index, 'queueUrls': len(queue.state['items'])}), flush=True)
        queue.retain_recent_profiles(atlas)
        queue.save()
    stopping = threading.Event()
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, lambda *_: stopping.set())
    count = 0
    report_path = ROOT / 'data/ucsd/coverage-20261016-report.json'
    queue.save()
    write_report(queue, report_path)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(16, args.workers))) as pool:
        running = {}
        while not stopping.is_set() and not (args.cache / 'STOP').exists():
            busy_hosts = {urllib.parse.urlsplit(x['url']).netloc for x in running.values()}
            # Spread slow hosts rather than filling all workers with Profiles.
            priority = {'unresolved_candidate': 0, 'department': 1, 'institute_directory': 1, 'faculty_directory': 2, 'directory': 3, 'discovered_lab': 4, 'identity_page': 4, 'lab_link_candidate': 4, 'profile_identity_review': 4, 'lab_destination': 5, 'profile': 6, 'new_faculty_profile': 6, 'profile_discovery': 7}
            items = sorted(queue.state['items'].values(), key=lambda x: min((priority.get(c['kind'], 8) for c in x['contexts']), default=8))
            # Reserve one worker for the long serialized Profiles queue while
            # independent domains progress; no second Profiles wire request.
            slow_candidates = [x for x in items if x['state'] == 'pending' and urllib.parse.urlsplit(x['url']).netloc == 'profiles.ucsd.edu' and x.get('retryAt', 0) <= time.time()]
            slow = min(slow_candidates, key=lambda x: (not any(c['kind'] == 'profile_identity_review' for c in x['contexts']),
                       0 if any(c.get('professorId') and c.get('sourceUrl') == 'https://profiles.ucsd.edu/sitemap.xml' for c in x['contexts']) else 2 if all(c['kind'] == 'profile_discovery' for c in x['contexts']) else 1)) if slow_candidates else None
            if slow:
                items = [slow] + [x for x in items if x is not slow]
            for item in items:
                host = urllib.parse.urlsplit(item['url']).netloc
                if len(running) >= args.workers or args.max_pages and count + len(running) >= args.max_pages:
                    break
                if host in busy_hosts or item['state'] != 'pending' or item.get('retryAt', 0) > time.time():
                    continue
                reason = queue.scope_policy.request_reason(item)
                if reason:
                    mark_scope_excluded(item, reason)
                    continue
                item['state'], item['attempts'] = 'running', item['attempts'] + 1
                running[pool.submit(fetcher.fetch, item['url'])] = item
                busy_hosts.add(host)
            if not running:
                deferred = [x['retryAt'] for x in queue.state['items'].values() if x['state'] == 'pending' and x.get('retryAt', 0) > time.time()]
                if deferred and not (args.max_pages and count >= args.max_pages):
                    queue.save()
                    write_report(queue, report_path)
                    stopping.wait(min(30, max(1, min(deferred) - time.time())))
                    continue
                break
            done, _ = concurrent.futures.wait(running, timeout=5, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                item = running.pop(future)
                try:
                    meta, body = future.result()
                except Exception as exc:
                    meta, body = {'sourceUrl': item['url'], 'observedAt': now(), 'status': 'fetch_error', 'error': str(exc)[:220]}, ''
                item.setdefault('attemptHistory', []).append(meta)
                item['fetch'] = meta
                transient = retryable_fetch(meta)
                if transient and item['attempts'] < 3:
                    item.update(state='pending', retryAt=max(meta.get('retryAfterEpoch', 0), time.time() + 30 * 2 ** item['attempts']))
                else:
                    item['state'] = 'done' if meta['status'] == 'ok' else 'unresolved'
                    analyze(queue, item, meta, body, atlas)
                count += 1
                queue.retain_recent_profiles(atlas)
                if count % 25 == 0:
                    print(json.dumps({'at': now(), 'completedThisRun': count, 'queueSize': len(queue.state['items']), 'states': dict(Counter(x['state'] for x in queue.state['items'].values())), 'labCandidates': len(queue.state['labCandidates']), 'facultyCards': len(queue.state['facultyListings'])}), flush=True)
                queue.save()
                if count % 10 == 0:
                    write_report(queue, report_path)
        # Finish outstanding wire requests and save every response on interruption.
        for future, item in running.items():
            try:
                meta, body = future.result()
                item['fetch'] = meta
                item.setdefault('attemptHistory', []).append(meta)
                transient = retryable_fetch(meta)
                if transient and item['attempts'] < 3:
                    item.update(state='pending', retryAt=max(meta.get('retryAfterEpoch', 0), time.time() + 30 * 2 ** item['attempts']))
                else:
                    item['state'] = 'done' if meta['status'] == 'ok' else 'unresolved'
                analyze(queue, item, meta, body, atlas)
            except Exception as exc:
                item.update(state='pending', interruption=str(exc)[:220])
    # A last profile/decision can support a previously excluded existing URL.
    # Reopen it and its bounded cached identity links before the runner decides
    # whether this batch drained every eligible source.
    reassess_scope(queue, args.cache)
    write_report(queue, report_path)
    print(json.dumps({'at': now(), 'counts': queue.state['counts'], 'wireRequests': fetcher.wire_requests}), flush=True)


if __name__ == '__main__':
    main()
