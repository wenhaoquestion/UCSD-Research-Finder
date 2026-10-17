"""Bind a lab PI's published full name to an unchanged original professor.

The original CSE own Website field and a named Jacobs contact column must
independently point to the same literal personal URI. Its own single heading
supplies the full name; the Jacobs column separately links the named lab.
Neither email-domain equivalence nor a name-only match supplies identity.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urlsplit

from atlas_urls import valid_url
from faculty_profile_bindings import captured_source
from faculty_scoped_titles import same_named_subject
from lab_resource_reviews import record_sha256
from refresh_labs import DOM, links, normalized

KIND = 'named_campus_self_website_and_pi_link_chain'


def cls(node):
    return set(node.attrs.get('class', '').split())


def personal_capture(item, cache):
    meta = item.get('fetch', {})
    path = Path(cache) / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
    if (meta.get('status') != 'ok' or meta.get('sourceUrl') != item['url']
            or not valid_url(item['url']) or not valid_url(meta.get('finalUrl', ''))
            or not meta.get('observedAt') or not path.exists()
            or hashlib.sha256(path.read_bytes()).hexdigest() != meta.get('sha256')):
        raise ValueError('Own-person chain requires its exact successful personal request and bytes')
    return {'requestedUrl': item['url'], 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'],
            'bodySha256': meta['sha256']}, path.read_text()


def observed_chain(person, lab, queue, cache, personal_uri, jacobs_uri, professors):
    """Reconstruct this narrow three-source identifier chain from actual HTML."""
    items = {i['url']: i for i in queue['items'].values()}
    original_uri = person['officialProfileUrl']
    original = items.get(original_uri); personal = items.get(personal_uri); jacobs = items.get(jacobs_uri)
    if (not all([original, personal, jacobs]) or len({original_uri, personal_uri, jacobs_uri}) != 3
            or person.get('personalWebsiteUrl') != personal_uri
            or {p['id'] for p in professors if p.get('personalWebsiteUrl') == personal_uri} != {person['id']}):
        raise ValueError('Own-person chain requires three exact sources and unique original self-website ownership')
    a, html_a = captured_source(original, cache); c, html_c = captured_source(jacobs, cache)
    b, html_b = personal_capture(personal, cache)
    for uri in [a['requestedUrl'], a['sourceUrl']]:
        p = urlsplit(uri)
        if p.hostname != 'cse.ucsd.edu' or not re.fullmatch(r'/people/faculty-profiles/[A-Za-z0-9_.-]+/?', p.path) or p.query or p.fragment:
            raise ValueError('Original chain root must remain the actual individual CSE primary profile')
    for uri in [c['requestedUrl'], c['sourceUrl']]:
        p = urlsplit(uri)
        if p.hostname != 'jacobsschool.ucsd.edu' or p.path != '/faculty/profile' or not p.query.startswith('id=') or not p.query[3:].isdigit() or p.fragment:
            raise ValueError('Corroborating chain source must be the actual named Jacobs individual profile')
    da, db, dc = DOM(html_a).main(), DOM(html_b).main(), DOM(html_c).main()
    ha = [n for n in da.walk() if n.tag == 'h1']
    hb = [n for n in db.walk() if n.tag == 'h1']
    hc = [n for n in dc.walk() if n.tag == 'h3' and 'faculty_profile_name' in cls(n)]
    if (len(ha) != 1 or len(hb) != 1 or len(hc) != 1
            or not same_named_subject(person['name'], ha[0].text())
            or not same_named_subject(person['name'], hb[0].text())
            or not same_named_subject(person['name'], hc[0].text())):
        raise ValueError('Every own chain subject must match the unchanged complete original first/family name')
    own_fields = [n for n in da.walk() if 'field--name-field-web-page' in cls(n)]
    if len(own_fields) != 1:
        raise ValueError('Original profile requires its single own Website field')
    original_links = [(n, label, uri) for n, label, uri in links(own_fields[0], a['sourceUrl'])]
    if len(original_links) != 1 or original_links[0][1:] != ('Website', personal_uri):
        raise ValueError('Original own Website field must literally link the selected personal source')
    columns = [n for n in dc.walk() if 'col-3' in cls(n)]
    candidates = []
    for column in columns:
        direct = [(n, label, uri) for n, label, uri in links(column, c['sourceUrl'])
                  if n.parent is not None and n.parent.tag == 'p' and n.parent.parent is column]
        self_links = [(n, label, uri) for n, label, uri in direct
                      if uri == personal_uri and normalized(label) == normalized(hb[0].text())]
        lab_links = [(n, label, uri) for n, label, uri in direct
                     if uri == lab['labWebsiteUrl'] and label == lab['labName']]
        if len(self_links) == len(lab_links) == 1:
            candidates.append((self_links[0], lab_links[0]))
    if len(candidates) != 1:
        raise ValueError('One named Jacobs own contact column must separately label its personal website and exact named lab')
    def link(row):
        node, label, uri = row
        return {'rawHref': node.attrs['href'], 'linkText': label, 'linkUrl': uri}
    return {'originalProfileCapture': a, 'personalCapture': b, 'jacobsCapture': c,
            'originalNameAsDisplayed': ha[0].text(), 'jacobsNameAsDisplayed': hc[0].text(),
            'fullOwnNameAsDisplayed': hb[0].text(), 'sharedSelfWebsiteUri': personal_uri,
            'originalWebsiteLink': link(original_links[0]), 'jacobsPersonalLink': link(candidates[0][0]),
            'jacobsLabLink': link(candidates[0][1]), 'labId': lab['id'], 'labWebsiteUri': lab['labWebsiteUrl']}


def verify_own_professor_chain(row, person, lab, professors, queue, cache):
    basis = row.get('personIdentityBasis', {})
    if basis.get('type') != KIND:
        return False
    original = basis.get('originalProfessorRecord')
    if original != person or basis.get('originalProfessorRecordSha256') != record_sha256(person):
        raise ValueError('Own-person chain requires the full unchanged original professor snapshot')
    actual = observed_chain(person, lab, queue, cache, basis.get('personalWebsiteRequestUri'),
                            basis.get('jacobsProfileRequestUri'), professors)
    if (basis.get('chain') != actual
            or normalized(row['fields'].get('principalInvestigator', '')) != normalized(actual['fullOwnNameAsDisplayed'])
            or row['fields'].get('principalInvestigatorProfileUrl') != person['officialProfileUrl']):
        raise ValueError('PI name and profile link must equal the actual captured own identity chain')
    for base in [actual['originalProfileCapture'], actual['personalCapture'], actual['jacobsCapture']]:
        if not any(all(proof.get(k) == v for k, v in base.items()) for proof in row.get('personEvidence', [])):
            raise ValueError('Each own chain capture requires its dated proof inside the person evidence')
    return True
