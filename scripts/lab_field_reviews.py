"""Apply captured lab leadership/contact claims without guessing identity.

An own-site role is distinct from a campus profile's linked, scoped directorship.
Exact resource origins and entity paths protect contacts on shared web hosts.
"""
from __future__ import annotations

import copy
import hashlib
import re
import urllib.parse
from pathlib import Path

from atlas_urls import url_key, valid_url
from lab_entities import LabIndex, named_lab_key, reviewed_resource_mismatch
from lab_resource_reviews import record_sha256
from person_identity_reviews import verify_person_proofs
from refresh_labs import DOM, every_node, links, normalized, evidence_items, unique_values, merge_observed_fields, person_matches, has_value
from lab_professor_own_chain import verify_own_professor_chain, KIND as OWN_PERSON_CHAIN_KIND


def has_named_pi(name, proofs):
    person = re.escape(normalized(name))
    pattern = (rf'\b(?:pi|principal investigator|led by|director)\s+(?:faculty profile\s+)?(?:(?:professor|prof|dr)\s+)*{person}\b'
               rf'|\b{person}\s+(?:(?:ph d|phd|m d|md)\s+)*(?:is\s+)?(?:the\s+)?(?:pi|principal investigator|director)\b')
    return any(re.search(pattern, normalized(p.get('evidence', ''))) for p in proofs)


def own_lab_source(lab, source, queue):
    """Use an actually captured primary resource/final origin, never www folds."""
    if reviewed_resource_mismatch(lab, lab['labWebsiteUrl']):
        return False
    destination = urllib.parse.urlsplit(source)
    for item in queue['items'].values():
        meta = item.get('fetch', {})
        if meta.get('status') != 'ok' or url_key(lab['labWebsiteUrl']) not in {url_key(item['url']), url_key(meta.get('finalUrl', ''))}:
            continue
        root = urllib.parse.urlsplit(meta.get('finalUrl', item['url']))
        prefix = root.path.rstrip('/')
        if prefix.rsplit('/', 1)[-1] in {'home', 'home_1', 'index'} or re.search(r'\.(?:html?|php)$', prefix):
            prefix = prefix.rsplit('/', 1)[0]
        if ((root.scheme.lower(), root.netloc.lower()) == (destination.scheme.lower(), destination.netloc.lower())
                and (not root.query or root.query == destination.query)
                and (not prefix or destination.path.rstrip('/') == prefix or destination.path.startswith(prefix + '/'))):
            return True
    return False


def named_subject(proof, name, cache):
    if proof.get('evidenceType') == 'json_record':
        record = proof.get('sourceRecord', {})
        return isinstance(record, dict) and normalized(' '.join(str(record.get(k, '')) for k in ['first_name', 'last_name'])) == normalized(name)
    path = Path(cache) / 'responses' / (hashlib.sha256(proof['requestedUrl'].encode()).hexdigest() + '.html')
    return any(person_matches(name, node.text()) for node in every_node(DOM(path.read_text()).root)
               if node.tag in {'title', 'h1', 'h2', 'h3'})


def verified_recruiting_fields(row, lab, queue):
    fields = row['fields']
    if not {'recruitingStatus', 'recruitingEvidence'} & fields.keys():
        return
    statement = fields.get('recruitingEvidence')
    status = fields.get('recruitingStatus')
    proofs = evidence_items(row.get('fieldEvidence', {}).get('recruitingStatus'))
    if (status not in {'Recruiting', 'Not recruiting'} or not isinstance(statement, dict)
            or set(statement) != {'text', 'url'} or len(proofs) != 1
            or evidence_items(row.get('fieldEvidence', {}).get('recruitingEvidence')) != proofs):
        raise ValueError('Lab recruiting requires its paired status, exact statement and captured proof')
    proof = proofs[0]
    if (proof.get('method') != 'reviewed_explicit_own_lab_recruiting_statement'
            or proof.get('evidenceType') != 'main_text_quote'
            or not isinstance(statement['text'], str) or not 1 <= len(statement['text']) <= 2000
            or statement['text'] != proof.get('evidence') or statement['url'] != proof.get('sourceUrl')
            or not own_lab_source(lab, statement['url'], queue)):
        raise ValueError('Lab recruiting requires an exact statement on its observed own resource')
    if lab.get('websiteSharing'):
        raise ValueError('Shared-resource recruiting requires a separately scoped named-lab review')
    text = normalized(statement['text'])
    negative = bool(re.search(r'\b(?:not (?:currently )?(?:recruiting|hiring|accepting (?:applications|students))|no (?:current |immediate |open )?(?:openings|positions)|positions (?:are )?filled)\b', text))
    positive = bool(re.search(r'\b(?:recruiting|hiring|seeking|accepting applications|open positions|looking for)\b', text))
    if not (negative if status == 'Not recruiting' else positive and not negative):
        raise ValueError('Lab recruiting status requires the explicitly corresponding published statement')


