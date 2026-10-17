"""Read-only admission of one explicitly reviewed, non-final collection batch.

This does not relax the completed-export gate, apply aliases/updates, or make
research-summary decisions. The pins authorize only the audited forty-eight IDs.
"""
from __future__ import annotations

import copy
from collections import Counter
from contextlib import redirect_stderr
import datetime as dt
import hashlib
from io import StringIO
import json
from pathlib import Path
import re
import urllib.parse

from lab_summary_content import ContentDOM, decode_cached_html
from rebuild_verified_atlas import url_key as lab_url_key
from refresh_labs import DOM as LegacyDOM
from validate_data import validate_lab, validate_references


COLLECTION = Path('/tmp/ucsd-research-20261016')
HANDOFF_RELATIVE_PATH = Path('data/ucsd/coverage-20261016-reviewed-lab-handoff.json')
DECISIONS_RELATIVE_PATH = Path('data/ucsd/coverage-20261016-decisions.json')
HANDOFF_SHA256 = 'deb1ef551008b7a9a00f38197d66271241ff608217af3a657b25b9c776ef4b25'
DECISIONS_SHA256 = '86aee4007e199b549a503f712cbe2e6940300a0375b5e4a5eaf9f05a0ca7e106'
BASELINE_SHA256 = 'ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e'
BASELINE_LAB_COUNT = 868
APPROVED_SNAPSHOT_DIRECTORY = Path(__file__).resolve().parents[1] / 'data/local-lab-summaries/approved-handoff-snapshots'
FROZEN_LAB_IDS = frozenset({
    'ucsd-live-lab-a8e8602372ef78', 'ucsd-live-lab-2982fe38ebc5a0',
    'ucsd-live-lab-8627bc69d4ee7d', 'ucsd-live-lab-33e60c6bf35e2b',
    'ucsd-live-lab-d4a949e47ec3f3', 'ucsd-live-lab-6244ff07b175a9',
    'ucsd-live-lab-da307b4f0f98b5', 'ucsd-live-lab-f2a96ed0a66637',
    'ucsd-live-lab-27d33fcd1710ce', 'ucsd-live-lab-f78bf84fc19eef',
    'ucsd-live-lab-848c82d9aba60e', 'ucsd-live-lab-176619ff4af12d',
    'ucsd-live-lab-eb3be693359889', 'ucsd-live-lab-9c13d3e2e45efe',
    'ucsd-live-lab-802bc4f0642435', 'ucsd-live-lab-7df54236890322',
    'ucsd-live-lab-db372d05c77570',
    'ucsd-live-lab-e4e6eca4020c54',
    'ucsd-live-lab-ae260ca4c6dbaa',
    'ucsd-live-lab-7d63fdc52b1a03',
    'ucsd-live-lab-0b30919c2bef2f',
    'ucsd-live-lab-d0957addf55506',
    'ucsd-live-lab-3ff4f6521ed9d9',
    'ucsd-live-lab-09d0d866944f48',
    'ucsd-live-lab-5c7a3b14f0f39c',
    'ucsd-live-lab-c9ffdf33197da6',
    'ucsd-live-lab-a15462c8329a59',
    'ucsd-live-lab-53daf590030749',
    'ucsd-live-lab-a463ff9c900f83',
    'ucsd-live-lab-ca190c92ae75b0',
    'ucsd-live-lab-67c5e21639c2e7',
    'ucsd-live-lab-18dfe0de4f1bd9',
    'ucsd-live-lab-41953ab3f34f92',
    'ucsd-live-lab-6275676900a682',
    'ucsd-live-lab-c08c695e2bc6da',
    'ucsd-live-lab-53e500e928b587',
    'ucsd-live-lab-bc4d171de42c21',
    'ucsd-live-lab-c696ccb21f46a2',
    'ucsd-live-lab-63bf4174cc6883',
    'ucsd-live-lab-00b256a358a3eb',
    'ucsd-live-lab-a34811a3af59ad',
    'ucsd-live-lab-11a3b833e5404b',
    'ucsd-live-lab-06657267a18486',
    'ucsd-live-lab-f65b4596f0a5e3',
    'ucsd-live-lab-be8be1252c1a12', 'ucsd-live-lab-dd94a07de965c1',
    'ucsd-live-lab-a92dafc16a6dae',
    'ucsd-live-lab-f5581b3b23f1d6',
})
SHARED_URL = 'https://www.ucsdrobotics.org/'
SHARED_GROUP_ID = 'ucsd-shared-homepage-802bc4f0642435'
SHARED_LAB_NAMES = {
    'ucsd-live-lab-802bc4f0642435': 'Flow Control Lab',
    'ucsd-live-lab-7df54236890322': 'Coordinated Robotics Lab',
}
SHARED_IDENTITY_QUOTES = {
    'ucsd-live-lab-802bc4f0642435': 'The UCSD Flow Control Lab , founded in 1998',
    'ucsd-live-lab-7df54236890322': 'The UCSD Coordinated Robotics Lab , founded in 2004',
}


