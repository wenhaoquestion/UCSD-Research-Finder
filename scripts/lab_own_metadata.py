"""Captured statements on reviewed, specifically named lab resources.

An exact captured primary or accepted alias can supply its own research,
name and explicit group affiliation. A named home can publish a research child
within its lab directory without making that child a homepage alias.
"""
import copy
import re
from urllib.parse import urlsplit

from atlas_urls import url_key
from lab_entities import LabIndex, named_lab_key, reviewed_resource_mismatch
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from refresh_labs import evidence_items, merge_observed_fields, unique_values
from lab_root_research_descriptions import verified_root_research_scope, KIND as ROOT_RESEARCH_KIND
from lab_child_research_fields import verified_child_research_fields, KIND as CHILD_RESEARCH_KIND

UCSD = 'University of California San Diego'
OWN_FIELDS = {'description', 'institution', 'department', 'labName', 'recordSubtype'}


def document_lab_name(value):
    # Identity comes from reviewed URI ownership; these are display qualifiers.
    return named_lab_key(re.sub(r'\b(?:website|web|site|homepage|home|welcome|to|at|ucsd)\b', '', named_lab_key(value)))


def verified_child_scope(row, queue, parent, expected_name):
    """A named home may publish a research child within its own lab directory.

    This is a description source relationship, not an alias of the home or a
    person/institution relationship. Both the requested and actual child must
    stay inside that directory throughout the captured redirect chain.
    """
    scope = row.get('sourceScope', {})
    proofs = row['evidence']
    child = scope.get('requestedUrl')
    item = next((i for i in queue['items'].values() if i['url'] == child), {})
    meta = item.get('fetch', {})
    parsed = urlsplit(parent)
    directory = parsed.path if parsed.path.endswith('/') else parsed.path.rsplit('/', 1)[0] + '/'
    link = scope.get('publishedLinkEvidence')
    subject = scope.get('researchSubject', '')
    subject_key = document_lab_name(subject)
    # Require an explicitly named group in the actual research sentence. A
    # campus-root navigation link or a collaborator's surname is insufficient.
    declaration = scope.get('subjectStatement', '')
    allowed_subject = set(document_lab_name(expected_name).split())
    named_subject = set(subject_key.split())
    generic = {'lab', 'laboratory', 'group', 'research'}
    if (scope.get('kind') != 'named_own_parent_published_child'
            or set(row['fields']) != {'description'} or directory == '/'
            or parsed.query or parsed.fragment or not subject_key
            or not named_subject - generic or not named_subject <= allowed_subject
            or not re.search(r'\b(?:lab|laboratory|group)\b', subject, re.I)
            or declaration not in row['fields']['description']
            or not re.fullmatch(r'(?:The ongoing )?[Rr]esearch in the ' + re.escape(subject)
                                + r' (?:aims|focuses|investigates)\b.*', declaration)
            or link not in proofs or link.get('sourceUrl') != parent
            or link.get('evidenceType') not in {'named_link', 'document_link'}
            or link.get('linkUrl') != child or meta.get('status') != 'ok'):
        raise ValueError('Lab child description requires its named parent, published link and scoped research subject')
    visited = child
    destinations = [child]
    for hop in meta.get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Lab child requires its actual continuous redirect chain')
        visited = hop.get('to'); destinations.append(visited)
    if visited != meta.get('finalUrl'):
        raise ValueError('Lab child requires its actual continuous redirect chain')
    for uri in destinations:
        part = urlsplit(uri)
        if ((part.scheme, part.netloc) != (parsed.scheme, parsed.netloc)
                or not part.path.startswith(directory) or part.path == directory
                or part.path == parsed.path or part.query or part.fragment
                or any(p in {'.', '..'} or '%' in p for p in part.path.split('/'))):
            raise ValueError('Lab child must stay within the named parent lab directory')
    if (set(p['sourceUrl'] for p in proofs) != {parent, visited}
            or any(p.get('sourceUrl') != parent for p in row['identityEvidence'])
            or any(p.get('sourceUrl') != visited or p.get('requestedUrl') != child
                   for p in evidence_items(row['fieldEvidence']['description']))):
        raise ValueError('Lab child description must use exactly its named parent and published child captures')
    return visited


