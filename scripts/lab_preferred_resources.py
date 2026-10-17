"""Select a captured owned lab resource without rewriting scientific identity.

Selection preserves the old listed URI and its check as historical observations.
It changes only navigation for already established, ID-scoped relationships.
"""
import copy
import hashlib
from pathlib import Path

from atlas_urls import url_key, valid_url
from lab_entities import LabIndex, reviewed_resource_mismatch
from lab_identity_merges import verify_capture_proofs
from lab_own_metadata import document_lab_name
from lab_resource_reviews import record_sha256
from lab_profile_source_upgrades import verified_profile_source_upgrade, apply_profile_source_upgrade
from refresh_labs import DOM, evidence_items, unique_values


def verified_preferred_resources(review, aliases, queue, cache, labs, label_updates=()):
    index = LabIndex(labs)
    owners, accepted = {}, {}
    for alias in aliases:
        if not alias.get('captureVerified'):
            raise ValueError('Preferred lab resources require verified aliases')
        lab = index.by_id.get(alias['labId'])
        owner = lab['id'] if lab else alias['labId']
        key = url_key(alias['url'])
        owners.setdefault(key, set()).add(owner)
        accepted[owner, key] = alias
    rows, seen = copy.deepcopy(review.get('entries', [])), set()
    items = {url_key(i['url']): i for i in queue['items'].values()}
    for row in rows:
        lab = index.by_id.get(row.get('labId'))
        original = row.get('originalLabRecord', {})
        old, new = row.get('previousPreferredUrl', ''), row.get('preferredUrl', '')
        if (lab is None or lab['id'] != row['labId'] or row['labId'] in seen
                or row.get('action') != 'select_preferred_lab_resource' or not row.get('reason')
                or not valid_url(new) or url_key(old) == url_key(new)
                or old != lab.get('labWebsiteUrl') or lab.get('websiteSharing')
                or any(original.get(k) != lab.get(k) for k in ['id', 'labName', 'labWebsiteUrl'])
                or record_sha256(original) != row.get('originalLabRecordSha256')
                or reviewed_resource_mismatch(lab, new)):
            raise ValueError('Preferred lab resource requires one unchanged canonical identity and original record')
        seen.add(row['labId'])
        alias = accepted.get((lab['id'], url_key(new)))
        other_owners = {r['id'] for r in index.candidates(new)} | owners.get(url_key(new), set())
        proofs, identity = row.get('evidence', []), row.get('identityEvidence', [])
        if (alias is None or other_owners != {lab['id']}
                or not all(p in proofs for p in alias['evidence'])):
            raise ValueError('Preferred lab resource requires its exact uniquely owned reviewed alias chain')
        verify_capture_proofs(proofs, queue, cache, row['labId'])
        if lab.get('profile_only') or row.get('profileSourceUpgrade'):
            verified_profile_source_upgrade(row, lab, queue, cache)
        expected_name = row.get('preferredLabName', lab['labName'])
        if expected_name != lab['labName']:
            updates = [u for u in label_updates if u.get('labId') == lab['id']
                       and u.get('fields') == {'labName': expected_name}]
            if len(updates) != 1:
                raise ValueError('Preferred resource label requires its explicit reviewed name update')
            declarations = evidence_items(updates[0].get('fieldEvidence', {}).get('labName'))
            verify_capture_proofs(declarations, queue, cache, lab['id'])
            if (not declarations or any(p not in proofs for p in declarations)
                    or not any(p.get('evidenceType') in {'document_title', 'document_heading'}
                               and url_key(p['sourceUrl']) == url_key(new)
                               and document_lab_name(p['evidence']) == document_lab_name(expected_name)
                               for p in declarations)):
                raise ValueError('Preferred resource name update requires its exact owned named document')
        named = [p for p in identity if p in proofs
                 and p.get('evidenceType') in {'document_title', 'document_heading'}
                 and url_key(p.get('sourceUrl', '')) == url_key(new)
                 and document_lab_name(p.get('evidence', '')) == document_lab_name(expected_name)]
        item = items.get(url_key(named[0]['requestedUrl']), {}) if named else {}
        meta = item.get('fetch', {})
        if (not document_lab_name(lab['labName']) or not document_lab_name(expected_name)
                or not named or any(p not in proofs for p in identity)
                or meta.get('status') != 'ok' or url_key(meta.get('finalUrl', '')) != url_key(new)):
            raise ValueError('Preferred lab resource requires its own successful captured named document')
        visited = item.get('url')
        for hop in meta.get('redirects', []):
            if hop.get('from') != visited or hop.get('httpStatus') not in {301,302,303,307,308}:
                raise ValueError('Preferred lab resource requires its actual continuous redirect chain')
            visited = hop.get('to')
        if visited != meta.get('finalUrl'):
            raise ValueError('Preferred lab resource requires its actual continuous redirect chain')
        row['selectedWebsiteCheck'] = {k: copy.deepcopy(meta[k]) for k in
            ['sourceUrl', 'observedAt', 'httpStatus', 'finalUrl'] if k in meta}
        row['selectedWebsiteCheck']['status'] = 'reachable'
        source = Path(cache)/'responses'/(hashlib.sha256(item['url'].encode()).hexdigest()+'.html')
        titles = [n.text() for n in DOM(source.read_text()).root.walk() if n.tag == 'title']
        if len(titles) == 1:
            row['selectedWebsiteCheck']['title'] = titles[0]
        row['captureVerified'] = True
    return rows


