"""Read own-profile qualifications and bind dated person observations.

Appointments retain their own scope separately from directory affiliations.
Identity reviews preserve original IDs and primary profile URIs, without
inferring transport equivalence from spelling or coauthor links.
"""
from __future__ import annotations

import copy
import hashlib
import re
import urllib.parse
from pathlib import Path

from atlas_urls import url_key
from collect_ucsd_coverage import profiles_identity_heading, profiles_appointment, safe_url, academic_title_clause
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import identity_name, individual_profile
from refresh_labs import DOM, every_node, person_matches, evidence


def captured_source(item, cache):
    """Read only the exact successful request's immutable saved response."""
    meta = item.get('fetch', {})
    path = Path(cache) / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
    raw = path.read_bytes() if path.is_file() else None
    hosts = [urllib.parse.urlsplit(uri).hostname or '' for uri in [item['url'],meta.get('finalUrl','')]]
    if (meta.get('status') != 'ok' or meta.get('sourceUrl') != item['url']
            or not all(host == 'ucsd.edu' or host.endswith('.ucsd.edu') for host in hosts)
            or not meta.get('observedAt') or raw is None
            or hashlib.sha256(raw).hexdigest() != meta.get('sha256')):
        raise ValueError('Person identity requires its exact successful campus capture')
    return {'requestedUrl':item['url'],'sourceUrl':meta['finalUrl'],'observedAt':meta['observedAt'],
            'bodySha256':meta['sha256']}, raw.decode('utf-8')


def profile_metadata(item, cache):
    """Read a Profiles page's own subject and head metadata."""
    base, markup = captured_source(item, cache)
    if any(urllib.parse.urlsplit(base[k]).hostname != 'profiles.ucsd.edu' for k in ['requestedUrl','sourceUrl']):
        raise ValueError('Person metadata requires its exact successful campus Profiles capture')
    meta = item['fetch']
    dom = DOM(markup)
    name, method = profiles_identity_heading(dom)
    canonical, rdf, declared_canonical, declared_rdf = set(), set(), set(), set()
    for node in every_node(dom.root):
        if node.tag != 'link' or not node.attrs.get('href'):
            continue
        parent = node.parent
        while parent is not None and parent.tag != 'head':
            parent = parent.parent
        if parent is None:
            continue
        href = urllib.parse.urljoin(meta['finalUrl'], node.attrs['href'])
        if node.attrs.get('rel') == 'canonical':
            declared_canonical.add(href)
            parsed = urllib.parse.urlsplit(href)
            # A directory, search page or generic profile endpoint cannot be
            # used as an individual person's canonical identifier.
            if (parsed.hostname == 'profiles.ucsd.edu' and parsed.scheme == 'https'
                    and re.fullmatch(r'/[A-Za-z][A-Za-z0-9._-]*', parsed.path)
                    and parsed.path.lower() not in {'/search','/about','/profile','/display','/login','/error'}
                    and not parsed.query and not parsed.fragment):
                canonical.add(href)
        if node.attrs.get('rel') == 'alternate' and node.attrs.get('type') == 'application/rdf+xml':
            declared_rdf.add(href)
            if re.fullmatch(r'https://researcherprofiles\.org/profile/([0-9]+)/\1\.rdf', href):
                rdf.add(href)
    if (not name or len(canonical) != 1 or len(rdf) != 1
            or declared_canonical != canonical or declared_rdf != rdf):
        raise ValueError('A person binding requires one named subject, canonical URI and personal RDF identifier')
    return {**base,'nameAsDisplayed':name,'nameMethod':method,
            'canonicalUri':next(iter(canonical)),'rdfAlternateUri':next(iter(rdf))}, markup