def own_group_affiliation(row, expected_name, source):
    """Read the group's own explicit affiliation, independently of a PI role."""
    claim = row.get('groupAffiliationStatement', {})
    fields = row['fields']
    institution, department = fields.get('institution'), fields.get('department')
    text = claim.get('evidence', '')
    names = [expected_name] + row['originalLabRecord'].get('aliasNames', [])
    patterns = [r'(?:Welcome to )?' + re.escape(name)
                + r' in the Department of ' + re.escape(str(department))
                + r' at the ' + re.escape(str(institution)) + r'\.' for name in names]
    if (not isinstance(institution, str) or not institution.strip() or len(institution) > 200
            or not isinstance(department, str) or not department.strip() or len(department) > 200
            or institution in {'Unknown', 'Not found'} or department in {'Unknown', 'Not found'}
            or claim not in row['evidence'] or claim.get('sourceUrl') != source
            or claim.get('evidenceType') != 'main_text_quote'
            or claim.get('method') != 'reviewed_own_lab_group_affiliation'
            or not any(re.fullmatch(pattern, text) for pattern in patterns)
            or any(evidence_items(row['fieldEvidence'].get(f)) != [claim] for f in ['institution', 'department'])):
        raise ValueError('Lab affiliation requires the named group and exact own institution and department statement')


