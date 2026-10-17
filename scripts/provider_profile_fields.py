"""Read the public provider page's own render data without executing scripts.

Only explicitly published academic positions qualify a roster observation.
Patient ratings, clinical specialties and biography text are never research,
student-rating, identity-merge or department-mapping evidence here.
"""
from __future__ import annotations

import json
import re
from urllib.parse import unquote, urlsplit

from collect_ucsd_coverage import academic_title_clause
from faculty_profile_bindings import captured_source
from faculty_scoped_titles import same_named_subject
from refresh_labs import DOM, every_node, evidence


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate provider document key')
        result[key] = value
    return result


def provider_position_qualification(item, cache, name):
    try:
        if not item or urlsplit(item.get('url', '')).hostname != 'providers.ucsd.edu':
            return None
        base, markup = captured_source(item, cache)
        requested, final = [urlsplit(base[key]) for key in ['requestedUrl', 'sourceUrl']]
        paths = [re.fullmatch(r'/details/([0-9]+)/[^/]+', uri.path) for uri in [requested, final]]
        if (any(uri.scheme != 'https' or uri.hostname != 'providers.ucsd.edu' or uri.query or uri.fragment
                for uri in [requested, final]) or not all(paths) or paths[0][1] != paths[1][1]):
            return None
        nodes = list(every_node(DOM(markup).root))
        payloads = []
        for node in nodes:
            if node.tag != 'script' or node.attrs.get('type') != 'module' or not node.parent or node.parent.tag != 'head':
                continue
            raw = ''.join(part for part in node.children if isinstance(part, str))
            # This is the literal serialized pageProps argument, not eval or
            # a guessed API endpoint. Do not inspect unrelated script objects.
            payloads.extend(re.findall(
                r'render\.render\(\s*\{\s*Page:\s*component\.default,\s*'
                r'pageProps:\s*JSON\.parse\(decodeURIComponent\(("(?:\\.|[^"\\])*")\)\)', raw))
        if len(payloads) != 1:
            return None
        encoded = json.loads(payloads[0])
        if re.search(r'%(?![0-9A-Fa-f]{2})', encoded):
            return None
        payload = json.loads(unquote(encoded, errors='strict'), object_pairs_hook=unique_object)
        document = payload['document']
        if not isinstance(document, dict):
            return None
        own_name = document['name']
        if not isinstance(own_name, str) or not same_named_subject(name, own_name.split(',')[0]):
            return None
        titles = [node.text() for node in nodes if node.tag == 'title']
        og = [node.attrs.get('content') for node in nodes
              if node.tag == 'meta' and node.attrs.get('property') == 'og:title']
        canonical = [node.attrs.get('href') for node in nodes if node.tag == 'link'
                     and node.attrs.get('rel') == 'canonical' and node.parent and node.parent.tag == 'head']
        marker = [node.attrs.get('data-entity-id') for node in nodes
                  if node.tag == 'script' and node.attrs.get('id') == 'yext-entity-data']
        displayed = lambda value: ' '.join(value.split())
        if (len(titles) != 1 or len(og) != 1 or displayed(og[0]) != displayed(titles[0])
                or displayed(document.get('c_metaTitle')) != displayed(titles[0])
                or displayed(titles[0].split('|')[0]) != displayed(own_name)
                or len(canonical) != 1 or canonical != [document.get('c_pagesURL')]
                or marker != [str(document.get('uid'))]
                or str(document.get('id')) != paths[0][1]
                or document.get('siteDomain') != 'providers.ucsd.edu'
                or document.get('c_affiliation') != 'UC_SAN_DIEGO_HEALTH'
                or document.get('meta', {}).get('entityType', {}).get('id') != 'healthcareProfessional'):
            return None
        declared = urlsplit(canonical[0])
        if (declared.scheme != 'https' or declared.hostname != 'providers.ucsd.edu'
                or declared.query or declared.fragment
                or not re.fullmatch(r'/details/' + paths[0][1] + r'/[^/]+', declared.path)
                or declared.path.lstrip('/') != document.get('slug')):
            return None
        positions = document.get('c_positions')
        if (not isinstance(positions, list) or not positions or len(positions) > 30
                or any(not isinstance(role, str) or not role.strip() or len(role) > 500 for role in positions)
                or not any(academic_title_clause(role) for role in positions)):
            return None
        fields = {'Provider positions': positions}
        excerpt = own_name + ' | Provider positions: ' + ' | '.join(positions)
        proof = {**evidence(item['fetch'], 'identity_matched_official_profile_title_field', excerpt),
                 **base, 'template': 'providers_named_render_payload_positions',
                 'subjectTag': 'pageProps.document.name', 'subjectClass': '',
                 'entityId': str(document['id']), 'siteEntityUid': str(document['uid']),
                 'canonicalUri': canonical[0], 'positionSourcePath': 'pageProps.document.c_positions',
                 'titleFieldsAsListed': fields}
        return {'nameAsDisplayed': own_name, 'roleAsListed': ' | '.join(dict.fromkeys(positions)),
                'unitAsListed': '', 'titleFieldsAsListed': fields, 'evidence': proof,
                'fieldEvidence': {field: proof for field in ['nameAsDisplayed', 'roleAsListed']}}
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