def jacobs_academic_qualification(item, cache, name):
    """Read the named subject's primary Jacobs appointment, not its biography.

    The qualification retains the complete displayed role and raw unit token.
    It neither maps that token to a department nor changes a roster affiliation.
    Unsupported primary roles/units remain a review limitation.
    """
    try:
        base, markup = captured_source(item, cache)
    except ValueError:
        return None
    requested, final = [urllib.parse.urlsplit(base[k]) for k in ['requestedUrl', 'sourceUrl']]
    hosts = {'jacobsschool.ucsd.edu', 'www.jacobsschool.ucsd.edu'}
    individual_request = (requested.path == '/faculty/profile' and re.fullmatch(r'id=[0-9]+', requested.query)
                          or requested.path == '/faculty/faculty_bios/index.sfe'
                          and re.fullmatch(r'fmp_recid=[0-9]+', requested.query))
    if (requested.hostname not in hosts or final.hostname not in hosts
            or not individual_request
            or final.path != '/faculty/profile'
            or not re.fullmatch(r'id=[0-9]+', final.query)):
        return None
    subjects = [n for n in DOM(markup).main().walk()
                if n.tag == 'h3' and 'faculty_profile_name' in n.attrs.get('class', '').split()]
    if len(subjects) != 1:
        return None
    listed, displayed = identity_name(name).split(), identity_name(subjects[0].text()).split()
    if (min(len(listed), len(displayed)) < 2 or listed[0] != displayed[0] or listed[-1] != displayed[-1]
            or listed[1:-1] and displayed[1:-1] and
            (len(listed[1:-1]) != len(displayed[1:-1]) or
             any(a != b and not (min(len(a), len(b)) == 1 and a[0] == b[0])
                 for a, b in zip(listed[1:-1], displayed[1:-1])))):
        return None
    subject = subjects[0]
    siblings = [n for n in subject.parent.children if hasattr(n, 'tag')]
    following = siblings[siblings.index(subject) + 1:]
    if (len(following) < 2 or following[0].tag != 'p'
            or 'mb-5' not in following[0].attrs.get('class', '').split()
            or following[1].tag != 'hr'):
        return None
    role = following[0].text()
    # These are literal tokens in this template, not inferred UCSD affiliations.
    # Require a primary academic appointment immediately followed by its unit;
    # a later affiliate token cannot qualify an external/industry primary post.
    match = re.match(r'(?:(?:Assistant|Associate|Adjunct|Clinical|Research|Teaching|Distinguished|Emeritus|Visiting)\s+)*'
                     r'Professor(?:\s+Emerit(?:us|a))?(?:\s+and\s+(?:Department\s+)?Chair)?,\s*'
                     r'(BENG|CSE|ECE|MAE|NENG|SE|Pediatrics)(?=\s|,|$)', role, re.I)
    if not match or len(role) > 500:
        return None
    proof = {**evidence(item['fetch'], 'identity_matched_jacobs_primary_appointment', subject.text() + ' | ' + role),
             **base, 'subjectTag': subject.tag, 'subjectClass': subject.attrs.get('class', ''),
             'roleTag': following[0].tag, 'roleClass': following[0].attrs.get('class', '')}
    return {'nameAsDisplayed': subject.text(), 'roleAsListed': role,
            'unitAsListed': match[1], 'evidence': proof,
            'fieldEvidence': {field: proof for field in ['nameAsDisplayed', 'roleAsListed', 'unitAsListed']}}


