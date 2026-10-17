#!/usr/bin/env python3
"""Export reviewed, completed collection evidence for the offline atlas build.

Requires explicit lab decisions. Does not overwrite original collection captures.
Previously evidenced scalar values survive; new captures corroborate those values
or fill missing fields. Profile lab links attach only to accepted/existing labs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import urllib.parse
from collections import Counter
from pathlib import Path

from collect_ucsd_coverage import ROOT, atomic_json, url_key
from review_ucsd_coverage import read, prepare, faculty_review, body_for
from refresh_labs import now, parse_profile, evidence_items, unique_values, normalized, merge_observed_fields, has_value
from rebuild_verified_atlas import url_key as atlas_url_key
from refresh_labs import DOM
from lab_identity_merges import verified_reviews as verified_lab_merges
from lab_resource_reviews import verified_resource_reviews, verified_alias_reviews
from person_identity_reviews import verified_person_reviews
from lab_field_reviews import verified_lab_fields, has_named_pi, own_lab_source
from lab_own_metadata import verified_own_metadata
from lab_ownership_reviews import verified_lab_ownership_reviews
from lab_preferred_resources import verified_preferred_resources
from published_organization_resources import verified_published_organizations, attach_published_organization_aliases
from lab_resource_associations import verified_resource_associations
from shared_lab_resources import verified_shared_resources
from refresh_faculty_directories import public_email
from lab_entities import LabIndex
from lab_program_affiliations import verified_program_affiliate_labs, SCOPE as PROGRAM_AFFILIATE_SCOPE
from lab_research_resource_reviews import verified_new_lab_scopes, SCOPE as CAMPUS_RESOURCE_SCOPE
from existing_lab_own_resources import verified_existing_own_resources, attach_existing_own_resources
from queue_resource_keys import normalize_queue_keys, rebind_decisions
from faculty_candidate_history import candidate_history, attach_history_patches
from professor_own_field_reviews import verified_professor_fields
from professor_profile_link_reviews import verified_profile_link_reviews
from faculty_department_normalizations import verified_department_normalizations
from faculty_profile_bindings import verified_profile_bindings
from professor_research_scope_reviews import verified_research_scopes
from professor_contact_scope_reviews import verified_contact_scopes
from rebuild_verified_atlas import RESEARCH_PHRASES


def reviewed_entity_rows(proposals, decisions):
    for proposal in proposals:
        decision = decisions['labs'].get(proposal['urlKey'], {})
        entities = decision.get('sharedEntities')
        if entities is None:
            if decision.get('action') == 'accept_shared_entities':
                raise ValueError('Shared website review is missing its named entities')
            yield proposal, decision
            continue
        if (decision.get('action') != 'accept_shared_entities' or not isinstance(entities, list)
                or len(entities) < 2 or not all(isinstance(e, dict) for e in entities)):
            raise ValueError('Shared website review requires at least two accepted named entities')
        ids = [e.get('stableLabId') for e in entities]
        if not all(ids) or len(set(ids)) != len(ids):
            raise ValueError('Shared entities require distinct frozen lab IDs')
        sharing = {'kind': 'distinct_named_labs', 'groupId': decision['sharingGroupId'],
                   'memberLabIds': sorted(ids), 'evidence': decision['sharingEvidence']}
        for entity in entities:
            yield proposal, {**entity, 'action': 'accept', 'websiteSharing': sharing}


def validate_reviewed_lab_sharing(labs, queue, cache):
    index = LabIndex(labs)
    index.validate_sharing()
    for lab in labs:
        for proof in lab.get('websiteSharing', {}).get('evidence', []):
            matches = [item for item in queue['items'].values()
                       if item.get('fetch', {}).get('status') == 'ok'
                       and item['fetch'].get('finalUrl') == proof['sourceUrl']
                       and item['fetch'].get('observedAt') == proof['observedAt']]
            valid = False
            for item in matches:
                path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
                if (path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == item['fetch'].get('sha256')
                        and proof['evidence'] in DOM(path.read_text()).main().text()):
                    valid = True
                    break
            if not valid:
                raise ValueError('Shared lab identity evidence does not match its dated capture: ' + lab['id'])


def preserve_supported_values(person, patch):
    patch = copy.deepcopy(patch)
    for field in list(patch.get('fieldEvidence', {})):
        if field not in patch or field in {'departmentAffiliations', 'directoryListings'}:
            continue
        old = person.get(field)
        if field == 'name' and patch.get('directoryListings') and old != patch[field]:
            patch.setdefault('previousFieldObservations', []).append({'field': field, 'value': old, 'fieldEvidence': copy.deepcopy(person.get('fieldEvidence', {}).get(field, []))})
            continue
        if field == 'officialProfileUrl' and patch.get('verifiedCanonicalProfile') and old != patch[field]:
            patch.setdefault('previousFieldObservations', []).append({'field': field, 'value': old, 'fieldEvidence': copy.deepcopy(person.get('fieldEvidence', {}).get(field, []))})
            patch['sourceUrls'] = unique_values(patch.get('sourceUrls', []) + [old, patch[field]])
            continue
        if old not in (None, '', 'Not found', 'Unknown', []) and old != patch[field] and person.get('fieldEvidence', {}).get(field):
            patch.setdefault('unappliedFieldObservations', []).append({'field': field, 'value': patch.pop(field), 'fieldEvidence': patch['fieldEvidence'].pop(field)})
    return patch


def accumulate_export_profile_patch(target, patch, person):
    """Keep reviewed identity choices and all accumulated source observations.

    Parsing another response can corroborate or enrich an owned profile. Its
    redirected address/displayed name does not reselect the canonical identity.
    History and source arrays already supplied by the faculty/history review
    must survive every subsequent profile response in this export batch.
    """
    patch = copy.deepcopy(patch)
    for field in ['name', 'officialProfileUrl']:
        chosen = target.get(field) or person.get(field)
        observed = patch.get(field)
        if chosen and observed and observed != chosen:
            patch.setdefault('additionalProfileObservations', []).append({
                'field': field, 'value': copy.deepcopy(observed),
                'fieldEvidence': evidence_items(patch.get('fieldEvidence', {}).get(field)),
                'reason': 'Captured own-profile observation retained separately; final export preserves the already reviewed canonical name and primary resource.'})
            patch.pop(field)
            patch.get('fieldEvidence', {}).pop(field, None)
            if field == 'officialProfileUrl':
                patch.pop('verifiedCanonicalProfile', None)
    history_fields = {'labAffiliations', 'unappliedFieldObservations', 'unresolvedLabLinks',
                      'previousFieldObservations', 'additionalProfileObservations',
                      'verificationHistory', 'sourceUrls', 'sourceUrlObservations'}
    observed = {k: v for k, v in patch.items() if k not in history_fields}
    observed['fieldEvidence'] = {k: v for k, v in patch.get('fieldEvidence', {}).items()
                                 if k not in history_fields}
    # A proof for a superseded URL/text belongs to that historical value. Do
    # not attach it to the next value or let an older queue item replace a
    # later observation merely because that item is iterated last.
    merged = merge_observed_fields(target, observed)
    for field, proofs in observed['fieldEvidence'].items():
        if field in observed and has_value(observed[field]) and merged.get(field) != observed[field]:
            observation = {'field': field, 'value': copy.deepcopy(observed[field]),
                           'fieldEvidence': copy.deepcopy(evidence_items(proofs)),
                           'reason': 'Older or independently scoped positive field observation retained without replacing the selected value.'}
            merged['previousFieldObservations'] = unique_values(merged.get('previousFieldObservations', []) + [observation])
    target.clear(); target.update(merged)
    for field, value in patch.items():
        if field == 'fieldEvidence':
            for name, proofs in value.items():
                if name in history_fields:
                    current = target.setdefault(field, {})
                    current[name] = unique_values(evidence_items(current.get(name)) + evidence_items(proofs))
        elif field in history_fields:
            target[field] = unique_values(target.get(field, []) + value)
        elif field in patch.get('fieldEvidence', {}):
            continue
        else:
            target[field] = value


def export_profile_routes(people, patches, queue, bindings, person_reviews=()):
    """Discovery context IDs cannot establish ownership of another profile.

    Original/accepted primaries and independently capture-verified personal
    identifier bindings are the only routes for applying parsed own fields.
    Same-name sitemap observations remain explicit held source observations.
    """
    aliases = {}
    for review in person_reviews:
        if (review.get('captureVerified') is not True or review.get('sourceProfessorId') not in people
                or review.get('targetProfessorId') not in people):
            raise ValueError('Export source aliases require independently verified original-person reviews')
        aliases[review['sourceProfessorId']] = review['targetProfessorId']
    if set(aliases) & set(aliases.values()):
        raise ValueError('Export source aliases must be acyclic direct reviewed decisions')
    routes = {}
    def add(uri, person):
        if not uri:
            return
        person = people[aliases.get(person['id'], person['id'])]
        candidates = routes.setdefault(url_key(uri), [])
        if all(p['id'] != person['id'] for p in candidates):
            candidates.append(person)
    for person in people.values():
        for uri in [person['officialProfileUrl'], patches.get(person['id'], {}).get('officialProfileUrl')]:
            add(uri, person)
    for binding in bindings:
        if binding.get('captureVerified') is not True or binding.get('professorId') not in people:
            raise ValueError('Additional export profile routes require independently verified person bindings')
        for capture in binding['captures']:
            if capture.get('canonicalUri') and capture.get('rdfAlternateUri'):
                add(capture['requestedUrl'], people[binding['professorId']])
    held, seen = [], set()
    for item in queue['items'].values():
        for context in item.get('contexts', []):
            pid = context.get('professorId')
            if pid not in people or context.get('sourceUrl') != 'https://profiles.ucsd.edu/sitemap.xml':
                continue
            if aliases.get(pid, pid) in {p['id'] for p in routes.get(url_key(item['url']), [])} or (pid, item['url']) in seen:
                continue
            seen.add((pid, item['url']))
            held.append({'professorIdContextOnly': pid, 'canonicalNameRetained': people[pid]['name'],
                         'originalProfileUri': people[pid]['officialProfileUrl'], 'discoveredProfileUri': item['url'],
                         'capture': copy.deepcopy(item.get('fetch', {})),
                         'reason': 'A sitemap discovery context or same-name appointment is not an independently verified person-to-resource binding.',
                         'status': 'additional_profile_source_identity_unverified', 'fieldsApplied': False})
    return routes, held


def resolve_profile_lab_links(patch, labs):
    retained, ambiguous = [], []
    for affiliation in patch.get('labAffiliations', []):
        # parse_profile generates candidate IDs from URLs. Such IDs do not
        # distinguish the separately named entities on a shared resource.
        target = labs.resolve(affiliation['url'], name=affiliation.get('labName'))
        if target is not None:
            retained.append({**affiliation, 'labId': target['id']})
        elif labs.candidates(affiliation['url']):
            ambiguous.append({**affiliation, 'reason': 'Shared website link does not identify one named lab'})
    patch['labAffiliations'] = retained
    if ambiguous:
        patch.setdefault('unresolvedLabLinks', []).extend(ambiguous)
    if patch.get('labAffiliationUrl') and labs.resolve(patch['labAffiliationUrl'], name=patch.get('labAffiliation')) is None:
        for field in ['labAffiliation', 'labAffiliationUrl']:
            patch.pop(field, None)
            patch['fieldEvidence'].pop(field, None)
    return patch


def reviewed_pi(decision):
    value = decision.get('principalInvestigator')
    if not value:
        return None
    proof = decision.get('piEvidence', [])
    if not has_named_pi(value, proof):
        raise ValueError('PI requires explicit reviewed person/leadership evidence')
    return {'fields': {'principalInvestigator': value}, 'fieldEvidence': {'principalInvestigator': proof}}


def attach_reviewed_lab_associations(patches, labs, people):
    """Use the same source-scoped reciprocal links in previews and final export."""
    for lab in labs:
        if any(pid not in people for pid in lab.get('professorIds', [])):
            raise ValueError('Unknown linked professor: ' + lab['id'])
        if lab.get('professorIds') and not evidence_items(lab.get('fieldEvidence', {}).get('labWebsiteUrl')):
            raise ValueError('Named directory lab association requires its source evidence')
    for lab in labs:
        for pid in lab.get('professorIds', []):
            affiliation = {'labId': lab['id'], 'labName': lab['labName'], 'url': lab['labWebsiteUrl'],
                           'relationship': 'official_directory_same_record',
                           'fieldEvidence': copy.deepcopy(lab['fieldEvidence']['labWebsiteUrl'])}
            links = patches.setdefault(pid, {'fieldEvidence': {}}).setdefault('labAffiliations', [])
            if affiliation not in links:
                links.append(affiliation)


def reviewed_contact(decision):
    value = decision.get('contactEmail')
    if not value:
        return None
    proof = evidence_items(decision.get('contactEvidence'))
    if public_email(value) != value or not proof or not any(value in p.get('evidence', '') for p in proof):
        raise ValueError('Lab contact requires one canonical public email and explicit reviewed contact evidence')
    return {'contactEmail': value, 'fieldEvidence': {'contactEmail': proof}}


def validate_reviewed_contacts(labs, queue, cache):
    for lab in labs:
        proofs = evidence_items(lab.get('fieldEvidence', {}).get('contactEmail'))
        if not proofs:
            continue
        if any(p.get('method') == 'reviewed_public_bracket_at_lab_contact' for p in proofs):
            verified = verified_program_affiliate_labs([lab], queue, cache)[0]
            if (verified['contactEmail'] != lab['contactEmail']
                    or verified['fieldEvidence'].get('contactEmail') != proofs):
                raise ValueError('Encoded lab contact differs from its exact verified own/program source pair')
            continue
        for proof in proofs:
            owned = own_lab_source(lab, proof['sourceUrl'], queue)
            found = False
            for item in queue['items'].values():
                meta = item.get('fetch', {})
                if not owned or meta.get('status') != 'ok' or meta.get('finalUrl') != proof['sourceUrl'] or meta.get('observedAt') != proof['observedAt']:
                    continue
                path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
                if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != meta.get('sha256'):
                    continue
                dom = DOM(path.read_text()).main()
                emails = set(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', dom.text()))
                emails.update(public_email(urllib.parse.unquote(node.attrs['href'])) for node in dom.walk() if node.tag == 'a' and node.attrs.get('href', '').lower().startswith('mailto:'))
                found = lab['contactEmail'] in emails
                if found:
                    break
            if not found:
                raise ValueError('Reviewed contact is absent from an own-lab dated capture: ' + lab['id'])


def validate_reviewed_descriptions(labs, queue, cache):
    from lab_identity_merges import verify_capture_proofs
    for lab in labs:
        proofs = evidence_items(lab.get('fieldEvidence', {}).get('description'))
        own = [p for p in proofs if p.get('method') == 'reviewed_own_lab_research_description']
        if not own:
            continue
        verify_capture_proofs(own, queue, cache, lab['id'])
        if (len(own) != len(proofs) or not all(own_lab_source(lab, p['sourceUrl'], queue)
                                             and lab['description'] == p['evidence'] for p in own)):
            raise ValueError('Lab description requires its exact quote on the captured own resource: ' + lab['id'])


def validate_reviewed_alias_names(labs, queue, cache):
    from lab_identity_merges import verify_capture_proofs
    from collect_ucsd_coverage import official
    for lab in labs:
        proofs = evidence_items(lab.get('fieldEvidence', {}).get('aliasNames'))
        if not proofs and not lab.get('aliasNames'):
            continue
        if not proofs or any(not isinstance(p.get('aliasName'), str)
                             or p.get('method') != 'reviewed_explicit_group_alias_name' for p in proofs):
            raise ValueError('Lab alias names require explicit typed captured proofs: ' + lab['id'])
        verify_capture_proofs(proofs, queue, cache, lab['id'])
        if (set(lab.get('aliasNames', [])) != {p.get('aliasName') for p in proofs}
                or any(not (own_lab_source(lab, p['sourceUrl'], queue)
                            or official(p['sourceUrl']) and p.get('evidenceType') == 'named_link'
                            and p.get('linkUrl') == lab['labWebsiteUrl']) for p in proofs)):
            raise ValueError('Lab alias name requires an own statement or exact named campus lab link: ' + lab['id'])


def verified_destination_reviews(queue, cache):
    review = read(ROOT / 'data/ucsd/legacy-lab-identity-review-20261016.json', {'entries': []})
    rows = []
    for row in review['entries']:
        if not row.get('action'):
            continue
        for proof in row['evidence']:
            item = queue['items'].get(url_key(proof['requestedUrl']))
            meta = item.get('fetch', {}) if item else {}
            body = body_for(item, cache) if item else ''
            if proof.get('evidenceType') == 'document_title':
                quotation_matches = proof['evidence'] in [node.text() for node in DOM(body).root.walk() if node.tag == 'title']
            else:
                quotation_matches = proof['evidence'] in DOM(body).main().text()
            if (meta.get('status') != 'ok' or meta.get('finalUrl') != proof['sourceUrl']
                    or meta.get('observedAt') != proof['observedAt']
                    or hashlib.sha256((cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')).read_bytes()).hexdigest() != proof['bodySha256']
                    or not quotation_matches):
                raise ValueError('Legacy destination review does not match its actual capture: ' + row['labId'])
        rows.append(row)
    return rows


def reviewed_lab_records(atlas, proposals, decisions):
    labs = LabIndex(atlas['labs'])
    new_labs, aliases, lab_updates, review = [], [], [], []
    proposal_keys = {p['urlKey'] for p in proposals}
    for key, decision in decisions['labs'].items():
        if decision.get('action') in {'accept', 'alias', 'accept_shared_entities'} and key not in proposal_keys:
            raise ValueError('Decision refers to a missing proposal: ' + key)
    rows = list(reviewed_entity_rows(proposals, decisions))
    # Resolve declared aliases after every explicitly accepted identity exists,
    # including a target introduced later in this same reviewed cohort.
    for proposal, decision in sorted(rows, key=lambda row: row[1].get('action') == 'alias'):
        if proposal['status'] == 'scope_excluded' and decision.get('action') in {'accept', 'alias'}:
            raise ValueError('Reviewed lab conflicts with a source-scope exclusion: ' + proposal['urlKey'])
        if decision.get('action') == 'alias':
            target = labs.by_id.get(decision.get('labId'))
            if target is None or not decision.get('aliasEvidence') or not decision.get('reason'):
                raise ValueError('Alias requires known lab ID, evidence, and review reason: ' + proposal['urlKey'])
            meta = proposal['destinationCheck']
            if meta.get('status') != 'ok':
                raise ValueError('Alias destination not accessible: ' + proposal['urlKey'])
            alias = {'labId': target['id'], 'url': meta['finalUrl'], 'fieldEvidence': decision['aliasEvidence'], 'reason': decision['reason']}
            aliases.append(alias)
            if decision.get('name'):
                if not decision.get('nameEvidence'):
                    raise ValueError('Reviewed label update requires explicit name evidence')
                lab_updates.append({'labId': target['id'], 'fields': {'labName': decision['name']}, 'fieldEvidence': {'labName': decision['nameEvidence']}})
            pi = reviewed_pi(decision)
            if pi:
                lab_updates.append({'labId': target['id'], **pi})
            labs.add_url(meta['finalUrl'], target)
            review.append({'urlKey': proposal['urlKey'], 'labId': target['id'], 'decision': decision})
            continue
        if decision.get('action') != 'accept':
            continue
        if proposal['status'] == 'existing_url_or_redirect' or proposal.get('sameWebsiteExistingLabIds'):
            raise ValueError('Cannot add existing lab: ' + proposal['urlKey'])
        if not decision.get('reason'):
            raise ValueError('Review reason required: ' + proposal['urlKey'])
        lab = copy.deepcopy(proposal['record'])
        if decision.get('websiteSharing'):
            lab['id'] = decision['stableLabId']
            lab['websiteSharing'] = copy.deepcopy(decision['websiteSharing'])
            lab['fieldEvidence']['websiteSharing'] = copy.deepcopy(lab['websiteSharing']['evidence'])
        if decision.get('stableLabId') and lab['id'] != decision['stableLabId']:
            raise ValueError('Reviewed stable lab ID changed; restore or explicitly reconcile its history: ' + proposal['urlKey'])
        meta = proposal['destinationCheck']
        if meta.get('status') != 'ok':
            raise ValueError('Accepted destination not accessible: ' + proposal['urlKey'])
        if proposal['status'] != 'reviewable_identity_match' and not decision.get('identityEvidence'):
            raise ValueError('Manual identity evidence required: ' + proposal['urlKey'])
        if decision.get('name'):
            if decision['name'] != lab['labName'] and not decision.get('identityEvidence'):
                raise ValueError('Changed lab name requires explicit identity evidence')
            lab['labName'] = decision['name']
        if decision.get('department'):
            if not decision.get('departmentEvidence'):
                raise ValueError('Department override requires field evidence')
            lab['department'] = decision['department']
        lab['recordSubtype'] = decision.get('recordSubtype', 'research_group' if 'group' in lab['labName'].lower() else 'lab')
        lab['labWebsiteUrl'] = meta['finalUrl']
        key = atlas_url_key(lab['labWebsiteUrl'])
        if labs.candidates(lab['labWebsiteUrl']) and not decision.get('websiteSharing'):
            raise ValueError('Accepted redirect duplicates existing/accepted lab: ' + key)
        # Only a reviewed explicit leadership source can add a PI; none is inferred.
        lab['principalInvestigator'] = lab['principalInvestigatorProfileUrl'] = 'Not found'
        lab.get('fieldEvidence', {}).pop('principalInvestigator', None)
        lab['fieldEvidence'] = {f: evidence_items(v) for f, v in lab['fieldEvidence'].items()}
        if decision.get('departmentUnresolvedReason'):
            if decision.get('department') or decision.get('departmentEvidence'):
                raise ValueError('Unresolved department cannot also have a verified override')
            lab['department'] = 'Unknown'
            lab['fieldEvidence'].pop('department', None)
            lab['unverifiedFields'] = unique_values(lab.get('unverifiedFields', []) + ['department'])
            lab['departmentAssessment'] = {'status': 'unresolved', 'reason': decision['departmentUnresolvedReason'], 'sourceObservedAt': meta['observedAt']}
        pi = reviewed_pi(decision)
        if pi:
            lab.update(pi['fields'])
            lab['fieldEvidence'].update(pi['fieldEvidence'])
            lab['principalInvestigatorIdentityScope'] = decision.get('principalInvestigatorIdentityScope', 'source_reported_name_only')
        contact = reviewed_contact(decision)
        if contact:
            lab['contactEmail'] = contact['contactEmail']
            lab['fieldEvidence'].update(contact['fieldEvidence'])
        if decision.get('identityEvidence'):
            lab['fieldEvidence']['labName'] = decision['identityEvidence']
        if decision.get('aliasNames') is not None:
            names = decision['aliasNames']; proofs = evidence_items(decision.get('aliasNameEvidence'))
            if (not isinstance(names, list) or not 1 <= len(names) <= 10
                    or any(not isinstance(n, str) or not n.strip() or len(n) > 200 for n in names)
                    or len(set(names)) != len(names) or lab['labName'] in names or not proofs
                    or any(not isinstance(p.get('aliasName'), str) for p in proofs)
                    or set(names) != {p.get('aliasName') for p in proofs}
                    or any(p.get('method') != 'reviewed_explicit_group_alias_name'
                           or p['aliasName'] not in p.get('evidence', '') for p in proofs)):
                raise ValueError('Reviewed lab alias names require exact published name proofs')
            lab['aliasNames'] = copy.deepcopy(names)
            lab['fieldEvidence']['aliasNames'] = copy.deepcopy(proofs)
        if decision.get('departmentEvidence'):
            lab['fieldEvidence']['department'] = decision['departmentEvidence']
        resource_review = decision.get('campusResearchResourceReview')
        if resource_review and (decision.get('programAffiliationReview')
                or decision.get('institution') != 'Unknown' or decision.get('institutionEvidence')
                or not decision.get('institutionUnresolvedReason')):
            raise ValueError('Campus resource scope requires unknown ownership and a separate unresolved reason')
        if (decision.get('institution') not in {None, 'University of California San Diego'}
                and not decision.get('programAffiliationReview') and not resource_review):
            raise ValueError('An explicit external institution requires its own program-affiliation review')
        if resource_review:
            lab['institution'] = 'Unknown'
            lab['campusResearchResourceReview'] = copy.deepcopy(resource_review)
            lab['relationshipScope'] = CAMPUS_RESOURCE_SCOPE
            lab['fieldEvidence'].pop('institution', None)
            lab['unverifiedFields'] = unique_values(lab.get('unverifiedFields', []) + ['institution'])
            lab['institutionAssessment'] = {'status': 'unresolved', 'reason': decision['institutionUnresolvedReason'], 'sourceObservedAt': meta['observedAt']}
        elif decision.get('programAffiliationReview'):
            lab['institution'] = decision.get('institution', '')
            lab['programAffiliationReview'] = copy.deepcopy(decision['programAffiliationReview'])
            lab['fieldEvidence']['institution'] = evidence_items(decision.get('institutionEvidence'))
            lab['relationshipScope'] = PROGRAM_AFFILIATE_SCOPE
        elif decision.get('institutionEvidence'):
            lab['institution'] = 'University of California San Diego'
            lab['fieldEvidence']['institution'] = decision['institutionEvidence']
            lab['relationshipScope'] = 'reviewed_ucsd_affiliation'
        if (lab['institution'] != 'University of California San Diego'
                and not lab.get('programAffiliationReview') and not resource_review):
            raise ValueError('Accepted UCSD lab requires reviewed UCSD affiliation evidence')
        lab['description'] = 'Research entity identified in the cited UC San Diego source.'
        lab['fieldEvidence']['description'] = copy.deepcopy(lab['fieldEvidence']['labName'])
        if decision.get('description') is not None:
            description, proofs = decision['description'], evidence_items(decision.get('descriptionEvidence'))
            if (not isinstance(description, str) or not description.strip() or len(description) > 2000 or not proofs
                    or any(p.get('method') != 'reviewed_own_lab_research_description'
                           or p.get('evidenceType', 'main_text_quote') != 'main_text_quote'
                           or p.get('evidence') != description for p in proofs)):
                raise ValueError('A reviewed lab description requires its complete exact source quote')
            lab['description'] = description
            lab['fieldEvidence']['description'] = copy.deepcopy(proofs)
        lab['fieldEvidence']['recordSubtype'] = copy.deepcopy(lab['fieldEvidence']['labName'])
        for proof in lab['fieldEvidence']['labWebsiteUrl']:
            proof['redirectEvidence'] = meta.get('redirects', [])
        lab['sourceUrls'] = unique_values(lab.get('sourceUrls', []) + [meta['finalUrl']] + [p['sourceUrl'] for values in lab['fieldEvidence'].values() for p in evidence_items(values)])
        lab.pop('destinationEvidence', None)
        labs.add(lab)
        new_labs.append(lab)
        review.append({'urlKey': proposal['urlKey'], 'labId': lab['id'], 'decision': decision})
    labs.validate_sharing()
    return new_labs, aliases, lab_updates, review, labs


def export_reviewed_lab_handoff(cache, decisions_path, output):
    """A separate incremental artifact; it cannot be used as completed capture."""
    from validate_data import validate_lab, valid_url
    protected = {ROOT / 'data/ucsd/coverage-expansion-evidence.json', ROOT / 'data/research-atlas.json', decisions_path}
    if output.resolve() in {p.resolve() for p in protected}:
        raise ValueError('Incremental handoff must not overwrite a final capture, served atlas or decisions')
    if output.exists() and read(output).get('collectionState') != 'reviewed_incremental':
        raise ValueError('Incremental handoff cannot replace an unrelated artifact')
    queue = read(cache / 'queue.json')
    normalize_queue_keys(queue)
    atlas_path = ROOT / 'data/research-atlas.json'
    original_atlas = atlas_path.read_bytes()
    atlas = json.loads(original_atlas)
    decisions = rebind_decisions(read(decisions_path), queue)
    proposals = prepare(queue, atlas, cache)
    labs, aliases, updates, review, _ = reviewed_lab_records(atlas, proposals, decisions)
    labs = verified_new_lab_scopes(labs, queue, cache)
    validate_reviewed_contacts(labs, queue, cache)
    validate_reviewed_descriptions(labs, queue, cache)
    validate_reviewed_alias_names(labs, queue, cache)
    validate_reviewed_lab_sharing(labs, queue, cache)
    existing_ids = {r['id'] for r in atlas['professors'] + atlas['labs']}
    professor_ids = {p['id'] for p in atlas['professors']}
    accepted_decisions = {r['labId']: r['decision'] for r in review if r['decision']['action'] == 'accept'}
    seen = set()
    for lab in labs:
        lab['sourceUrls'] = unique_values(lab['sourceUrls'] + [p['sourceUrl'] for values in lab['fieldEvidence'].values() for p in evidence_items(values)])
        lab['verification'] = {'status': 'source_checked', 'fieldsVerified': sorted(lab['fieldEvidence']),
                               'lastEvidenceAt': max(p['observedAt'] for values in lab['fieldEvidence'].values() for p in evidence_items(values)),
                               'issues': ['Incremental reviewed record; unknown fields and unfinished global collection remain explicit.']}
        if lab.get('programAffiliationReview') or lab.get('campusResearchResourceReview'):
            lab['verification']['lastAttemptedAt'] = lab['websiteCheck']['observedAt']
        validate_lab(lab)
        if lab['id'] in existing_ids or lab['id'] in seen:
            raise ValueError('Incremental ID collision: ' + lab['id'])
        seen.add(lab['id'])
        if not set(lab.get('professorIds', [])) <= professor_ids:
            raise ValueError('Incremental lab references an unreviewed professor ID')
        if accepted_decisions[lab['id']].get('stableLabId') != lab['id']:
            raise ValueError('Freeze each reviewed lab ID before handing it off')
        if not all(valid_url(u) for u in lab['sourceUrls']):
            raise ValueError('Incremental record has an invalid source reference')
    # Require every field-evidence date to resolve to an actual saved capture.
    captures = {}
    for item in queue['items'].values():
        meta = item.get('fetch', {})
        if meta.get('status') == 'ok':
            for url in [item['url'], meta.get('sourceUrl', ''), meta.get('finalUrl', '')]:
                captures[(url_key(url), meta['observedAt'])] = item
    sources = {}
    for lab in labs:
        for proofs in lab['fieldEvidence'].values():
            for proof in evidence_items(proofs):
                key = (url_key(proof['sourceUrl']), proof['observedAt'])
                item = captures.get(key)
                if item is None:
                    raise ValueError('Field evidence has no matching observed capture: ' + str(key))
                capture_path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
                digest = hashlib.sha256(capture_path.read_bytes()).hexdigest()
                if digest != item['fetch'].get('sha256'):
                    raise ValueError('Field evidence capture hash mismatch: ' + proof['sourceUrl'])
                sources[key] = {'sourceUrl': proof['sourceUrl'], 'requestedUrl': item['url'], 'observedAt': proof['observedAt'],
                                'bodySha256': digest, 'cachePath': str(cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html'))}
    handoff = {'schemaVersion': 1, 'generatedAt': now(), 'collectionState': 'reviewed_incremental', 'isFinalExport': False,
               'queueCheckpointAt': queue['updatedAt'], 'queueStates': queue.get('counts', {}), 'labs': labs, 'labAliases': aliases,
               'labUpdates': updates, 'sourceManifest': list(sources.values()), 'recordCount': len(labs), 'reviewedAliasCount': len(aliases),
               'decisionArtifactSha256': hashlib.sha256(decisions_path.read_bytes()).hexdigest(),
               'servedAtlasSha256': hashlib.sha256(original_atlas).hexdigest(), 'servedAtlasModified': False,
               'policy': 'Read-only reviewed incremental handoff owned by the collection task. Not a final capture or a served dataset. Stable IDs are frozen in the decisions file; unknown fields and content-date limitations remain explicit. The summary task must not modify collection data or infer completion/current operations from this handoff.'}
    if atlas_path.read_bytes() != original_atlas:
        raise ValueError('Served atlas changed while preparing incremental handoff')
    atomic_json(output, handoff)
    print(json.dumps({'handoff': str(output), 'records': len(labs), 'aliases': len(aliases), 'state': handoff['collectionState']}))


def export(cache, decisions_path):
    queue = read(cache / 'queue.json')
    pending = [x for x in queue['items'].values() if x['state'] in {'pending', 'running'}]
    if pending:
        raise ValueError(f'Eligible queue is incomplete: {len(pending)} pending/running URLs')
    normalize_queue_keys(queue)
    atlas = read(ROOT / 'data/research-atlas.json')
    decisions = rebind_decisions(read(decisions_path), queue)
    if not decisions or not isinstance(decisions.get('labs'), dict):
        raise ValueError('Explicit per-lab decisions file is required')
    proposals = prepare(queue, atlas, cache)
    faculty = faculty_review(queue, atlas, cache)
    people = {p['id']: p for p in atlas['professors'] + faculty['professors']}
    new_labs, aliases, lab_updates, review, labs = reviewed_lab_records(atlas, proposals, decisions)
    base_alias_reviews = verified_alias_reviews(read(ROOT / 'data/ucsd/lab-alias-resource-review-20261016.json', {'entries': []}), aliases, queue, cache)
    organization_resources = verified_published_organizations(
        read(ROOT / 'data/ucsd/lab-published-organization-resource-review-20261016.json', {'entries': []}),
        queue, cache, atlas['labs'] + new_labs, list(people.values()), aliases)
    resource_coverage = {'labAliases': aliases, 'labAliasResourceReviews': base_alias_reviews}
    attach_published_organization_aliases(resource_coverage, organization_resources)
    existing_own_resources = verified_existing_own_resources(
        read(ROOT / 'data/ucsd/lab-existing-own-resource-review-20261016.json', {'entries': []}),
        queue, cache, atlas['labs'] + new_labs)
    attach_existing_own_resources(resource_coverage, existing_own_resources)
    for row in organization_resources:
        labs.add_url(row['resourceAlias']['url'], labs.by_id[row['labId']])
    for row in existing_own_resources:
        labs.add_url(row['resourceAlias']['url'], labs.by_id[row['labId']])
    new_labs = verified_new_lab_scopes(new_labs, queue, cache)
    validate_reviewed_contacts(new_labs, queue, cache)
    validate_reviewed_descriptions(new_labs, queue, cache)
    validate_reviewed_alias_names(new_labs, queue, cache)
    validate_reviewed_lab_sharing(new_labs, queue, cache)
    for item in queue['items'].values():
        meta = item.get('fetch', {})
        if meta.get('status') != 'ok' or not meta.get('redirects'):
            continue
        target = labs.resolve(meta['finalUrl'])
        if target:
            labs.add_url(item['url'], target)
            if target in new_labs and atlas_url_key(item['url']) != atlas_url_key(target['labWebsiteUrl']):
                target['alternateWebsiteUrls'] = unique_values(target.get('alternateWebsiteUrls', []) + [item['url']])
    patches = {pid: preserve_supported_values(people[pid], patch) for pid, patch in faculty['byProfessorId'].items()}
    history_patches, held_candidates = candidate_history(
        read(ROOT / 'data/ucsd/faculty-candidate-observation-history-20261016.json', {'entries':[]}),
        list(people.values()), faculty, queue, cache)
    attach_history_patches(patches, history_patches)
    profile_bindings = verified_profile_bindings(
        read(ROOT / 'data/ucsd/faculty-profile-identity-review-20261016.json', {'entries': []}), queue, cache, atlas)
    person_reviews = verified_person_reviews(
        read(ROOT / 'data/ucsd/person-identity-review-20261016.json', {'entries': []}), queue, cache, atlas, faculty_review=faculty)
    by_profile, profile_source_holds = export_profile_routes(people, patches, queue, profile_bindings.values(), person_reviews)
    for item in queue['items'].values():
        if item.get('fetch', {}).get('status') != 'ok' or item['state'] != 'done':
            continue
        matches = by_profile.get(url_key(item['url']), [])
        if len(matches) != 1:
            continue
        p = matches[0]
        patch, _ = parse_profile(p, item['fetch'], body_for(item, cache))
        if not patch['verification'].get('identityMatched'):
            continue
        if item['fetch'].get('redirects') and url_key(p['officialProfileUrl']) == url_key(item['url']):
            patch['verifiedCanonicalProfile'] = True
        if any(c.get('professorId') == p['id'] and c.get('sourceUrl') == 'https://profiles.ucsd.edu/sitemap.xml' for c in item['contexts']):
            patch['verifiedCanonicalProfile'] = True
        patch = resolve_profile_lab_links(patch, labs)
        patch = preserve_supported_values(p, patch)
        target = patches.setdefault(p['id'], {'fieldEvidence': {}})
        accumulate_export_profile_patch(target, patch, p)
    attach_reviewed_lab_associations(patches, new_labs, people)
    checks = []
    for item in queue['items'].values():
        meta = item.get('fetch')
        if not meta:
            continue
        checks.append({**meta, 'fetchStatus': meta['status'], 'status': 'reachable' if meta['status'] == 'ok' else 'unavailable', 'title': item.get('page', {}).get('title', '')})
    coverage = {'newProfessorRecords': len(faculty['professors']), 'professorPatches': len(patches), 'acceptedNewLabs': len(new_labs), 'reviewedLabAliases': len(aliases),
                'queueUrls': len(queue['items']), 'queueStates': queue['counts'], 'uncertainFacultyListings': len(faculty['uncertainListings']),
                'separateCentersAndInstitutes': len(queue['centers']), 'sourceChecks': len(checks)}
    output = {'schemaVersion': 1, 'generatedAt': now(), 'collectionState': 'completed', 'professors': faculty['professors'],
              'byProfessorId': patches, 'labs': new_labs, 'labAliases': aliases, 'labUpdates': lab_updates, 'checks': checks, 'coverage': coverage,
              'heldFacultyCandidates': held_candidates,
              'unverifiedAdditionalProfileSourceObservations': profile_source_holds,
              'reviewedLabDecisions': review, 'uncertainFacultyListings': faculty['uncertainListings'],
              'sourceListingSelectionHistory': faculty.get('sourceListingSelectionHistory', []),
              'destinationIdentityReviews': verified_destination_reviews(queue, cache),
              'labIdentityMerges': verified_lab_merges(read(ROOT / 'data/ucsd/coverage-20261016-existing-lab-merges.json', {'entries': []}), queue, cache),
              'labResourceReviews': verified_resource_reviews(read(ROOT / 'data/ucsd/lab-resource-identity-review-20261016.json', {'entries': []}), queue, cache,
                  read(ROOT / 'data/ucsd/lab-evidence.json')['labs'] + new_labs, atlas['labs']),
              'labAliasResourceReviews': resource_coverage['labAliasResourceReviews'],
              'publishedOrganizationResourceReviews': organization_resources,
              'existingOwnLabResourceReviews': existing_own_resources,
              'personIdentityReviews': person_reviews,
              'reviewedLabFieldUpdates': verified_lab_fields(read(ROOT / 'data/ucsd/lab-field-review-20261016.json', {'entries': []}), queue, cache,
                  atlas['labs'] + new_labs, atlas['professors'] + faculty['professors']),
              'policy': 'Original evidence captures retained. Only explicit academic titles qualify new faculty. PI leadership is never inferred. Reachability is separate from identity and current affiliation.'}
    output['labResourceAssociationReviews'] = verified_resource_associations(
        read(ROOT / 'data/ucsd/lab-resource-association-review-20261016.json', {'entries': []}), queue, cache,
        atlas['labs'] + new_labs, output['destinationIdentityReviews'])
    output['sharedLabResourceReviews'] = verified_shared_resources(
        read(ROOT / 'data/ucsd/shared-lab-resource-review-20261016.json', {'entries': []}), queue, cache, atlas['labs'] + new_labs)
    output['reviewedProfessorFieldUpdates'] = verified_professor_fields(
        read(ROOT / 'data/ucsd/professor-own-field-review-20261016.json', {'entries': []}), queue, cache,
        atlas['professors'] + faculty['professors'], output['personIdentityReviews'], faculty_review=faculty)
    output['reviewedProfessorResearchScopes'] = verified_research_scopes(
        read(ROOT / 'data/ucsd/professor-research-scope-review-20261016.json', {'entries': []}),
        queue, cache, people, by_profile, RESEARCH_PHRASES, output['reviewedProfessorFieldUpdates'])
    output['reviewedProfessorContactScopes'] = verified_contact_scopes(
        read(ROOT / 'data/ucsd/professor-contact-scope-review-20261016.json', {'entries': []}),
        queue, cache, people)
    output['reviewedDepartmentNormalizations'] = verified_department_normalizations(
        read(ROOT / 'data/ucsd/faculty-department-normalization-review-20261016.json', {'rules': [], 'entries': []}),
        queue, cache, atlas['professors'] + faculty['professors'],
        read(ROOT / 'data/ucsd/departments.json', {'departments': []})['departments'])
    output['professorProfileLinkReviews'] = verified_profile_link_reviews(
        read(ROOT / 'data/ucsd/professor-profile-link-review-20261016.json', {'entries': []}),
        queue, cache, atlas['professors'] + faculty['professors'])
    output['labOwnMetadataReviews'] = verified_own_metadata(
        read(ROOT / 'data/ucsd/lab-own-metadata-review-20261016.json', {'entries': []}),
        output['labAliasResourceReviews'], queue, cache, atlas['labs'] + new_labs, lab_updates)
    output['labOwnershipReviews'] = verified_lab_ownership_reviews(
        read(ROOT / 'data/ucsd/lab-own-institution-review-20261016.json', {'entries': []}),
        queue, cache, atlas['labs'] + new_labs)
    output['labPreferredResourceReviews'] = verified_preferred_resources(
        read(ROOT / 'data/ucsd/lab-preferred-resource-review-20261016.json', {'entries': []}),
        output['labAliasResourceReviews'], queue, cache, atlas['labs'] + new_labs, lab_updates)
    atomic_json(ROOT / 'data/ucsd/coverage-expansion-evidence.json', output)
    atomic_json(ROOT / 'data/ucsd/coverage-20261016-centers.json', {'schemaVersion': 1, 'generatedAt': now(), 'entities': list(queue['centers'].values()), 'policy': 'Separate center/institute discovery records; not counted as PI laboratories or proof of leadership.'})
    atomic_json(ROOT / 'data/ucsd/coverage-20261016-queue.json', queue)
    print(json.dumps(coverage, indent=2))


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--cache', type=Path, default=ROOT / '.cache/coverage-20261016')
    cli.add_argument('--decisions', type=Path, default=ROOT / 'data/ucsd/coverage-20261016-decisions.json')
    cli.add_argument('--reviewed-lab-handoff', type=Path, help='Write only a separate read-only incremental lab handoff; final export remains completion-gated')
    args = cli.parse_args()
    if args.reviewed_lab_handoff:
        export_reviewed_lab_handoff(args.cache, args.decisions, args.reviewed_lab_handoff)
    else:
        export(args.cache, args.decisions)
