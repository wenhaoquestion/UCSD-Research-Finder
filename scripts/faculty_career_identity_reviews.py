"""Review a published leading initial through two independently named careers.

This scope requires literal own biographies, personal contacts and two named
roster chains. Research topics, surname similarity and shared lab sites cannot
substitute for the complete personal career or establish a lab/PI edge.
"""
import copy
import re
from urllib.parse import urljoin

from faculty_profile_bindings import captured_source, jacobs_academic_qualification
from lab_resource_reviews import record_sha256
from matsci_own_fields import classes, matsci_own_fields, retained_directory_primary
from refresh_labs import DOM, every_node, evidence_items, unique_values

KIND = 'named_own_career_and_contact_with_published_leading_initial'


def one(nodes, label):
    nodes = list(nodes)
    if len(nodes) != 1:
        raise ValueError('Career identity requires one scoped ' + label)
    return nodes[0]


def proof(base, kind, text, **extra):
    return {**base, 'status': 'verified', 'method': KIND,
            'evidenceType': kind, 'evidence': text, **extra}


def captured_document(item, cache):
    base, html = captured_source(item, cache)
    visited = base['requestedUrl']
    for hop in item['fetch'].get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Career identity requires the actual continuous redirect chain')
        visited = hop.get('to')
    if visited != base['sourceUrl'] or item['fetch'].get('httpStatus') != 200:
        raise ValueError('Career identity requires a successful exact captured resource')
    dom = DOM(html)
    title = one((n for n in every_node(dom.root) if n.tag == 'title'), 'document title').text()
    return base, dom, title