def scoped_directorship(row, lab, queue, cache, members):
    scope = row.get('piScope', {})
    if scope.get('kind') != 'named_profile_link_to_two_labs':
        return False
    sharing = lab.get('websiteSharing', {})
    if (sharing.get('kind') != 'distinct_named_labs' or len(sharing.get('memberLabIds', [])) != 2
            or sorted(scope.get('directedLabIds', [])) != sorted(sharing['memberLabIds'])):
        raise ValueError('Scoped directorship requires the complete reviewed two-lab group')
    subject, clause, scope_link, lab_link = [scope[key] for key in ['subjectEvidence', 'clauseEvidence', 'scopeLinkEvidence', 'namedLabLinkEvidence']]
    if (any(p not in row['evidence'] for p in [subject, clause, scope_link, lab_link])
            or len({p['requestedUrl'] for p in [subject, clause, scope_link, lab_link]}) != 1
            or not named_subject(subject, row['fields']['principalInvestigator'], cache)):
        raise ValueError('Scoped leadership requires one named individual profile and its actual links')
    host = urllib.parse.urlsplit(subject['sourceUrl']).hostname or ''
    if not (host == 'ucsd.edu' or host.endswith('.ucsd.edu')):
        raise ValueError('Linked lab directorship requires an official campus person profile')
    if not re.search(r'\b(?:he|she) directs (?:two|2) distinct research laboratories\b', normalized(clause['evidence'])):
        raise ValueError('A generic profile/lab link does not establish directorship')
    if (scope_link.get('evidenceType') != 'named_link' or lab_link.get('evidenceType') != 'named_link'
            or lab_link.get('linkText') != lab['labName']
            or any(url_key(p.get('linkUrl', '')) != url_key(lab['labWebsiteUrl']) for p in [scope_link, lab_link])):
        raise ValueError('Leadership must link the named lab and the specific reviewed shared resource')
    path = Path(cache) / 'responses' / (hashlib.sha256(subject['requestedUrl'].encode()).hexdigest() + '.html')
    dom = DOM(path.read_text()).main()
    actual_links = {(label, url_key(uri)) for _, label, uri in links(dom, subject['sourceUrl'])}
    if not all((member['labName'], url_key(lab['labWebsiteUrl'])) in actual_links for member in members):
        raise ValueError('The profile must separately name and link every directed lab')
    own_texts = []
    for proof in row['identityEvidence']:
        source_path = Path(cache) / 'responses' / (hashlib.sha256(proof['requestedUrl'].encode()).hexdigest() + '.html')
        own_texts.append(normalized(DOM(source_path.read_text()).main().text()))
    if not all(any(re.search(r'\b' + re.escape(normalized(member['labName'])) + r'\b', text) for text in own_texts) for member in members):
        raise ValueError('The linked own resource must actually identify every distinct lab')
    if not any(clause['evidence'] in node.text() and person_matches(row['fields']['principalInvestigator'], node.text())
               and any(label == scope_link['linkText'] and url_key(uri) == url_key(scope_link['linkUrl'])
               for _, label, uri in links(node, subject['sourceUrl'])) for node in dom.walk() if node.tag == 'p'):
        raise ValueError('The lab link must occur inside the captured leadership clause')
    return True


