"""Apply explicit destination-identity reviews while archiving prior records."""
from __future__ import annotations

import copy


NON_LAB_TYPES = {'educational_resource', 'departmental_division', 'research_field_directory', 'course', 'clinical_trials_overview'}


def apply_destination_identity_reviews(data, reviews):
    by_id = {l['id']: l for l in data['labs']}
    # Validate the entire review before mutating any records.
    for row in reviews:
        if row.get('action') not in {'isolate_non_lab', 'record_destination_assessment'}:
            raise ValueError('Unsupported destination identity review action')
        if not row.get('evidence') or any(not all(p.get(k) for k in ['sourceUrl', 'observedAt', 'evidence']) for p in row['evidence']):
            raise ValueError('Destination identity review requires dated source evidence')
        if row['action'] == 'isolate_non_lab' and row.get('observedPageType') not in NON_LAB_TYPES:
            raise ValueError('A mismatched lab destination alone cannot exclude a lab')
        if row['labId'] not in by_id and not (row['action'] == 'isolate_non_lab' and row.get('originalRecord', {}).get('id') == row['labId']):
            raise ValueError('Unknown legacy identity review ID: ' + row['labId'])
    removed, removed_ids = [], set()
    for row in reviews:
        target = by_id.get(row['labId'])
        if target is None:
            # A subsequent build must not replace the original archive, which
            # includes affected relationships from the first isolation.
            continue
        assessment = {k: copy.deepcopy(v) for k, v in row.items() if k != 'originalRecord'}
        if row['action'] == 'record_destination_assessment':
            target['destinationIdentityAssessment'] = assessment
            target.setdefault('verification', {})['destinationIdentityStatus'] = row['identityStatus']
            continue
        archived = {'reason': 'Reviewed destination is ' + row['observedPageType'] + ', not an independent research lab/group.',
                    'record': copy.deepcopy(target), 'identityReview': assessment, 'affectedProfessorObservations': []}
        if row.get('originalRecord'):
            archived['originalReviewRecord'] = copy.deepcopy(row['originalRecord'])
        for person in data['professors']:
            affiliations = person.get('labAffiliations', [])
            removed_links = [a for a in affiliations if a.get('labId') == target['id']]
            scalar_match = person.get('labAffiliationUrl', '').rstrip('/') == target['labWebsiteUrl'].rstrip('/')
            if not removed_links and not scalar_match:
                continue
            observation = {'professorId': person['id'], 'labAffiliations': copy.deepcopy(removed_links), 'fields': {}}
            history = person.setdefault('previousFieldObservations', [])
            if removed_links:
                history.append({'field': 'labAffiliations', 'value': copy.deepcopy(removed_links), 'reason': archived['reason'], 'identityReviewEvidence': row['evidence']})
                person['labAffiliations'] = [a for a in affiliations if a.get('labId') != target['id']]
            if scalar_match:
                for field in ['labAffiliation', 'labAffiliationUrl']:
                    old = {'field': field, 'value': person.get(field), 'fieldEvidence': copy.deepcopy(person.get('fieldEvidence', {}).get(field, [])), 'reason': archived['reason']}
                    observation['fields'][field] = copy.deepcopy(old)
                    history.append(old)
                    person[field] = 'Not found'
                    person.get('fieldEvidence', {}).pop(field, None)
            archived['affectedProfessorObservations'].append(observation)
        removed.append(archived)
        removed_ids.add(target['id'])
    data['labs'] = [l for l in data['labs'] if l['id'] not in removed_ids]
    return removed