def career_binding(source, target, source_fields, request, people, queue, cache, faculty):
    if (source['id'] == target['id'] or len(source['name'].split()) < 2
            or not re.fullmatch(r'[A-Z]\. ' + re.escape(source['name']), target['name'])
            or source['department'] != 'Electrical and Computer Engineering'
            or target['department'] != source['department']):
        raise ValueError('Career scope retains an exact published leading initial and unchanged ECE identities')
    items = {i['url']: i for i in queue['items'].values()}
    if (source_fields.get('sourceProfessorId') != source['id']
            or source_fields.get('professorId') != source['id']
            or source_fields.get('originalSourceProfessorRecord') != source
            or source_fields.get('originalSourceRecordSha256') != record_sha256(source)
            or source_fields.get('sourceTemplate') != 'matsci_drupal_labelled_own_fields'):
        raise ValueError('Career scope requires the complete preceding accepted own-field identity')
    own_item = retained_directory_primary(source_fields, source, faculty, items, cache)
    actual = matsci_own_fields(own_item, cache, source['name'])
    if any(source_fields.get(k) != actual.get(k) for k in ['fields', 'fieldEvidence']):
        raise ValueError('Accepted Materials fields must still equal their captured source')
    if source_fields.get('sourceObservation') != actual:
        raise ValueError('Accepted own-field observation changed')
    try:
        target_item = items[request['targetOwnRequestedUri']]
        roster_item = items[request['targetRosterRequestedUri']]
        source_roster_item = items[source_fields['publishedOriginalPrimaryEvidence']['requestedUrl']]
    except KeyError as error:
        raise ValueError('Career identity requires both actual named roster chains') from error
    sb, sd, st = captured_document(own_item, cache)
    tb, td, tt = captured_document(target_item, cache)
    rb, rd, rt = captured_document(roster_item, cache)
    mb, md, mt = captured_document(source_roster_item, cache)
    if (tb['sourceUrl'] != target['officialProfileUrl']
            or rb['requestedUrl'] != 'https://ece.ucsd.edu/people/faculty'
            or rb['sourceUrl'] != rb['requestedUrl']
            or len({sb['requestedUrl'], tb['requestedUrl'], rb['requestedUrl'], mb['requestedUrl']}) != 4):
        raise ValueError('Career identity preserves the original individual target and independent departmental roster')
    if {p['id'] for p in people + (faculty or {}).get('professors', [])
            if p.get('officialProfileUrl') == target['officialProfileUrl']} != {target['id']}:
        raise ValueError('The retained original target primary must have one scientist owner')
    qualification = jacobs_academic_qualification(target_item, cache, target['name'])
    if qualification is None or qualification['unitAsListed'] != 'ECE':
        raise ValueError('The original Jacobs own subject requires its primary ECE academic role')
    article = one((n for n in every_node(sd.main()) if n.tag == 'article'
                   and 'faculty-listing' in classes(n) and n.attrs.get('role') == 'article'
                   and n.attrs.get('about') == actual['articleAbout']), 'Materials own article')
    bio = one((n for n in every_node(article) if n.tag == 'div'
               and {'field--name-body', 'field__item'} <= classes(n)), 'Materials own Bio')
    department = one((n for n in every_node(article) if 'field--name-field-department' in classes(n)), 'own department')
    email = one((n for n in every_node(article) if 'field--name-field-faculty-email' in classes(n)), 'own email').text()
    subject = one((n for n in every_node(td.main()) if n.tag == 'h3'
                   and 'faculty_profile_name' in classes(n)), 'Jacobs own subject')
    if subject.text() != target['name'] or department.text() != source['department']:
        raise ValueError('Own subject and literal department must retain the reviewed identity')
    blocks = [n for n in subject.parent.children if hasattr(n, 'tag') and n.tag == 'div' and 'mb-5' in classes(n)]
    bio_blocks = []
    for block in blocks:
        children = [n for n in block.children if hasattr(n, 'tag')]
        if (len(children) == 2 and children[0].tag == 'p' and children[0].text() == 'Capsule Bio:'
                and 'font-weight-bold' in classes(children[0]) and children[1].tag == 'p'):
            bio_blocks.append(children[1])
    other_bio = one(bio_blocks, 'direct own Capsule Bio')
    career = bio.text()
    prefix = target['name'][:2] + ' ' + source['name'].split()[-1] + ' is a '
    if (career != other_bio.text() or len(career) < 1500 or len(career.split()) < 200
            or not career.startswith(prefix) or 'Professor' not in career[:180]
            or 'Ph.D' not in career or 'M.Sc' not in career
            or len(set(re.findall(r'\b(?:19|20)\d{2}\b', career))) < 3):
        raise ValueError('Identity requires the same complete distinctive personal career, degrees and dated milestones')
    row = subject.parent.parent
    if 'row' not in classes(row) or 'col-9' not in classes(subject.parent):
        raise ValueError('Jacobs contact must be in the same single-person row')
    contact = one((n for n in row.children if hasattr(n, 'tag') and 'col-3' in classes(n)), 'Jacobs own contact column')
    contact_email = one((n for n in every_node(contact) if n.tag == 'p' and n.text().startswith('Email:')), 'Jacobs own Email')
    if (not re.fullmatch(r'[A-Za-z0-9._%+-]+@ucsd\.edu', email)
            or contact_email.text() != 'Email: ' + email or target.get('email') != email
            or source.get('email') not in {'Not found', email}):
        raise ValueError('Both own personal contact fields must share the original target professional email')
    for person in people + (faculty or {}).get('professors', []):
        if person['id'] not in {source['id'], target['id']} and str(person.get('email', '')).lower() == email.lower():
            raise ValueError('A third original contact owner prevents career identity consolidation')
    for pid, patch in (faculty or {}).get('byProfessorId', {}).items():
        if pid not in {source['id'], target['id']} and patch.get('officialProfileUrl') == target['officialProfileUrl']:
            raise ValueError('A third reviewed individual primary owner prevents consolidation')
        if pid not in {source['id'], target['id']} and str(patch.get('email', '')).lower() == email.lower():
            raise ValueError('A third reviewed contact owner prevents career identity consolidation')
    cards = []
    for card in every_node(rd.main()):
        if card.tag != 'div' or 'faculty-member' not in classes(card):
            continue
        headings = [n for n in every_node(card) if n.tag == 'h2']
        if len(headings) == 1 and headings[0].text() == target['name']:
            anchor = one((n for n in every_node(headings[0]) if n.tag == 'a' and n.attrs.get('href')), 'named ECE heading link')
            mails = [n for n in every_node(card) if n.tag == 'a' and n.attrs.get('href', '').startswith('mailto:')]
            role = one((n for n in every_node(card) if n.tag == 'p'), 'ECE card role/contact')
            if (urljoin(rb['sourceUrl'], anchor.attrs['href']) != tb['requestedUrl']
                    or anchor.text() != target['name'] or len(mails) != 1
                    or mails[0].attrs['href'] != 'mailto:' + email or mails[0].text() != email
                    or not re.match(r'^(?:Distinguished )?Professor ', role.text())):
                raise ValueError('The named ECE faculty card must literally link its own request and contact')
            cards.append((card, anchor))
    card, anchor = one(cards, 'named ECE faculty card')
    source_cards = [n for n in every_node(md.main()) if n.tag == 'div' and 'faculty-listing' in classes(n)
                    and any(a.tag == 'a' and a.text() == source['name']
                            and urljoin(mb['sourceUrl'], a.attrs.get('href', '')) == sb['sourceUrl'] for a in every_node(n))]
    source_card = one(source_cards, 'named Materials faculty card')
    if source_card.text() != source['name'] + ' Professor ' + source['department']:
        raise ValueError('The Materials roster must explicitly name the same subject, academic role and department')
    evidence = [source_fields['publishedOriginalPrimaryEvidence'],
                proof(mb, 'main_text_quote', source_card.text()),
                proof(sb, 'document_title', st),
                proof(sb, 'document_heading', source['name'], headingTag='h1'),
                proof(sb, 'main_text_quote', department.text()),
                proof(sb, 'main_text_quote', career), proof(sb, 'main_text_quote', email),
                proof(rb, 'document_title', rt), proof(rb, 'main_text_quote', card.text()),
                proof(rb, 'named_link', target['name'] + ' -> ' + tb['requestedUrl'],
                      linkText=target['name'], linkUrl=tb['requestedUrl'], rawHref=anchor.attrs['href']),
                proof(tb, 'document_heading', target['name'], headingTag='h3'),
                proof(tb, 'main_text_quote', qualification['roleAsListed']),
                proof(tb, 'main_text_quote', career), proof(tb, 'main_text_quote', contact_email.text())]
    return {'kind': KIND, 'sourceOwnCapture': sb, 'targetOwnCapture': tb,
            'sourceName': source['name'], 'targetName': target['name'], 'email': email,
            'careerAsPublished': career, 'careerSha256': record_sha256(career),
            'targetRoleAsPublished': qualification['roleAsListed'],
            'targetRosterCard': card.text(), 'sourceRosterCard': source_card.text(),
            'evidence': evidence,
            'scope': 'Two independent own subjects publish an identical complete personal career and professional email; named Materials and ECE roster chains independently retain their own resources. Keep the published leading initial, original Jacobs primary and stable target ID. No expanded initial, legal-name, HR-currentness or lab/PI inference.'}