def own_profile_links(item, cache, name):
    """Read self-labelled contact links on a named individual department page.

    Profiles publication/coauthor lists, navigation, biographies with arbitrary
    person links and generic directories do not establish a self-profile link.
    """
    base, markup = captured_source(item, cache)
    parsed = urllib.parse.urlsplit(base['sourceUrl'])
    if parsed.hostname == 'profiles.ucsd.edu' or not individual_profile(base['sourceUrl']):
        raise ValueError('Own contact links require an individual department page, not a Profiles coauthor page')
    dom = DOM(markup); nodes = list(dom.main().walk())
    jacobs = (parsed.hostname in {'jacobsschool.ucsd.edu','www.jacobsschool.ucsd.edu'}
              and parsed.path == '/faculty/profile' and bool(urllib.parse.parse_qs(parsed.query).get('id')))
    subjects = [n for n in nodes if n.tag == ('h3' if jacobs else 'h1')
                and (not jacobs or 'faculty_profile_name' in n.attrs.get('class','').split())]
    if not subjects or any(not person_matches(identity_name(name), n.text()) for n in subjects):
        raise ValueError('The captured individual page must name only the reviewed subject in its primary person headings')
    subject = min(subjects,key=lambda n:(len(n.text()),n.text()))
    output = []
    for node in nodes:
        if node.tag != 'a' or not node.attrs.get('href') or node.text() not in {'UCSD Profile','UCSD Profiles','Personal Website','Website'}:
            continue
        uri = urllib.parse.urljoin(base['sourceUrl'],node.attrs['href'])
        if urllib.parse.urlsplit(uri).hostname != 'profiles.ucsd.edu':
            continue
        ancestors = []; parent = node.parent
        while parent is not None:
            ancestors.append(parent); parent = parent.parent
        context, kind, heading = None, None, None
        for ancestor in ancestors:
            classes = ancestor.attrs.get('class','').split()
            if (parsed.hostname == 'pharmacology.ucsd.edu'
                    and re.fullmatch(r'/faculty/department-faculty1?/[^/]+\.html', parsed.path)
                    and ancestor.tag == 'div' and 'sidebarContactCallout' in classes
                    and ancestor.parent and 'facultyMeta' in ancestor.parent.attrs.get('class', '').split()
                    and node.text() in {'UCSD Profile', 'UCSD Profiles'}):
                paragraphs = [p for p in ancestor.children if hasattr(p, 'tag') and p.tag == 'p'
                              and node in list(p.walk())]
                preceding = ([p for p in ancestor.children[:ancestor.children.index(paragraphs[0])]
                              if hasattr(p, 'tag')] if len(paragraphs) == 1 else [])
                if (preceding and preceding[-1].tag == 'h4' and preceding[-1].text() == 'Websites'
                        and any(p.tag == 'h4' and p.text() == 'CONTACT' for p in preceding[:-1])):
                    context, kind, heading = ancestor, 'pharmacology_own_contact_websites', 'Websites'; break
            if (parsed.hostname == 'radonc.ucsd.edu' and parsed.path.startswith('/faculty/radiation-oncology/')
                    and ancestor is node.parent and ancestor.tag == 'div' and 'styled' in classes
                    and node.text() in {'UCSD Profile', 'UCSD Profiles'}):
                siblings = [s for s in ancestor.children[:ancestor.children.index(node)] if hasattr(s, 'tag')]
                if siblings and siblings[-1].tag == 'h2' and siblings[-1].text() == 'Links':
                    context, kind, heading = ancestor, 'radonc_own_links_heading', 'Links'; break
            if ancestor.tag == 'p' and 'metaContact' in classes and node.text() in {'UCSD Profile','UCSD Profiles'}:
                context,kind = ancestor,'own_contact_paragraph'; break
            if ancestor.tag == 'ul' and 'profile-contact-list' in classes and node.text() == 'Personal Website':
                context,kind = ancestor,'own_profile_contact_list'; break
            if ancestor.tag == 'div' and 'field--name-field-web-page' in classes and node.text() == 'Website':
                context,kind = ancestor,'own_website_field'; break
            if ancestor.tag == 'p' and ancestor.parent and node.text() in {'UCSD Profile','UCSD Profiles'}:
                siblings = ancestor.parent.children[:ancestor.parent.children.index(ancestor)]
                headings = [s.text() for s in siblings if hasattr(s,'tag') and s.tag in {'h2','h3','h4'}]
                if headings and headings[-1] == 'Links':
                    context,kind,heading = ancestor,'own_related_links','Links'; break
            if jacobs and ancestor.tag == 'div' and {'row','mb-5'} <= set(classes) and node.text() == 'Website':
                owners = [n for n in ancestor.walk() if n.tag == 'h3' and 'faculty_profile_name' in n.attrs.get('class','').split()]
                if len(owners) == 1 and owners[0].text() == subject.text():
                    context,kind = node.parent,'jacobs_own_website_field'; break
        if context is not None:
            output.append({**base,'nameAsDisplayed':subject.text(),'subjectTag':subject.tag,
                'subjectClass':subject.attrs.get('class',''),'rawHref':node.attrs['href'],'linkUrl':uri,
                'linkText':node.text(),'linkContext':{'kind':kind,'tag':context.tag,
                    'class':context.attrs.get('class',''),'text':context.text(),'precedingHeading':heading}})
    return output