class HandoffImportError(ValueError):
    """The optional batch exists but fails an admission/provenance guard."""


def _require(condition, message):
    if not condition:
        raise HandoffImportError(message)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def _json(data, label):
    try:
        value = json.loads(data, object_pairs_hook=_unique_object)
    except (ValueError, UnicodeError) as exc:
        raise HandoffImportError('Invalid JSON in ' + label) from exc
    _require(isinstance(value, dict), label + ' must be an object')
    return value


def _read(path, label, digest=None):
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise HandoffImportError('Cannot read ' + label + ': ' + str(path)) from exc
    actual = _sha256(data)
    if digest is not None:
        _require(actual == digest, label + ' SHA256 does not match audited pin')
    return _json(data, label), actual


def _timestamp(value, label):
    try:
        _require(isinstance(value, str), label + ' must be an original UTC timestamp')
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        _require(parsed.tzinfo is not None and parsed.utcoffset() == dt.timedelta(0),
                 label + ' must be timezone-aware UTC')
    except (ValueError, TypeError) as exc:
        raise HandoffImportError(label + ' must be an original UTC timestamp') from exc
    return parsed


def _url(value):
    if not isinstance(value, str) or re.search(r'\s', value) or any(ord(c) < 32 for c in value):
        return False
    try:
        p = urllib.parse.urlsplit(value)
        return (p.scheme in {'http', 'https'} and bool(p.hostname)
                and not p.username and not p.password)
    except (ValueError, TypeError, AttributeError):
        return False


def _capture_url_key(value):
    _require(_url(value), 'Invalid capture URL')
    p = urllib.parse.urlsplit(value)
    return (p.scheme, p.netloc.lower(), p.path.rstrip('/') or '/', p.query)


def _counts(value, label):
    _require(isinstance(value, dict) and all(
        isinstance(k, str) and type(v) is int and v >= 0 for k, v in value.items()),
        label + ' must contain nonnegative integer counts')
    return copy.deepcopy(value)


def _validate_schema(baseline, labs):
    stderr = StringIO()
    try:
        with redirect_stderr(stderr):
            for lab in labs:
                validate_lab(lab)
            validate_references({'professors': baseline['professors'],
                                 'labs': baseline['labs'] + labs})
    except (SystemExit, KeyError, TypeError, ValueError) as exc:
        raise HandoffImportError('Lab schema/references failed: ' + stderr.getvalue().strip()) from exc


def _shared_decision(key, decision):
    """Only this reviewed pair may bind two entities to one web resource."""
    _require(key == SHARED_URL and decision.get('sharingGroupId') == SHARED_GROUP_ID,
             'Unreviewed shared URL/group')
    _require(isinstance(decision.get('reason'), str) and decision['reason'].strip(),
             'Shared decision reason required')
    entities = decision.get('sharedEntities')
    _require(isinstance(entities, list) and len(entities) == 2
             and all(isinstance(e, dict) for e in entities), 'Shared decision requires exactly two entities')
    ids = [e.get('stableLabId') for e in entities]
    _require(all(isinstance(lid, str) for lid in ids)
             and len(set(ids)) == 2 and set(ids) == set(SHARED_LAB_NAMES), 'Unreviewed shared entity IDs')
    proofs = decision.get('sharingEvidence')
    _require(isinstance(proofs, list) and proofs and all(
        isinstance(p, dict) and p.get('sourceUrl') == SHARED_URL and p.get('status') == 'verified'
        and isinstance(p.get('evidence'), str) for p in proofs), 'Shared source evidence required')
    _require(any(all(quote in p['evidence'] for quote in SHARED_IDENTITY_QUOTES.values())
                 and 'The two labs collaborate closely' in p['evidence'] for p in proofs),
             'Shared evidence must identify both distinct collaborating labs')
    for entity in entities:
        lid = entity['stableLabId']
        identity = entity.get('identityEvidence')
        _require(entity.get('name') == SHARED_LAB_NAMES[lid]
                 and isinstance(identity, list) and len(identity) == 1
                 and isinstance(identity[0], dict)
                 and identity[0].get('sourceUrl') == SHARED_URL
                 and identity[0].get('observedAt') == proofs[0].get('observedAt')
                 and identity[0].get('status') == 'verified'
                 and identity[0].get('evidence') == SHARED_IDENTITY_QUOTES[lid],
                 'Shared entity needs its exact reviewed name/identity proof')
    sharing = {'kind': 'distinct_named_labs', 'groupId': SHARED_GROUP_ID,
               'memberLabIds': sorted(ids), 'evidence': proofs}
    return entities, sharing


