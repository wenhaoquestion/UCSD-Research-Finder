"""Verify a campus directory resource relationship without inventing ownership.

A named person's directory card can link a scientific group while establishing
neither the group's employing institution nor that person's PI appointment.
"""
import copy
import hashlib
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from lab_identity_merges import verify_capture_proofs
from lab_program_affiliations import verified_program_affiliate_labs
from lab_resource_reviews import record_sha256
from refresh_labs import DOM, every_node, links, normalized

KIND = 'named_campus_linked_research_group'
SCOPE = 'official_campus_research_resource'


def _root_request(uri):
    """Only the empty HTTP root path is equivalent to its request slash."""
    s = urlsplit(uri)
    return urlunsplit((s.scheme, s.netloc, s.path or '/', s.query, s.fragment))


def verified_campus_research_groups(labs, queue, cache):
    result = copy.deepcopy(labs)
    items = {i['url']: i for i in queue['items'].values()}
    for lab in result:
        row = lab.get('campusResearchResourceReview')
        if (not isinstance(row, dict) or row.get('kind') != KIND
                or lab.get('relationshipScope') != SCOPE
                or lab.get('recordSubtype') != 'research_group'
                or lab.get('institution') != 'Unknown' or lab.get('department') != 'Unknown'
                or lab.get('principalInvestigator') != 'Not found'
                or lab.get('principalInvestigatorProfileUrl') != 'Not found'
                or lab.get('contactEmail') != 'Not found' or lab.get('researchAreas')
                or lab.get('professorIds') or lab.get('relatedProfessorNames')
                or lab.get('websiteSharing') or lab.get('programAffiliationReview')
                or lab.get('recruitingStatus') != 'Unknown'
                or row.get('labId') != lab['id'] or not row.get('reason')
                or row.get('labWebsiteUrl') != lab['labWebsiteUrl']):
            raise ValueError('Campus resource group requires explicit unknown ownership and no inferred people or fields')
        fields = lab.get('fieldEvidence', {})
        if any(fields.get(k) for k in ['institution', 'department', 'principalInvestigator',
                                      'principalInvestigatorProfileUrl', 'contactEmail', 'researchAreas']):
            raise ValueError('Directory resource relationship cannot prove ownership, PI, contact or research keywords')
        for field in ['institution', 'department']:
            assessment = lab.get(field+'Assessment', {})
            if assessment.get('status') != 'unresolved' or not assessment.get('reason'):
                raise ValueError('Unknown group ownership requires an explicit unresolved assessment')
        raw = queue.get('labCandidates', {}).get(row.get('originalRequestedUri'), {}).get('record')
        if (raw is None or raw != row.get('originalSourceRecord') or raw['id'] != lab['id']
                or row.get('originalSourceRecordSha256') != record_sha256(raw)):
            raise ValueError('Campus resource requires unchanged frozen source ID and raw record')
        proofs = row.get('evidence', [])
        verify_capture_proofs(proofs, queue, cache, lab['id'])
        keys = ['ownTitleEvidence', 'ownBrandEvidence', 'ownMissionEvidence', 'ownTeamTitleEvidence',
                'ownTeamRoleEvidence', 'ownGroupContextEvidence', 'directoryTitleEvidence',
                'campusCardEvidence', 'campusLinkEvidence', 'transportEvidence']
        if any(row.get(k) not in proofs for k in keys):
            raise ValueError('Campus resource requires all separately scoped scientific and directory proofs')
        title, brand, mission, team_title, role, group, directory_title, card, link, transport = [row[k] for k in keys]
        own_uri = row['originalRequestedUri']
        team_uri, directory_uri = row.get('teamSourceUrl'), row.get('directorySourceUrl')
        host = urlsplit(directory_uri or '').hostname or ''
        if (not (host == 'ucsd.edu' or host.endswith('.ucsd.edu'))
                or not row.get('directoryNameAsPublished') or not row.get('listedNameAsPublished')
                or any(p['sourceUrl'] != directory_uri or p['requestedUrl'] != directory_title['requestedUrl']
                       for p in [directory_title, card, link])
                or directory_title.get('evidenceType') != 'document_title'
                or directory_title['evidence'] != row['directoryNameAsPublished']):
            raise ValueError('Campus resource requires the exact official directory and published title')

        def document(proof):
            path = Path(cache)/'responses'/(hashlib.sha256(proof['requestedUrl'].encode()).hexdigest()+'.html')
            return DOM(path.read_text())

        def successful(proof):
            meta = items[proof['requestedUrl']]['fetch']
            if meta.get('httpStatus') != 200 or meta.get('sha256') != proof['bodySha256']:
                raise ValueError('Campus resource requires actual successful captures')
            visited = proof['requestedUrl']
            for hop in meta.get('redirects', []):
                if hop.get('from') != visited or hop.get('httpStatus') not in {301,302,303,307,308}:
                    raise ValueError('Campus resource requires a continuous observed transport chain')
                visited = hop.get('to')
            if visited != proof['sourceUrl']:
                raise ValueError('Campus resource cannot infer a destination URL')
            return meta

        for proof in proofs:
            successful(proof)
        if (title.get('evidenceType') != 'document_title' or not title['evidence'].startswith(lab['labName']+' ')
                or brand.get('evidenceType') != 'document_link' or brand.get('linkText') != lab['labName']
                or brand.get('linkUrl') != lab['labWebsiteUrl']
                or any(p['requestedUrl'] != own_uri or p['sourceUrl'] != lab['labWebsiteUrl']
                       for p in [title, brand, mission])
                or brand not in fields.get('labName', [])
                or mission.get('evidenceType') != 'main_text_quote'
                or not normalized(mission['evidence']).startswith('we ')
                or not any(n.tag == 'p' and n.text() == mission['evidence'] for n in every_node(document(mission).main()))
                or lab.get('description') != mission['evidence']
                or fields.get('description') != [mission]):
            raise ValueError('Named group and collective research description require exact own published content')
        own_host = urlsplit(lab['labWebsiteUrl']).hostname
        director = row.get('projectDirectorNameAsPublished', '')
        if (not director or any(p['sourceUrl'] != team_uri for p in [team_title, role, group])
                or urlsplit(team_uri or '').hostname != own_host
                or team_title.get('evidenceType') != 'document_title'
                or team_title['evidence'] != 'Our Team – '+lab['labName']
                or role.get('evidenceType') != 'main_text_quote'
                or role['evidence'] != 'Project Director '+director+' '+row.get('projectDirectorRoleAsPublished', '')
                or group.get('evidenceType') != 'main_text_quote'
                or lab['labName']+' lab' not in group['evidence']):
            raise ValueError('Own team must establish a named scientific collective; Project Director is not a PI claim')
        team = document(role).main()
        if (not any(n.tag in {'h1','h2','h3'} and n.text() == 'Project Director' for n in every_node(team))
                or not any(n.tag in {'h1','h2','h3'} and n.text() == 'Current Research Assistants' for n in every_node(team))):
            raise ValueError('Own team evidence requires explicit group roles')
        # Published first/family-name compatibility scopes the card to this
        # resource; it never creates or merges a canonical human identity.
        listed_parts, own_parts = normalized(row['listedNameAsPublished']).split(), normalized(director).split()
        if (len(listed_parts) < 2 or len(own_parts) < 2
                or (listed_parts[0], listed_parts[-1]) != (own_parts[0], own_parts[-1])):
            raise ValueError('Directory and own team subjects are incompatible')
        selectors = row.get('campusCardSelectorAttributes', {})
        if not selectors or any(not isinstance(k,str) or not isinstance(v,str) for k,v in selectors.items()):
            raise ValueError('Campus card requires explicit structural selectors')
        cards = [n for n in every_node(document(card).main()) if n.tag in {'div','article','section','tr'}
                 and all(n.attrs.get(k) == v for k,v in selectors.items())
                 and [c.text() for c in every_node(n) if c.tag == 'h3'] == [row['listedNameAsPublished']]]
        if (len(cards) != 1 or card.get('evidenceType') != 'main_text_quote' or cards[0].text() != card['evidence']
                or link.get('evidenceType') != 'named_link' or link.get('linkText') != 'Lab Web Site'
                or (link['linkText'], link['linkUrl']) not in [(s,u) for _,s,u in links(cards[0], directory_uri)]):
            raise ValueError('Literal lab link and named subject must belong to one unique campus card')
        literal = row.get('literalCampusHref')
        if (not isinstance(literal,str) or _root_request(literal) != link['linkUrl']
                or not any(n.tag == 'a' and n.text() == link['linkText'] and n.attrs.get('href') == literal
                           for n in every_node(cards[0]))
                or transport.get('evidenceType') != 'redirect_chain'
                or transport['requestedUrl'] != link['linkUrl'] or transport['sourceUrl'] != lab['labWebsiteUrl']):
            raise ValueError('Campus resource requires its literal link and actually observed redirect to the group')
        alternate = transport['requestedUrl']
        if lab.get('alternateWebsiteUrls') not in (None, [], [alternate]):
            raise ValueError('Campus group alternate resource requires this exact observed transport')
        lab['alternateWebsiteUrls'] = [alternate]
        fields['alternateWebsiteUrls'] = [transport, brand]
        row['captureVerified'] = True
        lab['campusResearchRelationships'] = [{'relationship': 'named_directory_resource_link',
            'directoryNameAsPublished': row['directoryNameAsPublished'], 'directorySourceUrl': directory_uri,
            'listedNameAsPublished': row['listedNameAsPublished'], 'linkLabelAsPublished': link['linkText'],
            'literalHref': literal, 'observedAt': card['observedAt'], 'captureVerified': True}]
        fields['campusResearchRelationships'] = [directory_title, card, link, transport]
        meta = items[own_uri]['fetch']
        lab['websiteCheck'] = {k: copy.deepcopy(meta[k]) for k in ['sourceUrl','observedAt','httpStatus','finalUrl']}
        lab['websiteCheck'].update(status='reachable', title=title['evidence'])
        lab.setdefault('verification', {})['lastAttemptedAt'] = meta['observedAt']
    return result


def verified_new_lab_scopes(labs, queue, cache):
    """Dispatch explicit scopes without weakening the existing owner verifier."""
    result = []
    for lab in labs:
        if lab.get('campusResearchResourceReview') or lab.get('relationshipScope') == SCOPE:
            result.extend(verified_campus_research_groups([lab], queue, cache))
        else:
            result.extend(verified_program_affiliate_labs([lab], queue, cache))
    return result
