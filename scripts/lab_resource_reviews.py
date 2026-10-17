"""Reviewed capture identity is separate from exact resource ownership.

Bindings preserve the existing canonical lab ID and original primary URI. A
listed but unvisited (or invalid) URI can never become a verified website alias.
"""
from __future__ import annotations

import copy
import hashlib
import json

from atlas_urls import valid_url, url_key
from lab_identity_merges import verify_capture_proofs


def record_sha256(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def observed_resource_keys(proofs, queue):
    items = {item['url']: item for item in queue['items'].values()}
    observed = set()
    for proof in proofs:
        meta = items[proof['requestedUrl']]['fetch']
        observed.update(url_key(u) for u in [proof['requestedUrl'], proof['sourceUrl']])
        for hop in meta.get('redirects', []):
            observed.update(url_key(hop[k]) for k in ['from', 'to'])
    return observed


def verified_alias_reviews(review, aliases, queue, cache):
    rows = copy.deepcopy(review.get('entries', []))
    expected = {(r['labId'], url_key(r['url'])) for r in aliases}
    actual = {(r['labId'], url_key(r['url'])) for r in rows}
    if expected != actual or len(actual) != len(rows):
        raise ValueError('Every accepted exact lab resource alias requires one capture review')
    for row in rows:
        original = row.get('originalAliasRecord', {})
        if (original.get('labId') != row['labId'] or original.get('url') != row['url']
                or row.get('originalAliasRecordSha256') != record_sha256(original) or not row.get('reason')):
            raise ValueError('Lab resource alias review lacks its original decision')
        verify_capture_proofs(row.get('evidence'), queue, cache, row['url'])
        if not valid_url(row['url']) or url_key(row['url']) not in observed_resource_keys(row['evidence'], queue):
            raise ValueError('Lab alias resource was not actually observed')
        row['captureVerified'] = True
    return rows


def verified_resource_reviews(review, queue, cache, captures, targets):
    source = {r['id']: r for r in captures}
    canonical = {r['id']: r for r in targets}
    rows = copy.deepcopy(review.get('entries', []))
    seen = set()
    for row in rows:
        incoming, target = source.get(row.get('captureId')), canonical.get(row.get('targetLabId'))
        if (row.get('action') != 'bind_capture_identity' or incoming is None or target is None
                or row['captureId'] in seen or not row.get('reason')
                or row.get('captureUri') != incoming['labWebsiteUrl']
                or row.get('targetUri') != target['labWebsiteUrl']
                or row.get('captureRecordSha256') != record_sha256(incoming)
                or row.get('originalCaptureRecord') != incoming):
            raise ValueError('Resource review requires unchanged explicit source and canonical records')
        seen.add(row['captureId'])
        verify_capture_proofs(row.get('evidence'), queue, cache, row['captureId'])
        state = row.get('resourceStatus')
        if state not in {'verified_same_lab', 'listed_unverified', 'invalid_as_listed'}:
            raise ValueError('Resource review requires an explicit URI status')
        if valid_url(row['captureUri']) == (state == 'invalid_as_listed'):
            raise ValueError('Invalid resource URI cannot be accepted as a website')
        if state == 'verified_same_lab':
            # The human-reviewed quotations identify the named group. Both exact
            # resources must also have been requested, including actual redirect
            # hops, rather than inferred from scheme/www/default-path spelling.
            observed = observed_resource_keys(row['evidence'], queue)
            if not {url_key(row['captureUri']), url_key(row['targetUri'])} <= observed:
                raise ValueError('Both exact resource URIs require actual positive captures')
            if not any(p.get('evidenceType', 'main_text_quote') != 'redirect_chain' for p in row['evidence']):
                raise ValueError('A redirect alone cannot identify the named lab')
        row['captureVerified'] = True
    return rows


def register_resource_reviews(index, captures, reviews):
    """Validate the whole batch before binding an ID or a verified URI."""
    incoming = {r['id']: r for r in captures}
    seen = set()
    for row in reviews:
        source, target = incoming.get(row.get('captureId')), index.by_id.get(row.get('targetLabId'))
        if (row.get('action') != 'bind_capture_identity' or not row.get('captureVerified') or not row.get('evidence') or not row.get('reason')
                or source is None or target is None or row['captureId'] in seen
                or row.get('captureRecordSha256') != record_sha256(source)
                or row.get('originalCaptureRecord') != source
                or row.get('captureUri') != source['labWebsiteUrl']
                or row.get('resourceStatus') not in {'verified_same_lab', 'listed_unverified', 'invalid_as_listed'}
                or (row['resourceStatus'] == 'verified_same_lab' and not valid_url(row['captureUri']))):
            raise ValueError('Capture identity binding lacks a verified unchanged source record')
        owner = index.by_id.get(row['captureId'])
        if owner is not None and owner['id'] != target['id']:
            raise ValueError('Capture ID already belongs to another lab')
        if row['resourceStatus'] == 'verified_same_lab' and any(r['id'] != target['id'] for r in index.candidates(row['captureUri'])):
            raise ValueError('Reviewed resource already belongs to another lab')
        seen.add(row['captureId'])
    for row in reviews:
        target = index.by_id[row['targetLabId']]
        if row['captureId'] not in target.get('aliasIds', []):
            target.setdefault('aliasIds', []).append(row['captureId'])
        target.setdefault('captureIdentityReviews', [])
        if row not in target['captureIdentityReviews']:
            target['captureIdentityReviews'].append(copy.deepcopy(row))
        if row['resourceStatus'] == 'verified_same_lab' and url_key(row['captureUri']) != url_key(target['labWebsiteUrl']):
            if row['captureUri'] not in target.get('alternateWebsiteUrls', []):
                target.setdefault('alternateWebsiteUrls', []).append(row['captureUri'])
            proofs = target.setdefault('fieldEvidence', {}).setdefault('alternateWebsiteUrls', [])
            for proof in row['evidence']:
                if proof not in proofs:
                    proofs.append(copy.deepcopy(proof))
        target['sourceUrls'] = list(dict.fromkeys(target.get('sourceUrls', []) + [p['sourceUrl'] for p in row['evidence']]))
        index.add(target)
