"""Review name-only associations between newly proposed individual sources.

The first independently qualified source keeps its stable proposed ID. Another
individual resource needs actual shared person declarations or a self-labelled
contact link. Unit differences neither prove nor disprove person identity.
"""
from __future__ import annotations

import copy
import urllib.parse

from atlas_urls import url_key
from faculty_profile_bindings import profile_metadata, own_profile_links, captured_source
from refresh_faculty_directories import build_evidence, identity_name, individual_profile
from refresh_labs import DOM, every_node
from candidate_primary_roots import reviewed_primary_roots

NAME_METHODS = {'same_full_name', 'same_department_full_given_name_spacing_variant',
                'unique_full_first_last', 'same_department_unique_full_first_last',
                'same_department_unique_legacy_initials_expanded_by_directory'}


def same_subject(expected, displayed):
    first, second = identity_name(expected).split(), identity_name(displayed).split()
    if min(len(first), len(second)) < 2 or first[0] != second[0] or first[-1] != second[-1]:
        return False
    # A published middle initial can be omitted before a compound surname.
    # This checks subject compatibility only; a literal source declaration is
    # still required to establish the actual resource association.
    shorter, longer = sorted([first[1:-1], second[1:-1]], key=len)
    remaining = iter(longer)
    return all(any(a == b or min(len(a), len(b)) == 1 and a[0] == b[0]
                   for b in remaining) for a in shorter)


def provider_metadata(item, cache, name):
    base, markup = captured_source(item, cache)
    parsed = urllib.parse.urlsplit(base['sourceUrl'])
    if parsed.hostname != 'providers.ucsd.edu' or not parsed.path.startswith('/details/'):
        return None
    nodes = list(every_node(DOM(markup).root))
    titles = [n.text() for n in nodes if n.tag == 'title']
    og = [n.attrs.get('content') for n in nodes if n.tag == 'meta' and n.attrs.get('property') == 'og:title']
    canonical = [urllib.parse.urljoin(base['sourceUrl'], n.attrs['href']) for n in nodes
                 if n.tag == 'link' and n.attrs.get('rel') == 'canonical' and n.attrs.get('href')
                 and n.parent and n.parent.tag == 'head']
    if len(titles) != 1 or og != titles or len(canonical) != 1:
        return None
    subject = titles[0].split('|')[0].split(',')[0].strip()
    target = urllib.parse.urlsplit(canonical[0])
    if (not same_subject(name, subject) or target.hostname != 'providers.ucsd.edu'
            or not individual_profile(canonical[0]) or target.query or target.fragment):
        return None
    return {**base, 'nameAsDisplayed': subject, 'canonicalUri': canonical[0],
            'nameMethod': 'matching_document_and_open_graph_person_titles'}


def clinical_profile_links(item, cache, name):
    metadata, markup = profile_metadata(item, cache)
    if not same_subject(name, metadata['nameAsDisplayed']):
        return []
    nodes = list(every_node(DOM(markup).root))
    containers = [n for n in nodes if n.tag == 'div' and n.attrs.get('id') == 'view_links_table']
    if len(containers) != 1:
        return []
    output = []
    for node in containers[0].walk():
        if node.tag != 'a' or node.text() != 'Clinical Profile' or not node.attrs.get('href'):
            continue
        parent = node.parent
        while parent is not None and parent is not containers[0] and parent.tag != 'tr':
            parent = parent.parent
        uri = urllib.parse.urljoin(metadata['sourceUrl'], node.attrs['href'])
        if (parent is not None and parent.tag == 'tr' and 'website-table' in parent.attrs.get('class', '').split()
                and parent.text() == 'Clinical Profile' and urllib.parse.urlsplit(uri).hostname == 'providers.ucsd.edu'
                and individual_profile(uri)):
            output.append({**metadata, 'linkUrl': uri, 'rawHref': node.attrs['href'],
                           'linkText': node.text(), 'contextId': 'view_links_table', 'rowText': parent.text()})
    return output


def observation_key(row):
    return (row['sourceUrl'], row['observedAt'], identity_name(row['name']), row['department'], row['listedRole'])


