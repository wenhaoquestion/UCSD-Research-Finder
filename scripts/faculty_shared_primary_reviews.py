"""Resolve two original names through their shared named individual primary.

Independent Bioengineering affiliate cards and a departmental faculty table
must literally link the same original Profiles URI. Its own subject, canonical
and personal RDF metadata, and academic appointment complete the identity
chain. Directory affiliation is separate from the own primary appointment.
"""
import copy
import re
from urllib.parse import urljoin, urlsplit

from collect_ucsd_coverage import profiles_appointment
from faculty_profile_bindings import captured_source, profile_metadata
from faculty_profile_chain_reviews import compatible_full_names, named_faculty_table_link
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import identity_name
from refresh_labs import DOM, every_node, unique_values, evidence_items

KIND = 'shared_original_primary_in_named_department_rosters'


def shared_primary_binding(source, target, request, people, queue, cache):
    uri = source['officialProfileUrl']
    parsed = urlsplit(uri)
    if (uri != target['officialProfileUrl'] or source['id'] == target['id']
            or parsed.scheme != 'https' or parsed.hostname != 'profiles.ucsd.edu'
            or not re.fullmatch(r'/[A-Za-z][A-Za-z0-9._-]*', parsed.path)
            or parsed.query or parsed.fragment
            or not compatible_full_names(source['name'], target['name'])
            or {p['id'] for p in people if p.get('officialProfileUrl') == uri}
               != {source['id'], target['id']}):
        raise ValueError('Shared-primary review requires exactly two compatible original owners of one individual URI')
    items = {i['url']: i for i in queue['items'].values()}
    try:
        own_item = items[uri]
        affiliate_item = items[request['sourceRosterRequestedUri']]
        table_item = items[request['targetRosterRequestedUri']]
    except KeyError as error:
        raise ValueError('Shared-primary review requires all three actual source captures') from error
    own, markup = profile_metadata(own_item, cache)
    assessment, appointment = profiles_appointment(own_item['fetch'], markup)
    if (own['sourceUrl'] != uri or own['canonicalUri'] != uri
            or identity_name(own['nameAsDisplayed']) != identity_name(source['name'])
            or appointment is None or assessment.get('mappedDepartment') != target['department']):
        raise ValueError('The shared own subject and appointment must identify the source name and target department')
    base, html = captured_source(affiliate_item, cache)
    if (base['requestedUrl'] not in source.get('sourceUrls', [])
            or source['department'] != 'Bioengineering'
            or any(urlsplit(base[k]).hostname != 'be.ucsd.edu'
                   or urlsplit(base[k]).path.rstrip('/') != '/faculty'
                   or urlsplit(base[k]).query for k in ['requestedUrl', 'sourceUrl'])):
        raise ValueError('The affiliate source must remain its exact retained Bioengineering faculty directory')
    dom = DOM(html)
    titles = [n.text() for n in every_node(dom.root) if n.tag == 'title']
    if len(titles) != 1 or not titles[0].endswith(' Department of Bioengineering'):
        raise ValueError('The affiliate document must declare its department independently')
    cards = []
    for card in every_node(dom.main()):
        if card.tag != 'div' or 'faculty-information' not in card.attrs.get('class', '').split():
            continue
        headings = [n for n in every_node(card) if n.tag == 'h3']
        # The public template contains empty nested h6 tags. They carry no
        # role claim; a second nonempty heading still makes scope ambiguous.
        roles = [n for n in every_node(card) if n.tag == 'h6' and n.text()]
        if len(headings) != 1 or len(roles) != 1:
            continue
        anchors = [n for n in every_node(headings[0]) if n.tag == 'a' and n.attrs.get('href')]
        if (len(anchors) != 1 or identity_name(headings[0].text()) != identity_name(source['name'])
                or anchors[0].text() != headings[0].text()
                or urljoin(base['sourceUrl'], anchors[0].attrs['href']) != uri
                or not re.match(r'^Affiliate(?:\s|$)', roles[0].text())):
            continue
        cards.append({**base, 'documentTitle': titles[0], 'nameAsDisplayed': headings[0].text(),
                      'rawHref': anchors[0].attrs['href'], 'linkUrl': uri,
                      'roleAsListed': 'Affiliate', 'cardText': card.text()})
    if len(cards) != 1:
        raise ValueError('One named affiliate card must literally link the shared primary in its own name heading')
    roster = named_faculty_table_link(target, table_item, cache)
    if len({base['requestedUrl'], roster['requestedUrl'], own['requestedUrl']}) != 3:
        raise ValueError('The two original names require independently captured directories and their own primary')
    return {'kind': KIND, 'sourceNamedAffiliateCard': cards[0], 'targetNamedFacultyRow': roster,
            'ownProfile': own, 'ownAppointmentAsListed': assessment,
            'publishedNames': [source['name'], target['name']],
            'scope': 'Two original named directory records literally link the same named original individual primary. Keep the full target name, own primary appointment and separately labelled affiliate directory observation; no legal-name or current-HR claim.'}


