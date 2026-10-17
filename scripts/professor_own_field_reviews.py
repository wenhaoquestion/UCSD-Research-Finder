"""Verify research/contact fields on a specifically named original own page.

Math's Drupal page title lives inside an aside. Only its explicit title block
is read outside the main content walk; other navigation/sidebars stay excluded.
These fields never qualify faculty, expand initials, or create/merge identities.
GPS biography summaries require their explicit own Profile tab; a personal
publication excerpt can be replaced only after a separate paper-scope review.
Rady research lists require the named own Research Areas tab and contact article;
they do not bind another profile or derive topics from publications.
"""
from __future__ import annotations

import copy
import json
import re
from urllib.parse import urlsplit, urljoin

from atlas_urls import valid_url
from faculty_profile_bindings import captured_source
from faculty_scoped_titles import same_named_subject
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import public_email
from refresh_labs import DOM, every_node, evidence, evidence_items, merge_observed_fields, unique_values
from professor_biography_reviews import gps_own_research_summary, verified_previous_paper_scope, apply_biography_summary
from rady_own_fields import rady_own_fields
from matsci_own_fields import matsci_own_fields, retained_directory_primary
from faculty_career_identity_reviews import retained_career_field_lineage
from labelled_profile_research import TEMPLATES as LABELLED_RESEARCH_TEMPLATES, labelled_research, reviewed_subject
from professor_research_scope_reviews import preserves_reviewed_research


def classes(node):
    return set(node.attrs.get('class', '').split())


def math_own_fields(item, cache, name):
    """Read only explicitly labelled fields in the single-person template."""
    base, markup = captured_source(item, cache)
    for uri in [base['requestedUrl'], base['sourceUrl']]:
        parsed = urlsplit(uri)
        if (parsed.hostname not in {'math.ucsd.edu', 'www.math.ucsd.edu'}
                or not re.fullmatch(r'/people/profiles/[A-Za-z0-9_.-]+/?', parsed.path)
                or parsed.query or parsed.fragment):
            raise ValueError('Math fields require an exact captured individual Math profile')
    dom = DOM(markup)
    blocks = [n for n in every_node(dom.root) if 'block-page-title-block' in classes(n)
              and n.attrs.get('id') == 'block-bootstrap-math-page-title']
    if len(blocks) != 1:
        raise ValueError('Math fields require the explicit single Drupal page-title block')
    subjects = [n for n in every_node(blocks[0]) if n.tag == 'h1' and 'title' in classes(n)]
    titles = [n for n in every_node(dom.root) if n.tag == 'title']
    if (len(subjects) != 1 or len(titles) != 1
            or not same_named_subject(name, subjects[0].text())
            or not same_named_subject(subjects[0].text(), titles[0].text().split('|', 1)[0].strip())):
        raise ValueError('Math page title and document title must name the unchanged complete subject')
    nodes = list(dom.main().walk())
    names = [n for n in nodes if n.attrs.get('id') == 'profile_full_name']
    roles = [n for n in nodes if n.attrs.get('id') == 'person_titles']
    if (len(names) != 1 or len(roles) != 1 or names[0].parent is not roles[0].parent
            or 'col-sm-9' not in classes(names[0].parent)
            or names[0].text() and not same_named_subject(name, names[0].text())):
        raise ValueError('Math fields require one matching single-person profile body')
    row = names[0].parent.parent
    columns = [n for n in row.children if hasattr(n, 'tag') and 'col-sm-3' in classes(n)]
    if 'row' not in classes(row) or len(columns) != 1:
        raise ValueError('Math fields require one own research/contact column')
    column = columns[0]
    fields, proofs = {}, {}
    labels = [n for n in column.walk() if n.tag == 'p' and n.text() == 'Research Areas']
    if len(labels) > 1:
        raise ValueError('Conflicting Math research-area sections require review')
    if labels:
        label = labels[0]
        children = [n for n in label.parent.children if hasattr(n, 'tag')]
        if ('mt-3' not in classes(label.parent) or not children or children[0] is not label
                or any(n.tag not in {'a', 'span'} or 'badge' not in classes(n) for n in children[1:])):
            raise ValueError('Research terms must be direct badges after the own Research Areas label')
        areas = list(dict.fromkeys(n.text() for n in children[1:] if n.text()))
        if areas and all(len(term) <= 160 and term.lower() not in {'coming soon', 'n/a', 'not found', 'unknown'} for term in areas):
            fields['researchAreas'] = areas
            proofs['researchAreas'] = [{**evidence(item['fetch'], 'named_math_own_research_area_badges',
                subjects[0].text() + ' | Research Areas: ' + ' | '.join(areas)), **base,
                'subjectTemplate': 'math_drupal_page_title_block', 'subjectBlockId': blocks[0].attrs['id'],
                'nameAsDisplayed': subjects[0].text(), 'fieldLabel': 'Research Areas', 'valuesAsListed': areas}]
    emails = [n for n in column.walk() if n.attrs.get('id') == 'person_email']
    if len(emails) > 1:
        raise ValueError('Conflicting own email fields require review')
    if emails:
        node = emails[0]
        label = [n for n in node.parent.children if hasattr(n, 'tag') and n.tag == 'strong' and n.text() == 'Email:']
        value = public_email(node.text())
        if node.tag == 'span' and node.parent.tag == 'p' and len(label) == 1 and value and value == node.text():
            fields['email'] = value
            proofs['email'] = [{**evidence(item['fetch'], 'named_math_own_public_email_field',
                subjects[0].text() + ' | Email: ' + value), **base,
                'subjectTemplate': 'math_drupal_page_title_block', 'subjectBlockId': blocks[0].attrs['id'],
                'nameAsDisplayed': subjects[0].text(), 'fieldLabel': 'Email:', 'valueAsListed': value}]
    return {'capture': base, 'nameAsDisplayed': subjects[0].text(), 'fields': fields, 'fieldEvidence': proofs,
            'scope': 'Own labelled research areas and public professional email only; no name, identity, appointment, affiliation or current-employment change.'}


