"""Explicit, capture-verified lab ID consolidation with lossless archives."""
from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path

from refresh_labs import DOM, merge_observed_fields, unique_values, evidence_items, every_node, links
from atlas_urls import url_key, valid_url


def redirect_text(redirects):
    return '; '.join(f"HTTP {row['httpStatus']}: {row['from']} -> {row['to']}" for row in redirects)


def verify_capture_proofs(proofs, queue, cache, label):
    """Verify dated quotations against the exact request's original bytes."""
    items = {item['url']: item for item in queue['items'].values()}
    if not proofs:
        raise ValueError('Identity review requires captured evidence: ' + label)
    for proof in proofs:
        item = items.get(proof.get('requestedUrl'))
        meta = item.get('fetch', {}) if item else {}
        path = Path(cache) / 'responses' / (hashlib.sha256(proof.get('requestedUrl', '').encode()).hexdigest() + '.html')
        if not path.exists() or meta.get('status') != 'ok' or meta.get('sourceUrl', proof.get('requestedUrl')) != proof.get('requestedUrl') or meta.get('finalUrl') != proof.get('sourceUrl') or meta.get('observedAt') != proof.get('observedAt') or hashlib.sha256(path.read_bytes()).hexdigest() != proof.get('bodySha256'):
            raise ValueError('Lab identity review does not match its actual capture: ' + label)
        kind = proof.get('evidenceType', 'main_text_quote')
        if kind == 'redirect_chain':
            valid = bool(proof.get('redirects')) and proof['redirects'] == meta.get('redirects') and proof.get('evidence') == redirect_text(proof['redirects'])
        elif kind == 'main_text_quote':
            valid = bool(proof.get('evidence')) and proof['evidence'] in DOM(path.read_text()).main().text()
        elif kind == 'document_title':
            valid = bool(proof.get('evidence')) and proof['evidence'] in [node.text() for node in every_node(DOM(path.read_text()).root) if node.tag == 'title']
        elif kind == 'document_heading':
            tag = proof.get('headingTag')
            valid = (tag in {'h1', 'h2', 'h3'} and bool(proof.get('evidence'))
                     and any(node.tag == tag and node.text() == proof['evidence']
                             for node in every_node(DOM(path.read_text()).root)))
        elif kind == 'html_attribute':
            tag, attribute, value = (proof.get(k) for k in ['elementTag', 'attributeName', 'attributeValue'])
            selectors = proof.get('selectorAttributes', {})
            valid = (isinstance(tag, str) and re.fullmatch(r'[a-z][a-z0-9-]*', tag)
                     and isinstance(attribute, str) and re.fullmatch(r'[a-z][a-z0-9:_-]*', attribute)
                     and isinstance(value, str) and bool(value) and isinstance(selectors, dict)
                     and all(isinstance(k, str) and isinstance(v, str) for k, v in selectors.items())
                     and proof.get('evidence') == f'{tag}[{attribute}] = {value}'
                     and any(node.tag == tag and node.attrs.get(attribute) == value
                             and all(node.attrs.get(k) == v for k, v in selectors.items())
                             for node in every_node(DOM(path.read_text()).root)))
        elif kind in {'named_link', 'document_link'}:
            dom = DOM(path.read_text())
            scope = dom.root if kind == 'document_link' else dom.main()
            valid = (proof.get('linkText'), proof.get('linkUrl')) in [(label, url) for _, label, url in links(scope, meta['finalUrl'])] and proof.get('evidence') == f"{proof.get('linkText')} -> {proof.get('linkUrl')}"
        else:
            valid = False
        if not valid:
            raise ValueError('Lab identity review quotation/redirect evidence changed: ' + label)


def verified_reviews(review, queue, cache):
    rows = copy.deepcopy(review.get('entries', []))
    items = {item['url']: item for item in queue['items'].values()}
    for row in rows:
        if row.get('action') != 'merge' or not row.get('reason') or not row.get('evidence'):
            raise ValueError('Lab identity merge requires an explicit reason and captured evidence')
        verify_capture_proofs(row['evidence'], queue, cache, row['sourceLabId'])
        observed = set()
        for proof in row['evidence']:
            observed.update(url_key(u) for u in [proof['requestedUrl'], proof['sourceUrl']])
            for hop in items[proof['requestedUrl']]['fetch'].get('redirects', []):
                observed.update(url_key(hop[k]) for k in ['from', 'to'])
        resources = row.get('acceptedAliasUrls', []) + ([row['primaryLabWebsiteUrl']] if row.get('primaryLabWebsiteUrl') else [])
        if any(not valid_url(uri) or url_key(uri) not in observed for uri in resources):
            raise ValueError('Lab merge resource has no actual positive capture: ' + row['sourceLabId'])
        row['captureVerified'] = True
    return rows