def verify_shared_primary_review(row, source, target, people, queue, cache):
    binding = shared_primary_binding(source, target, row.get('sharedPrimaryRequest', {}), people, queue, cache)
    if (row.get('sharedPrimaryBinding') != binding
            or row.get('identityBasis') != {'type': KIND, 'value': binding['ownProfile']['rdfAlternateUri']}
            or row.get('fields') != {'name': target['name'], 'department': target['department'],
                                     'officialProfileUrl': target['officialProfileUrl']}):
        raise ValueError('The shared-primary decision must equal its actual chain and preserve target identity fields')
    keys = ['sourceCardEvidence', 'sourceTitleEvidence', 'sourceLinkEvidence', 'targetLinkEvidence',
            'targetDepartmentEvidence', 'ownNameEvidence', 'ownCanonicalEvidence', 'ownRdfEvidence',
            'ownAppointmentEvidence']
    proofs = row['evidence']
    if any(row.get(k) not in proofs for k in keys):
        raise ValueError('Shared-primary review requires every separately scoped captured proof')
    card, title, link, table, dept, name, canonical, rdf, appointment = [row[k] for k in keys]
    bcard, brow, own = [binding[k] for k in ['sourceNamedAffiliateCard', 'targetNamedFacultyRow', 'ownProfile']]
    expected = [(card, bcard['requestedUrl'], 'main_text_quote', bcard['cardText']),
                (title, bcard['requestedUrl'], 'document_title', bcard['documentTitle']),
                (link, bcard['requestedUrl'], 'named_link', bcard['nameAsDisplayed']+' -> '+own['canonicalUri']),
                (table, brow['requestedUrl'], 'named_link', brow['nameAsDisplayed']+' -> '+own['canonicalUri']),
                (dept, brow['requestedUrl'], 'document_heading', 'Department of '+target['department']+' Faculty Directory'),
                (name, own['requestedUrl'], 'document_heading', own['nameAsDisplayed']),
                (appointment, own['requestedUrl'], 'main_text_quote', binding['ownAppointmentAsListed']['titleAsListed'])]
    if any((p.get('requestedUrl'), p.get('evidenceType'), p.get('evidence')) != (u, k, text)
           for p, u, k, text in expected):
        raise ValueError('Each identity and appointment proof must belong to its actual named source scope')
    for proof, value, selectors in [(canonical, own['canonicalUri'], {'rel': 'canonical'}),
                                     (rdf, own['rdfAlternateUri'], {'rel': 'alternate', 'type': 'application/rdf+xml'})]:
        if (proof.get('requestedUrl') != own['requestedUrl'] or proof.get('evidenceType') != 'html_attribute'
                or proof.get('elementTag') != 'link' or proof.get('attributeName') != 'href'
                or proof.get('attributeValue') != value or proof.get('selectorAttributes') != selectors):
            raise ValueError('Personal identifiers must be the own head metadata,not a reference elsewhere')
    if (name.get('headingTag') != 'h2' or dept.get('headingTag') != 'h1'
            or any(p.get('linkUrl') != own['canonicalUri'] for p in [link, table])
            or row.get('fieldEvidence') != {'name': [table], 'department': [appointment, dept],
                                           'officialProfileUrl': [canonical, table]}):
        raise ValueError('Retained canonical fields require their own named and appointment evidence')
    affiliations = [{'department': target['department'], 'status': 'own_appointment_as_listed',
                     'roleAsListed': binding['ownAppointmentAsListed']['titleAsListed'],
                     'fieldEvidence': [appointment, dept]},
                    {'department': source['department'], 'status': 'affiliate_as_listed',
                     'roleAsListed': 'Affiliate', 'fieldEvidence': [card, title]}]
    if row.get('departmentEvidence') != affiliations or row.get('unsupportedDepartmentValues'):
        raise ValueError('Affiliate context and primary appointment must remain separately sourced and labelled')
    snapshots = row.get('previousCandidateObservations', [])
    if len(snapshots) != 2:
        raise ValueError('Retain both complete preceding compiled candidate records')
    for original in [source, target]:
        selected = [x for x in snapshots if x.get('record', {}).get('id') == original['id']]
        if (len(selected) != 1 or not re.fullmatch(r'[0-9a-f]{64}', selected[0].get('candidateAtlasSha256', ''))
                or selected[0].get('recordSha256') != record_sha256(selected[0]['record'])
                or any(selected[0]['record'].get(k) != original.get(k)
                       for k in ['id', 'name', 'department', 'officialProfileUrl'])):
            raise ValueError('Both preceding candidate snapshots must retain their full bytes and unchanged original identity')


def retain_shared_primary_observations(target, row):
    """Keep compiled snapshots and the actual shorter published subject name."""
    aliases = [row['originalSourceRecord']['name'], row['sharedPrimaryBinding']['ownProfile']['nameAsDisplayed']]
    target['aliasNames'] = [n for n in unique_values(target.get('aliasNames', []) + aliases) if n != target['name']]
    target['fieldEvidence']['aliasNames'] = unique_values(evidence_items(target['fieldEvidence'].get('aliasNames'))
        + [row['sourceLinkEvidence'], row['ownNameEvidence']])
    for snapshot in row['previousCandidateObservations']:
        observation = {'field': 'sharedPrimaryPreviousCandidate', 'value': copy.deepcopy(snapshot['record']),
                       'recordSha256': snapshot['recordSha256'], 'candidateAtlasSha256': snapshot['candidateAtlasSha256'],
                       'sourceProfessorId': snapshot['record']['id'], 'reason': row['reason']}
        target['previousFieldObservations'] = unique_values(target.get('previousFieldObservations', []) + [observation])
        if snapshot['record']['id'] == row['sourceProfessorId']:
            original = snapshot['record']
            for field in ['appointmentStatus', 'personalWebsiteUrl']:
                if field not in original:
                    continue
                contextual = {'field': field, 'value': copy.deepcopy(original[field]),
                              'fieldEvidence': copy.deepcopy(evidence_items(original.get('fieldEvidence', {}).get(field))),
                              'sourceProfessorId': original['id'],
                              'reason': 'Original directory field retained separately. An affiliate label and a Research link do not replace the canonical individual appointment or establish a personal self-website.'}
                target['additionalProfileObservations'] = unique_values(target.get('additionalProfileObservations', []) + [contextual])