def additional_math_source_identity(person, actual, feed_item, cache, contact_owners, target_id):
    """Bind an additional named source by two published personal contacts.

    The older explicit named card stays a dated observation, never a current
    appointment claim. The newly captured feed must independently publish the
    exact extra profile link, email and personal website. No URI alias follows.
    """
    email = public_email(person.get('email', ''))
    website = person.get('personalWebsiteUrl', '')
    if (not email or not re.fullmatch(r'[^@]+@(?:[^@.]+\.)*ucsd\.edu', email)
            or email.split('@')[0].lower() in {'info', 'contact', 'webmaster', 'support', 'admin', 'advising', 'department'}
            or not valid_url(website)
            or actual['capture']['requestedUrl'] == person['officialProfileUrl']
            or actual['fields'].get('email') != email
            or not same_named_subject(person['name'], actual['nameAsDisplayed'])
            or contact_owners['email'].get(email.lower()) != {target_id}
            or contact_owners['personalWebsiteUrl'].get(website) != {target_id}):
        raise ValueError('Additional own source requires the complete subject and uniquely owned public email and website')
    fields = person.get('fieldEvidence', {})
    def proofs(field):
        value = fields.get(field, [])
        return value if isinstance(value, list) else [value]
    anchors = []
    for contact in proofs('email'):
        if (contact.get('status') != 'verified' or contact.get('method') != 'explicit_person_card_value'
                or contact.get('sourceUrl') != 'https://soeapp.ucsd.edu/tools/eah/department.php'
                or not contact.get('observedAt') or contact.get('evidence') != f"{person['name']} | email: {email}"):
            continue
        matching = lambda proof: (proof.get('status') == 'verified'
            and (proof.get('sourceUrl'), proof.get('observedAt')) == (contact['sourceUrl'], contact['observedAt']))
        names = [p for p in proofs('name') if matching(p)
                 and p.get('method') == 'official_directory_public_feed_rendering_rules'
                 and person['name'] in p.get('evidence', '').split(' | ')]
        sites = [p for p in proofs('personalWebsiteUrl') if matching(p)
                 and p.get('method') == 'explicit_person_card_value'
                 and p.get('evidence') == f"{person['name']} | personalWebsiteUrl: {website}"]
        if len(names) == len(sites) == 1:
            anchors.append({'name': names[0], 'email': contact, 'personalWebsiteUrl': sites[0]})
    if len(anchors) != 1:
        raise ValueError('Additional source requires one unchanged dated named-card contact observation')
    capture, markup = captured_source(feed_item, cache)
    if any(urlsplit(capture[k]).hostname not in {'math.ucsd.edu', 'www.math.ucsd.edu'}
           or urlsplit(capture[k]).path != '/export/people/faculty'
           or urlsplit(capture[k]).query or urlsplit(capture[k]).fragment for k in ['requestedUrl', 'sourceUrl']):
        raise ValueError('Additional source requires the exact captured Math metadata feed')
    rows = json.loads(markup)
    if not isinstance(rows, list):
        raise ValueError('Math feed must contain its original record array')
    matches = [r for r in rows if isinstance(r, dict)
               and public_email(str(r.get('field_work_email') or '')).lower() == email.lower()]
    if (len(matches) != 1 or matches[0].get('field_work_email') != email
            or matches[0].get('field_website') != website
            or not isinstance(matches[0].get('view_node_1'), str)
            or urljoin(capture['sourceUrl'], matches[0]['view_node_1']) != actual['capture']['requestedUrl']):
        raise ValueError('Math feed must explicitly link the exact extra source and both unchanged personal contacts')
    return {'type': 'published_named_card_contacts_and_literal_math_feed_link',
            'requestedUrl': actual['capture']['requestedUrl'], 'directoryCapture': capture,
            'directoryRow': copy.deepcopy(matches[0]), 'originalNamedCardEvidence': copy.deepcopy(anchors[0]),
            'emailAsListed': email, 'personalWebsiteAsListed': website,
            'scope': 'Additional field-source association only; no primary URI replacement, URI equivalence, identity merge, name, department or current-employment change.'}