def verified_lab_fields(review, queue, cache, labs, professors):
    index = LabIndex(labs); index.validate_sharing()
    people = {pid: p for p in professors for pid in [p['id']] + p.get('aliasIds', [])}
    rows, seen = copy.deepcopy(review.get('entries', [])), set()
    allowed = {'principalInvestigator', 'principalInvestigatorProfileUrl', 'contactEmail', 'additionalContactEmails',
               'recruitingStatus', 'recruitingEvidence'}
    for row in rows:
        lab = index.by_id.get(row.get('labId'))
        original = row.get('originalLabRecord', {})
        fields, proofs = row.get('fields', {}), row.get('evidence', [])
        if (lab is None or row['labId'] in seen or not row.get('reason') or not fields or set(fields) - allowed
                or row.get('originalLabRecordSha256') != record_sha256(original)
                or any(original.get(k) != lab.get(k) for k in ['id', 'labName', 'labWebsiteUrl'])
                or lab.get('destinationIdentityAssessment', {}).get('identityStatus') == 'mismatch'):
            raise ValueError('Lab field review requires an unchanged explicit identity, original record and reason')
        seen.add(row['labId']); verify_person_proofs(proofs, queue, cache, row['labId'])
        identity = row.get('identityEvidence', [])
        names = [lab['labName']] + lab.get('aliasNames', [])
        tokens = [set(named_lab_key(name).split()) - {'lab', 'research', 'group', 'website', 'at', 'of', 'and'} for name in names]
        if (not identity or any(p not in proofs for p in identity)
                or not any(any(t and t <= set(named_lab_key(p['evidence']).split()) for t in tokens)
                           and own_lab_source(lab, p['sourceUrl'], queue) for p in identity)):
            raise ValueError('Own resource evidence must identify the specifically named lab')
        for field in fields:
            evidence = evidence_items(row.get('fieldEvidence', {}).get(field))
            if not evidence or any(p not in proofs for p in evidence):
                raise ValueError('Every lab field requires its own verified captured proof')
        verified_recruiting_fields(row, lab, queue)
        if 'principalInvestigator' in fields:
            pi_proofs = evidence_items(row['fieldEvidence']['principalInvestigator'])
            direct = (not lab.get('websiteSharing') and has_named_pi(fields['principalInvestigator'], pi_proofs)
                      and all(own_lab_source(lab, p['sourceUrl'], queue) for p in pi_proofs))
            if not direct and not scoped_directorship(row, lab, queue, cache, index.candidates(lab['labWebsiteUrl'])):
                raise ValueError('Lab PI requires explicit own-site leadership or a named, linked profile scope')
        for field in ['contactEmail', 'additionalContactEmails']:
            if field not in fields:
                continue
            if field == 'additionalContactEmails' and not isinstance(fields[field], list):
                raise ValueError('Additional contacts must be separate canonical email values')
            values = fields[field] if isinstance(fields[field], list) else [fields[field]]
            for value in values:
                if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', value):
                    raise ValueError('Lab contacts must be individually canonical public emails')
                if not any(value in p['evidence'] and own_lab_source(lab, p['sourceUrl'], queue) for p in row['fieldEvidence'][field]):
                    raise ValueError('Lab contact requires an exact own-lab source, without scheme/www/path assumptions')
        if row.get('professorId') or 'principalInvestigatorProfileUrl' in fields:
            person = people.get(row.get('professorId')); name = fields.get('principalInvestigator')
            person_proofs = row.get('personEvidence', [])
            if person is None or not person_proofs or any(p not in proofs for p in person_proofs):
                raise ValueError('Lab leadership links require a specifically matched existing professor')
            own_chain = verify_own_professor_chain(row, person, lab, list({p['id']: p for p in people.values()}.values()), queue, cache)
            if not own_chain and (normalized(person['name']) != normalized(name)
                                  or not all(named_subject(p, name, cache) for p in person_proofs)):
                raise ValueError('Lab leadership links require a specifically matched existing professor')
            if any(p.get('evidenceType') == 'json_record' for p in person_proofs):
                basis = row.get('personIdentityBasis', {})
                original_person = row.get('originalProfessorRecord', {})
                email = basis.get('email')
                owners = {p['id'] for p in people.values() if email and p.get('email') == email}
                if (basis.get('type') != 'unique_named_campus_json_email' or owners != {person['id']}
                        or not email or email != person.get('email')
                        or record_sha256(original_person) != row.get('originalProfessorRecordSha256')
                        or any(original_person.get(k) != person.get(k) for k in ['id', 'name', 'email', 'officialProfileUrl'])
                        or any(p.get('evidenceType') != 'json_record'
                               or p['sourceRecord'].get('email') != email
                               or not ((urllib.parse.urlsplit(p['sourceUrl']).hostname or '').lower() == 'ucsd.edu'
                                       or (urllib.parse.urlsplit(p['sourceUrl']).hostname or '').lower().endswith('.ucsd.edu'))
                               or not {p['requestedUrl'], p['sourceUrl']} & set(person.get('sourceUrls', []))
                               for p in person_proofs)):
                    raise ValueError('Structured person evidence requires an exact campus record, unique published email and preserved professor identity')
            if 'principalInvestigatorProfileUrl' in fields and not any(valid_url(fields['principalInvestigatorProfileUrl']) and url_key(fields['principalInvestigatorProfileUrl']) in {url_key(p['requestedUrl']), url_key(p['sourceUrl'])} for p in person_proofs):
                raise ValueError('PI profile URL must be the actual captured named person resource')
        if row.get('linkProfessorLab') and (row.get('personIdentityBasis', {}).get('type') != OWN_PERSON_CHAIN_KIND or not row.get('professorId')):
            raise ValueError('Professor lab association requires the verified original own-person identity chain')
        row['captureVerified'] = True
    return rows


