"""Verify external lab ownership separately from a UCSD graduate-program link.

A program card and explicit own-site rotation guidance establish that connection;
they do not establish a UCSD department appointment, lab ownership, or PI identity.
"""
import copy
import hashlib
import re
import urllib.parse
from pathlib import Path

from lab_identity_merges import verify_capture_proofs
from lab_own_metadata import document_lab_name
from lab_resource_reviews import record_sha256
from refresh_labs import DOM, every_node, links, normalized

KIND = 'ucsd_graduate_program_external_lab'
SCOPE = 'ucsd_graduate_program_affiliate'


def verified_program_affiliate_labs(labs, queue, cache):
    """Return verified copies; reject unreviewed foreign ownership in new labs."""
    result = copy.deepcopy(labs)
    items = {i['url']: i for i in queue['items'].values()}
    for lab in result:
        row = lab.get('programAffiliationReview')
        if not row and lab.get('institution') == 'University of California San Diego':
            continue
        if (not isinstance(row, dict) or row.get('kind') != KIND
                or lab.get('relationshipScope') != SCOPE
                or lab.get('recordSubtype') != 'lab' or lab.get('websiteSharing')
                or lab.get('professorIds') or lab.get('relatedProfessorNames')
                or row.get('labId') != lab['id'] or row.get('labWebsiteUrl') != lab['labWebsiteUrl']
                or row.get('institution') != lab['institution']
                or lab['institution'] in {'', 'Unknown', 'Not found', 'University of California San Diego'}
                or lab.get('department') != 'Unknown' or not row.get('reason')):
            raise ValueError('External new lab requires its explicit graduate-program scope and own institution')
        raw = queue.get('labCandidates', {}).get(row.get('originalRequestedUri'), {}).get('record')
        if (raw is None or raw != row.get('originalSourceRecord') or raw['id'] != lab['id']
                or row.get('originalSourceRecordSha256') != record_sha256(raw)):
            raise ValueError('Program affiliate requires the unchanged frozen source ID and raw record')
        proofs = row.get('evidence', [])
        verify_capture_proofs(proofs, queue, cache, lab['id'])
        keys = ['ownIdentityEvidence', 'ownInstitutionEvidence', 'ownStudentAccessEvidence',
                'programEvidence', 'campusCardEvidence', 'campusLabLinkEvidence']
        if any(row.get(k) not in proofs for k in keys):
            raise ValueError('Program affiliate requires all six separately scoped proofs')
        identity, institution, access, program, card, link = [row[k] for k in keys]
        if (identity.get('evidenceType') not in {'document_title', 'document_heading'}
                or document_lab_name(identity['evidence']) != document_lab_name(lab['labName'])
                or any(p['requestedUrl'] != row['originalRequestedUri']
                       or p['sourceUrl'] != lab['labWebsiteUrl'] for p in [identity, institution, access])
                or identity not in lab.get('fieldEvidence', {}).get('labName', [])
                or lab.get('fieldEvidence', {}).get('institution') != [institution]):
            raise ValueError('External institution and group identity require their exact own captured resource')
        source = items[row['originalRequestedUri']]['fetch']
        if source.get('httpStatus') != 200:
            raise ValueError('Program affiliate requires its actual successful HTTP response')
        visited = row['originalRequestedUri']
        for hop in source.get('redirects', []):
            if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
                raise ValueError('Program affiliate requires actual continuous transport observations')
            visited = hop.get('to')
        if visited != lab['labWebsiteUrl']:
            raise ValueError('Program affiliate primary is not the actually captured destination')
        own_document = DOM((Path(cache)/'responses'/(hashlib.sha256(row['originalRequestedUri'].encode()).hexdigest()+'.html')).read_text())
        dom = own_document.main()
        text = institution['evidence']
        if (institution.get('evidenceType') != 'main_text_quote' or len(text) > 800
                or not normalized(text).startswith(normalized(lab['labName']+' '+lab['institution'])+' ')
                or not any(n.tag in {'address', 'p', 'div', 'section'} and n.text() == text for n in every_node(dom))):
            raise ValueError('Foreign institution requires the specifically named own lab contact block')
        text = access['evidence']
        if (access.get('evidenceType') != 'main_text_quote' or len(text) > 1200
                or not re.search(r'\bfor (?:ucsd|uc san diego) graduate students we (?:consider|accept) rotation students\b', normalized(text))
                or re.search(r'\b(?:not|never|no)\b', normalized(text))
                or not any(n.tag == 'p' and n.text() == text for n in every_node(dom))):
            raise ValueError('A campus link alone cannot establish own UCSD graduate rotation access')
        program_uri = row.get('programSourceUrl', '')
        host = urllib.parse.urlsplit(program_uri).hostname or ''
        if (not (host == 'ucsd.edu' or host.endswith('.ucsd.edu'))
                or not row.get('programName') or len(row['programName']) < 5
                or any(p['sourceUrl'] != program_uri for p in [program, card, link])
                or len({p['requestedUrl'] for p in [program, card, link]}) != 1
                or program.get('evidenceType') not in {'document_title', 'document_heading'}
                or row['programName'] not in program['evidence']
                or link.get('evidenceType') != 'named_link' or link.get('linkUrl') != row['originalRequestedUri']):
            raise ValueError('Program relationship requires its named official program and literal lab link')
        selectors = row.get('campusCardSelectorAttributes', {})
        if not selectors or any(not isinstance(k, str) or not isinstance(v, str) for k, v in selectors.items()):
            raise ValueError('Program faculty evidence requires an explicit unique own card')
        path = Path(cache)/'responses'/(hashlib.sha256(card['requestedUrl'].encode()).hexdigest()+'.html')
        matches = [n for n in every_node(DOM(path.read_text()).main()) if n.tag in {'div', 'article', 'section', 'tr'}
                   and all(n.attrs.get(k) == v for k, v in selectors.items())]
        if (len(matches) != 1 or matches[0].text() != card['evidence']
                or card.get('evidenceType') != 'main_text_quote'
                or [n.text() for n in every_node(matches[0]) if n.tag == 'h3'] != [row.get('facultyNameAsListed')]
                or not row.get('facultyRoleAsListed') or row['facultyRoleAsListed'] not in card['evidence']
                or lab['institution'] not in row['facultyRoleAsListed']
                or (link['linkText'], link['linkUrl']) not in [(s, u) for _, s, u in links(matches[0], program_uri)]):
            raise ValueError('The lab link, external faculty role and named subject must belong to one program card')
        titles = [n.text() for n in every_node(own_document.root) if n.tag == 'title']
        lab['websiteCheck'] = {k: copy.deepcopy(source[k]) for k in ['sourceUrl', 'observedAt', 'httpStatus', 'finalUrl']}
        lab['websiteCheck']['status'] = 'reachable'
        if len(titles) == 1:
            lab['websiteCheck']['title'] = titles[0]
        lab.setdefault('verification', {})['lastAttemptedAt'] = source['observedAt']
        contact = row.get('encodedContactEmail')
        if contact is None and any(p.get('method') == 'reviewed_public_bracket_at_lab_contact'
                                   for p in lab.get('fieldEvidence', {}).get('contactEmail', [])):
            raise ValueError('An encoded contact proof requires its explicit source-pair decoding review')
        if contact is not None:
            raw_contact, decoded = contact.get('rawText', ''), contact.get('canonicalEmail', '')
            match = re.fullmatch(r'([A-Za-z0-9._%+-]+)\s*\[at\]\s*([A-Za-z0-9.-]+\.[A-Za-z]{2,})', raw_contact)
            if (match is None or decoded != match[1]+'@'+match[2]
                    or raw_contact not in re.findall(r'[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\.[A-Za-z]{2,}', institution['evidence'])
                    or decoded not in re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', card['evidence'])):
                raise ValueError('Encoded lab contact requires its literal own bracket-at form and independently published canonical program-card address')
            lab['contactEmail'] = decoded
            lab['fieldEvidence']['contactEmail'] = [dict(p, method='reviewed_public_bracket_at_lab_contact',
                rawContactText=raw_contact, decodedContactEmail=decoded) for p in [institution, card]]
        row['captureVerified'] = True
        relation = {'institution': 'University of California San Diego', 'programName': row['programName'],
                    'relationship': 'program_listing_and_own_rotation_guidance',
                    'facultyNameAsListed': row['facultyNameAsListed'], 'facultyRoleAsListed': row['facultyRoleAsListed'],
                    'programSourceUrl': program_uri, 'studentAccessStatement': {'text': access['evidence'],
                        'url': access['sourceUrl'], 'observedAt': access['observedAt']}, 'captureVerified': True}
        lab['campusProgramRelationships'] = [relation]
        lab.setdefault('fieldEvidence', {})['campusProgramRelationships'] = [program, card, link, access]
    return result