def _replace(record, field, value, proofs, reason):
    if record.get(field) != value:
        observation = {'field': field, 'value': copy.deepcopy(record.get(field)),
                       'fieldEvidence': copy.deepcopy(record.get('fieldEvidence', {}).get(field, [])),
                       'reason': reason}
        record['previousFieldObservations'] = unique_values(record.get('previousFieldObservations', []) + [observation])
        record[field] = copy.deepcopy(value)
        if proofs:
            record.setdefault('fieldEvidence', {})[field] = copy.deepcopy(proofs)
        else:
            record.get('fieldEvidence', {}).pop(field, None)


def apply_preferred_resources(data, reviews):
    index = LabIndex(data['labs'])
    for row in reviews:
        lab = index.by_id.get(row.get('labId'))
        if (not row.get('captureVerified') or not row.get('evidence') or lab is None
                or row.get('profileSourceUpgrade') and not row['profileSourceUpgrade'].get('captureVerified')
                or lab['id'] != row['labId'] or lab.get('websiteSharing')
                or lab['labName'] != row.get('preferredLabName', row['originalLabRecord']['labName'])
                or lab.get('labWebsiteUrl') not in {row['previousPreferredUrl'], row['preferredUrl']}
                or {r['id'] for r in index.candidates(row['preferredUrl'])} != {lab['id']}
                or row.get('selectedWebsiteCheck', {}).get('status') != 'reachable'):
            raise ValueError('Preferred lab resource requires a verified unchanged canonical target')
    for row in reviews:
        lab = index.by_id[row['labId']]
        old, new, proofs = row['previousPreferredUrl'], row['preferredUrl'], row['evidence']
        _replace(lab, 'labWebsiteUrl', new, proofs, row['reason'])
        apply_profile_source_upgrade(lab, row)
        selected, current = row['selectedWebsiteCheck'], lab.get('websiteCheck') or {}
        if (url_key(new) not in {url_key(current.get('sourceUrl', '')), url_key(current.get('finalUrl', ''))}
                or current.get('observedAt', '') < selected['observedAt']):
            # A reachability check is a dated response observation; keep it
            # separate from scientific field proofs that survive later checks.
            _replace(lab, 'websiteCheck', selected, [], row['reason'])
        verification = lab.setdefault('verification', {})
        verification['lastAttemptedAt'] = max(verification.get('lastAttemptedAt') or '', lab['websiteCheck']['observedAt'])
        lab['preferredResourceReviews'] = unique_values(lab.get('preferredResourceReviews', []) + [row])
        lab['sourceUrls'] = unique_values(lab.get('sourceUrls', []) + [old, new] + [p['sourceUrl'] for p in proofs])
        # Keep the original relationship statements and labels. These proofs
        # establish a resource choice, not a new appointment or leadership role.
        for person in data['professors']:
            previous = copy.deepcopy(person.get('labAffiliations', []))
            matched = [a for a in previous if index.by_id.get(a.get('labId')) is lab
                       and a.get('url') == old]
            if not matched:
                continue
            # Assembly resolves old lab IDs at its final reference pass. Save
            # both the literal input and that canonical association snapshot,
            # so resource selection cannot hide the previous published value.
            canonical = [dict(a, labId=lab['id']) if index.by_id.get(a.get('labId')) is lab
                         and a.get('url') == old else a for a in previous]
            _replace(person, 'labAffiliations', canonical,
                     evidence_items(person.get('fieldEvidence', {}).get('labAffiliations')),
                     row['reason'])
            previous = copy.deepcopy(person['labAffiliations'])
            affiliations = copy.deepcopy(previous)
            for affiliation in affiliations:
                if index.by_id.get(affiliation.get('labId')) is lab and affiliation.get('url') == old:
                    affiliation['url'] = new
                    affiliation['resourceSelectionEvidence'] = copy.deepcopy(proofs)
                    if lab.get('recordSubtype') == 'ngo':
                        affiliation.update(recordSubtype='ngo', relationship='faculty_organization_link')
            _replace(person, 'labAffiliations', unique_values(affiliations),
                     evidence_items(person.get('fieldEvidence', {}).get('labAffiliations')),
                     row['reason'])
            if person.get('labAffiliationUrl') == old and person.get('labAffiliation') in {lab['labName'], *(a.get('labName') for a in matched)}:
                _replace(person, 'labAffiliationUrl', new, proofs, row['reason'])
            person['sourceUrls'] = unique_values(person.get('sourceUrls', []) + [p['sourceUrl'] for p in proofs])