def verify_career_review(row, source, target, people, queue, cache, faculty):
    binding = career_binding(source, target, row.get('sourceOwnFieldReview', {}),
                             row.get('careerIdentityRequest', {}), people, queue, cache, faculty)
    p = binding['evidence']
    if (row.get('careerIdentityBinding') != binding or row.get('evidence') != p
            or row.get('identityBasis') != {'type': KIND, 'value': binding['careerSha256']}
            or row.get('fields') != {'name': target['name'], 'department': target['department'],
                                     'officialProfileUrl': target['officialProfileUrl']}
            or row.get('fieldEvidence') != {'name': [p[10], p[9]], 'department': [p[4], p[8]],
                                           'officialProfileUrl': [p[10], p[9]]}
            or row.get('departmentEvidence') != [{'department': target['department'],
                'status': 'named_department_rosters_and_own_profile', 'fieldEvidence': [p[1], p[4], p[8]]}]
            or row.get('unsupportedDepartmentValues')):
        raise ValueError('Career decision must equal its complete recomputed subject-scoped binding')
    snapshots = row.get('previousCandidateObservations', [])
    if len(snapshots) != 2:
        raise ValueError('Retain both complete preceding compiled identities')
    for original in [source, target]:
        snapshot = one((s for s in snapshots if s.get('record', {}).get('id') == original['id']), 'preceding identity snapshot')
        previous = snapshot['record']
        expected_uri = binding['sourceOwnCapture']['sourceUrl'] if original is source else target['officialProfileUrl']
        if (snapshot.get('recordSha256') != record_sha256(previous)
                or not re.fullmatch(r'[0-9a-f]{64}', snapshot.get('candidateAtlasSha256', ''))
                or any(previous.get(k) != original.get(k) for k in ['id', 'name', 'department'])
                or previous.get('officialProfileUrl') != expected_uri or previous.get('email') != binding['email']):
            raise ValueError('Preceding complete identities must preserve the reviewed own resources and contact')


