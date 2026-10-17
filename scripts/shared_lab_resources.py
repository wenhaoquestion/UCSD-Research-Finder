"""Captured shared landing pages belong to a complete named lab group.

Resource sharing never selects one scientific entity for an unqualified link.
The primary site, scientific IDs and existing group declaration stay intact.
"""
from __future__ import annotations

import copy
import re

from atlas_urls import valid_url, url_key
from lab_entities import LabIndex, reviewed_shared_group, label_key
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from refresh_labs import unique_values, evidence_items


def name_part(name):
    return re.sub(r'\s+', ' ', re.sub(r'\blabs?\b', '', label_key(name))).strip()


def verified_shared_resources(review, queue, cache, labs):
    index = LabIndex(labs); index.validate_sharing()
    rows, seen = copy.deepcopy(review.get('entries', [])), set()
    for row in rows:
        members = index.candidates(row.get('primaryUri', ''))
        ids = sorted(member['id'] for member in members)
        if (row.get('action') != 'register_shared_lab_resource' or row.get('resourceKind') != 'shared_landing_page'
                or not reviewed_shared_group(members) or row.get('groupId') != members[0]['websiteSharing']['groupId']
                or sorted(row.get('memberLabIds', [])) != ids or not row.get('reason')
                or not valid_url(row.get('resourceUri', '')) or url_key(row['resourceUri']) in seen
                or url_key(row['resourceUri']) == url_key(row.get('primaryUri', ''))
                or any(member['labWebsiteUrl'] != row['primaryUri'] for member in members)
                or any(member['id'] not in ids for member in index.candidates(row['resourceUri']))):
            raise ValueError('Shared resource requires the complete distinct named group and an exact different URI')
        seen.add(url_key(row['resourceUri']))
        originals = {record['id']: record for record in row.get('originalLabRecords', [])}
        if sorted(originals) != ids or len(row['originalLabRecords']) != len(ids):
            raise ValueError('Shared resource requires every original scientific record')
        for member in members:
            original = originals[member['id']]
            if (record_sha256(original) != row.get('originalLabRecordSha256', {}).get(member['id'])
                    or any(original.get(k) != member.get(k) for k in ['id', 'labName', 'labWebsiteUrl', 'websiteSharing'])):
                raise ValueError('Shared resource original identity/group changed')
        proofs = row.get('evidence', [])
        verify_capture_proofs(proofs, queue, cache, row['resourceUri'])
        group = row.get('collectiveNameEvidence', {})
        link = row.get('primaryLinkEvidence', {})
        if (group not in proofs or group.get('evidenceType') != 'main_text_quote'
                or group.get('requestedUrl') != row['resourceUri'] or not row.get('collectiveName')
                or row['collectiveName'] not in group['evidence']
                or not all(name_part(member['labName']) and re.search(r'\b' + re.escape(name_part(member['labName'])) + r'\b', label_key(row['collectiveName'])) for member in members)
                or link not in proofs or link.get('evidenceType') != 'named_link'
                or link.get('requestedUrl') != row['resourceUri']
                or url_key(link.get('linkUrl', '')) != url_key(row['primaryUri'])):
            raise ValueError('Landing resource must actually name the group and link its reviewed primary site')
        for member in members:
            identity = row.get('memberIdentityEvidence', {}).get(member['id'], [])
            if (not identity or any(proof not in proofs or proof.get('requestedUrl') != row['primaryUri']
                                   or proof.get('evidenceType') != 'main_text_quote' for proof in identity)
                    or not any(re.search(r'\b' + re.escape(label_key(member['labName'])) + r'\b', label_key(proof['evidence'])) for proof in identity)):
                raise ValueError('The actual primary page must separately identify every member lab')
        row['captureVerified'] = True
    return rows


def apply_shared_resources(data, reviews):
    index = LabIndex(data['labs'])
    for row in reviews:
        members = index.candidates(row.get('primaryUri', ''))
        if (not row.get('captureVerified') or not row.get('evidence') or not row.get('reason')
                or row.get('action') != 'register_shared_lab_resource' or row.get('resourceKind') != 'shared_landing_page'
                or not valid_url(row.get('resourceUri', '')) or not reviewed_shared_group(members)
                or sorted(row.get('memberLabIds', [])) != sorted(member['id'] for member in members)
                or row.get('groupId') != members[0]['websiteSharing']['groupId']
                or any(member['id'] not in row['memberLabIds'] for member in index.candidates(row['resourceUri']))):
            raise ValueError('Shared resource requires a captured complete existing lab group')
    for row in reviews:
        for lab_id in row['memberLabIds']:
            member = index.by_id[lab_id]
            member['sharedResourceReviews'] = unique_values(member.get('sharedResourceReviews', []) + [copy.deepcopy(row)])
            member['alternateWebsiteUrls'] = unique_values(member.get('alternateWebsiteUrls', []) + [row['resourceUri']])
            fields = member.setdefault('fieldEvidence', {})
            fields['alternateWebsiteUrls'] = unique_values(evidence_items(fields.get('alternateWebsiteUrls')) + row['evidence'])
            member['sourceUrls'] = unique_values(member.get('sourceUrls', []) + [proof['sourceUrl'] for proof in row['evidence']])
