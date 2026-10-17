"""Normalize reviewed own-appointment unit labels after faculty admission.

These explicit rules target existing academic-unit categories, including schools
and institutes. They never qualify a person, bind a second profile, merge IDs,
infer a parent department, or establish current employment.
"""
from __future__ import annotations

import copy

from collect_ucsd_coverage import profiles_appointment
from faculty_profile_bindings import captured_source, profile_metadata
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import identity_name
from refresh_labs import DOM, every_node, evidence_items, unique_values


# Each reviewed pair is deliberately exact. A new abbreviation, subdivision,
# title or homepage requires a new source review; there is no fuzzy fallback.
RULES = {
    'Ob/Gyn & Reproductive sciences': (
        'ucsd-obstetrics-gynecology-and-reproductive-sciences', 'https://obgyn.ucsd.edu/',
        'Department of Obstetrics, Gynecology & Reproductive Sciences',
        'Obstetrics, Gynecology & Reproductive Sciences', 'expanded_ob_gyn_abbreviation'),
    'Orthopedic Surgery': (
        'ucsd-orthopaedic-surgery', 'https://ortho.ucsd.edu/',
        'Department of Orthopedic Surgery', 'Orthopedic Surgery', 'registered_spelling_variant'),
    'Radiation Medicine and Applied Science': (
        'ucsd-radiation-medicine', 'https://radonc.ucsd.edu/',
        'Department of Radiation Medicine and Applied Sciences',
        'Radiation Medicine and Applied Sciences', 'terminal_plural_and_registered_short_label'),
    'School of Pharmacy and Pharmaceutical Science': (
        'ucsd-pharmacy-and-pharmaceutical-sciences', 'https://pharmacy.ucsd.edu/',
        'Home | Skaggs School of Pharmacy and Pharmaceutical Sciences',
        'Skaggs School of Pharmacy and Pharmaceutical Sciences', 'school_brand_and_terminal_plural'),
    'School of Global Policy & Strategy': (
        'ucsd-global-policy-and-strategy', 'https://gps.ucsd.edu/',
        'School of Global Policy and Strategy', 'School of Global Policy and Strategy',
        'conjunction_and_registered_school_label'),
    'HALICIOGLU DATA SCIENCE INST': (
        'ucsd-halicio-lu-data-science-institute', 'https://datascience.ucsd.edu/',
        'Halıcıoğlu Data Science Institute – UC San Diego', 'Halıcıoğlu Data Science Institute',
        'institute_abbreviation_and_registered_transliteration'),
    'Scripps Institution of Oceanography Department': (
        'ucsd-scripps-institution-of-oceanography', 'https://scripps.ucsd.edu/',
        'Scripps Institution of Oceanography |', 'Scripps Institution of Oceanography',
        'trailing_department_designator'),
    'Division of Biological Science': (
        'ucsd-biological-sciences', 'https://biology.ucsd.edu/',
        'Biological Sciences', 'Biological Sciences', 'umbrella_biological_sciences_label'),
    'Herbert Wertheim School of Public Health & Human Longevity Science': (
        'ucsd-public-health', 'https://hwsph.ucsd.edu/',
        'UC San Diego Herbert Wertheim School of Public Health and Human Longevity Science',
        'Herbert Wertheim School of Public Health and Human Longevity Science',
        'conjunction_and_registered_public_health_school_label'),
}


def proof(capture, kind, text, **details):
    return {**capture, 'status': 'verified', 'method': 'reviewed_own_appointment_unit_label',
            'evidenceType': kind, 'evidence': text, **details}


def unit_observation(raw_unit, registry, item, cache):
    rule = RULES.get(raw_unit)
    if rule is None:
        raise ValueError('Unreviewed unit spelling or hierarchy requires separate review')
    unit_id, homepage, title, published, kind = rule
    if registry.get('id') != unit_id or registry.get('homepage') != homepage or item['url'] != homepage:
        raise ValueError('Unit normalization requires the unchanged registered academic-unit homepage')
    capture, markup = captured_source(item, cache)
    meta = item['fetch']
    # All currently reviewed unit roots were direct HTTP 200 responses. Do not
    # silently accept new redirects or a different resource under the same host.
    if meta.get('httpStatus') != 200 or capture['sourceUrl'] != homepage or meta.get('redirects'):
        raise ValueError('Unit normalization requires its reviewed direct successful homepage capture')
    titles = [n.text() for n in every_node(DOM(markup).root) if n.tag == 'title']
    if titles != [title]:
        raise ValueError('The registered unit must explicitly publish its reviewed own document title')
    return {'sourceUnitAsPublished': raw_unit, 'unitNameAsPublished': published,
            'normalizationKind': kind, 'canonicalDepartmentId': unit_id,
            'canonicalDepartment': registry['name'], 'capture': capture,
            'fieldEvidence': [proof(capture, 'document_title', title)],
            'scope': 'Existing academic-unit category only; schools, institutes and umbrella units remain at that scope. No finer department or current-employment claim.'}