def named_roster_profile_links(item, cache, name, original_uri):
    """Read only a primary faculty-card name linking the exact retained URI.

    The complete label/role/date/hash remain separate from the linked person's
    own profile name. Neither name similarity nor a link in a biography earns
    this association; the verifier also requires two own personal identifiers.
    """
    base, markup = captured_source(item, cache)
    parsed = urllib.parse.urlsplit(base['sourceUrl'])
    if parsed.hostname == 'profiles.ucsd.edu' or not re.search(r'/faculty(?:/|$|[-_.])', parsed.path):
        return []
    output = []
    for node in DOM(markup).main().walk():
        if node.tag != 'a' or not node.attrs.get('href') or not node.parent or node.parent.tag != 'h3':
            continue
        label = node.text(); displayed = label.split(',', 1)[0].strip()
        if identity_name(displayed) != identity_name(name) or node.parent.text() != label:
            continue
        uri = safe_url(urllib.parse.urljoin(base['sourceUrl'], node.attrs['href']))
        if not uri or uri != safe_url(original_uri):
            continue
        heading = node.parent; container = heading.parent
        if not container or 'profile-listing-data' not in container.attrs.get('class', '').split():
            continue
        card = container.parent
        if (not card or card.tag != 'li' or 'profile-listing-card' not in card.attrs.get('class', '').split()
                or len([n for n in card.walk() if n.tag == 'h3']) != 1):
            continue
        siblings = [n for n in container.children if hasattr(n, 'tag')]
        following = siblings[siblings.index(heading) + 1:]
        if (not following or following[0].tag not in {'p', 'strong'} or len(following[0].text()) > 300
                or not academic_title_clause(following[0].text())):
            continue
        output.append({**base,'nameAsDisplayed':displayed,'nameLabelAsDisplayed':label,'subjectTag':'h3',
                       'rawHref':node.attrs['href'],'linkUrl':uri,'roleAsListed':following[0].text(),
                       'roleTag':following[0].tag,'cardTag':card.tag,'cardClass':card.attrs.get('class','')})
    return output


def _compatible_published_names(original, profile):
    """Reject unrelated subjects; this is never an identity basis by itself."""
    old, new = identity_name(original).split(), identity_name(profile).split()
    if min(len(old), len(new)) < 2 or min(len(old[0]), len(new[0])) < 2:
        return False
    prefix = 0
    for a, b in zip(old[0], new[0]):
        if a != b:
            break
        prefix += 1
    if old[0] != new[0] and prefix < 5:
        return False
    # Preserve published compound/added surnames without rewriting either name.
    family = ''.join(old[1:])
    return any(family == ''.join(new[start:end])
               for start in range(1, len(new)) for end in range(start + 1, len(new) + 1))