def retained_career_field_lineage(row, reviews):
    """A name variant reaches own fields only through this verified merger."""
    matches = [r for r in reviews if r.get('captureVerified') is True
               and r.get('identityBasis', {}).get('type') == KIND
               and r.get('sourceProfessorId') == row.get('sourceProfessorId')
               and r.get('targetProfessorId') == row.get('professorId')]
    if len(matches) != 1:
        return None
    review = matches[0]
    previous = review['sourceOwnFieldReview']
    expected = copy.deepcopy(previous)
    expected['professorId'] = review['targetProfessorId']
    expected['reviewedPersonAliasLineage'] = {'kind': KIND, 'identityBasis': review['identityBasis'],
        'sourceProfessorId': review['sourceProfessorId'], 'targetProfessorId': review['targetProfessorId'],
        'previousOwnFieldReviewSha256': record_sha256(previous)}
    observed = {k: v for k, v in row.items() if k != 'captureVerified'}
    return review if observed == expected else None


def retain_career_observations(target, row):
    # Resource choice is an explicit identity decision, not a claim that the
    # older Jacobs capture is newer than the Materials observation. Replaying
    # an alias directory patch must not displace the retained original primary.
    for field, value in row['fields'].items():
        if target.get(field) != value:
            observation = {'field': field, 'value': copy.deepcopy(target.get(field)),
                           'fieldEvidence': copy.deepcopy(evidence_items(target.get('fieldEvidence', {}).get(field))),
                           'reason': 'Retained original individual identity selected by the verified career review; other published resource/name remains historical.'}
            target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [observation])
            target[field] = copy.deepcopy(value)
        target.setdefault('fieldEvidence', {})[field] = copy.deepcopy(row['fieldEvidence'][field])
    target['aliasNames'] = [n for n in unique_values(target.get('aliasNames', []) + [row['originalSourceRecord']['name']])
                            if n != target['name']]
    target['fieldEvidence']['aliasNames'] = unique_values(evidence_items(target['fieldEvidence'].get('aliasNames'))
                                                         + [row['evidence'][3]])
    for snapshot in row['previousCandidateObservations']:
        observation = {'field': 'careerIdentityPreviousCandidate', 'value': copy.deepcopy(snapshot['record']),
                       'recordSha256': snapshot['recordSha256'], 'candidateAtlasSha256': snapshot['candidateAtlasSha256'],
                       'sourceProfessorId': snapshot['record']['id'], 'reason': row['reason']}
        target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [observation])