def reviewed_new_candidate_sources(records, professors, queue, cache, primary_review=None):
    ordered, retained_roots = reviewed_primary_roots(primary_review or {'entries': []}, records, professors, queue, cache)
    working = copy.deepcopy(ordered)
    items = {item['url']: item for item in queue['items'].values()}
    metadata, contacts, held, primary_roots, corroborations = {}, {}, {}, {}, {}

    def person_metadata(uri, name):
        if uri not in metadata:
            try:
                metadata[uri] = profile_metadata(items[uri], cache)[0]
            except (KeyError, ValueError):
                metadata[uri] = None
        value = metadata[uri]
        return value if value and same_subject(name, value['nameAsDisplayed']) else None

    def self_links(uri, name):
        key = (uri, name)
        if key not in contacts:
            try:
                contacts[key] = own_profile_links(items[uri], cache, name)
            except (KeyError, ValueError):
                contacts[key] = []
        return contacts[key]

    def source_identity(root, incoming, name):
        first, second = person_metadata(root, name), person_metadata(incoming, name)
        if first and second and all(first[k] == second[k] for k in ['canonicalUri', 'rdfAlternateUri']):
            return {'type': 'shared_canonical_and_personal_rdf', 'captures': [first, second]}
        for own, counterpart, other in [(first, second, incoming), (second, first, root)]:
            if own and counterpart is None and own['canonicalUri'] == other:
                return {'type': 'captured_person_canonical_declares_other_literal_uri', 'captures': [own]}
        providers = []
        for uri in [root, incoming]:
            try:
                providers.append(provider_metadata(items[uri], cache, name))
            except (KeyError, ValueError):
                providers.append(None)
        if all(providers) and providers[0]['canonicalUri'] == providers[1]['canonicalUri']:
            return {'type': 'matching_named_provider_canonical_declarations', 'captures': providers}
        for own_uri, other in [(root, incoming), (incoming, root)]:
            try:
                links = [p for p in clinical_profile_links(items[own_uri], cache, name) if p['linkUrl'] == other]
            except (KeyError, ValueError):
                links = []
            if len(links) == 1:
                return {'type': 'captured_person_clinical_profile_link', 'captures': links}
        for own_uri, profile in [(root, second), (incoming, first)]:
            if profile:
                links = [p for p in self_links(own_uri, name)
                         if p['linkUrl'] in {profile['requestedUrl'], profile['sourceUrl']}]
                if len(links) == 1:
                    return {'type': 'official_own_profile_contact_link', 'captures': [links[0], profile]}
        return None

    while True:
        additions, patches, uncertain = build_evidence(working, professors)
        raw_by_key = {observation_key(row): row for row in working}
        removed, annotated = set(), False
        for person in additions:
            root = None
            for listing in patches[person['id']]['directoryListings']:
                row = raw_by_key[observation_key(listing)]
                uri = row.get('profileUrl', '')
                if not individual_profile(uri):
                    continue
                if root is None:
                    root = row
                    continue
                if listing['identityMatchMethod'] not in NAME_METHODS or url_key(uri) == url_key(root['profileUrl']):
                    continue
                proof = source_identity(root['profileUrl'], uri, person['name'])
                key = observation_key(row)
                if proof:
                    capture = proof['captures'][-1]
                    row['identityProfessorId'] = person['id']
                    row['identityMatchMethod'] = 'captured_new_candidate_profile_source_identity'
                    row['identityEvidence'] = {'sourceUrl': capture['sourceUrl'], 'observedAt': capture['observedAt'],
                        'method': 'captured_new_candidate_profile_source_identity', 'status': 'verified',
                        'evidence': person['name'] + ' | ' + root['profileUrl'] + ' → ' + uri,
                        'newCandidateSourceIdentity': proof}
                    primary_roots[person['id']] = copy.deepcopy(root)
                    corroborations[key] = copy.deepcopy(row)
                    annotated = True
                else:
                    removed.add(key)
                    captures = [person_metadata(root['profileUrl'], person['name']), person_metadata(uri, row['name'])]
                    held[key] = {'listing': copy.deepcopy(row),
                        'reason': 'distinct_profile_same_or_similar_name_requires_identity_review',
                        'candidateProfessorIds': [], 'candidateProposedProfessorIds': [person['id']],
                        'existingCandidateProfileUri': root['profileUrl'], 'incomingProfileUri': uri,
                        'actualPersonMetadata': captures,
                        'scope': 'Retain the first independently qualified source under its unchanged proposed ID. A distinct individual resource matched only by name is an unresolved observation; no additional person, alias, shared appointment or different-human conclusion is asserted.'}
        if not removed and not annotated:
            break
        working = [row for row in working if observation_key(row) not in removed]

    def primary_proof(row):
        return {**(row.get('metadataEvidence') or row['evidence']),
                'method': 'explicit_individual_profile_link_from_directory',
                'evidence': row['name'] + ' → ' + row['profileUrl']}

    for person in additions:
        root = primary_roots.get(person['id'])
        if root is None:
            continue
        patch = patches[person['id']]
        for row in corroborations.values():
            if row.get('identityProfessorId') != person['id']:
                continue
            old = {'field': 'officialProfileUrl', 'value': row['profileUrl'],
                   'fieldEvidence': [primary_proof(row)],
                   'reason': 'Additional positively identified source URI retained as an observation; the first accepted primary URI stays unchanged.'}
            for target in [person, patch]:
                if old not in target.setdefault('previousFieldObservations', []):
                    target['previousFieldObservations'].append(copy.deepcopy(old))
        for target in [person, patch]:
            target['officialProfileUrl'] = root['profileUrl']
            target.setdefault('fieldEvidence', {})['officialProfileUrl'] = primary_proof(root)
    retained = {p['id']: p for p in additions}
    for root in retained_roots:
        person = retained.get(root['professorId'])
        if person is None or person['officialProfileUrl'] != root['originalProfessorRecord']['officialProfileUrl']:
            raise ValueError('A reviewed prior candidate must retain its same stable ID and original primary')
    return additions, patches, uncertain + list(held.values()), {
        'heldNameOnlySourceAssociations': len(held), 'positivelyCorroboratedAdditionalSources': len(corroborations),
        'firstPrimaryUrisRetained': len(primary_roots), 'holds': list(held.values()),
        'previouslyQualifiedPrimaryRoots': retained_roots}
