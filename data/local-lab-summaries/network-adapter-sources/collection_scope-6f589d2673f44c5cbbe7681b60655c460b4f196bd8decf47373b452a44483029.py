"""Bound external discovery to specifically associated UCSD people/labs."""
from __future__ import annotations

import re
import unicodedata
import urllib.parse


def key(url):
    p = urllib.parse.urlsplit(url or '')
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/') or '/', p.query, '')) if p.hostname else ''


def official(url):
    host = urllib.parse.urlsplit(url or '').hostname or ''
    return host == 'ucsd.edu' or host.endswith('.ucsd.edu')


def words(value):
    value = unicodedata.normalize('NFKD', value or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


def specific_lab_name(name):
    text = words(name)
    if re.search(r'lab (?:logo|brand|safety|fun|personnel|alumni)|visual identity|brand guidelines|teaching lab|laboratories for accelerating|resource group|support group|support network|nonforprofit|nonprofit', text):
        return False
    useful = re.sub(r'\b(?:the|lab|laboratory|laboratories|group|research|website|web|site|home|homepage|ucsd|at|of|university|california|san|diego|visit)\b', '', text).strip()
    return bool(useful and re.search(r'\blab\b|laborator|\bgroup\b', text))


def generic_external_url(url):
    p = urllib.parse.urlsplit(url)
    path = urllib.parse.unquote(p.path).lower()
    if re.search(r'/(?:visual-identity|branding|brand-guidelines|logo|style-guide)(?:/|$)', path):
        return 'External branding/visual-identity resource, not a specific UCSD person or research lab.'
    if (p.hostname or '').endswith('nih.gov') and re.search(r'research-funded|research-initiatives|funding|grants', path):
        return 'External funder/program overview, not an individual UCSD lab identity source.'
    return None


class ScopePolicy:
    def __init__(self, state, atlas, decisions=None, legacy=None, original_candidates=None, original_reviews=None):
        self.state, self.atlas = state, atlas
        self.decisions = (decisions or {}).get('labs', {})
        self.people = {p['id']: p for p in atlas['professors']}
        self.originals = {key(c.get('labWebsiteUrl', '')): c for c in (original_candidates or {}).get('candidates', []) if c.get('status') == 'unverified' and key(c.get('labWebsiteUrl', ''))}
        self.baseline = {key(u): lab for lab in atlas['labs'] for u in [lab['labWebsiteUrl']] + lab.get('alternateWebsiteUrls', [])}
        self.no_identity = {key(row['originalRecord']['labWebsiteUrl']) for row in (legacy or {}).get('entries', [])
                            if row.get('observedPageType') != 'lab'}
        self.known_nonlab = {key(row['originalRecord']['labWebsiteUrl']): row.get('observedPageType') for row in (legacy or {}).get('entries', []) if row.get('observedPageType') != 'lab'}
        self.known_nonlab.update({key(proof['sourceUrl']): row.get('observedPageType') for row in (legacy or {}).get('entries', []) if row.get('observedPageType') != 'lab' for proof in row.get('evidence', [])})
        self.no_identity.update(url for url, c in self.originals.items() if (original_reviews or {}).get('reviews', {}).get(c['candidate_id'], {}).get('status') == 'unresolved_current_ucsd_affiliation')
        self.by_final = {}
        for item in state['items'].values():
            self.observe(item)

    def observe(self, item):
        final = item.get('fetch', {}).get('finalUrl')
        if final:
            rows = self.by_final.setdefault(key(final), [])
            if not any(r is item for r in rows):
                rows.append(item)

    def lookup(self, url):
        item = self.state['items'].get(key(url))
        return [item] if item else self.by_final.get(key(url), [])

    def decision(self, item):
        return self.decisions.get(key(item['url']), {})

    def expected(self, item):
        names, persons = [], []
        if item['contexts'] and all(c['kind'] == 'identity_page' for c in item['contexts']):
            for root in self.roots(item):
                if root is not item:
                    root_names, root_persons = self.expected(root)
                    names.extend(root_names); persons.extend(root_persons)
        candidate = self.state.get('labCandidates', {}).get(key(item['url']), {})
        record = candidate.get('record', {})
        old = self.baseline.get(key(item['url']), {})
        for lab in [record, old]:
            if lab.get('labName'):
                names.append(lab['labName'])
            if lab.get('principalInvestigator') not in {None, '', 'Not found', 'Unknown'}:
                persons.append(lab['principalInvestigator'])
            persons.extend(self.people[pid]['name'] for pid in lab.get('professorIds', []) if pid in self.people)
        original = self.originals.get(key(item['url']))
        if original:
            names.append(original['labName'])
        decision = self.decision(item)
        if decision.get('name'):
            names.append(decision['name'])
        for observation in candidate.get('observations', []):
            if observation.get('label'):
                names.append(observation['label'])
            persons.extend(self.people[pid]['name'] for pid in observation.get('professorIds', []) if pid in self.people)
        for context in item.get('contexts', []):
            if context.get('professorId') in self.people:
                persons.append(self.people[context['professorId']]['name'])
            for source in self.lookup(context.get('sourceUrl', '')):
                eligibility = source.get('profileEligibility', {})
                campus_person = eligibility.get('nameAsDisplayed') and eligibility.get('titleAsListed') and (eligibility.get('schoolAsListed', '').lower().startswith('vc-') or re.search(r'UC San Diego|School of|Jacobs|Academic Affairs', eligibility.get('schoolAsListed', ''), re.I))
                if campus_person and not re.search(r'Salk|Burnham|Sanford|Harvard|Stanford', eligibility.get('titleAsListed', ''), re.I):
                    persons.append(eligibility['nameAsDisplayed'])
                if official(source['url']):
                    headline = words(source.get('page', {}).get('title', '') + ' ' + ' '.join(source.get('page', {}).get('headings', [])[:1]))
                    for c in source['contexts']:
                        person = self.people.get(c.get('professorId'))
                        if person and words(person['name']) in headline:
                            persons.append(person['name'])
        return names, persons

    def associated(self, item):
        if self.decision(item).get('action') in {'accept', 'alias'} or key(item['url']) in self.baseline:
            return True
        names, persons = self.expected(item)
        if persons:
            return True
        if not any(specific_lab_name(n) for n in names):
            return False
        for context in item.get('contexts', []):
            source = context.get('sourceUrl', '')
            if official(source) and re.search(r'faculty|faculty-labs|/research/(?:labs|groups)|/laborator|/labs(?:[/.]|$)', urllib.parse.urlsplit(source).path, re.I):
                return True
        original = self.originals.get(key(item['url']))
        if original and official(original.get('officialAffiliationSourceUrl', '')) and re.search(r'faculty|/research|/labs', original.get('officialAffiliationSourceUrl', ''), re.I):
            return True
        return False

    def can_expand(self, item):
        if key(item['url']) in self.no_identity:
            return False
        if self.decision(item).get('action') in {'exclude_link', 'separate_research_unit', 'separate_research_facility', 'separate_student_research_group', 'separate_named_groups_on_directory'}:
            return False
        base = item.get('fetch', {}).get('finalUrl', item['url'])
        if generic_external_url(base):
            return False
        if not official(base) and self.primary_is_generic(item):
            return False
        if item['contexts'] and all(c['kind'] == 'identity_page' for c in item['contexts']):
            return any(root is not item and self.can_expand(root) and (official(base) or self.inside_external_entity(root, base)) for root in self.roots(item))
        if official(base):
            return True
        if not self.associated(item):
            return False
        if self.decision(item).get('action') in {'accept', 'alias'}:
            return True
        names, persons = self.expected(item)
        page = item.get('page', {})
        title = words(page.get('title', ''))
        headings = page.get('headings', [])[:1]
        headline = words(' '.join([page.get('title', '')] + headings))
        if self.primary_is_generic(item):
            return False
        if key(item['url']) in self.baseline:
            # The old valid lab URL is already a specific UCSD association.
            # Permit bounded identity checks across abbreviations/new names;
            # accepting that identity or changing its ID still needs review.
            return True
        for name in names:
            if specific_lab_name(name) and words(name) in headline:
                return True
            core = set(re.sub(r'\b(?:the|lab|laboratory|laboratories|research|group|homepage|website|at|ucsd|university|california|san|diego)\b', '', words(name)).split())
            if specific_lab_name(name) and core and core <= set(headline.split()) and re.search(r'\blab\b|laborator|\bgroup\b', headline):
                # Navigation permission only: a direction added to a known lab
                # name is not evidence for entity acceptance or an ID merge.
                return True
        for person in persons:
            tokens = words(person).split()
            if len(tokens) >= 2 and re.search(r'\b' + re.escape(tokens[0]) + r'\b', headline) and re.search(r'\b' + re.escape(tokens[-1]) + r'\b', headline):
                return True
            if tokens and re.search(r'\b' + re.escape(tokens[-1]) + r'\s+(?:lab|laboratory|research group)\b', headline):
                return True
        body = words(page.get('mainTextExcerpt', ''))
        campus_body = bool(re.search(r'\bucsd\b|uc san diego|university of california san diego', body))
        resource_body = bool(re.search(r'non profit|nonprofit|advocacy|support network|charitable', body))
        if campus_body and not resource_body:
            if any(len(words(p).split()) >= 2 and words(p) in body for p in persons):
                return True
            for name in names:
                core = set(re.sub(r'\b(?:the|lab|laboratory|laboratories|research|group|ucsd|at|of)\b', '', words(name)).split())
                if specific_lab_name(name) and core and core <= set(body.split()) and re.search(r'\blab\b|laborator|\bgroup\b', body):
                    return True
        return False

    def primary_is_generic(self, item):
        page = item.get('page', {})
        names, persons = self.expected(item)
        title = words(page.get('title', ''))
        first = words(' '.join(page.get('headings', [])[:1]))
        if re.search(r'\b(?:for sale|nonforprofit|nonprofit|support network|resource group)\b', title):
            return True
        lab_title = bool(re.search(r'\blab\b|laborator|\bresearch group\b', title + ' ' + first))
        person_title = any(len(words(p).split()) >= 2 and words(p) in title for p in persons)
        named_title = any(specific_lab_name(n) and words(n) in title for n in names)
        generic = any(re.match(r'^(?:welcome to (?:the )?)?(?:the )?(?:faculty of|school of|department of|university of|national institute)\b', h) for h in [title, first, words(page.get('mainTextExcerpt', '')[:160])])
        return generic and not (lab_title or person_title or named_title)

    def roots(self, item):
        pending, seen, found = [item], set(), {}
        while pending:
            current = pending.pop()
            current_key = key(current['url'])
            if current_key in seen:
                continue
            seen.add(current_key)
            if any(c['kind'] in {'lab_destination', 'discovered_lab', 'lab_link_candidate', 'unresolved_candidate'} for c in current['contexts']):
                found[current_key] = current
                continue
            for context in current['contexts']:
                if context['kind'] == 'identity_page':
                    pending.extend(self.lookup(context.get('sourceUrl', '')))
        return list(found.values())

    @staticmethod
    def inside_external_entity(root, target):
        p = urllib.parse.urlsplit(root.get('fetch', {}).get('finalUrl', root['url']))
        t = urllib.parse.urlsplit(target)
        if p.netloc != t.netloc:
            return False
        parts = p.path.strip('/').split('/')
        if p.hostname == 'sites.google.com':
            size = 3 if parts[0] == 'a' else 2
            prefix = '/' + '/'.join(parts[:size])
        else:
            path = re.sub(r'/(?:home|index\.(?:html?|php))/?$', '', p.path.rstrip('/'), flags=re.I)
            if path and ('.' in path.rsplit('/', 1)[-1]):
                path = path.rsplit('/', 1)[0]
            prefix = path.rstrip('/')
        return not prefix or t.path == prefix or t.path.startswith(prefix + '/')

    def request_reason(self, item):
        contexts = item['contexts']
        if any(c['kind'] in {'department', 'directory', 'faculty_directory', 'institute_directory', 'profile', 'new_faculty_profile', 'profile_discovery'} for c in contexts) and official(item['url']):
            return None
        identities_only = all(c['kind'] == 'identity_page' for c in contexts)
        if identities_only:
            roots = self.roots(item)
            for root in roots:
                if self.can_expand(root) and (official(item['url']) or self.inside_external_entity(root, item['url'])):
                    return None
            return 'Identity navigation lacks a specifically associated matching UCSD person/lab source, or leaves its external entity path.'
        if official(item['url']):
            return None
        reason = generic_external_url(item['url'])
        if reason:
            return reason
        if self.decision(item).get('action') in {'exclude_link', 'separate_research_unit', 'separate_research_facility', 'separate_student_research_group', 'separate_named_groups_on_directory'}:
            return 'Reviewed external non-lab/resource classification; retain its evidence without identity expansion.'
        if not self.associated(item):
            return 'External candidate has no specific named UCSD person/lab association; retain discovery evidence for review without a new request.'
        return None

    def destination_reason(self, item):
        if official(item['url']) and any(c['kind'] in {'department', 'directory', 'faculty_directory', 'institute_directory', 'profile', 'new_faculty_profile', 'profile_discovery'} for c in item['contexts']):
            return None
        final = item.get('fetch', {}).get('finalUrl', item['url'])
        if official(final):
            return None
        if generic_external_url(final):
            return generic_external_url(final)
        if key(item['url']) in self.known_nonlab or key(final) in self.known_nonlab:
            return 'Previously source-reviewed non-lab/general destination; retain the capture without identity expansion.'
        if self.primary_is_generic(item):
            return 'Explicit external institutional/resource primary heading or domain-sale page; retain the capture without identity expansion.'
        return None