def _shared_record(lab, decision, sharing):
    lid = lab['id']
    fields = lab.get('fieldEvidence', {})
    _require(lab.get('labWebsiteUrl') == SHARED_URL and lab.get('labName') == SHARED_LAB_NAMES[lid]
             and lab.get('recordSubtype') == 'lab' and lab.get('websiteSharing') == sharing
             and fields.get('websiteSharing') == sharing['evidence']
             and fields.get('labName') == decision['identityEvidence'],
             'Incomplete or inconsistent reviewed shared record')
    _require(lab.get('principalInvestigator') == 'Not found'
             and lab.get('principalInvestigatorProfileUrl') == 'Not found'
             and lab.get('professorIds') == [] and not decision.get('principalInvestigator')
             and not decision.get('piEvidence') and 'principalInvestigator' not in fields,
             'Shared pair PI/professor links must remain unresolved')


def _external_program_lab(lab, decision):
    """Exactly one audited Salk lab; program access never becomes UCSD ownership."""
    review = decision.get('programAffiliationReview', {})
    relationships = lab.get('campusProgramRelationships', [])
    _require(lab.get('id') == 'ucsd-live-lab-f65b4596f0a5e3'
             and lab.get('labName') == 'Kosuri Lab'
             and lab.get('labWebsiteUrl') == 'https://kosurilab.com/'
             and lab.get('institution') == decision.get('institution') == 'Salk Institute for Biological Studies'
             and lab.get('relationshipScope') == 'ucsd_graduate_program_affiliate'
             and lab.get('department') == 'Unknown' and lab.get('professorIds') == []
             and lab.get('principalInvestigator') == 'Not found'
             and review.get('kind') == 'ucsd_graduate_program_external_lab'
             and review.get('labId') == lab['id'] and review.get('labWebsiteUrl') == lab['labWebsiteUrl'],
             'Unreviewed external program lab or promoted institution/PI')
    _require(len(relationships) == 1
             and relationships[0].get('institution') == 'University of California San Diego'
             and relationships[0].get('programName') == 'Bioinformatics and Systems Biology'
             and relationships[0].get('relationship') == 'program_listing_and_own_rotation_guidance'
             and relationships[0].get('facultyRoleAsListed') == 'Assistant Professor, Salk Institute for Biological Studies'
             and relationships[0].get('programSourceUrl') == 'https://bioinformatics.ucsd.edu/faculty',
             'External lab program scope changed')
    proofs = lab.get('fieldEvidence', {}).get('campusProgramRelationships', [])
    _require(all(review.get(k) in proofs for k in ['ownStudentAccessEvidence', 'campusCardEvidence', 'campusLabLinkEvidence']),
             'External lab requires independent own-access and named campus-card evidence')


def _unknown_owner_group(lab, decision):
    """An exact audited research group can have unresolved institutional ownership."""
    review = decision.get('campusResearchResourceReview', {})
    _require(lab.get('id') == 'ucsd-live-lab-a92dafc16a6dae'
             and lab.get('labName') == 'Insight' and lab.get('recordSubtype') == 'research_group'
             and lab.get('labWebsiteUrl') == 'https://insight.ucsd.edu/'
             and lab.get('institution') == decision.get('institution') == 'Unknown'
             and lab.get('department') == 'Unknown' and lab.get('principalInvestigator') == 'Not found'
             and lab.get('professorIds') == [] and lab.get('relationshipScope') == 'official_campus_research_resource'
             and review.get('kind') == 'named_campus_linked_research_group'
             and review.get('labId') == lab['id'], 'Unknown-owner research group was promoted or changed')
    _require(lab.get('institutionAssessment', {}).get('status') == 'unresolved'
             and lab['institutionAssessment'].get('reason') == decision.get('institutionUnresolvedReason')
             and 'institution' in lab.get('unverifiedFields', [])
             and 'institution' not in lab.get('fieldEvidence', {}), 'Unresolved institution was promoted')
    proofs = lab.get('fieldEvidence', {}).get('campusResearchRelationships', [])
    _require(all(review.get(k) in proofs for k in ['campusCardEvidence', 'campusLinkEvidence', 'transportEvidence']),
             'Named campus card and exact transport resource evidence required')