def verified_profile_bindings(review, queue, cache, atlas):
    """Validate the complete explicit batch before returning any row bindings."""
    people = {p['id']:p for p in atlas['professors']}
    items = {item['url']:item for item in queue['items'].values()}
    owners = {}
    for person in people.values():
        owners.setdefault(url_key(person['officialProfileUrl']), set()).add(person['id'])
    by_observation, identifiers, seen = {}, {}, set()
    for raw in review.get('entries', []):
        row = copy.deepcopy(raw)
        person = people.get(row.get('professorId'))
        if (row.get('action') != 'bind_observation_to_existing_person' or not row.get('reason')
                or person is None or row.get('originalProfessorRecordSha256') != record_sha256(person)
                or row.get('originalProfileUri') != person['officialProfileUrl']):
            raise ValueError('A profile binding requires its unchanged explicit original person ID and record')
        proofs = row.get('captures', [])
        kind = row.get('identityBasis',{}).get('type')
        allowed_lengths = {2} if kind == 'shared_canonical_and_personal_rdf' else {3} if kind == 'official_named_roster_original_profile_link' else {2,3}
        if len(proofs) not in allowed_lengths or len({p.get('requestedUrl') for p in proofs}) != len(proofs):
            raise ValueError('A person binding requires distinct actual named source requests')
        actual, markups = [], []
        for index, proof in enumerate(proofs):
            item = items.get(proof.get('requestedUrl'))
            if item is None:
                raise ValueError('Person metadata binding capture is absent from this snapshot')
            if index == 2 and kind == 'official_named_roster_original_profile_link':
                choices = named_roster_profile_links(item,cache,person['name'],person['officialProfileUrl'])
                if proof not in choices:
                    raise ValueError('The reviewed roster link is not the exact named faculty-card primary profile link')
                observed,markup = proof,captured_source(item,cache)[1]
            elif index == 0 and kind == 'official_own_profile_contact_link':
                choices = own_profile_links(item,cache,person['name'])
                if proof not in choices:
                    raise ValueError('The reviewed link is not an actual self-labelled own-profile contact field')
                observed,markup = proof,captured_source(item,cache)[1]
            else:
                observed, markup = profile_metadata(item, cache)
            reviewed_contact_name = (kind == 'official_own_profile_contact_link' and index > 0
                                     and row.get('nameReview')
                                     and _compatible_published_names(person['name'], observed['nameAsDisplayed']))
            if observed != proof or (kind != 'official_named_roster_original_profile_link'
                                     and not person_matches(identity_name(person['name']), observed['nameAsDisplayed'])
                                     and not reviewed_contact_name):
                raise ValueError('Person metadata binding subject, date, declaration or raw bytes changed')
            actual.append(observed); markups.append(markup)
        if actual[0]['requestedUrl'] != safe_url(person['officialProfileUrl']):
            raise ValueError('The original person URI must itself have been requested')
        canonical, rdf = actual[1]['canonicalUri'], actual[1]['rdfAlternateUri']
        if kind == 'shared_canonical_and_personal_rdf':
            if (actual[0]['canonicalUri'] != canonical or actual[0]['rdfAlternateUri'] != rdf
                    or row['identityBasis'] != {'type':kind,'canonicalUri':canonical,'rdfAlternateUri':rdf}):
                raise ValueError('The two own pages must explicitly declare the same canonical and personal RDF identifiers')
        elif kind == 'official_named_roster_original_profile_link':
            roster, original = actual[2], actual[0]
            expected_names = {'rosterNameAsDisplayed':roster['nameAsDisplayed'],
                              'profileNameAsDisplayed':actual[1]['nameAsDisplayed'],
                              'scope':'Separate published display names; no legal-name-change or current-employment claim.'}
            if (roster['requestedUrl'] not in {safe_url(u) for u in person.get('sourceUrls', [])}
                    or roster['linkUrl'] != original['requestedUrl']
                    or original['canonicalUri'] != canonical or original['rdfAlternateUri'] != rdf
                    or identity_name(original['nameAsDisplayed']) != identity_name(actual[1]['nameAsDisplayed'])
                    or not _compatible_published_names(person['name'], actual[1]['nameAsDisplayed'])
                    or row.get('nameReview') != expected_names
                    or row['identityBasis'] != {'type':kind,'canonicalUri':canonical,'rdfAlternateUri':rdf,
                                               'rosterRequestedUri':roster['requestedUrl']}):
                raise ValueError('A named roster binding requires its retained source, exact original link, compatible subjects and shared personal identifiers')
        elif kind == 'official_own_profile_contact_link':
            if row.get('nameReview') is not None:
                expected_names = {'originalNameAsDisplayed':actual[0]['nameAsDisplayed'],
                                  'profileNameAsDisplayed':actual[1]['nameAsDisplayed'],
                                  'scope':'Separate published display names; no legal-name-change or current-employment claim.'}
                if (row['nameReview'] != expected_names
                        or not _compatible_published_names(person['name'], actual[1]['nameAsDisplayed'])
                        or any(identity_name(p['nameAsDisplayed']) != identity_name(actual[1]['nameAsDisplayed'])
                               for p in actual[2:])):
                    raise ValueError('A reviewed own-link name variation requires its exact separately published subjects')
            link_key = url_key(safe_url(actual[0]['linkUrl']))
            if len(actual) == 2:
                linked = link_key in {url_key(actual[1]['requestedUrl']),url_key(actual[1]['sourceUrl'])}
            else:
                linked = (link_key == url_key(actual[2]['requestedUrl'])
                          and actual[2]['canonicalUri'] == canonical and actual[2]['rdfAlternateUri'] == rdf)
                hops = items[actual[2]['requestedUrl']]['fetch'].get('redirects',[])
                visited = actual[2]['requestedUrl']
                for hop in hops:
                    if hop.get('from') != visited or hop.get('httpStatus') not in {301,302,303,307,308}:
                        raise ValueError('The linked resource requires its actual continuous redirect chain')
                    visited = hop.get('to')
                if visited != actual[2]['sourceUrl'] or row.get('linkedTransportRedirects') != hops:
                    raise ValueError('The linked resource requires its actual continuous redirect chain')
            if not linked or row['identityBasis'] != {'type':kind,'linkedProfileUri':actual[0]['linkUrl'],'canonicalUri':canonical,'rdfAlternateUri':rdf}:
                raise ValueError('The actual own-profile link requires its exact captured destination or independently captured shared personal identifiers')
        else:
            raise ValueError('Unknown captured person identity basis')
        if owners.get(url_key(actual[0]['requestedUrl']), set()) != {person['id']} or owners.get(url_key(canonical), {person['id']}) != {person['id']}:
            raise ValueError('Multiple existing IDs own a reviewed profile; a separate person merge is required')
        identifier = (canonical, rdf)
        if identifier in identifiers and identifiers[identifier] != person['id']:
            raise ValueError('Two existing person IDs cannot acquire the same reviewed profile identity')
        identifiers[identifier] = person['id']
        assessment, appointment = profiles_appointment(items[actual[1]['requestedUrl']]['fetch'], markups[1])
        if appointment is None or row.get('qualificationAsListed') != {k:assessment[k] for k in ['nameAsDisplayed','titleAsListed','schoolAsListed']}:
            raise ValueError('The reviewed observation requires its own unchanged explicit faculty appointment table')
        key = (url_key(actual[1]['sourceUrl']), actual[1]['observedAt'], identity_name(actual[1]['nameAsDisplayed']))
        if key in seen:
            raise ValueError('A captured observation must have exactly one explicit person binding')
        seen.add(key)
        row['captureVerified'] = True
        by_observation[key] = row
    return by_observation


def binding_evidence(binding):
    proof = binding['captures'][1]
    return {'sourceUrl':proof['sourceUrl'],'requestedUrl':proof['requestedUrl'],
            'observedAt':proof['observedAt'],'bodySha256':proof['bodySha256'],
            'method':('reviewed_named_roster_original_profile_link_identity' if binding['identityBasis']['type']=='official_named_roster_original_profile_link'
                      else 'reviewed_explicit_own_profile_contact_link_identity' if binding['identityBasis']['type']=='official_own_profile_contact_link'
                      else 'reviewed_shared_canonical_and_personal_rdf_identity'),'evidence':proof['nameAsDisplayed'],
            'status':'verified','profileIdentityBinding':copy.deepcopy(binding)}
