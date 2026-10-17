"""Review the research meaning of literal own-profile text, independently of identity.

An overview can contain degrees, clinical services and committee names. Those
are not research directions merely because a topic dictionary matches them.
These decisions select exact research passages from an already owned resource,
or retain the earlier fields as history when no research passage is selected.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from urllib.parse import urlsplit

from atlas_urls import url_key
from faculty_profile_bindings import captured_source, profile_metadata
from faculty_scoped_titles import same_named_subject
from refresh_labs import DOM, every_node, clean, UCSD_PROFILES_OVERVIEW, UCSD_PROFILES_KEYWORDS


FIELDS = ('researchSummary', 'researchAreas')
DEPENDENCIES = ('researchKeywords', 'researchAreasFromDirectory')
MISSING = 'Not found'
METHOD = 'reviewed_literal_own_research_scope'
RESEARCH_GROUP = 'http://profiles.catalyst.harvard.edu/ontology/prns#PropertyGroupResearch'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def proofs(person, field):
    value = person.get('fieldEvidence', {}).get(field, [])
    return [value] if isinstance(value, dict) else value


def research_scope(item, cache, previous_summary, reviewed_paragraph=None, reviewed_research_group=False):
    capture, markup = captured_source(item, cache)
    meta = item['fetch']; visited = item['url']
    for hop in meta.get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Research scope requires the actual continuous redirect chain')
        visited = hop.get('to')
    if meta.get('httpStatus') != 200 or visited != capture['sourceUrl']:
        raise ValueError('Research scope requires the exact successful resource')
    dom = DOM(markup); nodes = list(dom.main().walk()); host = urlsplit(capture['sourceUrl']).hostname
    if host == 'profiles.ucsd.edu':
        if reviewed_paragraph is not None:
            raise ValueError('Profiles research must stay inside its own complete overview property')
        personal, _ = profile_metadata(item, cache)
        subjects = [personal['nameAsDisplayed']]; template = 'profiles_page_title_h2'
        sections = [n for n in nodes if n.attrs.get('id') == UCSD_PROFILES_OVERVIEW]
        if len(sections) != 1:
            raise ValueError('Research scope requires one own Profiles overview')
        text = sections[0].text(); kind = 'profiles_own_overview'
        previous_overview = text
        if reviewed_research_group:
            groups = [n for n in nodes if n.attrs.get('id') == RESEARCH_GROUP]
            if (len(groups) != 1 or 'research activities and funding' not in groups[0].text().lower()
                    or 'Description:' not in groups[0].text() or 'Role:' not in groups[0].text()
                    or previous_overview[:1000] != previous_summary):
                raise ValueError('An own funding description requires its complete declared research group and previous overview')
            text = groups[0].text(); kind = 'profiles_own_research_funding_group'
    else:
        if reviewed_research_group:
            raise ValueError('Only a captured personal Profiles resource can supply its own research funding group')
        if host == 'jacobsschool.ucsd.edu':
            subjects = [n.text() for n in nodes if n.tag == 'h3' and 'faculty_profile_name' in n.attrs.get('class', '').split()]
            template = 'jacobs_own_h3'
        elif host == 'datascience.ucsd.edu' and urlsplit(capture['sourceUrl']).path.startswith('/people/'):
            subjects = [n.text() for n in nodes if n.tag == 'h4' and n.parent and 'photo' in n.parent.attrs.get('class', '').split()]
            template = 'hdsi_own_photo_name_h4'
        else:
            subjects = [n.text() for n in nodes if n.tag == 'h1']; template = 'own_h1'
        paragraphs = {n.text() for n in nodes if n.tag == 'p' and n.text()[:1000] == previous_summary}
        if len(paragraphs) != 1:
            raise ValueError('Research scope requires the unchanged complete own paragraph behind the previous excerpt')
        text = next(iter(paragraphs)); kind = 'named_main_own_paragraph'
        previous_paragraph = text
        if reviewed_paragraph is not None:
            published = {n.text() for n in nodes if n.tag == 'p' and n.text() == reviewed_paragraph}
            if len(published) != 1 or reviewed_paragraph == previous_paragraph:
                raise ValueError('A replacement own research paragraph must exist separately on the same named resource')
            text = reviewed_paragraph; kind = 'named_main_reviewed_research_paragraph'
    if (len(subjects) != 1 or reviewed_paragraph is None and not reviewed_research_group and text[:1000] != previous_summary
            or not 90 <= len(text) <= 20000):
        raise ValueError('Research scope requires one own subject and the complete preceding source context')
    result = {'capture': capture, 'kind': kind, 'nameAsDisplayed': subjects[0],
              'subjectTemplate': template, 'fullText': text, 'fullTextSha256': hashlib.sha256(text.encode()).hexdigest()}
    if reviewed_paragraph is not None:
        result['previousExcerptParagraphText'] = previous_paragraph
    if reviewed_research_group:
        result['previousOverviewText'] = previous_overview
        result['researchGroupId'] = RESEARCH_GROUP
    return result


def keyword_scope(item, cache):
    """The explicit own research-keyword property is independent of biography."""
    capture, markup = captured_source(item, cache)
    visited = item['url']
    for hop in item['fetch'].get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Research keywords require their actual continuous redirect chain')
        visited = hop.get('to')
    if item['fetch'].get('httpStatus') != 200 or visited != capture['sourceUrl']:
        raise ValueError('Research keywords require the exact successful resource')
    dom = DOM(markup); nodes = list(dom.main().walk())
    if urlsplit(capture['sourceUrl']).hostname == 'scripps.ucsd.edu':
        subjects = [n.text() for n in nodes if n.tag == 'h1']
        sections = [n for n in every_node(dom.root) if 'views-field-research-topic' in n.attrs.get('class','').split()]
        if (not urlsplit(capture['sourceUrl']).path.startswith('/profiles/') or len(subjects)!=1 or len(sections)!=1):
            raise ValueError('Scripps research topics require their named individual field')
        terms = list(dict.fromkeys(clean(n.text()) for n in every_node(sections[0]) if n.tag=='a' and clean(n.text())))[:30]
        labels = [n.text() for n in every_node(sections[0]) if 'views-label-research-topic' in n.attrs.get('class','').split()]
        if not terms or len(labels)!=1 or labels[0].rstrip(': ') != 'Research Topics':
            raise ValueError('Scripps research values require their literal Research Topics label')
        return {'capture':capture,'nameAsDisplayed':subjects[0],'researchFieldClass':'views-field-research-topic',
                'fieldLabelAsPublished':labels[0],'terms':terms}
    personal, _ = profile_metadata(item, cache)
    sections = [n for n in nodes if n.attrs.get('id') == UCSD_PROFILES_KEYWORDS]
    if len(sections) != 1:
        raise ValueError('Independent research labels require one explicit own keyword property')
    ancestors = []; parent = sections[0].parent
    while parent is not None:
        ancestors.append(parent); parent = parent.parent
    if len([n for n in ancestors if n.attrs.get('id') == RESEARCH_GROUP]) != 1:
        raise ValueError('Independent keywords must belong to the declared own Research group')
    terms = list(dict.fromkeys(clean(n.text()) for n in every_node(sections[0])
                              if n.tag == 'a' and 1 < len(clean(n.text())) <= 80))[:30]
    if not terms:
        raise ValueError('Independent research keywords must contain their actual published values')
    return {'capture': {k:personal[k] for k in ['requestedUrl','sourceUrl','observedAt','bodySha256']},
            'nameAsDisplayed':personal['nameAsDisplayed'],'fieldId':UCSD_PROFILES_KEYWORDS,
            'researchGroupId':RESEARCH_GROUP,'terms':terms}


def payload(row, patterns):
    """Recompute every positive field from its explicit reviewed passages."""
    scope = row['sourceScope']; text = scope['fullText']; passages = row.get('researchPassages')
    claims = row.get('areaClaims'); retained = row.get('retainedDirectoryAreas', [])
    own = row.get('retainedOwnFieldAreas', []); keywords = row.get('retainedKeywordAreas', [])
    if (not isinstance(passages, list) or len(passages) > 12 or len(set(passages)) != len(passages)
            or any(not isinstance(p, str) or not p or p not in text for p in passages)
            or not isinstance(claims, list) or len(claims) > 20
            or any(not isinstance(values, list) or len(values) != len(set(values)) for values in [retained,own,keywords])
            or len(set(retained+own+keywords)) != len(retained+own+keywords)):
        raise ValueError('Research decisions require literal passages from their complete owned source scope')
    summary = ' '.join(passages) if passages else MISSING
    if passages and not 60 <= len(summary) <= 8000:
        raise ValueError('Research summary must retain complete bounded literal research passages')
    if not passages and (claims or row.get('disposition') != 'hold_no_explicit_research_passage_selected'):
        raise ValueError('A source-scoped hold cannot assert positive research topics or global absence')
    if passages and row.get('disposition') != 'reviewed_explicit_own_research_passages':
        raise ValueError('Positive research fields require an explicit semantic scope decision')
    labels = list(retained+own+keywords); by_passage = {}
    for claim in claims:
        if set(claim) != {'label', 'literalPhrase', 'evidencePassage'}:
            raise ValueError('Every research area needs its exact phrase and own research passage')
        label, phrase, passage = [claim[k] for k in ['label', 'literalPhrase', 'evidencePassage']]
        if (not isinstance(label, str) or not 2 <= len(label) <= 160 or not isinstance(phrase, str)
                or not 2 <= len(phrase) <= 160 or passage not in passages
                or not re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', passage)
                or not (label.casefold() == phrase.casefold()
                        or label in patterns and re.fullmatch(patterns[label], phrase, re.I))):
            raise ValueError('A research label must be a literal selected topic or an existing explicit phrase mapping')
        if label in labels:
            raise ValueError('Research labels must be unique across retained and selected claims')
        labels.append(label); by_passage.setdefault(passage, []).append(copy.deepcopy(claim))
    common = {**scope['capture'], 'method': METHOD, 'status': 'verified', 'evidenceType': 'main_text_quote',
              'nameAsDisplayed': scope['nameAsDisplayed'], 'sourceScopeKind': scope['kind'],
              'fullSourceScopeSha256': scope['fullTextSha256']}
    evidence = {}
    if passages:
        evidence['researchSummary'] = [{**common, 'evidence': passage, 'summaryPartIndex': i,
                                        'summaryPassageCount': len(passages)} for i, passage in enumerate(passages)]
    area_proofs = copy.deepcopy(row.get('retainedDirectoryEvidence', []))
    area_proofs.extend(copy.deepcopy(row.get('retainedOwnFieldEvidence', [])))
    if keywords:
        sources = row.get('retainedKeywordSources', [])
        if len(sources) != 1:
            raise ValueError('Retained keyword labels need one separately verified exact keyword capture')
        source = sources[0]
        for label in keywords:
            pattern = patterns.get(label, re.escape(label))
            if not any(re.search(r'(?<!\w)(?:'+pattern+r')(?!\w)', term, re.I) for term in source['terms']):
                raise ValueError('An independent keyword cannot support an unrelated research label')
        area_proofs.append({**source['capture'],'method':'reviewed_declared_own_research_keywords','status':'verified',
                            'evidence':'; '.join(source['terms']),'nameAsDisplayed':source['nameAsDisplayed'],
                            **{k:source[k] for k in ['fieldId','researchGroupId','researchFieldClass','fieldLabelAsPublished'] if k in source},
                            'areaLabels':copy.deepcopy(keywords)})
    for passage, area_claims in by_passage.items():
        area_proofs.append({**common, 'evidence': passage, 'areaClaims': area_claims})
    if area_proofs:
        evidence['researchAreas'] = area_proofs
    return {'researchSummary': summary, 'researchAreas': labels}, evidence


def verified_research_scopes(review, queue, cache, people, routes, patterns, own_field_reviews=()):
    items = {i['url']: i for i in queue['items'].values()}; verified = []; seen = set()
    for raw in review.get('entries', []):
        row = copy.deepcopy(raw); pid = row.get('professorId'); person = people.get(pid)
        previous = row.get('previousFields', {}); dependencies = row.get('previousDependencies', {})
        item = items.get(row.get('sourceScope', {}).get('capture', {}).get('requestedUrl'))
        if (person is None or pid in seen or not row.get('reason') or not row.get('semanticAssessment')
                or row.get('originalPersonIdentity') != {k: person.get(k) for k in ['id', 'name', 'department', 'officialProfileUrl']}
                or set(previous) != set(FIELDS) or set(dependencies) != set(DEPENDENCIES)
                or row.get('previousFieldsSha256') != digest(previous)
                or set(row.get('previousFieldEvidence', {})) != set(FIELDS)
                or set(row.get('previousDependencyEvidence', {})) != set(DEPENDENCIES)
                or not re.fullmatch(r'[0-9a-f]{64}', row.get('sourceCandidateAtlasSha256', ''))
                or item is None or [p['id'] for p in routes.get(url_key(item['url']), [])] != [pid]):
            raise ValueError('Research scope requires an unchanged original identity, unique reviewed source route and previous fields')
        selected_paragraph = (row['sourceScope']['fullText']
                              if row['sourceScope'].get('kind') == 'named_main_reviewed_research_paragraph' else None)
        scope = research_scope(item, cache, previous['researchSummary'], selected_paragraph,
                               row['sourceScope'].get('kind') == 'profiles_own_research_funding_group')
        if (scope != row.get('sourceScope') or not same_named_subject(person['name'], scope['nameAsDisplayed'])
                or row.get('retainedCanonicalIdentity', {}).get('id') != pid
                or row['retainedCanonicalIdentity'].get('name') != person['name']
                or not row['retainedCanonicalIdentity'].get('department')):
            raise ValueError('Research scope must equal the exact named source and actual capture')
        retained = row.get('retainedDirectoryAreas', [])
        directory_proofs = [p for p in row.get('previousFieldEvidence', {}).get('researchAreas', [])
                            if p.get('method') == 'explicit_research_areas_in_official_directory']
        if (any(label not in previous['researchAreas'] or label not in dependencies['researchAreasFromDirectory'] for label in retained)
                or row.get('retainedDirectoryEvidence', []) != (directory_proofs if retained else [])):
            raise ValueError('Independently sourced directory labels must retain their unchanged old field proofs')
        own = row.get('retainedOwnFieldAreas', [])
        reviewed_own = [r for r in own_field_reviews if r.get('captureVerified') and r.get('professorId')==pid
                        and set(own) & set(r.get('fields',{}).get('researchAreas',[]))]
        own_labels = {label for r in reviewed_own for label in r['fields']['researchAreas']}
        own_proofs = []
        for r in reviewed_own:
            for proof in r['fieldEvidence']['researchAreas']:
                if proof not in own_proofs:own_proofs.append(proof)
        if (any(label not in previous['researchAreas'] or label not in own_labels for label in own)
                or row.get('retainedOwnFieldEvidence', []) != own_proofs):
            raise ValueError('Retained own research labels require the separately capture-verified original field review')
        keywords = row.get('retainedKeywordAreas', []); keyword_sources = row.get('retainedKeywordSources', [])
        if not keywords and keyword_sources or keywords and len(keyword_sources)!=1:
            raise ValueError('Independent keyword labels require their own exact source review')
        for source in keyword_sources:
            keyword_item = items.get(source.get('capture',{}).get('requestedUrl'))
            if (keyword_item is None or [p['id'] for p in routes.get(url_key(keyword_item['url']),[])] != [pid]
                    or keyword_scope(keyword_item,cache) != source
                    or not same_named_subject(person['name'],source['nameAsDisplayed'])
                    or source['terms'] != dependencies['researchKeywords']
                    or any(label not in previous['researchAreas'] for label in keywords)):
                raise ValueError('Retained keyword labels must equal the independently owned published research property')
        fields, evidence = payload(row, patterns)
        if row.get('fields') != fields or row.get('fieldEvidence') != evidence:
            raise ValueError('Research fields and proofs must equal the explicit reviewed source passages')
        row['captureVerified'] = True; row['semanticScopeReviewed'] = True
        verified.append(row); seen.add(pid)
    return verified


def preserves_reviewed_research(record):
    for row in record.get('professorResearchScopeReviews', []):
        if (row.get('captureVerified') and row.get('semanticScopeReviewed')
                and all(record.get(f) == row['fields'][f] for f in FIELDS)
                and all(proofs(record, f) == row.get('fieldEvidence', {}).get(f, []) for f in FIELDS)
                and all(record.get(f, []) == row['previousDependencies'][f]
                        and proofs(record, f) == row['previousDependencyEvidence'][f] for f in DEPENDENCIES)):
            return True
    return False


def apply_research_scopes(data, reviews, patterns):
    people = {p['id']: p for p in data['professors']}
    if len({row.get('professorId') for row in reviews}) != len(reviews):
        raise ValueError('Only one research scope decision may apply to a retained person')
    for row in reviews:
        person = people.get(row.get('professorId'))
        if (not row.get('captureVerified') or not row.get('semanticScopeReviewed') or person is None
                or row.get('retainedCanonicalIdentity') != {k: person.get(k) for k in ['id', 'name', 'department', 'officialProfileUrl']}
                or payload(row, patterns) != (row.get('fields'), row.get('fieldEvidence'))):
            raise ValueError('Only exact capture-verified research scope decisions can reach their retained identity')
        if any(person.get(f, []) != row['previousDependencies'][f]
               or proofs(person, f) != row['previousDependencyEvidence'][f] for f in DEPENDENCIES):
            raise ValueError('New keyword/directory evidence requires a new research scope review')
        if preserves_reviewed_research(person) and row in person.get('professorResearchScopeReviews', []):
            continue
        if (any(person.get(f) != row['previousFields'][f] or proofs(person, f) != row['previousFieldEvidence'][f] for f in FIELDS)
                or row['previousFieldsSha256'] != digest(row['previousFields'])):
            raise ValueError('Research scope cannot replace a newer or independently changed field observation')
    for row in reviews:
        person = people[row['professorId']]
        if preserves_reviewed_research(person) and row in person.get('professorResearchScopeReviews', []):
            continue
        for field in FIELDS:
            observation = {'field': field, 'value': copy.deepcopy(person[field]),
                           'fieldEvidence': copy.deepcopy(proofs(person, field)), 'reason': row['reason'],
                           'sourceCandidateAtlasSha256': row['sourceCandidateAtlasSha256'], 'researchScopeReview': True}
            history = person.setdefault('previousFieldObservations', [])
            if observation not in history:
                history.append(observation)
            person[field] = copy.deepcopy(row['fields'][field])
            person.setdefault('fieldEvidence', {}).pop(field, None)
            if row['fieldEvidence'].get(field):
                person['fieldEvidence'][field] = copy.deepcopy(row['fieldEvidence'][field])
        person.setdefault('professorResearchScopeReviews', []).append(copy.deepcopy(row))
        person['sourceUrls'] = list(dict.fromkeys(person.get('sourceUrls', []) + [row['sourceScope']['capture'][k] for k in ['requestedUrl', 'sourceUrl']]))
        person['unverifiedFields'] = [f for f in person.get('unverifiedFields', []) if f not in FIELDS]
        verification = person.setdefault('verification', {})
        verification['fieldsVerified'] = sorted(f for f in person['fieldEvidence'] if f != 'profileLinkIdentityReview')
        dates = [p['observedAt'] for values in person['fieldEvidence'].values()
                 for p in (values if isinstance(values, list) else [values]) if p.get('observedAt')]
        if dates:
            verification['lastEvidenceAt'] = max(dates)
        else:
            verification.pop('lastEvidenceAt', None)
            if verification.get('status') == 'source_checked':
                verification['status'] = 'needs_review' if person.get('unresolvedLabLinks') else 'legacy_unverified'