def _validate_decisions(handoff, decisions, baseline):
    labs = handoff.get('labs')
    _require(isinstance(labs, list) and all(isinstance(l, dict) for l in labs),
             'Handoff labs must be a list of objects')
    ids = [lab.get('id') for lab in labs]
    _require(all(isinstance(i, str) for i in ids) and len(ids) == len(set(ids))
             and set(ids) == FROZEN_LAB_IDS, 'Handoff must contain exactly the frozen lab IDs')
    _require(type(handoff.get('recordCount')) is int
             and handoff['recordCount'] == len(FROZEN_LAB_IDS) == len(labs), 'Handoff recordCount mismatch')
    _require(type(decisions.get('schemaVersion')) is int and decisions['schemaVersion'] == 1
             and isinstance(decisions.get('labs'), dict), 'Unsupported decisions schema')
    accepted = {}
    for key, decision in decisions['labs'].items():
        _require(isinstance(decision, dict), 'Malformed per-URL decision')
        action = decision.get('action')
        sharing = None
        if action == 'accept_shared_entities':
            entities, sharing = _shared_decision(key, decision)
        else:
            _require(not any(field in decision for field in
                             ['sharedEntities', 'sharingGroupId', 'sharingEvidence']),
                     'Shared entities require explicit accept_shared_entities action')
            if action != 'accept':
                continue
            lid = decision.get('stableLabId')
            _require(not isinstance(lid, str) or lid not in SHARED_LAB_NAMES,
                     'Shared pair requires explicit accept_shared_entities action')
            entities = [decision]
        for entity in entities:
            lid = entity.get('stableLabId')
            _require(isinstance(lid, str) and lid not in accepted, 'Duplicate/missing accepted stableLabId')
            accepted[lid] = (key, entity, sharing)
    _require(set(accepted) == FROZEN_LAB_IDS, 'Explicit accept decisions do not match frozen IDs')
    known_ids = {r['id'] for r in baseline['labs'] + baseline['professors']}
    _require(not known_ids.intersection(ids), 'Incremental ID collides with baseline')
    known_urls = {lab_url_key(u) for lab in baseline['labs']
                  for u in [lab['labWebsiteUrl']] + lab.get('alternateWebsiteUrls', [])}
    new_urls = {}
    bindings = []
    for lab in labs:
        lid = lab['id']
        key, decision, sharing = accepted[lid]
        _require(_url(key) and _url(lab.get('labWebsiteUrl')), 'Invalid accepted lab URL')
        canonical = lab_url_key(lab['labWebsiteUrl'])
        _require(canonical == lab_url_key(key), 'Decision URL is not the accepted lab URL')
        fields = lab.get('fieldEvidence')
        _require(isinstance(fields, dict) and fields, 'Lab fieldEvidence required')
        if sharing:
            _shared_record(lab, decision, sharing)
        else:
            _require('websiteSharing' not in lab
                     and 'websiteSharing' not in fields, 'Unreviewed sharing metadata')
        # Baseline collisions always fail. Only the already-validated pair can
        # share a new-batch URL; a sharing-shaped object grants no exception.
        _require(canonical not in known_urls, 'Incremental lab URL collision')
        owners = new_urls.setdefault(canonical, set())
        _require(not owners or (sharing and owners <= set(SHARED_LAB_NAMES)), 'Incremental lab URL collision')
        owners.add(lid)
        _require(isinstance(decision.get('reason'), str) and decision['reason'].strip(), 'Accept reason required')
        if lab.get('id') == 'ucsd-live-lab-f65b4596f0a5e3':
            _external_program_lab(lab, decision)
        elif lab.get('id') == 'ucsd-live-lab-a92dafc16a6dae':
            _unknown_owner_group(lab, decision)
        else:
            _require(lab.get('institution') == 'University of California San Diego', 'Unexpected institution')
        _require(lab.get('recordSubtype') in {'lab', 'research_group'}, 'Unexpected incremental entity type')
        for source_field, target_field in [('name', 'labName'), ('recordSubtype', 'recordSubtype'),
                                           ('department', 'department'), ('principalInvestigator', 'principalInvestigator')]:
            if source_field in decision:
                _require(lab.get(target_field) == decision[source_field], 'Reviewed field override changed: ' + lid)
        _require(all(isinstance(proofs, list) and proofs
                     and all(isinstance(proof, dict) for proof in proofs)
                     for proofs in fields.values()), 'Field evidence must be nonempty proof lists')
        for decision_field, lab_field in [('institutionEvidence', 'institution'),
                                           ('identityEvidence', 'labName'), ('departmentEvidence', 'department'),
                                           ('piEvidence', 'principalInvestigator')]:
            proofs = decision.get(decision_field, [])
            if decision_field == 'institutionEvidence' and lid != 'ucsd-live-lab-a92dafc16a6dae':
                _require(proofs, 'Reviewed institution evidence required')
            _require(isinstance(proofs, list) and all(p in fields.get(lab_field, []) for p in proofs),
                     'Reviewed field evidence changed: ' + lid)
        if decision.get('principalInvestigator'):
            _require(decision.get('piEvidence'), 'Explicit PI evidence required')
            _require(lab.get('principalInvestigatorIdentityScope') == decision.get(
                'principalInvestigatorIdentityScope', 'source_reported_name_only'), 'PI identity scope changed')
        else:
            _require(lab.get('principalInvestigator') == 'Not found', 'PI inferred without reviewed decision')
        if decision.get('departmentUnresolvedReason'):
            _require(lab.get('department') == 'Unknown' and 'department' not in fields
                     and lab.get('departmentAssessment', {}).get('status') == 'unresolved'
                     and lab['departmentAssessment'].get('reason') == decision['departmentUnresolvedReason']
                     and 'department' in lab.get('unverifiedFields', []), 'Unresolved department was promoted')
        binding = {'labId': lid, 'decisionUrlKey': key,
                   'action': 'accept_shared_entities' if sharing else 'accept'}
        if sharing:
            binding['sharingGroupId'] = sharing['groupId']
        bindings.append(binding)
    _validate_schema(baseline, labs)
    return labs, bindings