def apply_lab_fields(data, reviews):
    labs = LabIndex(data['labs'])
    people = {pid: p for p in data['professors'] for pid in [p['id']] + p.get('aliasIds', [])}
    for row in reviews:
        if not row.get('captureVerified') or row['labId'] not in labs.by_id or not row.get('evidence'):
            raise ValueError('Lab fields require a verified identity-scoped review')
        if row.get('professorId') and row['professorId'] not in people:
            raise ValueError('Reviewed lab leadership references a missing professor')
    for row in reviews:
        lab = labs.by_id[row['labId']]
        updated = merge_observed_fields(lab, {**row['fields'], 'fieldEvidence': row['fieldEvidence']})
        lab.clear(); lab.update(updated)
        lab['labFieldReviews'] = unique_values(lab.get('labFieldReviews', []) + [row])
        lab['sourceUrls'] = unique_values(lab.get('sourceUrls', []) + [p['sourceUrl'] for p in row['evidence']])
        if not row.get('professorId'):
            continue
        person = people[row['professorId']]
        evidence = unique_values(row['fieldEvidence']['principalInvestigator'] + row['personEvidence'])
        if row.get('linkProfessorLab'):
            evidence = unique_values(evidence + row['identityEvidence'] + [p for p in row['evidence'] if p.get('evidenceType') == 'named_link'])
        lab['professorIds'] = unique_values(lab.get('professorIds', []) + [person['id']])
        lab['relatedProfessorNames'] = unique_values(lab.get('relatedProfessorNames', []) + [person['name']])
        for field in ['professorIds', 'relatedProfessorNames']:
            lab.setdefault('fieldEvidence', {})[field] = unique_values(evidence_items(lab.get('fieldEvidence', {}).get(field)) + evidence)
        affiliation = {'labId': lab['id'], 'labName': lab['labName'], 'url': lab['labWebsiteUrl'],
                       'relationship': 'principal_investigator', 'fieldEvidence': evidence}
        old = [a for a in person.get('labAffiliations', []) if a.get('labId') in [lab['id']] + lab.get('aliasIds', [])]
        if old != [affiliation]:
            if old:
                person['previousFieldObservations'] = unique_values(person.get('previousFieldObservations', []) + [{'field': 'labAffiliations', 'value': old, 'reason': row['reason']}])
            person['labAffiliations'] = [a for a in person.get('labAffiliations', []) if a not in old] + [affiliation]
        person['sourceUrls'] = unique_values(person.get('sourceUrls', []) + [p['sourceUrl'] for p in evidence])
        if row.get('linkProfessorLab'):
            person['professorLabIdentityReviews'] = unique_values(person.get('professorLabIdentityReviews', []) + [row])
            if not has_value(person.get('labAffiliation')) and not has_value(person.get('labAffiliationUrl')):
                proof = unique_values(row['identityEvidence'] + evidence)
                updated = merge_observed_fields(person, {'labAffiliation': lab['labName'], 'labAffiliationUrl': lab['labWebsiteUrl'],
                    'fieldEvidence': {'labAffiliation': proof, 'labAffiliationUrl': proof}})
                person.clear(); person.update(updated)
