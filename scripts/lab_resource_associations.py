"""Review a resource's observed lab separately from an older listed identity.

The old scientific record and its literal website remain intact. A positive
capture can associate that exact resource with another existing lab, without a
person/lab merge or a claim about when, why, or whether the old group ended.
"""
from __future__ import annotations

import copy

from atlas_urls import url_key, valid_url
from lab_entities import named_lab_key
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from lab_field_reviews import has_named_pi, own_lab_source
from refresh_labs import evidence_items, unique_values


def verified_resource_associations(review, queue, cache, labs, destination_reviews):
    records = {lab['id']: lab for lab in labs}
    rows, seen = copy.deepcopy(review.get('entries', [])), set()
    for row in rows:
        previous = records.get(row.get('mismatchedLabId'))
        current = records.get(row.get('currentLabId'))
        uri = row.get('resourceUri', '')
        if (row.get('action') != 'record_resource_mismatch_and_current_lab' or not row.get('reason')
                or previous is None or current is None or previous is current or not valid_url(uri)
                or uri != previous.get('labWebsiteUrl') or row.get('currentLabUri') != current.get('labWebsiteUrl')
                or previous.get('websiteSharing') or current.get('websiteSharing') or url_key(uri) in seen):
            raise ValueError('Resource association requires two distinct unchanged lab identities and one exact URI')
        seen.add(url_key(uri))
        for label, record in [('previous', previous), ('current', current)]:
            original = row.get(label + 'LabRecord', {})
            if (record_sha256(original) != row.get(label + 'LabRecordSha256')
                    or any(original.get(k) != record.get(k) for k in ['id', 'labName', 'labWebsiteUrl'])):
                raise ValueError('Resource association requires original identity snapshots')
        if not any(r.get('labId') == previous['id'] and r.get('identityStatus') == 'mismatch'
                   and r.get('action') == 'record_destination_assessment'
                   and any(p.get('requestedUrl') == uri for p in r.get('evidence', []))
                   for r in destination_reviews):
            raise ValueError('The older lab requires a separately verified exact-resource mismatch assessment')
        proofs = row.get('evidence', [])
        verify_capture_proofs(proofs, queue, cache, uri)
        roots = [row.get('resourceEvidence', {}), row.get('currentLabEvidence', {})]
        if any(proof not in proofs or proof.get('evidenceType') != 'document_title'
               or proof.get('requestedUrl') != source for proof, source in zip(roots, [uri, current['labWebsiteUrl']])):
            raise ValueError('Both exact resources require their actual captured lab titles')
        # Identical bytes alone could be a generic default page. Require the
        # specifically named current lab and its explicit own-site PI as well.
        names = {named_lab_key(n) for n in [current['labName']] + current.get('aliasNames', [])}
        if (not named_lab_key(roots[0]['evidence']) or named_lab_key(roots[0]['evidence']) not in names
                or roots[0]['evidence'] != roots[1]['evidence']
                or roots[0]['bodySha256'] != roots[1]['bodySha256']):
            raise ValueError('Both actual responses must be the same specifically named lab page')
        leadership = row.get('currentLabLeadershipEvidence', [])
        if (not row.get('currentLabPrincipalInvestigator') or not leadership
                or any(p not in proofs or not own_lab_source(current, p['sourceUrl'], queue) for p in leadership)
                or not has_named_pi(row.get('currentLabPrincipalInvestigator', ''), leadership)):
            raise ValueError('Current lab requires its own explicit named leadership evidence')
        row['captureVerified'] = True
    return rows


def apply_resource_associations(data, reviews):
    records = {lab['id']: lab for lab in data['labs']}
    for row in reviews:
        previous, current = records.get(row.get('mismatchedLabId')), records.get(row.get('currentLabId'))
        if (not row.get('captureVerified') or not row.get('evidence') or not row.get('reason')
                or row.get('action') != 'record_resource_mismatch_and_current_lab'
                or previous is None or current is None or previous is current
                or previous['labWebsiteUrl'] != row.get('resourceUri')
                or current['labWebsiteUrl'] != row.get('currentLabUri')):
            raise ValueError('Resource association requires verified captures and unchanged existing records')
    for row in reviews:
        previous, current = records[row['mismatchedLabId']], records[row['currentLabId']]
        for record in [previous, current]:
            record['resourceAssociationReviews'] = unique_values(record.get('resourceAssociationReviews', []) + [copy.deepcopy(row)])
        current['alternateWebsiteUrls'] = unique_values(current.get('alternateWebsiteUrls', []) + [row['resourceUri']])
        field = current.setdefault('fieldEvidence', {})
        field['alternateWebsiteUrls'] = unique_values(evidence_items(field.get('alternateWebsiteUrls')) + row['evidence'])
        current['sourceUrls'] = unique_values(current.get('sourceUrls', []) + [p['sourceUrl'] for p in row['evidence']])
