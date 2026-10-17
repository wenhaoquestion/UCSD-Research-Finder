#!/usr/bin/env python3
"""Prepare an offline evidence review from the public collection checkpoint.

This command only writes review artifacts. Publication requires explicit accepted
URL keys in coverage-20261016-decisions.json and a completed eligible queue.
It never infers PI leadership from a lab name, a directory neighbor, or a URL.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import urllib.parse
from collections import Counter
from pathlib import Path

from collect_ucsd_coverage import ROOT, atomic_json, official, url_key, academic_title_clause, profiles_identity_heading
from refresh_labs import DOM, clean, evidence, make_lab, now, normalized, valid_lab_label, person_matches, links, discover_faculty
from refresh_faculty_directories import build_evidence, identity_name, match_existing, profile_identity, text_name, public_email, possible_legacy_initial_alias
from queue_resource_keys import normalize_queue_keys
from faculty_profile_bindings import verified_profile_bindings, binding_evidence, jacobs_academic_qualification
from faculty_scoped_titles import scoped_academic_qualification
from provider_profile_fields import provider_position_qualification
from faculty_own_overviews import own_overview_listing
from candidate_profile_associations import reviewed_new_candidate_sources
from rebuild_verified_atlas import url_key as atlas_url_key


def read(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def body_for(item, cache):
    path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html')
    return path.read_text() if path.exists() and item.get('fetch', {}).get('status') == 'ok' else ''


def lab_identity_name(text):
    text = normalized(text)
    text = re.sub(r'\blaborator(?:y|ies)\b', 'lab', text)
    return re.sub(r'\b(?:the|website|web|site|homepage|home|welcome|to|visit|at|ucsd)\b', '', text).strip()


def homepage_identity_key(url):
    """Flag root/home variants for review, without declaring an entity alias."""
    p = urllib.parse.urlsplit(url)
    path = p.path.rstrip('/')
    if path.endswith('/home'):
        path = path[:-5] or '/'
    return atlas_url_key(urllib.parse.urlunsplit((p.scheme, p.netloc, path, p.query, '')))


def credential_free_name(name):
    # The old comma reader may move suffix degrees to the front of a name.
    # Strip credentials before identity matching; preserve genuine name order.
    degrees = r'Ph\.?D\.?|M\.?D\.?|D\.?O\.?|M\.?P\.?H\.?|M\.?P\.?A\.?|M\.?A\.?|M\.?Sc\.?|M\.?S\.?|MEd|MAS|MMM|MSW|MMSc|MBBS|DSc|ScD|DPhil|EdD|PharmD|MSPH|DMSc|DDS|MBA|FACOG|DABCC\s*\(CC\)|FCSHP|FASHP|FABM|DFASHRM|FRCPSC|FASCO|FACP|ATSF|FACS|FAAD|MRCP|FACC|FAHA|FAAP|Au\.?D\.?|CCC-[A-Z]+|BCS-S|IBCLC'
    name = re.sub(r'(?<![A-Za-z])(?:' + degrees + r')(?![A-Za-z])', '', name)
    name = clean(name.replace(',', ' ').replace('\u200b', ''))
    # A comma inversion can place a degree before the "- PI" label. Remove
    # the role only after credentials, so it cannot become a second identity.
    return re.sub(r'^(?:Dr\.?\s+|[-–—]\s*PI\s+)', '', name)


def department_owner(url, fallback):
    host = (urllib.parse.urlsplit(url).hostname or '').removeprefix('www.')
    for d in read(ROOT / 'data/ucsd/departments.json')['departments']:
        home = (urllib.parse.urlsplit(d['homepage']).hostname or '').removeprefix('www.')
        if host == home and host not in {'biology.ucsd.edu', 'physicalsciences.ucsd.edu'}:
            return d['name']
    return {'biology.ucsd.edu': 'Biological Sciences', 'bmb.ucsd.edu': 'Biochemistry and Molecular Biophysics',
            'cne.ucsd.edu': 'NanoEngineering', 'pulmonary.ucsd.edu': 'Medicine', 'gpm.ucsd.edu': 'Medicine'}.get(host, fallback)


def canonical_department(label):
    def key(value):
        return re.sub(r'[^a-z0-9]+', '', re.sub(r'\band\b', '', value.lower()).replace('&', ''))
    names = [row['name'] for row in read(ROOT / 'data/ucsd/departments.json')['departments'] if key(row['name']) == key(label)]
    return names[0] if len(names) == 1 else label


def preserve_source_department_context(patches, additions, records):
    """Keep unmapped source routing separate from academic affiliations.

    Identity matching and new-record eligibility have already run with the old
    routing values. This step cannot create or accept a professor. Whole old
    listings and the original collected category remain attached as history.
    """
    contexts = {(r['sourceUrl'], r['observedAt'], identity_name(r['name']), r['listedRole']): r
                for r in records if r.get('sourceDepartmentContextOnly')}
    affected, observations = [], []
    for pid, patch in patches.items():
        changed = False
        for listing in patch.get('directoryListings', []):
            key = (listing['sourceUrl'], listing['observedAt'], identity_name(listing['name']), listing['listedRole'])
            row = contexts.get(key)
            if row is None:
                continue
            original = copy.deepcopy(listing)
            listing.update(department='Unknown', sourceDepartmentContext=row['department'],
                           sourceDepartmentContextAsCollected=row['sourceDepartmentContextAsCollected'],
                           departmentMappingStatus='unverified_source_context_only',
                           sourceDepartmentContextReview={
                               'previousListing': original,
                               'reason': 'Generic source routing is not a named academic department. Original person, role, dates, links and observation remain; no absence of other appointments is inferred.'})
            observations.append({'professorId': pid, 'sourceUrl': listing['sourceUrl'],
                                 'observedAt': listing['observedAt'], 'name': listing['name'],
                                 'sourceDepartmentContext': row['department'],
                                 'sourceDepartmentContextAsCollected': row['sourceDepartmentContextAsCollected']})
            changed = True
        if changed:
            remaining = {r['department'] for r in patch['directoryListings']}
            patch['departmentAffiliations'] = [value for value in patch.get('departmentAffiliations', [])
                                               if value != 'Interdisciplinary' or value in remaining]
            affected.append(pid)
    for person in additions:
        patch = patches.get(person['id'])
        if patch:
            person['directoryListings'] = patch['directoryListings']
            person['departmentAffiliations'] = patch['departmentAffiliations']
    return {'professorsAffected': len(affected), 'sourceRowObservations': len(observations),
            'professorIds': affected, 'observations': observations,
            'identityMatchingAndEligibilityUnchanged': True, 'originalListingsRetained': True,
            'scope': 'Unmapped generic source context only; independently stated units, known source owners and preferred main departments are unchanged.'}


def prefer_literal_directory_rows(rows, queue, cache):
    """Prefer hrefs actually present in the same dated saved response.

    Old normalized observations remain whole in the review and listing history;
    transport success or URI spelling alone never earns preference.
    """
    groups, saved, history = {}, {}, []
    for row in rows:
        key = tuple(row.get(k) for k in ['sourceUrl', 'name', 'department', 'listedRole'])
        groups.setdefault(key, []).append(row)
    selected = []
    for candidates in groups.values():
        unique = list({json.dumps(r, sort_keys=True): r for r in candidates}.values())
        if len(unique) == 1:
            selected.append(copy.deepcopy(unique[0]))
            continue
        def score(row):
            uri = row['sourceUrl']
            if uri not in saved:
                item = queue['items'].get(url_key(uri), {})
                meta = item.get('fetch', {})
                raw = body_for(item, cache) if item else ''
                saved[uri] = (meta, {url for _, _, url in links(DOM(raw).main(), meta.get('finalUrl', uri))})
            meta, hrefs = saved[uri]
            if meta.get('status') != 'ok' or meta.get('observedAt') != row.get('observedAt'):
                return 0
            return sum(weight for field, weight in [('profileUrl', 8), ('namedLinkUrl', 8), ('personalWebsiteUrl', 2), ('googleScholarUrl', 1)]
                       if row.get(field) and row[field] in hrefs)
        chosen = max(unique, key=score)
        selected.append(copy.deepcopy(chosen))
        previous = [copy.deepcopy(r) for r in unique if r != chosen]
        if previous:
            meta, _ = saved.get(chosen['sourceUrl'], ({}, set()))
            item = queue['items'].get(url_key(chosen['sourceUrl']), {})
            path = Path(cache) / 'responses' / (hashlib.sha256(item.get('url', '').encode()).hexdigest() + '.html')
            history.append({'selected': copy.deepcopy(chosen), 'previousSourceListingObservations': previous,
                'selectionMethod': 'exact_hrefs_in_same_dated_saved_response' if score(chosen) else 'original_order_no_matching_dated_href_proof',
                'bodySha256': hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
                'observedAt': meta.get('observedAt'), 'sourceObservationsModified': False})
    return selected, history


def prepare(queue, atlas, cache):
    normalize_queue_keys(queue)
    known = {atlas_url_key(u): lab for lab in atlas['labs'] for u in [lab['labWebsiteUrl']] + lab.get('alternateWebsiteUrls', [])}
    known_homes = {}
    for lab in atlas['labs']:
        for u in [lab['labWebsiteUrl']] + lab.get('alternateWebsiteUrls', []):
            known_homes.setdefault(homepage_identity_key(u), set()).add(lab['id'])
    items = queue['items']
    candidates = copy.deepcopy(queue['labCandidates'])
    manual = read(ROOT / 'data/ucsd/coverage-20261016-manual-candidates.json', {'candidates': []})
    for row in manual['candidates']:
        key = url_key(row['url'])
        item = items.get(key)
        if not item or item.get('fetch', {}).get('status') != 'ok':
            continue
        meta = item['fetch']
        text = DOM(body_for(item, cache)).main().text()
        if not official(meta['finalUrl']) or normalized(row['excerpt']) not in normalized(text):
            raise ValueError('Manual candidate quote is not supported by its official capture: ' + key)
        lab = make_lab(row['labName'], meta['finalUrl'], row['department'], meta, row['excerpt'])
        lab['recordSubtype'] = row.get('recordSubtype', 'lab')
        proof = evidence(meta, 'reviewed_official_lab_self_identification', row['excerpt'])
        lab['fieldEvidence'].update(labName=proof, labWebsiteUrl=proof)
        if row.get('departmentExplicitInExcerpt'):
            lab['fieldEvidence']['department'] = proof
        lab['contentDateNote'] = row.get('contentDateNote', '')
        candidates[key] = {'record': lab, 'observations': [{'department': row['department'], 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'], 'label': row['labName'], 'fieldEvidence': lab['fieldEvidence'], 'professorIds': []}]}
    # Named official lab homepages can establish their own identity without a PI.
    for key, item in items.items():
        is_link_candidate = any(c['kind'] == 'lab_link_candidate' for c in item['contexts'])
        if key in candidates or (not official(item.get('fetch', {}).get('finalUrl', item['url'])) and not is_link_candidate):
            continue
        contexts = [c for c in item['contexts'] if c['kind'] in {'unresolved_candidate', 'lab_destination', 'discovered_lab', 'lab_link_candidate'}]
        if not contexts or item.get('fetch', {}).get('status') != 'ok':
            continue
        markup = body_for(item, cache)
        dom = DOM(markup)
        choices = [n.text() for n in dom.main().walk() if n.tag in {'h1', 'h2'} and valid_lab_label(n.text()) and len(n.text()) < 110]
        if not choices:
            continue
        name = choices[0]
        if re.search(r'centers?|institutes?|labs? and|labs? &|research labs|group meetings|lab members', name, re.I):
            continue
        lab = make_lab(name, item['fetch']['finalUrl'], contexts[0]['department'], item['fetch'], name)
        if item.get('discoveryEvidence'):
            lab['fieldEvidence']['labName'] = [lab['fieldEvidence']['labName']] + item['discoveryEvidence']
            lab['fieldEvidence']['labWebsiteUrl'] = item['discoveryEvidence']
        candidates[key] = {'record': lab, 'observations': [{'department': lab['department'], 'sourceUrl': lab['labWebsiteUrl'], 'observedAt': item['fetch']['observedAt'], 'label': name, 'fieldEvidence': lab['fieldEvidence'], 'professorIds': []}], 'state': 'needs_identity_review'}
    proposals = []
    for key, candidate in candidates.items():
        lab = copy.deepcopy(candidate['record'])
        dest = items.get(key)
        meta = dest.get('fetch', {}) if dest else {}
        final = url_key(meta.get('finalUrl', lab['labWebsiteUrl']))
        old = known.get(atlas_url_key(key)) or known.get(atlas_url_key(final))
        markup = body_for(dest, cache) if dest else ''
        dom = DOM(markup)
        main = dom.main().text()
        name = lab['labName']
        identity = lab_identity_name(name)
        visible = lab_identity_name(main[:10000])
        h = [n.text() for n in dom.main().walk() if n.tag in {'h1', 'h2', 'h3'} and len(n.text()) < 200]
        title = next((n.text() for n in dom.root.walk() if n.tag == 'title'), '')
        reasons = []
        if dest and dest['state'] == 'scope_excluded':
            status = 'scope_excluded'
            reasons.append(dest['scopeAssessment']['reason'])
        elif old:
            status = 'existing_url_or_redirect'
        else:
            if meta.get('status') != 'ok':
                reasons.append('destination_' + meta.get('status', 'not_checked'))
            if not valid_lab_label(name) or re.search(r'^https?://|\bcenters?|institutes?|facilities|^lab web$|research laboratories and', name, re.I):
                reasons.append('non_specific_or_non_lab_label')
            if re.search(r'^(?:for lab|lab (?:members|photos|staff|contact|life|seminars)|open lab positions|current lab|former lab|group news|more group|need a website|large group|read more|more about)|celebration|mailing list|lunch group|^all hands on deck', name, re.I) or re.search(r'/(?:news|events|images|story)/|lab[_-]members|labphotos|groupnews|/alumni\.', lab['labWebsiteUrl'], re.I):
                reasons.append('subpage_or_non_entity_link')
            if not identity or not any(len(x) >= 3 and x not in {'lab', 'group', 'research'} for x in identity.split()) or identity not in visible:
                reasons.append('destination_does_not_confirm_link_label')
            if re.search(r'apache2.{0,80}default page|index of /|domain.{0,40}for sale', title + ' ' + main[:700], re.I):
                reasons.append('default_or_parked_page')
            if not official(meta.get('finalUrl', lab['labWebsiteUrl'])) and not re.search(r'UC\s*San\s*Diego|University of California.{0,12}San Diego|\bUCSD\b', main, re.I):
                reasons.append('ucsd_affiliation_not_confirmed_on_destination')
            if 'external_institution' == lab.get('relationshipScope'):
                reasons.append('other_institution_relationship')
            status = 'reviewable_identity_match' if not reasons else 'unresolved'
        if meta.get('status') == 'ok':
            lab['destinationEvidence'] = {'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'], 'title': title, 'headings': h[:8], 'evidence': clean(main)[:1200], 'sha256': meta.get('sha256')}
        same_website = sorted(known_homes.get(homepage_identity_key(final), set()) | known_homes.get(homepage_identity_key(key), set())) if not old else []
        possible_aliases = sorted(set([l['id'] for l in atlas['labs'] if lab_identity_name(l['labName']) == lab_identity_name(name)] + same_website)) if not old else []
        if possible_aliases and status == 'reviewable_identity_match':
            status = 'possible_alias_requires_review'
        proposals.append({'urlKey': key, 'status': status, 'reasons': reasons, 'existingLabId': old['id'] if old else None, 'possibleAliasExistingLabIds': possible_aliases,
                          'sameNameExistingLabIds': [l['id'] for l in atlas['labs'] if not old and lab_identity_name(l['labName']) == lab_identity_name(name)],
                          'sameWebsiteExistingLabIds': same_website,
                          'urlDedupIsIdentityConfirmation': False,
                          'record': lab, 'observations': candidate['observations'], 'destinationCheck': meta})
    return proposals


def source_listing_counts(rows):
    """Count distinct normalized names per source without rescanning all rows."""
    names_by_source = {}
    for row in rows:
        source = url_key(row['sourceUrl'])
        names_by_source.setdefault(source, set()).add(identity_name(row['name']))
    return {source: len(names) for source, names in names_by_source.items()}


def faculty_review(queue, atlas, cache, profile_identity_review=None):
    normalize_queue_keys(queue)
    # Multiple existing full-name identities require review, never arbitrary sorting.
    names = {}
    surnames = {}
    for p in atlas['professors']:
        names.setdefault(identity_name(p['name']), []).append(p)
        bits = identity_name(p['name']).split()
        if bits:
            surnames.setdefault(bits[-1], []).append(p)
    records, ambiguous = [], []
    source_rows = list(queue['facultyListings'])
    class CachedDirectory:
        def __init__(self, selected):
            self.selected = selected
        def fetch(self, url):
            item = queue['items'].get(url_key(url)) if url == self.selected else None
            return (item['fetch'], body_for(item, cache)) if item and item.get('fetch') else ({'sourceUrl': url, 'status': 'not_captured'}, '')
    for directory in ['https://cse.ucsd.edu/people/faculty-profiles', 'https://datascience.ucsd.edu/faculty/', 'https://cogsci.ucsd.edu/people/faculty/index.html', 'https://psychology.ucsd.edu/people/profiles/faculty/index.html']:
        _, _, memberships = discover_faculty(CachedDirectory(directory), atlas['professors'])
        for listing in memberships.values():
            proof, section = listing['evidence'], listing['directorySection']
            left, profile = proof['evidence'].rsplit(' → ', 1)
            name = left[len(section) + 2:]
            source_rows.append({'name': name, 'department': department_owner(proof['sourceUrl'], 'Interdisciplinary'),
                'listedRole': 'Faculty directory listing', 'appointmentStatus': {'former': 'former', 'emeritus': 'emeritus', 'deceased': 'deceased'}.get(listing['facultyStatus'], 'listed_faculty'),
                'directorySection': section, 'sourceUrl': proof['sourceUrl'], 'observedAt': proof['observedAt'], 'evidence': proof,
                'profileUrl': profile, 'namedLinkUrl': profile, 'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': [], 'explicitFacultyRosterLink': True})
    # Materials Science publishes explicit name/title/department triples using
    # h5/strong/i instead of the campus profile-card template. Reparse the saved
    # public response without consuming another request or changing its date.
    mats = queue['items'].get(url_key('https://matsci.ucsd.edu/index.php/faculty'))
    if mats and mats.get('fetch', {}).get('status') == 'ok':
        meta = mats['fetch']
        for node in DOM(body_for(mats, cache)).main().walk():
            if node.tag != 'h5' or not node.parent:
                continue
            card = node.parent
            role = next((n.text() for n in card.walk() if n.tag == 'strong'), '')
            department = next((n.text() for n in card.walk() if n.tag == 'i'), '')
            profile = next((u for _, _, u in links(node, meta['finalUrl'])), '')
            if not role or not department or not profile:
                continue
            proof = evidence(meta, 'official_materials_faculty_name_title_department_card', card.text())
            source_rows.append({'name': node.text(), 'department': department, 'departmentExplicitlyListed': True,
                'listedRole': role, 'appointmentStatus': 'emeritus' if 'emerit' in role.lower() else 'listed_faculty',
                'directorySection': 'Materials Science affiliated faculty', 'sourceUrl': meta['finalUrl'], 'observedAt': meta['observedAt'],
                'evidence': proof, 'profileUrl': profile, 'namedLinkUrl': profile, 'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': []})
    for item in queue['items'].values():
        meta=item.get('fetch',{})
        if (meta.get('status')=='ok' and urllib.parse.urlsplit(meta.get('finalUrl','')).hostname=='profiles.ucsd.edu'
                and item.get('profileEligibility',{}).get('status') in {None,'missing_identity_or_appointment_table'}):
            listing=own_overview_listing(item,cache)
            if listing:source_rows.append(listing)
    raw_source_row_count = len(source_rows)
    source_rows, listing_history = prefer_literal_directory_rows(source_rows, queue, cache)
    seen = set()
    profile_headers = {}
    discovery_peers = {}
    for row in source_rows:
        if row.get('profileDiscovery'):
            discovery_peers.setdefault((identity_name(row['name']), row['department']), set()).add(profile_identity(row['profileUrl']))
    identity_review = read(ROOT / 'data/ucsd/faculty-identity-review-20261016.json', {'aliases': [], 'holdbacks': []})
    profile_bindings = verified_profile_bindings(
        profile_identity_review if profile_identity_review is not None else
        read(ROOT / 'data/ucsd/faculty-profile-identity-review-20261016.json', {'entries': []}), queue, cache, atlas)
    source_holds = [hold for hold in identity_review.get('holdbacks', []) if hold.get('sourceScoped')]
    for raw in source_rows:
        row = copy.deepcopy(raw)
        row['name'] = credential_free_name(row['name'])
        row['email'] = public_email(row.get('email', ''))
        if not row.get('departmentExplicitlyListed') and not row.get('profileDiscovery'):
            owner = department_owner(row['sourceUrl'], None)
            if owner in {None, 'Interdisciplinary'}:
                row['sourceDepartmentContextOnly'] = True
                row['sourceDepartmentContextAsCollected'] = row['department']
            row['department'] = owner or 'Interdisciplinary'
        department = canonical_department(row['department'])
        if department != row['department']:
            row['departmentAsListed'], row['department'] = row['department'], department
        hold = next((h for h in source_holds if h.get('listedName') == row['name'] and url_key(h.get('sourceUrl', '')) == url_key(row['sourceUrl'])), None)
        if hold:
            item = queue['items'].get(url_key(row['sourceUrl']))
            path = cache / 'responses' / (hashlib.sha256(item['url'].encode()).hexdigest() + '.html') if item else None
            captured = (item and item.get('fetch', {}).get('observedAt') == hold.get('observedAt') and path.exists()
                        and hashlib.sha256(path.read_bytes()).hexdigest() == hold.get('bodySha256')
                        and hold.get('sourceExcerpt') in DOM(body_for(item, cache)).main().text())
            ambiguous.append({'listing': row, 'reason': hold['reason'] if captured else 'source_scoped_identity_review_capture_changed_requires_review', 'identityReview': hold})
            continue
        profile_key = url_key(row.get('profileUrl', ''))
        if profile_key not in profile_headers:
            item = queue['items'].get(profile_key)
            if item and item.get('fetch', {}).get('status') == 'ok' and official(item['fetch']['finalUrl']):
                profile_dom = DOM(body_for(item, cache))
                is_profiles = urllib.parse.urlsplit(item['fetch']['finalUrl']).hostname == 'profiles.ucsd.edu'
                profile_name, _ = profiles_identity_heading(profile_dom) if is_profiles else ('', '')
                headings = [profile_name] if profile_name else [n.text() for n in profile_dom.main().walk() if n.tag == 'h1' and len(n.text()) < 180]
                contact = profile_dom.main().text()
                if is_profiles:
                    contact = ' '.join(node.text() for node in profile_dom.main().walk() if node.tag == 'tr' and any(c.tag == 'th' and c.text() == 'Email' for c in node.children if hasattr(c, 'tag')))
                emails = list(set(re.findall(r'[\w.+%-]+@(?:[\w-]+\.)*ucsd\.edu', contact)))
                emails = [e for e in emails if e.split('@')[0].lower() not in {'info', 'webmaster', 'support', 'ctri-support', 'advising'}]
                profile_headers[profile_key] = (item['fetch'], headings, emails)
            else:
                profile_headers[profile_key] = (None, [], [])
        meta, headings, emails = profile_headers[profile_key]
        correction = next((c for c in identity_review.get('nameCorrections', []) if c['listedName'] == row['name'] and url_key(c['sourceUrl']) == url_key(row['sourceUrl']) and profile_identity(c['profileUrl']) == profile_identity(row['profileUrl'])), None)
        if correction:
            valid = meta and correction['canonicalName'] in headings
            for proof in correction['captures']:
                item = next((x for x in queue['items'].values() if x['url'] == proof['requestedUrl']), None)
                path = cache / 'responses' / (hashlib.sha256(proof['requestedUrl'].encode()).hexdigest() + '.html')
                valid = (valid and item and item.get('fetch', {}).get('observedAt') == proof['observedAt'] and item.get('fetch', {}).get('finalUrl') == proof['sourceUrl']
                         and path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == proof['bodySha256']
                         and proof['evidence'] in DOM(body_for(item, cache)).main().text())
                if proof['requestedUrl'] == row['sourceUrl'] and item:
                    valid = valid and any(profile_identity(url) == profile_identity(correction['profileUrl']) and credential_free_name(text_name(label)) == row['name']
                                          for _, label, url in links(DOM(body_for(item, cache)).main(), item['fetch']['finalUrl']))
            if not valid:
                ambiguous.append({'listing': row, 'reason': 'reviewed_name_correction_capture_changed_requires_review', 'identityReview': correction})
                continue
            row['nameAsListed'], row['name'] = row['name'], correction['canonicalName']
            row['nameEvidence'] = evidence(meta, 'reviewed_exact_linked_profile_heading_display_name', row['name'])
        if not row.get('email') and len(emails) == 1 and any(person_matches(row['name'], h) for h in headings):
            row['email'] = emails[0]
            row['contactEvidence'] = {'email': evidence(meta, 'identity_matched_official_profile_professional_contact', row['name'] + ' | ' + emails[0])}
        bits = identity_name(row['name']).split()
        matches = [p for p in surnames.get(bits[-1] if bits else '', []) if len(identity_name(p['name']).split()[0]) > 1 and any(person_matches(identity_name(p['name']), h) for h in headings)]
        local = [p for p in matches if p['department'] == row['department']]
        matched = local[0] if len(local) == 1 else matches[0] if len(matches) == 1 else None
        if matched and row.get('profileDiscovery'):
            strong = profile_identity(matched['officialProfileUrl']) == profile_identity(row['profileUrl']) or (row.get('email') and row['email'].lower() == matched.get('email', '').lower()) or ('catalog.ucsd.edu' in matched['officialProfileUrl'] and matched['department'] == row['department'])
            if not strong:
                matched = None
        if matched:
            heading = next(h for h in headings if person_matches(identity_name(matched['name']), h))
            row['identityProfessorId'] = matched['id']
            row['identityEvidence'] = evidence(meta, 'explicit_directory_link_to_official_profile_heading', heading)
            previous = queue['items'].get(url_key(matched['officialProfileUrl']), {}).get('fetch', {})
            if previous.get('httpStatus') in {404, 410} or 'catalog.ucsd.edu' == urllib.parse.urlsplit(matched['officialProfileUrl']).hostname:
                row['verifiedCanonicalProfileUrl'] = meta['finalUrl']
        binding = profile_bindings.get((url_key(row['sourceUrl']), row['observedAt'], identity_name(row['name']))) if row.get('profileDiscovery') else None
        if binding:
            row['identityProfessorId'] = binding['professorId']
            row['identityEvidence'] = binding_evidence(binding)
            row['identityMatchMethod'] = 'reviewed_captured_person_identifiers'
        for alias in identity_review.get('aliases', []):
            if row['name'] != alias['listedName'] or row.get('email', '').lower() != alias['sharedEmail'].lower():
                continue
            target = next((p for p in atlas['professors'] if p['id'] == alias['professorId']), None)
            receipt = queue['items'].get(url_key(alias['sourceUrl']))
            text = DOM(body_for(receipt, cache)).main().text() if receipt else ''
            if not target or normalized(alias['excerpt']) not in normalized(text) or not person_matches(identity_name(target['name']), alias['excerpt']):
                continue
            proof = evidence(receipt['fetch'], 'reviewed_full_name_and_shared_professional_contact_identity', alias['excerpt'])
            row['identityProfessorId'], row['identityEvidence'] = target['id'], proof
            row['identityMatchMethod'] = 'reviewed_official_full_name_and_shared_professional_contact'
            if meta and any(person_matches(row['name'], h) for h in headings):
                row['verifiedCanonicalProfileUrl'] = meta['finalUrl']
                row['canonicalProfileEvidence'] = [proof, evidence(meta, 'linked_official_profile_heading_identity', row['name'] + ' | ' + row['email'])]
        key = (row['sourceUrl'], row['name'], row['department'], row['listedRole'])
        if key in seen:
            continue
        seen.add(key)
        established_member = row.get('explicitFacultyRosterLink') and match_existing(row, atlas['professors'])[0] is not None
        if not academic_title_clause(row['listedRole']) and row['appointmentStatus'] not in {'deceased', 'emeritus'} and not established_member:
            # Faculty pages can include NPs, audiologists, and administrative staff.
            profile = queue['items'].get(url_key(row['profileUrl']))
            qualification = (jacobs_academic_qualification(profile, cache, row['name'])
                             or scoped_academic_qualification(profile, cache, row['name'])
                             or provider_position_qualification(profile, cache, row['name'])) if profile else None
            jacobs_uris = [urllib.parse.urlsplit(uri) for uri in
                           [row['profileUrl'], profile.get('fetch', {}).get('finalUrl', '') if profile else '']]
            jacobs_profile = any(uri.hostname in {'jacobsschool.ucsd.edu', 'www.jacobsschool.ucsd.edu'}
                                 and uri.path in {'/faculty/profile', '/faculty/faculty_bios/index.sfe'}
                                 for uri in jacobs_uris)
            markup = body_for(profile, cache) if profile else ''
            dom = DOM(markup)
            headings = [n.text() for n in dom.root.walk() if n.tag in {'h1', 'title'}]
            academic = None
            for node in dom.main().walk():
                if node.tag in {'td', 'dd', 'h2', 'h3', 'p'} and len(node.text()) < 200:
                    academic = re.match(r'(?:(?:Assistant|Associate|Adjunct|Clinical|Research|Teaching|Distinguished|Emeritus|Visiting)\s+)*(?:Professor|Lecturer)(?:\s+Emerit(?:us|a))?(?=\s*(?:[,(/]|of\b|in\b|at\b|$))', node.text(), re.I)
                    if academic:
                        break
            if qualification:
                row['academicQualification'] = qualification
            elif not jacobs_profile and academic and any(person_matches(row['name'], h) for h in headings):
                row['listedRole'] = academic[0]
                row['evidence'] = evidence(profile['fetch'], 'identity_matched_official_profile_academic_title', row['name'] + ' | ' + academic[0])
            else:
                ambiguous.append({'listing': row, 'reason': 'explicit_academic_title_not_observed'})
                continue
        # Qualification and person identity are separate checks, regardless
        # of whether the title came from Profiles, a roster or an own field.
        candidate, match_method = match_existing(row, atlas['professors'])
        if candidate and 'legacy_initials' in match_method:
            ambiguous.append({'listing': row,
                              'reason': 'qualified_title_legacy_initial_alias_requires_identity_review',
                              'candidateProfessorIds': [candidate['id']],
                              'scope': 'An explicit faculty observation qualifies the named source only. Same-unit initials are an identity-review lead, not evidence to expand an original name or replace its primary URI.'})
            continue
        matches = names.get(identity_name(row['name']), [])
        same_department = [p for p in matches if p['department'] == row['department']]
        if row.get('profileDiscovery'):
            proposed, method = match_existing(row, atlas['professors'])
            strong = method in {'same_individual_profile', 'same_public_professional_email', 'explicit_directory_link_to_identity_matched_official_profile', 'reviewed_official_full_name_and_shared_professional_contact', 'reviewed_captured_person_identifiers'}
            catalog_upgrade = proposed and 'catalog.ucsd.edu' in proposed['officialProfileUrl'] and proposed['department'] == row['department']
            if (proposed and not strong and not catalog_upgrade) or (not proposed and len(discovery_peers.get((identity_name(raw['name']), raw['department']), set())) > 1):
                ambiguous.append({'listing': row, 'reason': 'distinct_profile_same_or_similar_name_requires_identity_review', 'candidateProfessorIds': [proposed['id']] if proposed else []})
                continue
        if len(matches) > 1 and len(same_department) != 1 and not row.get('identityProfessorId'):
            ambiguous.append({'listing': row, 'reason': 'multiple_existing_full_name_identities', 'candidateProfessorIds': [p['id'] for p in matches]})
        else:
            records.append(row)
    records.sort(key=lambda row: row['department'] == 'Interdisciplinary')
    observed_aliases = {}
    for row in records:
        if not row.get('profileDiscovery'):
            person, _ = match_existing(row, atlas['professors'], records)
            if person:
                observed_aliases.setdefault((identity_name(row['name']), row['department']), set()).add(person['id'])
    filtered = []
    for row in records:
        if row.get('profileDiscovery') and not row.get('identityProfessorId') and (identity_name(row['name']), row['department']) in observed_aliases:
            person, method = match_existing(row, atlas['professors'], records)
            if person is None:
                ambiguous.append({'listing': row, 'reason': 'known_directory_name_alias_requires_profile_identifier', 'candidateProfessorIds': sorted(observed_aliases[(identity_name(row['name']), row['department'])])})
                continue
        filtered.append(row)
    records = filtered
    primary_reviews = read(ROOT / 'data/ucsd/faculty-candidate-primary-root-review-20261016.json', {'entries': []})
    captured_uris = {item['url'] for item in queue['items'].values()}
    # Global source-specific reviews do not apply to unrelated partial source
    # snapshots. If either reviewed resource is present, require the complete
    # qualified root and both captures rather than silently ignoring a failure.
    applicable_roots = [entry for entry in primary_reviews.get('entries', [])
                        if entry.get('originalProfessorRecord', {}).get('officialProfileUrl') in captured_uris
                        or entry.get('sourceObservation', {}).get('rosterCapture', {}).get('requestedUrl') in captured_uris]
    additions, patches, uncertain, new_source_associations = reviewed_new_candidate_sources(
        records, atlas['professors'], queue, cache, {'entries': applicable_roots})
    for patch in patches.values():
        for listing in patch.get('directoryListings', []):
            prior = [entry for entry in listing_history if entry['selected']['sourceUrl'] == listing['sourceUrl']
                     and identity_name(credential_free_name(entry['selected']['name'])) == identity_name(listing['name'])
                     and entry['selected']['observedAt'] == listing['observedAt']]
            if prior:
                listing['sourceListingSelectionHistory'] = copy.deepcopy(prior)
    # Campus centers and graduate programs also list faculty from partner
    # institutions. Their participation alone does not establish a UCSD post.
    holdbacks = {x['proposedProfessorId']: x for x in identity_review.get('holdbacks', []) if not x.get('sourceScoped')}
    cross_department_initials = {}
    for person in additions:
        if person['department'] in {'Unknown', 'Interdisciplinary'}:
            continue
        candidates = [old['id'] for old in atlas['professors']
                      if old['department'] != person['department'] and possible_legacy_initial_alias(person['name'], old)]
        if candidates:
            observations = [r for r in records if identity_name(r['name']) == identity_name(person['name'])
                            and profile_identity(r.get('profileUrl', '')) == profile_identity(person['officialProfileUrl'])]
            cross_department_initials[person['id']] = {
                'listing': copy.deepcopy(next((r for r in observations if r.get('profileDiscovery')), observations[0])),
                'reason': 'cross_department_legacy_initials_requires_identity_review',
                'candidateProfessorIds': candidates, 'provisionalRecordSnapshot': copy.deepcopy(person),
                'scope': 'Complete name and an initial-only original in another department are an alias-review lead only; retain the qualified observation without creating a duplicate or inferring identity/absence from the unit difference.'}
    unsupported = {p['id'] for p in additions if p['department'] == 'Interdisciplinary' or p['id'] in holdbacks or p['id'] in cross_department_initials}
    for p in additions:
        if p['id'] in unsupported:
            ambiguous.append(cross_department_initials[p['id']] if p['id'] in cross_department_initials else
                             {'listing': p, 'reason': holdbacks[p['id']]['reason'] if p['id'] in holdbacks else 'ucsd_department_appointment_not_established_by_program_or_center_listing', 'identityReview': holdbacks.get(p['id'])})
    additions = [p for p in additions if p['id'] not in unsupported]
    for pid in unsupported:
        patches.pop(pid, None)
    context_review = preserve_source_department_context(patches, additions, records)
    return {'professors': additions, 'byProfessorId': patches, 'uncertainListings': ambiguous + uncertain,
            'newCandidateSourceAssociationReview': new_source_associations,
            'sourceDepartmentContextReview': context_review,
            'sourceListingSelectionHistory': listing_history,
            'sourceListingCounts': source_listing_counts(source_rows),
            'coverage': {'rawCards': len(source_rows), 'rawSourceRowObservations': raw_source_row_count,
                         'supersededSourceRowObservations': sum(len(e['previousSourceListingObservations']) for e in listing_history),
                         'newProfessorCount': len(additions), 'professorsWithDirectoryEvidence': len(patches), 'uncertainListings': len(ambiguous + uncertain)}}


def source_coverage(queue, faculty_counts=None):
    normalize_queue_keys(queue)
    faculty, labs, centers = Counter(), Counter(), Counter()
    for row in queue['facultyListings']:
        faculty[url_key(row['sourceUrl'])] += 1
    if faculty_counts:
        faculty = Counter(faculty_counts)
    for candidate in queue['labCandidates'].values():
        for observation in candidate['observations']:
            labs[url_key(observation['sourceUrl'])] += 1
    for entity in queue['centers'].values():
        for observation in entity['observations']:
            centers[url_key(observation['evidence']['sourceUrl'])] += 1
    sources = []
    for item in queue['items'].values():
        if not any(c['kind'] in {'department', 'directory', 'faculty_directory', 'institute_directory'} for c in item['contexts']):
            continue
        meta = item.get('fetch', {})
        final = url_key(meta.get('finalUrl', item['url']))
        counts = {'facultyCards': faculty[final], 'labLinkObservations': labs[final], 'centerLinkObservations': centers[final]}
        sources.append({'sourceUrl': item['url'], 'finalUrl': meta.get('finalUrl'), 'observedAt': meta.get('observedAt'),
            'fetchStatus': meta.get('status', item['state']), 'title': item.get('page', {}).get('title'),
            'departmentContexts': sorted({c['department'] for c in item['contexts']}),
            'sourceDepartment': department_owner(item['url'], 'Interdisciplinary'), 'counts': counts,
            'contentReviewStatus': 'explicit_records_extracted' if any(counts.values()) else 'discovery_only_or_no_supported_records_extracted'})
        if item.get('structuredProfileDiscovery'):
            sources[-1]['personMetadataDiscovery'] = item['structuredProfileDiscovery']
    return sources


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--cache', type=Path, default=ROOT / '.cache/coverage-20261016')
    args = cli.parse_args()
    q = read(args.cache / 'queue.json')
    atlas = read(ROOT / 'data/research-atlas.json')
    proposals = prepare(q, atlas, args.cache)
    faculty = faculty_review(q, atlas, args.cache)
    report = {'schemaVersion': 1, 'generatedAt': now(), 'queueStates': q['counts'],
              'labReviewStatuses': dict(Counter(x['status'] for x in proposals)), 'labs': proposals,
              'faculty': faculty, 'centersAndInstitutes': list(q['centers'].values()),
              'sourceCoverage': source_coverage(q, faculty['sourceListingCounts']),
              'policy': 'Review artifact only. No PI inference; shared directories, failed pages, alias ambiguity and unsupported names remain unresolved.'}
    atomic_json(ROOT / 'data/ucsd/coverage-20261016-review.json', report)
    print(json.dumps({'queueStates': q['counts'], 'labs': report['labReviewStatuses'], 'faculty': faculty['coverage'], 'centers': len(q['centers'])}, indent=2))
    for item in proposals:
        if item['status'] == 'reviewable_identity_match':
            r = item['record']
            print(r['labName'], '|', r['labWebsiteUrl'], '|', r['department'])


if __name__ == '__main__':
    main()