def appointment_observation(person, item, cache):
    metadata, markup = profile_metadata(item, cache)
    primary = person.get('officialProfileUrl')
    if (primary != item['url'] or primary != metadata['sourceUrl'] or primary != metadata['canonicalUri']
            or identity_name(person.get('name', '')) != identity_name(metadata['nameAsDisplayed'])):
        raise ValueError('Unit labels require the unchanged own primary and exact accepted subject; no new person binding')
    assessment, listing = profiles_appointment(item['fetch'], markup)
    if not listing or listing['departmentMappingStatus'] != 'explicit_unit_unmapped':
        raise ValueError('Unit normalization requires a previously unmapped explicit academic appointment')
    # Other basicInfo blocks may contain grants. Only one may contain the own
    # labelled appointment rows, and each label must occur exactly once.
    blocks = []
    for block in DOM(markup).main().walk():
        if block.tag != 'div' or 'basicInfo' not in block.attrs.get('class', '').split():
            continue
        rows = {}
        for node in block.walk():
            cells = [c for c in node.children if hasattr(c, 'tag') and c.tag in {'th', 'td'}]
            if node.tag == 'tr' and len(cells) == 2 and cells[0].tag == 'th' and cells[1].tag == 'td':
                label = cells[0].text()
                if label in {'Title(s)', 'School'}:
                    rows.setdefault(label, []).append((cells[1].text(), node.text()))
        if rows:
            blocks.append(rows)
    if len(blocks) != 1 or any(len(blocks[0].get(k, [])) != 1 for k in ['Title(s)', 'School']):
        raise ValueError('Own appointment labels must be unique in the named profile template')
    rows = blocks[0]
    if (rows['Title(s)'][0][0] != assessment['titleAsListed']
            or rows['School'][0][0] != assessment['schoolAsListed']):
        raise ValueError('Scoped own appointment must agree with the admitted source observation')
    capture = {k: metadata[k] for k in ['requestedUrl', 'sourceUrl', 'observedAt', 'bodySha256']}
    proofs = [proof(capture, 'document_heading', metadata['nameAsDisplayed'], headingTag='h2')]
    proofs += [proof(capture, 'main_text_quote', rows[k][0][1]) for k in ['Title(s)', 'School']]
    return {'metadata': metadata, 'assessment': assessment, 'fieldEvidence': proofs}


def verified_department_normalizations(review, queue, cache, professors, departments):
    people = {p['id']: p for p in professors}
    registry = {d['id']: d for d in departments}
    items = {i['url']: i for i in queue['items'].values()}
    owners = {}
    for p in professors:
        owners.setdefault(p.get('officialProfileUrl'), set()).add(p['id'])
    rules, seen, verified = {}, set(), []
    for row in review.get('rules', []):
        raw = row.get('sourceUnitAsPublished')
        original = row.get('originalDepartmentRecord', {})
        if (raw in rules or raw not in RULES or not row.get('reason')
                or row.get('originalDepartmentRecordSha256') != record_sha256(original)
                or registry.get(original.get('id')) != original):
            raise ValueError('Unit rule requires one unchanged registered category and explicit review')
        item = items.get(original['homepage'])
        if item is None:
            raise ValueError('Registered unit homepage is absent from this frozen source cohort')
        actual = unit_observation(raw, original, item, cache)
        if row.get('unitObservation') != actual:
            raise ValueError('Unit rule must equal its actual published title and capture')
        verify_capture_proofs(actual['fieldEvidence'], queue, cache, raw)
        rules[raw] = row
    for raw in review.get('entries', []):
        row = copy.deepcopy(raw)
        original = row.get('originalProfessorRecord', {})
        pid = row.get('professorId')
        person = people.get(pid)
        rule = rules.get(row.get('sourceUnitAsPublished'))
        if (person is None or rule is None or pid in seen or original.get('id') != pid
                or not row.get('reason') or row.get('originalProfessorRecordSha256') != record_sha256(original)
                or any(person.get(k) != original.get(k) for k in ['id', 'name', 'institution', 'officialProfileUrl'])
                or person.get('department') != 'Unknown' or original.get('department') != 'Unknown'
                or owners.get(person['officialProfileUrl']) != {pid}):
            raise ValueError('Unit normalization requires an accepted unchanged unique primary identity with Unknown category')
        item = items.get(person['officialProfileUrl'])
        if item is None:
            raise ValueError('Own primary is absent from this frozen source cohort')
        actual = appointment_observation(original, item, cache)
        assessment = actual['assessment']
        accepted = [r for r in original.get('directoryListings', [])
                    if r.get('sourceUrl') == assessment['sourceUrl'] and r.get('observedAt') == assessment['observedAt']
                    and r.get('departmentMappingStatus') == 'explicit_unit_unmapped'
                    and r.get('departmentAsListed') == assessment['departmentAsListed']
                    and r.get('listedRole') == assessment['titleAsListed']
                    and identity_name(r.get('name', '')) == identity_name(actual['metadata']['nameAsDisplayed'])]
        if (len(accepted) != 1 or assessment['departmentAsListed'] != row['sourceUnitAsPublished']
                or row.get('appointmentObservation') != actual):
            raise ValueError('Unit normalization must retain its exact previously accepted own appointment observation')
        verify_capture_proofs(actual['fieldEvidence'], queue, cache, pid)
        row.update(unitReview=copy.deepcopy(rule), captureVerified=True)
        verified.append(row); seen.add(pid)
    return verified


