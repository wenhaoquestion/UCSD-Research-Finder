"""Replace a profile-only lab resource using a literal named campus card.

The old profile can be unavailable and its old label proof can be defective.
That history is retained; two links in one named campus card and a captured
named own lab establish the resource choice without creating a person edge.
"""
import copy
import hashlib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from refresh_labs import DOM, every_node, links, normalized, unique_values

KIND = 'profile_only_lab_to_named_own_site_via_campus_card'


def verified_profile_source_upgrade(row, lab, queue, cache):
    binding = row.get('profileSourceUpgrade')
    if (not isinstance(binding, dict) or binding.get('kind') != KIND
            or lab.get('profile_only') is not True or lab.get('sourceKind') != 'profile_only'
            or lab.get('independentLabWebsiteVerified') is not False
            or binding.get('baselineLabRecord') != lab
            or binding.get('baselineLabRecordSha256') != record_sha256(lab)
            or lab.get('professorIds') or lab.get('relatedProfessorNames')
            or lab.get('principalInvestigator') != 'Not found'
            or lab.get('principalInvestigatorProfileUrl') != 'Not found'
            or lab.get('institution') != 'University of California San Diego'
            or lab.get('fieldEvidence', {}).get('department')
            or not binding.get('departmentUnresolvedReason')
            or row.get('preferredLabName', lab['labName']) != lab['labName']):
        raise ValueError('Profile-only resource upgrade requires the unchanged baseline identity and no inferred person edge')
    proofs = binding.get('evidence', [])
    verify_capture_proofs(proofs, queue, cache, lab['id'])
    keys = ['campusCardEvidence', 'campusProfileLinkEvidence', 'campusLabLinkEvidence', 'transportEvidence',
            'ownTitleEvidence', 'ownNameEvidence', 'ownInstitutionEvidence', 'ownPeopleTitleEvidence',
            'ownPiSectionEvidence']
    if any(binding.get(k) not in proofs for k in keys) or any(p not in row['evidence'] for p in proofs):
        raise ValueError('Profile-only upgrade requires all separately scoped card, own lab and PI-section proofs')
    card, profile_link, lab_link, transport, title, name, institution, people_title, pi = [binding[k] for k in keys]
    directory = binding.get('campusDirectoryUrl', '')
    host = urlsplit(directory).hostname or ''
    if (not (host == 'ucsd.edu' or host.endswith('.ucsd.edu'))
            or any(p['sourceUrl'] != directory or p['requestedUrl'] != card['requestedUrl']
                   for p in [card, profile_link, lab_link])
            or card.get('evidenceType') != 'main_text_quote'):
        raise ValueError('Profile-only upgrade requires one actual official directory capture')
    def document(proof):
        return DOM((Path(cache)/'responses'/(hashlib.sha256(proof['requestedUrl'].encode()).hexdigest()+'.html')).read_text())
    items = {i['url']: i for i in queue['items'].values()}
    for p in proofs:
        meta = items[p['requestedUrl']]['fetch']
        if meta.get('httpStatus') != 200 or meta.get('sha256') != p['bodySha256']:
            raise ValueError('Profile-only upgrade requires actual successful captured sources')
        visited = p['requestedUrl']
        for hop in meta.get('redirects', []):
            if hop.get('from') != visited or hop.get('httpStatus') not in {301,302,303,307,308}:
                raise ValueError('Profile-only upgrade requires continuous observed transport')
            visited = hop.get('to')
        if visited != p['sourceUrl']:
            raise ValueError('Profile-only upgrade cannot infer resource destinations')
    selectors = binding.get('campusCardSelectorAttributes', {})
    if not selectors or any(not isinstance(k,str) or not isinstance(v,str) for k,v in selectors.items()):
        raise ValueError('Profile-only upgrade requires an explicit unique card selector')
    cards = [n for n in every_node(document(card).main()) if n.tag in {'div','article','section','tr'}
             and all(n.attrs.get(k) == v for k,v in selectors.items())]
    person = binding.get('personNameAsPublished', '')
    if (len(cards) != 1 or cards[0].text() != card['evidence'] or not person
            or [n.text() for n in every_node(cards[0]) if n.tag == 'h3'] != [person]
            or profile_link.get('evidenceType') != 'named_link' or profile_link.get('linkText') != 'Profile'
            or profile_link.get('linkUrl') != row['previousPreferredUrl']
            or lab_link.get('evidenceType') != 'named_link' or lab_link.get('linkText') != 'Lab Site'
            or not all((p['linkText'],p['linkUrl']) in [(t,u) for _,t,u in links(cards[0],directory)]
                       for p in [profile_link,lab_link])):
        raise ValueError('Original profile and own lab links must belong to the same uniquely named campus card')
    literal = binding.get('literalCampusLabHref', '')
    parsed = urlsplit(literal)
    requested = urlunsplit((parsed.scheme,parsed.netloc,parsed.path or '/',parsed.query,parsed.fragment))
    new = row['preferredUrl']
    if (requested != lab_link['linkUrl'] or not any(n.tag == 'a' and n.attrs.get('href') == literal
            and n.text() == 'Lab Site' for n in every_node(cards[0]))
            or transport.get('evidenceType') != 'redirect_chain'
            or transport['requestedUrl'] != requested or transport['sourceUrl'] != new
            or title.get('evidenceType') != 'document_title' or title['evidence'] != lab['labName']
            or name.get('evidenceType') != 'document_heading' or name.get('headingTag') != 'h1'
            or name['evidence'] != lab['labName']
            or institution.get('evidenceType') != 'document_heading'
            or institution['evidence'] != lab['labName']+' at UC San Diego'
            or any(p['sourceUrl'] != new for p in [title,name,institution])):
        raise ValueError('Profile-only upgrade requires the exact literal transport and independently named own UCSD lab')
    # Read only the named PI section, stopping before the next heading. Alumni
    # and lab-member names elsewhere cannot become the canonical PI string.
    own_host = urlsplit(new).hostname
    if (urlsplit(pi['sourceUrl']).hostname != own_host or pi.get('evidenceType') != 'main_text_quote'
            or people_title['sourceUrl'] != pi['sourceUrl']
            or people_title.get('evidenceType') != 'document_title'
            or people_title['evidence'] != 'People · '+lab['labName']):
        raise ValueError('Own PI context must belong to this named lab people page')
    headings = [n for n in every_node(document(pi).main()) if n.tag == 'h1' and n.attrs.get('id') == 'pi']
    if len(headings) != 1:
        raise ValueError('Own lab requires one explicitly scoped PI heading')
    heading = headings[0]
    label = ' '.join(n.text() if hasattr(n,'text') else n for n in heading.children
                     if not (getattr(n,'tag',None) == 'a'))
    if normalized(label) != 'pi':
        raise ValueError('Own lab section must explicitly label PI')
    section = [heading]
    for n in heading.parent.children[heading.parent.children.index(heading)+1:]:
        if getattr(n,'tag','') in {'h1','h2','h3','h4','h5','h6'}: break
        if hasattr(n,'text'): section.append(n)
    text = ' '.join(n.text() for n in section if n.text())
    subjects = [n.text() for n in section if n.tag == 'p' and n.text()
                and not any(c.tag == 'a' for c in every_node(n))]
    if text != pi['evidence'] or subjects != [person]:
        raise ValueError('Only the single published name inside the explicit PI section may be recorded')
    binding['captureVerified'] = True