def _named_link_present(proof, dom):
    """A named-link receipt is a literal anchor relationship, not page prose."""
    label, target = proof.get('linkText'), proof.get('linkUrl')
    literal = proof.get('literalHref', target)
    if 'literalHref' in proof and (not isinstance(literal, str) or not _url(proof.get('sourceUrl'))
                                   or urllib.parse.urljoin(proof['sourceUrl'], literal) != target):
        return False
    return (isinstance(label, str) and bool(label.strip()) and _url(target)
            and proof.get('evidence') == label + ' -> ' + target
            and any(n.tag == 'a' and n.text() == label
                    and n.attrs.get('href') == literal for n in dom.root.walk()))


def _field_proof_present(proof, dom, texts):
    quote = proof.get('evidence')
    if proof.get('evidenceType') in {'named_link', 'document_link'}:
        return _named_link_present(proof, dom)
    if not isinstance(quote, str) or not quote.strip():
        return False
    if proof.get('evidenceType') == 'document_title':
        return any(n.tag == 'title' and n.text() == quote for n in dom.root.walk())
    if proof.get('evidenceType') == 'document_heading':
        tag = proof.get('headingTag')
        return tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'} and any(
            n.tag == tag and n.text() == quote for n in dom.root.walk())
    if proof.get('evidenceType') == 'html_attribute':
        tag, attribute, value = (proof.get(k) for k in ['elementTag', 'attributeName', 'attributeValue'])
        if tag == 'a' and attribute == 'href':
            # Contact receipts require the literal mailto and its named anchor;
            # arbitrary attribute text or a neighboring person's address fails.
            label = proof.get('linkTextAsPublished')
            return (isinstance(value, str) and re.fullmatch(r'mailto:[^\s?@]+@[^\s?@]+', value) is not None
                    and isinstance(label, str) and bool(label.strip())
                    and proof.get('selectorAttributes') == {'href': value}
                    and quote == 'a[href] = ' + value
                    and any(n.tag == 'a' and n.attrs.get('href') == value and n.text() == label
                            for n in dom.root.walk()))
        return (tag in {'frame', 'iframe'} and attribute == 'src' and isinstance(value, str)
                and quote == tag + '[src] = ' + value and any(
                    n.tag == tag and n.attrs.get('src') == value for n in dom.root.walk()))
    return any(quote in text for text in texts)