def verified_professor_fields(review, queue, cache, professors, person_reviews=(), faculty_review=None):
    people = {p['id']: p for p in professors}
    items = {item['url']: item for item in queue['items'].values()}
    aliases = {}
    for row in person_reviews:
        if not row.get('captureVerified'):
            raise ValueError('Professor field aliases require separately verified person reviews')
        aliases[row['sourceProfessorId']] = row['targetProfessorId']
    owners = {}
    contact_owners = {'email': {}, 'personalWebsiteUrl': {}}
    for person in people.values():
        owners.setdefault(person['officialProfileUrl'], set()).add(aliases.get(person['id'], person['id']))
        for field in contact_owners:
            value = public_email(person.get(field, '')).lower() if field == 'email' else person.get(field, '')
            if value:
                contact_owners[field].setdefault(value, set()).add(aliases.get(person['id'], person['id']))
    verified, seen = [], set()
    for raw in review.get('entries', []):
        row = copy.deepcopy(raw)
        source_id = row.get('sourceProfessorId')
        source = people.get(source_id)
        target_id = aliases.get(source_id, source_id)
        original = row.get('originalSourceProfessorRecord', {})
        retained = row.get('retainedDirectoryPrimaryIdentity')
        if (source is None or source_id in seen or row.get('professorId') != target_id or target_id not in people
                or not row.get('reason') or row.get('originalSourceRecordSha256') != record_sha256(original)
                or source != original
                or not retained and owners.get(source['officialProfileUrl']) != {target_id}):
            raise ValueError('Professor fields require their unchanged original identity, unique source ownership and explicit verified target')
        seen.add(source_id)
        additional = row.get('additionalSourceIdentity')
        lineage = retained_career_field_lineage(row, person_reviews) if source_id != target_id else None
        subject_continuity = False
        if retained and (additional or source_id != target_id and lineage is None
                         or row.get('sourceTemplate') != 'matsci_drupal_labelled_own_fields'):
            raise ValueError('Retained directory primary requires its own scope and separately verified person alias lineage')
        requested = additional.get('requestedUrl') if additional else source['officialProfileUrl']
        item = retained_directory_primary(row, source, faculty_review, items, cache) if retained else items.get(requested)
        if item is None:
            raise ValueError('Professor own-field source is absent from this actual snapshot')
        if additional and owners.get(requested, {target_id}) != {target_id}:
            raise ValueError('An additional own source already owned by another original ID requires separate identity review')
        if row.get('sourceTemplate') in LABELLED_RESEARCH_TEMPLATES:
            previous = row.get('previousCompiledProfessorRecord', {})
            if (additional or retained or source_id != target_id
                    or row.get('previousCompiledProfessorRecordSha256') != record_sha256(previous)
                    or not re.fullmatch(r'[0-9a-f]{64}', row.get('sourceCandidateAtlasSha256', ''))
                    or any(previous.get(k) != source.get(k) for k in ['id', 'name', 'department', 'officialProfileUrl'])):
                raise ValueError('Labelled research requires its original unique own primary and complete preceding identity snapshot')
            selected_subject = reviewed_subject(source['name'], row['sourceTemplate'], row.get('sourceSubjectContinuity'))
            actual = labelled_research(item, cache, selected_subject, row['sourceTemplate'], row.get('reviewedResearchPhrases'))
            if row.get('sourceSubjectContinuity'):
                actual['sourceSubjectContinuity'] = copy.deepcopy(row['sourceSubjectContinuity'])
                subject_continuity = actual['nameAsDisplayed'] == selected_subject
        elif row.get('sourceTemplate') == 'gps_profile_tabs_biography':
            if additional:
                raise ValueError('GPS biography requires the unchanged original own primary, not an additional source')
            actual = gps_own_research_summary(item, cache, source['name'], row.get('fields', {}).get('researchSummary'))
            personal = any('personal_site' in p.get('method', '') for p in
                           evidence_items(source.get('fieldEvidence', {}).get('researchSummary')))
            if personal or row.get('previousSummaryScopeReview'):
                row['previousSummaryScopeReview'] = verified_previous_paper_scope(
                    row.get('previousSummaryScopeReview', {}), source, queue, cache)
        elif row.get('sourceTemplate') == 'rady_profile_tabs_own_fields':
            if additional:
                raise ValueError('Rady fields require the unchanged original own primary, not an additional source')
            actual = rady_own_fields(item, cache, source['name'])
        elif row.get('sourceTemplate') == 'matsci_drupal_labelled_own_fields':
            if additional:
                raise ValueError('Materials fields require the unchanged original own primary, not an additional source')
            actual = matsci_own_fields(item, cache, source['name'])
        else:
            actual = math_own_fields(item, cache, source['name'])
        if additional:
            feed = items.get(additional.get('directoryCapture', {}).get('requestedUrl'))
            if feed is None or additional != additional_math_source_identity(source, actual, feed, cache, contact_owners, target_id):
                raise ValueError('Additional source identity must match its complete recomputed contact and literal-link proof')
        if (not actual['fields'] or row.get('sourceObservation') != actual
                or row.get('fields') != actual['fields'] or row.get('fieldEvidence') != actual['fieldEvidence']
                or set(row['fields']) - {'researchAreas', 'email', 'researchSummary'}
                or not (same_named_subject(people[target_id]['name'], actual['nameAsDisplayed']) or lineage or subject_continuity)):
            raise ValueError('Every professor field must equal its actual named own-source field and dated proof')
        row['captureVerified'] = True
        verified.append(row)
    return verified