def verified_own_metadata(review, aliases, queue, cache, labs, label_updates=()):
    index = LabIndex(labs)
    owners = {}
    for alias in aliases:
        if not alias.get('captureVerified'):
            raise ValueError('Own lab metadata requires verified resource aliases')
        owner = index.by_id.get(alias['labId'])
        owners.setdefault(url_key(alias['url']), set()).add(owner['id'] if owner else alias['labId'])
    rows, seen = copy.deepcopy(review.get('entries', [])), set()
    for row in rows:
        lab = index.by_id.get(row.get('labId'))
        original = row.get('originalLabRecord', {})
        fields, proofs = row.get('fields', {}), row.get('evidence', [])
        if (lab is None or row['labId'] != lab['id'] or row['labId'] in seen or not row.get('reason')
                or original.get('id') != lab['id'] or original.get('labName') != lab['labName']
                or row.get('originalLabRecordSha256') != record_sha256(original)
                or not fields or (set(fields) - OWN_FIELDS and not
                    (row.get('sourceScope',{}).get('kind') == CHILD_RESEARCH_KIND and set(fields) == {'researchAreas'}))
                or not document_lab_name(lab['labName'])
                or lab.get('websiteSharing')):
            raise ValueError('Own lab metadata requires one unchanged named identity and original record')
        seen.add(row['labId'])
        verify_capture_proofs(proofs, queue, cache, row['labId'])
        identity = row.get('identityEvidence', [])
        expected_name = row.get('documentLabName', lab['labName'])
        if 'labName' in fields and fields['labName'] != expected_name:
            raise ValueError('Own lab name must be its explicit document name')
        if expected_name != lab['labName'] and 'labName' not in fields:
            updates = [u for u in label_updates if u.get('labId') == lab['id']
                       and u.get('fields') == {'labName': expected_name}]
            if len(updates) != 1:
                raise ValueError('Own lab metadata requires its explicit reviewed name update')
            declarations = evidence_items(updates[0].get('fieldEvidence', {}).get('labName'))
            verify_capture_proofs(declarations, queue, cache, lab['id'])
            if (not declarations or any(p not in proofs for p in declarations)
                    or not any(p in identity and p.get('evidenceType') in {'document_title', 'document_heading'}
                               and document_lab_name(p['evidence']) == document_lab_name(expected_name)
                               for p in declarations)):
                raise ValueError('Own lab metadata name requires its exact owned document declaration')
        source = proofs[0]['sourceUrl']
        owned = owners.get(url_key(source))
        if owned is None:
            # An exact current primary request already identifies the resource.
            # Subpages, host spelling and inferred protocol equivalence do not.
            primary = [i for i in queue['items'].values()
                       if i['url'] == lab['labWebsiteUrl'] and i.get('fetch', {}).get('status') == 'ok'
                       and i['fetch'].get('finalUrl') == source
                       and any(p['requestedUrl'] == i['url'] for p in proofs)]
            if (len(primary) == 1 and not reviewed_resource_mismatch(lab, lab['labWebsiteUrl'])
                    and {l['id'] for l in index.candidates(lab['labWebsiteUrl'])} == {lab['id']}):
                item = primary[0]; visited = item['url']
                for hop in item['fetch'].get('redirects', []):
                    if hop.get('from') != visited or hop.get('httpStatus') not in {301,302,303,307,308}:
                        raise ValueError('Own lab primary requires its actual continuous redirect chain')
                    visited = hop.get('to')
                if visited != source:
                    raise ValueError('Own lab primary requires its actual continuous redirect chain')
                owned = {lab['id']}
        child_scope = row.get('sourceScope')
        if child_scope:
            if child_scope.get('kind') == CHILD_RESEARCH_KIND:
                if (owned != {lab['id']} or expected_name != lab['labName'] or source != lab['labWebsiteUrl']
                        or {target['id'] for target in index.candidates(source)} != {lab['id']}):
                    raise ValueError('Child research headings require the unchanged uniquely owned named lab primary')
                verified_child_research_fields(row, queue, cache, source, expected_name)
                row['captureVerified'] = True
                continue
            elif child_scope.get('kind') == ROOT_RESEARCH_KIND:
                verified_root_research_scope(row, queue, cache, source, expected_name)
            else:
                verified_child_scope(row, queue, source, expected_name)
        if (not document_lab_name(expected_name) or not identity or any(p not in proofs for p in identity)
                or (not child_scope and len({p['sourceUrl'] for p in proofs}) != 1)
                or owned != {lab['id']}
                or not any(p.get('evidenceType') in {'document_title', 'document_heading'}
                           and document_lab_name(p['evidence']) in
                           {document_lab_name(n) for n in [expected_name]+lab.get('aliasNames', [])}
                           for p in identity)):
            raise ValueError('Own lab metadata requires its exact reviewed alias and named document')
        if row.get('groupAffiliationStatement') or 'department' in fields:
            own_group_affiliation(row, expected_name, source)
        if 'recordSubtype' in fields:
            # Unknown institution and unsupported department routing are not
            # affiliations of a separately named NGO. Keep that source context
            # in history instead of rendering it as an organizational unit.
            if (fields['recordSubtype'] != 'ngo' or set(fields) - {'recordSubtype', 'description'}
                    or lab.get('institution') not in {None, '', 'Unknown', 'Not found'}
                    or evidence_items(lab.get('fieldEvidence', {}).get('institution'))
                    or evidence_items(lab.get('fieldEvidence', {}).get('department'))):
                raise ValueError('NGO classification requires unresolved institutional and department context')
        for field, value in fields.items():
            claimed = evidence_items(row.get('fieldEvidence', {}).get(field))
            if (len(claimed) != 1 or claimed[0] not in proofs
                    or claimed[0].get('evidenceType') not in
                    ({'document_title', 'document_heading'} if field == 'labName' else {'main_text_quote'})):
                raise ValueError('Each own lab field requires its exact captured statement')
            proof = claimed[0]
            if field == 'labName':
                if (proof not in identity or proof.get('sourceUrl') != source
                        or proof.get('method') != 'reviewed_own_lab_name_declaration'
                        or proof.get('evidence') != value or not isinstance(value, str)
                        or not value.strip() or len(value) > 200):
                    raise ValueError('Lab name requires its exact owned document declaration')
            elif field == 'description':
                if (not isinstance(value, str) or not value.strip() or len(value) > 2000
                        or proof.get('method') != ('reviewed_own_organization_description' if fields.get('recordSubtype') == 'ngo'
                                                   else 'reviewed_own_lab_research_description')
                        or proof.get('evidence') != value):
                    raise ValueError('Lab description requires the complete exact own research quote')
            elif field == 'recordSubtype':
                if (proof.get('sourceUrl') != source or proof.get('method') != 'reviewed_own_organization_type'
                        or not re.search(r'\bis a (?:global )?NGO\b', proof.get('evidence', ''))):
                    raise ValueError('NGO type requires its explicit owned organization statement')
            elif row.get('groupAffiliationStatement') and field in {'institution', 'department'}:
                pass  # The paired, exact named-group declaration was checked above.
            elif (value != UCSD or lab.get('institution') not in {None, '', 'Unknown', 'Not found', UCSD}
                  or proof.get('method') != 'reviewed_own_lab_contact_institution'
                  or not re.match(r'Contact(?: us)?\b', proof.get('evidence', ''), re.I)
                  or not re.search(r'\bUniversity of California,?\s+San Diego\b', proof['evidence'])):
                raise ValueError('Lab institution requires its explicit own contact affiliation, not a domain or person appointment')
        row['captureVerified'] = True
    return rows