def _redirect_proof_present(proof, captures):
    """A single recorded redirect is metadata evidence, never invented prose."""
    chain = proof.get('redirects')
    if not isinstance(chain, list) or len(chain) != 1 or not isinstance(chain[0], dict):
        return False
    hop = chain[0]
    if hop.get('httpStatus') not in {301, 302, 303, 307, 308}:
        return False
    return (proof.get('evidence') == f"HTTP {hop['httpStatus']}: {hop.get('from')} -> {hop.get('to')}"
            and hop.get('from') == proof.get('requestedUrl')
            and any(meta.get('redirects') == chain
                    and meta.get('sourceUrl') == proof.get('requestedUrl')
                    and meta.get('observedAt') == proof.get('observedAt')
                    and meta.get('sha256') == proof.get('bodySha256')
                    and meta.get('finalUrl') == hop.get('to') for meta in captures))


SUPPLEMENT_SHA256 = '4958449205052720577065ba790917203a39121af2c78ba124241e5e67f38000'
SUPPLEMENT_URLS = frozenset({
    'https://cenl.ucsd.edu/lab-navigation.html',
    'https://cenl.ucsd.edu/lab-main.html',
    'https://cenl.ucsd.edu/Personel.html',
    'https://meyersgroup.ucsd.edu/body_frame.htm',
})


def _load_supplement(snapshot_dir):
    """Only four audited collector captures, frozen independently of its live queue."""
    bundle, _ = _read(snapshot_dir / ('frame-source-captures-' + SUPPLEMENT_SHA256 + '.json'),
                      'Audited frame capture receipts', SUPPLEMENT_SHA256)
    result = {}
    for entry in bundle.get('items', []):
        item, receipt = entry['item'], entry['receipt']
        url, meta = item['url'], item['fetch']
        _require(url in SUPPLEMENT_URLS and url not in result, 'Unapproved/duplicate supplemental URI')
        _require(receipt.get('requestedUrl') == url and receipt.get('capture') == meta
                 and receipt.get('wireRequests') == 1 and receipt.get('maximumContentAttempts') == 1
                 and receipt.get('liveQueueWritten') is False and meta.get('status') == 'ok'
                 and meta.get('sourceUrl') == url and meta.get('httpStatus') == 200,
                 'Supplement receipt/capture mismatch')
        path = Path(entry['cachePath'])
        _require(path.resolve().is_relative_to((snapshot_dir / 'frame-capture-responses').resolve())
                 and path.name == _sha256(url.encode()) + '.html', 'Unapproved supplement cache path')
        _require(_sha256(path.read_bytes()) == entry['bodySha256'] == meta.get('sha256'),
                 'Supplement raw hash mismatch')
        _timestamp(meta.get('observedAt'), 'Supplement original observation')
        result[url] = entry
    _require(set(result) == SUPPLEMENT_URLS, 'Incomplete audited supplement')
    return result