def apply_profile_source_upgrade(lab, row):
    binding = row.get('profileSourceUpgrade')
    if not binding:
        return
    def claim(field, value, proofs=None):
        old_proofs = lab.get('fieldEvidence', {}).get(field, [])
        if lab.get(field) != value or proofs is not None and old_proofs != proofs:
            archived = [p for o in lab.get('previousFieldObservations', []) if o.get('field') == field
                        for p in o.get('fieldEvidence', [])]
            # Legacy expansion inputs are replayed on each build. Already
            # archived defective proofs must stay historical rather than
            # growing a new mixed old/new observation on every rebuild.
            if lab.get(field) != value or any(p not in (proofs or []) and p not in archived for p in old_proofs):
                lab['previousFieldObservations'] = unique_values(lab.get('previousFieldObservations', []) + [{
                    'field':field,'value':copy.deepcopy(lab.get(field)), 'fieldEvidence':copy.deepcopy(old_proofs),
                    'reason':row['reason']}])
            lab[field] = copy.deepcopy(value)
            if proofs is not None: lab.setdefault('fieldEvidence', {})[field] = copy.deepcopy(proofs)
    claim('labName',lab['labName'],[binding['ownTitleEvidence'],binding['ownNameEvidence']])
    claim('labWebsiteUrl',row['preferredUrl'],row['evidence'])
    claim('institution','University of California San Diego',[binding['ownInstitutionEvidence']])
    claim('department','Unknown')
    lab.get('fieldEvidence', {}).pop('department',None)
    lab['departmentAssessment'] = {'status':'unresolved', 'reason':binding['departmentUnresolvedReason'],
        'sourceObservedAt':binding['ownInstitutionEvidence']['observedAt']}
    lab['unverifiedFields'] = unique_values(lab.get('unverifiedFields', []) + ['department'])
    claim('principalInvestigator',binding['personNameAsPublished'],[binding['ownPiSectionEvidence']])
    claim('principalInvestigatorIdentityScope','source_reported_name_only')
    claim('sourceKind','lab_website'); claim('profile_only',False); claim('independentLabWebsiteVerified',True)
    claim('identityReview',{'reason':row['reason'],'limitations':[
        'The original profile-only resource and defective skip-link label proof remain in history.',
        'The own-site PI name is source reported;no canonical professor association or person identity merge is inferred.']})
    alternate = binding['transportEvidence']['requestedUrl']
    lab['alternateWebsiteUrls'] = unique_values(lab.get('alternateWebsiteUrls', []) + [alternate])
    lab.setdefault('fieldEvidence', {})['alternateWebsiteUrls'] = unique_values(
        lab.get('fieldEvidence', {}).get('alternateWebsiteUrls', [])
        + [binding['transportEvidence'],binding['ownTitleEvidence']])
    verification = lab.setdefault('verification', {})
    verification['fieldsVerified'] = sorted(set(verification.get('fieldsVerified', [])) | {'labName','institution','principalInvestigator'})