def apply_reviewed_merges(data, reviews):
    by_id = {lab['id']: lab for lab in data['labs']}
    sources = [row['sourceLabId'] for row in reviews]
    targets = {row['targetLabId'] for row in reviews}
    if len(set(sources)) != len(sources) or set(sources) & targets:
        raise ValueError('Lab merges must be explicit, acyclic source-to-canonical decisions')
    # Validate the complete batch before mutating an identity or relationship.
    for row in reviews:
        source, target = by_id.get(row['sourceLabId']), by_id.get(row['targetLabId'])
        if not row.get('captureVerified') or not row.get('evidence') or not row.get('reason') or target is None:
            raise ValueError('Lab merge requires a canonical identity and verified source captures')
        if source is None and row['sourceLabId'] not in target.get('aliasIds', []):
            raise ValueError('Lab merge source is missing without a preserved alias ID')
        if target.get('websiteSharing') or (source and source.get('websiteSharing')):
            raise ValueError('Shared website entities require a separate group identity review before merging')
        if any(not all(proof.get(k) for k in ['sourceUrl', 'observedAt', 'evidence', 'bodySha256']) for proof in row['evidence']):
            raise ValueError('Lab merge evidence lacks dated raw capture provenance')
    removed = []
    for row in reviews:
        source, target = by_id.get(row['sourceLabId']), by_id[row['targetLabId']]
        original = copy.deepcopy(source) if source else None
        source = source or row.get('originalSourceRecord', {'id': row['sourceLabId'], 'labWebsiteUrl': ''})
        old_target = copy.deepcopy(target)
        proof = row['evidence']
        fields = {key: row[review_key] for key, review_key in [('labName', 'primaryLabName'), ('labWebsiteUrl', 'primaryLabWebsiteUrl')] if row.get(review_key)}
        updated = merge_observed_fields(target, {**fields, 'fieldEvidence': {key: proof for key in fields}})
        target.clear()
        target.update(updated)
        target['aliasIds'] = unique_values(target.get('aliasIds', []) + [source['id']] + source.get('aliasIds', []))
        target['appliedEvidencePatches'] = unique_values(target.get('appliedEvidencePatches', []) + source.get('appliedEvidencePatches', []))
        for field in ['aliasResourceReviews', 'captureIdentityReviews', 'additionalLabResourceObservations', 'additionalLabLinkObservations']:
            if source.get(field):
                target[field] = unique_values(target.get(field, []) + source[field])
        target['professorIds'] = unique_values(target.get('professorIds', []) + source.get('professorIds', []))
        target['sourceUrls'] = unique_values(target.get('sourceUrls', []) + source.get('sourceUrls', []) + [p['sourceUrl'] for p in proof])
        aliases = unique_values(target.get('alternateWebsiteUrls', []) + source.get('alternateWebsiteUrls', []) + row.get('acceptedAliasUrls', []))
        target['alternateWebsiteUrls'] = [u for u in aliases if u.rstrip('/') != target['labWebsiteUrl'].rstrip('/')]
        alternate_proofs = evidence_items(target.get('fieldEvidence', {}).get('alternateWebsiteUrls')) + evidence_items(source.get('fieldEvidence', {}).get('alternateWebsiteUrls'))
        if alternate_proofs:
            target.setdefault('fieldEvidence', {})['alternateWebsiteUrls'] = unique_values(alternate_proofs)
        target.setdefault('fieldEvidence', {})['identityReview'] = unique_values(evidence_items(target.get('fieldEvidence', {}).get('identityReview')) + proof)
        target['identityReview'] = {'reason': row['reason'], 'limitations': row.get('limitations', [])}
        affected = []
        for person in data['professors']:
            affiliations = person.get('labAffiliations', [])
            alias_urls = {u.rstrip('/') for u in row.get('acceptedAliasUrls', []) + source.get('alternateWebsiteUrls', []) + [source['labWebsiteUrl'], old_target['labWebsiteUrl']] if u}
            matching = [a for a in affiliations if (a.get('labId') in [source['id']] + source.get('aliasIds', []) or a.get('url', '').rstrip('/') in alias_urls)
                        and any(a.get(k) != v for k, v in [('labId', target['id']), ('labName', target['labName']), ('url', target['labWebsiteUrl'])])]
            scalar_match = bool(person.get('labAffiliationUrl')) and person['labAffiliationUrl'].rstrip('/') in alias_urls and any(person.get(k) != v for k, v in [('labAffiliation', target['labName']), ('labAffiliationUrl', target['labWebsiteUrl'])])
            if not matching and not scalar_match:
                continue
            affected.append(copy.deepcopy(person))
            if matching:
                observation = {'field': 'labAffiliations', 'value': copy.deepcopy(matching), 'reason': row['reason']}
                person['previousFieldObservations'] = unique_values(person.get('previousFieldObservations', []) + [observation])
                for affiliation in matching:
                    affiliation.update(labId=target['id'], labName=target['labName'], url=target['labWebsiteUrl'], identityReviewEvidence=copy.deepcopy(proof))
                deduplicated = {}
                for affiliation in affiliations:
                    identity = (affiliation.get('labId'), affiliation.get('url'), affiliation.get('relationship'))
                    if identity not in deduplicated:
                        deduplicated[identity] = affiliation
                    else:
                        existing = deduplicated[identity]
                        combined = unique_values(evidence_items(existing.get('fieldEvidence')) + evidence_items(affiliation.get('fieldEvidence')))
                        if combined != evidence_items(existing.get('fieldEvidence')):
                            existing['fieldEvidence'] = combined
                person['labAffiliations'] = list(deduplicated.values())
            if scalar_match:
                fields = {'labAffiliation': target['labName'], 'labAffiliationUrl': target['labWebsiteUrl']}
                updated = merge_observed_fields(person, {**fields, 'fieldEvidence': {key: proof for key in fields}})
                person.clear()
                person.update(updated)
            person['sourceUrls'] = unique_values(person.get('sourceUrls', []) + [p['sourceUrl'] for p in proof])
        if original is not None:
            removed.append({'reason': row['reason'], 'record': original, 'originalReviewRecord': copy.deepcopy(row.get('originalSourceRecord', original)),
                            'targetBeforeMerge': old_target, 'identityReview': copy.deepcopy(row), 'affectedProfessorRecords': affected})
            del by_id[source['id']]
    data['labs'] = [lab for lab in data['labs'] if lab['id'] in by_id]
    return removed
