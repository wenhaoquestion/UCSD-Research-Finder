"""Read literal labelled research fields on an unchanged own Materials page.

This personal-field reader neither qualifies faculty nor binds an additional
URI. A lab mentioned inside a personal research summary is not a lab identity,
PI relationship, or institutional appointment claim.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit

from faculty_profile_bindings import captured_source
from faculty_scoped_titles import same_named_subject
from lab_resource_reviews import record_sha256
from lab_identity_merges import verify_capture_proofs
from refresh_labs import DOM, every_node


def classes(node):
    return set(node.attrs.get('class', '').split())


def retained_directory_primary(row, original, faculty, items, cache):
    """Reverify an already selected own URI over an old shared catalog page.

    A preceding canonical snapshot and the current faculty review must select
    the same literal named roster link. This cannot replace an individual
    primary, introduce a profile alias, or merge scientist IDs.
    """
    previous = row.get('previousCompiledProfessorRecord', {})
    identity = row.get('retainedDirectoryPrimaryIdentity', {})
    prior = urlsplit(original['officialProfileUrl'])
    uri = previous.get('officialProfileUrl')
    publisher = 'https://matsci.ucsd.edu/index.php/faculty'
    proof = row.get('publishedOriginalPrimaryEvidence', {})
    if (prior.hostname != 'catalog.ucsd.edu' or prior.query or prior.fragment
            or not re.fullmatch(r'/faculty/[A-Z]+\.html', prior.path)
            or previous.get('id') != original['id'] or previous.get('name') != original['name']
            or row.get('previousCompiledProfessorRecordSha256') != record_sha256(previous)
            or identity != {'type': 'retain_accepted_directory_selected_own_primary',
                            'originalBaselineProfileUri': original['officialProfileUrl'],
                            'retainedPrimaryUri': uri}
            or not isinstance(faculty, dict) or not uri or uri == original['officialProfileUrl']):
        raise ValueError('Materials directory fields require an unchanged accepted primary over a shared catalog source')
    patch = faculty.get('byProfessorId', {}).get(original['id'], {})
    if patch.get('officialProfileUrl') != uri or patch.get('verifiedCanonicalProfile') is not True:
        raise ValueError('Current faculty review must independently retain the same own primary')
    item = items.get(uri)
    if item is None:
        raise ValueError('Retained Materials own primary lacks its actual capture')
    capture, _ = captured_source(item, cache)
    expected_identity = {'sourceUrl': capture['sourceUrl'], 'observedAt': capture['observedAt'],
                         'method': 'explicit_directory_link_to_official_profile_heading',
                         'evidence': original['name'], 'status': 'verified'}
    listings = [r for r in patch.get('directoryListings', [])
                if r.get('sourceUrl') == publisher and r.get('observedAt') == proof.get('observedAt')
                and r.get('name') == original['name'] and r.get('namedLinkUrl') == uri
                and r.get('identityMatchMethod') == 'explicit_directory_link_to_identity_matched_official_profile'
                and r.get('identityEvidence') == expected_identity]
    old_proofs = previous.get('fieldEvidence', {}).get('officialProfileUrl', [])
    if isinstance(old_proofs, dict):
        old_proofs = [old_proofs]
    anchors = [p for p in old_proofs if p.get('sourceUrl') == publisher
               and p.get('observedAt') == proof.get('observedAt') and p.get('status') == 'verified'
               and p.get('method') == 'explicit_individual_profile_link_from_directory'
               and p.get('evidence') == original['name']+' → '+uri]
    if (len(listings) != 1 or len(anchors) != 1 or proof.get('requestedUrl') != publisher
            or proof.get('sourceUrl') != publisher or proof.get('evidenceType') != 'named_link'
            or proof.get('linkText') != original['name'] or proof.get('linkUrl') != uri):
        raise ValueError('Accepted primary and current review must share the exact dated named roster link')
    verify_capture_proofs([proof], {'items': items}, cache, original['id'])
    publisher_capture, markup = captured_source(items[publisher], cache)
    nodes = [n for n in every_node(DOM(markup).main()) if n.tag == 'a'
             and n.text() == original['name'] and n.attrs.get('href') == proof.get('rawHref')
             and urljoin(publisher_capture['sourceUrl'], n.attrs['href']) == uri]
    if len(nodes) != 1:
        raise ValueError('Materials primary requires one unchanged literal named publisher anchor')
    selected = {pid for pid, value in faculty.get('byProfessorId', {}).items()
                if value.get('officialProfileUrl') == uri}
    if selected != {original['id']}:
        raise ValueError('Retained Materials primary must have one reviewed scientist owner')
    return item


def matsci_own_fields(item, cache, name):
    capture, markup = captured_source(item, cache)
    paths = []
    for uri in [capture['requestedUrl'], capture['sourceUrl']]:
        parsed = urlsplit(uri)
        if (parsed.hostname != 'matsci.ucsd.edu' or parsed.query or parsed.fragment
                or not re.fullmatch(r'/(?:index\.php/)?faculty/[a-z0-9-]+/?', parsed.path)):
            raise ValueError('Materials research fields require the exact captured individual faculty resource')
        paths.append(parsed.path.removeprefix('/index.php'))
    visited = capture['requestedUrl']
    for hop in item['fetch'].get('redirects', []):
        if hop.get('from') != visited or hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
            raise ValueError('Materials fields require the actual continuous redirect chain')
        visited = hop.get('to')
    if visited != capture['sourceUrl'] or item['fetch'].get('httpStatus') != 200 or paths[0] != paths[1]:
        raise ValueError('Materials fields require one successful unchanged individual resource')
    dom = DOM(markup); nodes = list(dom.main().walk())
    subjects = [n for n in nodes if n.tag == 'h1']
    titles = [n.text() for n in every_node(dom.root) if n.tag == 'title']
    canonicals = [urljoin(capture['sourceUrl'], n.attrs['href']) for n in every_node(dom.root)
                  if n.tag == 'link' and n.attrs.get('rel') == 'canonical' and n.attrs.get('href')
                  and n.parent and n.parent.tag == 'head']
    if (len(subjects) != 1 or len(titles) != 1 or canonicals != [capture['sourceUrl']]
            or not same_named_subject(name, subjects[0].text())
            or not same_named_subject(subjects[0].text(), titles[0].split('|', 1)[0].strip())):
        raise ValueError('Materials fields require the unchanged complete subject in H1,title and own canonical')
    articles = [n for n in nodes if n.tag == 'article' and 'faculty-listing' in classes(n)
                and n.attrs.get('role') == 'article'
                and n.attrs.get('about', '').removeprefix('/index.php') == paths[1]]
    if len(articles) != 1:
        raise ValueError('Materials research fields require one matching named Drupal faculty article')
    article = articles[0]
    field_nodes = list(article.walk())
    fields, evidence, observations = {}, {}, []
    specifications = [('field--name-field-research-focus', 'Research Focus', 'researchAreas'),
                      ('field--name-field-research-summary', 'Research Summary', 'researchSummary')]
    for class_name, label, field in specifications:
        containers = [n for n in field_nodes if class_name in classes(n)]
        if len(containers) > 1:
            raise ValueError('Conflicting own Materials research fields require review')
        if not containers:
            continue
        container = containers[0]
        children = [n for n in container.children if hasattr(n, 'tag')]
        if (container.tag != 'div' or 'field--label-above' not in classes(container)
                or len(children) != 2 or children[0].tag != 'div' or children[1].tag != 'div'
                or classes(children[0]) != {'field__label'} or children[0].text() != label
                or classes(children[1]) != {'field__item'}
                or any(n is not children[1] and n.tag not in {'p', 'span', 'strong', 'em', 'a', 'br', 'b', 'i'}
                       for n in children[1].walk())):
            raise ValueError('Materials research values must follow their unique direct own field label')
        value = children[1].text()
        if not value or value.lower() in {'unknown', 'not found', 'n/a', 'coming soon'}:
            continue
        if len(value) > 2000:
            raise ValueError('Materials research field exceeds the reviewed plain-text scope')
        if field == 'researchAreas':
            # Semicolons explicitly separate these published phrases. Commas
            # can belong inside a single focus statement and are kept intact.
            values = [part.strip() for part in value.split(';')]
            if any(not part or len(part) > 160 for part in values):
                raise ValueError('Materials focus phrases require complete literal nonempty values')
            selected = list(dict.fromkeys(values))
        else:
            selected = value
        observation = {'fieldClass': class_name, 'labelAsPublished': label, 'valueAsPublished': value,
                       'semicolonSeparated': field == 'researchAreas' and ';' in value}
        observations.append(observation)
        fields[field] = selected
        evidence[field] = [{**capture, 'status': 'verified', 'evidenceType': 'main_text_quote',
            'method': 'named_matsci_own_labelled_research_field',
            'subjectTemplate': 'matsci_drupal_labelled_own_fields', 'nameAsDisplayed': subjects[0].text(),
            'articleAbout': article.attrs['about'], **observation, 'evidence': value}]
    return {'capture': capture, 'sourceTemplate': 'matsci_drupal_labelled_own_fields',
            'nameAsDisplayed': subjects[0].text(), 'documentTitle': titles[0], 'canonicalUri': canonicals[0],
            'articleAbout': article.attrs['about'], 'fieldObservations': observations,
            'fields': fields, 'fieldEvidence': evidence,
            'scope': 'Literal own labelled Research Focus and Research Summary only. Bio,publications,navigation and other people are excluded. No name,primary,identity,rank,unit,lab/PI relationship,or current-HR change.'}
