"""Flag an evidenced composite profile link without resolving person identity."""
from __future__ import annotations

import copy
from urllib.parse import urldefrag, urlsplit

from atlas_urls import valid_url
from faculty_profile_bindings import profile_metadata
from faculty_scoped_titles import same_named_subject
from lab_resource_reviews import record_sha256
from refresh_labs import unique_values


def verified_profile_link_reviews(review, queue, cache, professors):
    people = {person['id']: person for person in professors}
    items = {item['url']: item for item in queue['items'].values()}
    verified, seen = [], set()
    for raw in review.get('entries', []):
        row = copy.deepcopy(raw)
        person = people.get(row.get('professorId'))
        if (person is None or person['id'] in seen or not row.get('reason')
                or row.get('action') != 'flag_composite_profile_link_identity_review'
                or row.get('originalProfessorRecordSha256') != record_sha256(person)
                or row.get('originalProfileUri') != person['officialProfileUrl']):
            raise ValueError('Profile link review requires the unchanged original person and URI')
        uri = person['officialProfileUrl']
        transport_uri, embedded_uri = urldefrag(uri)
        if (not valid_url(uri) or not valid_url(embedded_uri)
                or urlsplit(transport_uri).hostname != 'profiles.ucsd.edu'
                or urlsplit(embedded_uri).hostname != 'profiles.ucsd.edu'
                or embedded_uri == transport_uri
                or [p['id'] for p in people.values() if p['officialProfileUrl'] == uri] != [person['id']]):
            raise ValueError('A composite review requires one exact owned URI with an embedded campus profile URL')
        captures = row.get('captures', [])
        if (len(captures) != 2 or [proof.get('requestedUrl') for proof in captures] != [transport_uri, embedded_uri]
                or any(proof['requestedUrl'] not in items for proof in captures)):
            raise ValueError('Both actual requests must be explicit; a fragment is never a requested person URI')
        actual = [profile_metadata(items[proof['requestedUrl']], cache)[0] for proof in captures]
        if (captures != actual or same_named_subject(person['name'], actual[0]['nameAsDisplayed'])
                or not same_named_subject(person['name'], actual[1]['nameAsDisplayed'])
                or actual[0]['canonicalUri'] == actual[1]['canonicalUri']
                or actual[0]['rdfAlternateUri'] == actual[1]['rdfAlternateUri']
                or row.get('identityResolved') is not False):
            raise ValueError('Review requires different captured identifiers and the exact named subjects; no identity resolution')
        row['captureVerified'] = True
        row['status'] = 'needs_review'
        verified.append(row)
        seen.add(person['id'])
    return verified


def apply_profile_link_reviews(data, reviews):
    people = {p['id']: p for p in data['professors']}
    for row in reviews:
        person = people.get(row.get('professorId'))
        if (not row.get('captureVerified') or row.get('status') != 'needs_review'
                or row.get('identityResolved') is not False or person is None
                or person['officialProfileUrl'] != row['originalProfileUri']):
            raise ValueError('Only the verified review may be attached to the unchanged original person')
    for row in reviews:
        person = people[row['professorId']]
        person['profileLinkIdentityReview'] = copy.deepcopy(row)
        proofs = [{**capture, 'method': 'reviewed_composite_profile_uri_named_subject_observation',
                   'evidence': capture['nameAsDisplayed'], 'status': 'review_required'}
                  for capture in row['captures']]
        fields = person.setdefault('fieldEvidence', {})
        fields['profileLinkIdentityReview'] = unique_values(fields.get('profileLinkIdentityReview', []) + proofs)
        person['sourceUrls'] = unique_values(person.get('sourceUrls', []) + [proof['sourceUrl'] for proof in proofs])
