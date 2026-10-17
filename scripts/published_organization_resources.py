"""Verify a named organization's actual site through its original publisher.

This resource review introduces no scientific record or person association.
An original faculty page, its published personal page, and the named external
organization must each be independently captured; no title or URL is guessed.
"""
import copy
import re
from urllib.parse import urlsplit

from atlas_urls import url_key, valid_url
from lab_entities import LabIndex
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256, verified_alias_reviews


def _capture_uri(proof, request, items):
    item = items.get(request, {})
    meta = item.get('fetch', {})
    visited = request
    for hop in meta.get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Published organization requires actual continuous resource redirects')
        visited = hop.get('to')
    if (meta.get('status') != 'ok' or visited != meta.get('finalUrl')
            or proof.get('requestedUrl') != request or proof.get('sourceUrl') != visited
            or proof.get('bodySha256') != meta.get('sha256')):
        raise ValueError('Published organization proof must use the exact captured request and final URI')
    return visited


def verified_published_organizations(review, queue, cache, labs, people, aliases=()):
    index = LabIndex(labs)
    people = {p['id']: p for p in people}
    items = {i['url']: i for i in queue['items'].values()}
    rows, seen = copy.deepcopy(review.get('entries', [])), set()
    for row in rows:
        lab, person = index.by_id.get(row.get('labId')), people.get(row.get('professorId'))
        old, original_person = row.get('originalLabRecord', {}), row.get('originalProfessorRecord', {})
        if (row.get('action') != 'register_published_organization_resource' or not row.get('reason')
                or lab is None or person is None or lab['id'] != row['labId'] or lab['id'] in seen
                or person['id'] not in lab.get('professorIds', []) or lab.get('websiteSharing')
                or record_sha256(old) != row.get('originalLabRecordSha256')
                or record_sha256(original_person) != row.get('originalProfessorRecordSha256')
                or any(old.get(k) != lab.get(k) for k in ['id', 'labName', 'labWebsiteUrl'])
                or any(original_person.get(k) != person.get(k) for k in ['id', 'name', 'officialProfileUrl'])):
            raise ValueError('Published organization requires unchanged original scientific and person identities')
        seen.add(lab['id'])
        proofs = row.get('evidence', [])
        verify_capture_proofs(proofs, queue, cache, lab['id'])
        campus, publisher, organization = [row.get(k, {}) for k in
            ['originalPersonIdentityEvidence', 'publisherIdentityEvidence', 'organizationIdentityEvidence']]
        personal_link, organization_link, association = [row.get(k, {}) for k in
            ['publishedPersonalLinkEvidence', 'publishedOrganizationLinkEvidence', 'associationEvidence']]
        if any(p not in proofs for p in [campus, publisher, organization, personal_link, organization_link, association]):
            raise ValueError('Published organization requires every named publisher-chain proof')
        campus_uri = _capture_uri(campus, person['officialProfileUrl'], items)
        publisher_uri = _capture_uri(publisher, lab['labWebsiteUrl'], items)
        requested = organization_link.get('linkUrl', '')
        new = _capture_uri(organization, requested, items)
        # The known original person, literal personal-site navigation and exact
        # named organization link do the identity work, not domain/surname reuse.
        campus_host = urlsplit(campus_uri).hostname or ''
        if (not (campus_host == 'ucsd.edu' or campus_host.endswith('.ucsd.edu'))
                or not valid_url(new) or url_key(new) == url_key(lab['labWebsiteUrl'])
                or campus.get('evidenceType') not in {'document_heading', 'document_title'}
                or publisher.get('evidenceType') not in {'document_heading', 'document_title'}
                or campus.get('evidence') != person['name'] or publisher.get('evidence') != person['name']
                or personal_link.get('sourceUrl') != campus_uri or personal_link.get('linkUrl') != lab['labWebsiteUrl']
                or personal_link.get('evidenceType') != 'named_link'
                or organization_link.get('sourceUrl') != publisher_uri or organization_link.get('evidenceType') != 'named_link'
                or organization_link.get('linkText') != lab['labName']
                or organization.get('evidenceType') not in {'document_heading', 'document_title'}
                or organization.get('evidence') != lab['labName']
                or association.get('sourceUrl') != campus_uri or association.get('evidenceType') != 'main_text_quote'
                or not re.search(r'\b(?:He|She|They|' + re.escape(person['name'])
                                 + r') is (?:also )?the co-founder of ' + re.escape(lab['labName']) + r'\b',
                                 association.get('evidence', ''))):
            raise ValueError('Organization resource requires the original named faculty/personal/organization publisher chain')
        owners = {l['id'] for l in index.candidates(new)} | {a['labId'] for a in aliases if url_key(a['url']) == url_key(new)}
        if owners - {lab['id']}:
            raise ValueError('Published organization resource already belongs to another scientific identity')
        alias = {'labId': lab['id'], 'url': new, 'fieldEvidence': proofs, 'reason': row['reason']}
        alias_review = {'labId': lab['id'], 'url': new, 'originalAliasRecord': alias,
                        'originalAliasRecordSha256': record_sha256(alias), 'reason': row['reason'], 'evidence': proofs}
        row['resourceAlias'] = alias
        row['resourceAliasReview'] = verified_alias_reviews({'entries': [alias_review]}, [alias], queue, cache)[0]
        row['captureVerified'] = True
        index.add_url(new, lab)
    return rows


def attach_published_organization_aliases(coverage, reviews):
    seen = {url_key(a['url']) for a in coverage['labAliases']}
    for row in reviews:
        if not row.get('captureVerified') or not row.get('resourceAliasReview', {}).get('captureVerified'):
            raise ValueError('Published organization alias must be capture verified')
        alias = row['resourceAlias']
        if url_key(alias['url']) in seen:
            raise ValueError('Published organization resource must not duplicate an existing alias review')
        seen.add(url_key(alias['url']))
    for row in reviews:
        coverage['labAliases'].append(copy.deepcopy(row['resourceAlias']))
        coverage['labAliasResourceReviews'].append(copy.deepcopy(row['resourceAliasReview']))