def apply_department_normalizations(data, reviews):
    people = {p['id']: p for p in data['professors']}
    seen = set()
    # Validate the entire batch before changing any category.
    for row in reviews:
        person = people.get(row.get('professorId'))
        old = row.get('originalProfessorRecord', {})
        unit = row.get('unitReview', {}).get('unitObservation', {})
        if (not row.get('captureVerified') or person is None or person['id'] in seen
                or not unit.get('canonicalDepartment') or not row.get('appointmentObservation')
                or row.get('originalProfessorRecordSha256') != record_sha256(old)
                or any(person.get(k) != old.get(k) for k in ['id', 'name', 'institution', 'officialProfileUrl'])
                or person.get('department') not in {'Unknown', unit['canonicalDepartment']}
                or person.get('directoryListings') != old.get('directoryListings')):
            raise ValueError('Only verified label normalization may update its same accepted canonical person')
        seen.add(person['id'])
    for row in reviews:
        person = people[row['professorId']]
        unit = row['unitReview']['unitObservation']
        own = row['appointmentObservation']
        proofs = copy.deepcopy(own['fieldEvidence'] + unit['fieldEvidence'])
        fields = person.setdefault('fieldEvidence', {})
        prior = evidence_items(fields.get('department'))
        # Earlier admission patches can replay older Unknown-field proofs. Keep
        # those proofs once, without accumulating mixed histories on each build.
        old = row['originalProfessorRecord']
        history = {'field': 'department', 'value': old['department'],
                   'fieldEvidence': copy.deepcopy(evidence_items(old.get('fieldEvidence', {}).get('department'))),
                   'reason': row['reason']}
        histories = person.setdefault('previousFieldObservations', [])
        if history not in histories:
            histories.append(history)
        archived = history['fieldEvidence']
        extras = [p for p in prior if p not in proofs and p not in archived]
        if extras:
            observation = {'field': 'department', 'value': person['department'], 'fieldEvidence': extras,
                           'reason': 'Earlier department proofs retained separately from the reviewed unit label.'}
            if observation not in histories:
                histories.append(observation)
        person['department'] = unit['canonicalDepartment']
        fields['department'] = proofs
        person['departmentLabelNormalization'] = {
            'captureVerified': True, **{k: unit[k] for k in ['sourceUnitAsPublished', 'unitNameAsPublished',
                'canonicalDepartmentId', 'canonicalDepartment', 'normalizationKind', 'scope']},
            'unitSourceUrl': unit['capture']['sourceUrl'], 'unitObservedAt': unit['capture']['observedAt'],
            'ownAppointmentSourceUrl': own['metadata']['sourceUrl'], 'ownAppointmentObservedAt': own['metadata']['observedAt']}
        person['departmentNormalizationReviews'] = unique_values(person.get('departmentNormalizationReviews', []) + [copy.deepcopy(row)])
        person['sourceUrls'] = unique_values(person.get('sourceUrls', []) + [p['sourceUrl'] for p in proofs])