def apply_professor_fields(data, reviews):
    people = {alias: p for p in data['professors'] for alias in [p['id']] + p.get('aliasIds', [])}
    for row in reviews:
        person = people.get(row.get('professorId'))
        owner = people.get(row.get('sourceProfessorId'))
        continuity = row.get('sourceSubjectContinuity')
        own_subject_continuity = bool(continuity and person and row.get('sourceTemplate') in LABELLED_RESEARCH_TEMPLATES
            and row.get('sourceProfessorId') == person['id'] == row.get('professorId')
            and person.get('officialProfileUrl') == row.get('originalSourceProfessorRecord', {}).get('officialProfileUrl')
            and row['sourceObservation'].get('sourceSubjectContinuity') == continuity
            and reviewed_subject(person['name'], row['sourceTemplate'], continuity) == row['sourceObservation']['nameAsDisplayed'])
        if (not row.get('captureVerified') or person is None or person is not owner
                or not row.get('fields') or set(row['fields']) - {'researchAreas', 'email', 'researchSummary'}
                or not (same_named_subject(person['name'], row['sourceObservation']['nameAsDisplayed'])
                        or retained_career_field_lineage(row, person.get('personIdentityReviews', [])) or own_subject_continuity)):
            raise ValueError('Only verified own fields may reach the explicitly retained canonical identity')
    for row in reviews:
        person = people[row['professorId']]
        # A later semantic review can retain these exact own badges while
        # adding other explicitly sourced topics. Replaying an already applied
        # older review must not restore its smaller list or create new history.
        superseded = row in person.get('professorFieldReviews', []) and preserves_reviewed_research(person)
        fields = {f:v for f,v in row['fields'].items() if not superseded or f not in {'researchSummary','researchAreas'}}
        evidence = {f:v for f,v in row['fieldEvidence'].items() if f in fields}
        updated = (apply_biography_summary(person, row) if not superseded and row['sourceObservation'].get('sourceTemplate') == 'gps_profile_tabs_biography'
                   else merge_observed_fields(person, {**fields, 'fieldEvidence': evidence}))
        person.clear(); person.update(updated)
        person['professorFieldReviews'] = unique_values(person.get('professorFieldReviews', []) + [row])
        if row.get('sourceTemplate') in LABELLED_RESEARCH_TEMPLATES:
            observation = {'field': 'labelledResearchPreviousCandidate', 'value': copy.deepcopy(row['previousCompiledProfessorRecord']),
                           'recordSha256': row['previousCompiledProfessorRecordSha256'],
                           'candidateAtlasSha256': row['sourceCandidateAtlasSha256'],
                           'sourceProfessorId': row['sourceProfessorId'], 'reason': row['reason']}
            person['previousFieldObservations'] = unique_values(person.get('previousFieldObservations', []) + [observation])
        base = row['sourceObservation']['capture']
        extra = row.get('additionalSourceIdentity', {})
        identity_sources = [extra['directoryCapture']['sourceUrl']] if extra else []
        person['sourceUrls'] = unique_values(person.get('sourceUrls', []) + [base['requestedUrl'], base['sourceUrl']] + identity_sources)