def _validate_sources(handoff, queue, collection, supplements=None):
    supplements = supplements or {}
    manifest = handoff.get('sourceManifest')
    _require(isinstance(manifest, list) and manifest, 'Source manifest required')
    _require(isinstance(queue.get('items'), dict), 'Actual collector queue required')
    response_root = (collection / '.cache/coverage-20261016/responses').resolve()
    generated = _timestamp(handoff['generatedAt'], 'generatedAt')
    captures = {}
    for item in queue['items'].values():
        if isinstance(item, dict):
            captures.setdefault(item.get('url'), []).append(item.get('fetch', {}))
    for url, entry in supplements.items():
        captures.setdefault(url, []).append(entry['item']['fetch'])
    text_by_source = {}
    dom_by_source = {}
    metadata_by_source = {}
    verified_manifest = []
    for source in manifest:
        _require(isinstance(source, dict), 'Invalid source manifest entry')
        source_url, requested = source.get('sourceUrl'), source.get('requestedUrl')
        _require(_url(source_url) and _url(requested), 'Invalid source manifest URL')
        observed = source.get('observedAt')
        _require(_timestamp(observed, 'source observedAt') <= generated, 'Source observation follows handoff')
        pair = (source_url, observed)
        _require(pair not in text_by_source, 'Duplicate source URL/time in manifest')
        digest = source.get('bodySha256')
        _require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest), 'Invalid source hash')
        cache_path = source.get('cachePath')
        _require(isinstance(cache_path, str) and Path(cache_path).is_absolute(), 'Absolute source cache path required')
        path = Path(cache_path)
        supplemental = supplements.get(requested)
        approved_supplement = (supplemental and path.resolve() == Path(supplemental['cachePath']).resolve())
        _require(path.resolve().is_relative_to(response_root) or approved_supplement,
                 'Source cache path escapes responses directory')
        _require(path.name == _sha256(requested.encode()) + '.html', 'Source filename does not match requested URL')
        try:
            body = path.read_bytes()
        except OSError as exc:
            raise HandoffImportError('Cannot read source cache: ' + str(path)) from exc
        _require(_sha256(body) == digest, 'Source raw-byte hash mismatch')
        matching = [meta for meta in captures.get(requested, []) if isinstance(meta, dict)
                    and meta.get('status') == 'ok' and meta.get('observedAt') == observed
                    and meta.get('sha256') == digest
                    and _capture_url_key(source_url) in {
                        _capture_url_key(u) for u in [requested, meta.get('sourceUrl'), meta.get('finalUrl')] if _url(u)}]
        _require(matching, 'Source has no actual queue capture with original URL/time/hash')
        metadata_by_source[pair] = matching
        # Legacy identity quotations may contain directory navigation. Retain
        # literal proof compatibility; this is never research-summary approval.
        markup, _, _ = decode_cached_html(body)
        dom_by_source[pair] = ContentDOM(markup)
        text_by_source[pair] = (LegacyDOM(body.decode(errors='replace')).main().text(),
                                ContentDOM(markup).main().text())
        verified_manifest.append({**copy.deepcopy(source), 'byteCount': len(body)})
    cited = set()
    quote_count = 0
    for lab in handoff['labs']:
        for proofs in lab['fieldEvidence'].values():
            _require(isinstance(proofs, list) and proofs, 'Field evidence must be nonempty lists')
            for proof in proofs:
                _require(isinstance(proof, dict), 'Invalid field proof')
                pair = (proof.get('sourceUrl'), proof.get('observedAt'))
                quote = proof.get('evidence')
                _require(pair in text_by_source, 'Field proof has no source manifest URL/time')
                supported = (_redirect_proof_present(proof, metadata_by_source[pair])
                             if proof.get('evidenceType') == 'redirect_chain'
                             else _field_proof_present(proof, dom_by_source[pair], text_by_source[pair]))
                _require(proof.get('status') == 'verified' and supported,
                         'Field quote not present in original capture (or named-link anchor mismatch)')
                cited.add(pair)
                quote_count += 1
    _require(cited == set(text_by_source), 'Unreferenced source manifest capture')
    return verified_manifest, quote_count