def apply_own_metadata(data, reviews):
    index = LabIndex(data['labs'])
    for row in reviews:
        lab = index.by_id.get(row.get('labId'))
        if (not row.get('captureVerified') or lab is None or lab['id'] != row['labId']
                or lab['labName'] not in {row.get('documentLabName', row['originalLabRecord']['labName']),
                                         row['originalLabRecord']['labName'] if 'labName' in row.get('fields', {}) else None}
                or not row.get('fields') or (set(row['fields']) - OWN_FIELDS and not
                    (row.get('sourceScope',{}).get('kind') == CHILD_RESEARCH_KIND
                     and set(row['fields']) == {'researchAreas'}))
                or not row.get('evidence')):
            raise ValueError('Own lab metadata requires a verified canonical target')
    for row in reviews:
        lab = index.by_id[row['labId']]
        fields, evidence = copy.deepcopy(row['fields']), copy.deepcopy(row['fieldEvidence'])
        if 'institution' in fields:
            fields['relationshipScope'] = ('reviewed_own_group_affiliation' if row.get('groupAffiliationStatement')
                                           else 'reviewed_ucsd_affiliation')
            evidence['relationshipScope'] = copy.deepcopy(evidence['institution'])
        if fields.get('recordSubtype') == 'ngo':
            fields.update(relationshipScope='associated_organization', relationshipType='faculty_organization_link')
            for field in ['relationshipScope', 'relationshipType']:
                evidence[field] = copy.deepcopy(evidence['recordSubtype'])
        updated = merge_observed_fields(lab, {**fields, 'fieldEvidence': evidence})
        lab.clear(); lab.update(updated)
        if (fields.get('recordSubtype') == 'ngo' and lab.get('recordSubtype') == 'ngo'
                and lab.get('department') in {row['originalLabRecord'].get('department'), 'Unknown'}
                and not evidence_items(lab.get('fieldEvidence', {}).get('department'))):
            old_department = row['originalLabRecord'].get('department', 'Unknown')
            if old_department not in {'Unknown', 'Not found', ''}:
                observation = {'field': 'department', 'value': old_department,
                               'fieldEvidence': copy.deepcopy(row['originalLabRecord'].get('fieldEvidence', {}).get('department', [])),
                               'reason': 'Original faculty-source routing context is not a verified department of this NGO.'}
                lab['previousFieldObservations'] = unique_values(lab.get('previousFieldObservations', []) + [observation])
            lab['department'] = 'Unknown'
            lab.get('fieldEvidence', {}).pop('department', None)
            lab['departmentAssessment'] = {'status': 'unresolved', 'sourceDepartmentContext': old_department,
                'reason': 'No organizational department is established by the retained faculty routing context. NGO type is stated on its own captured site.'}
        lab['labOwnMetadataReviews'] = unique_values(lab.get('labOwnMetadataReviews', []) + [row])
        lab['sourceUrls'] = unique_values(lab.get('sourceUrls', []) + [p['sourceUrl'] for p in row['evidence']])