def load_reviewed_handoff(baseline_atlas: dict, *, collection=COLLECTION,
                          approved_snapshot_dir=None) -> tuple[list[dict], dict | None]:
    """Return only the pinned additions and provenance, without writing anything.

    Without an approved snapshot, an absent exact handoff file returns ``([], None)``. An existing invalid,
    unreadable or changed admission artifact fails closed. For the production
    collection, an exact hash-pinned approved snapshot retains the already
    reviewed batch when the collector regenerates its mutable handoff. Changes
    in that mutable file are reported separately, never automatically admitted.
    ``collection`` permits isolated fixtures; production pins/IDs stay explicit.
    """
    collection = Path(collection)
    mutable_path = collection / HANDOFF_RELATIVE_PATH
    if approved_snapshot_dir is None and collection.resolve() == COLLECTION.resolve():
        approved_snapshot_dir = APPROVED_SNAPSHOT_DIRECTORY
    snapshot_dir = Path(approved_snapshot_dir) if approved_snapshot_dir is not None else None
    frozen_path = (snapshot_dir / (HANDOFF_RELATIVE_PATH.stem + '-' + HANDOFF_SHA256 + '.json')) if snapshot_dir else None
    path = frozen_path if frozen_path and (frozen_path.exists() or frozen_path.is_symlink()) else mutable_path
    if not path.exists() and not path.is_symlink():
        return [], None
    handoff, handoff_hash = _read(path, 'Reviewed handoff', HANDOFF_SHA256)
    frozen_decisions = (snapshot_dir / (DECISIONS_RELATIVE_PATH.stem + '-' + DECISIONS_SHA256 + '.json')) if snapshot_dir else None
    decisions_path = frozen_decisions if frozen_decisions and (frozen_decisions.exists() or frozen_decisions.is_symlink()) else collection / DECISIONS_RELATIVE_PATH
    decisions, decisions_hash = _read(decisions_path, 'Review decisions', DECISIONS_SHA256)
    baseline, baseline_hash = _read(collection / 'data/research-atlas.json', 'Baseline atlas', BASELINE_SHA256)
    _require(baseline == baseline_atlas, 'Caller baseline does not match audited baseline')
    _require(isinstance(baseline.get('labs'), list) and len(baseline['labs']) == BASELINE_LAB_COUNT
             and isinstance(baseline.get('professors'), list), 'Unexpected baseline scope')
    _require(type(handoff.get('schemaVersion')) is int and handoff['schemaVersion'] == 1,
             'Unsupported handoff schema')
    _require(handoff.get('collectionState') == 'reviewed_incremental'
             and handoff.get('isFinalExport') is False and handoff.get('servedAtlasModified') is False,
             'Handoff is not the authorized non-final incremental batch')
    _require(handoff.get('decisionArtifactSha256') == decisions_hash, 'Decision artifact binding mismatch')
    _require(handoff.get('servedAtlasSha256') == baseline_hash, 'Handoff baseline binding mismatch')
    generated = _timestamp(handoff.get('generatedAt'), 'generatedAt')
    _require(_timestamp(handoff.get('queueCheckpointAt'), 'queueCheckpointAt') <= generated,
             'Queue checkpoint follows handoff')
    queue_path = collection / '.cache/coverage-20261016/queue.json'
    queue, queue_hash = _read(queue_path, 'Collector queue')
    _timestamp(queue.get('updatedAt'), 'Collector queue updatedAt')
    labs, bindings = _validate_decisions(handoff, decisions, baseline)
    supplements = (_load_supplement(snapshot_dir) if snapshot_dir is not None
                   and collection.resolve() == COLLECTION.resolve() else {})
    sources, quote_count = _validate_sources(handoff, queue, collection, supplements)
    aliases, updates = handoff.get('labAliases'), handoff.get('labUpdates')
    _require(isinstance(aliases, list) and isinstance(updates, list), 'Malformed ignored alias/update inventories')
    receipt = {
        'schemaVersion': 1, 'sourceFile': str(path.resolve()), 'sourceSha256': handoff_hash,
        'usesFrozenApprovedSnapshot': path != mutable_path,
        'originalCollectorHandoffPath': str(mutable_path.resolve()),
        'observedMutableHandoffSha256': _sha256(mutable_path.read_bytes()) if mutable_path.is_file() else None,
        'mutableRevisionAutomaticallyAdmitted': False,
        'generatedAt': handoff['generatedAt'], 'collectionState': 'reviewed_incremental',
        'isFinalExport': False, 'servedAtlasModified': False, 'baselineSha256': baseline_hash,
        'decisionArtifactPath': str(decisions_path.resolve()), 'decisionArtifactSha256': decisions_hash,
        'acceptedLabIds': [lab['id'] for lab in labs], 'decisionBindings': bindings,
        'queueCheckpointAt': handoff['queueCheckpointAt'],
        'handoffQueueCounts': _counts(handoff.get('queueStates'), 'Handoff queue states'),
        'globalQueueCounts': _counts(queue.get('counts'), 'Actual queue counts'),
        'globalQueueItemStateCounts': dict(Counter(item.get('state', 'unknown') for item in queue['items'].values()
                                                   if isinstance(item, dict))),
        'globalQueueUpdatedAt': queue['updatedAt'], 'globalQueueSnapshotSha256': queue_hash,
        'globalCollectionDeclaredComplete': False,
        'auditedSupplementalCaptureCount': len(supplements),
        'supplementalCapturesAreNotLiveQueueWrites': True,
        'auditedSupplementSha256': SUPPLEMENT_SHA256 if supplements else None,
        'ignoredLabAliases': len(aliases), 'declaredReviewedAliasCount': handoff.get('reviewedAliasCount'),
        'ignoredLabUpdates': len(updates), 'sourceManifest': sources,
        'validation': {'acceptedRecords': len(labs), 'rawByteCapturesVerified': len(sources),
                       'actualQueueCaptureTimesVerified': len(sources), 'exactFieldQuotesVerified': quote_count},
        'scope': 'Append-only eligible summary inputs; no aliases, updates, faculty inference or automatic research support.',
    }
    return copy.deepcopy(labs), receipt
