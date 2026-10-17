#!/usr/bin/env python3
"""Bounded public gaps through the active collector's shared host gate.

Collector code/caches are read-only. Responses, robots, wire temporary files,
retry receipts and research results stay in this summary worktree. The shared
directory contains only the explicitly authorized host locks and clocks.
"""
from __future__ import annotations
import argparse
import datetime as dt
import email.utils
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.robotparser

from local_lab_summaries import ROOT, BASELINE_HASH, OUT, COLLECTION, CACHE, atomic, read, now, valid_time, key, request_key, checked_url, hydrate, research_links, html_meta_refreshes
from lab_summary_content import ContentDOM as DOM,decode_cached_html

PROTOCOL='fcntl-host-clock-v2'
SHARED=Path('/tmp/ucsd-research-network-20261016')
CODE=COLLECTION/'scripts/collect_ucsd_coverage.py'
GATE_CODE=COLLECTION/'scripts/network_coordination.py'
SOURCE_ORDER=('lab_destinations.py','refresh_labs.py','refresh_faculty_directories.py',
              'collection_lock.py','collection_scope.py','network_coordination.py','collect_ucsd_coverage.py')
DEFAULT_PAGE_MAX_BYTES=2_000_000
REVIEWED_PAGE_MAX_BYTES=8_000_000


def verified_source(path,expected):
    """Read exact loaded bytes, even while the collector edits its next version."""
    snapshot=OUT/'network-adapter-sources'/(path.stem+'-'+expected+'.py')
    if snapshot.exists() and hashlib.sha256(snapshot.read_bytes()).hexdigest()==expected:
        return snapshot.read_bytes(),str(snapshot)
    current=path.read_bytes()
    if hashlib.sha256(current).hexdigest()==expected:return current,str(path)
    # The running collector may still use HEAD while its next revision is
    # edited. A Git object is acceptable only on exact loaded-hash equality.
    result=subprocess.run(['git','-C',str(COLLECTION),'show','HEAD:scripts/'+path.name],capture_output=True,check=False)
    if not result.returncode and hashlib.sha256(result.stdout).hexdigest()==expected:
        return result.stdout,'collector Git HEAD:scripts/'+path.name
    raise RuntimeError('Network not started: collector loaded-code hashes differ from every available exact source')


def cached_robots_boundary(url):
    """Retain an explicit cached denial without probing another site route."""
    p=urllib.parse.urlsplit(url);robots_url=f'{p.scheme}://{p.netloc}/robots.txt'
    stem='robots-'+hashlib.sha256(robots_url.encode()).hexdigest()
    for directory in (OUT/'gap-cache',CACHE/'responses'):
        meta=read(directory/(stem+'.json'),{})
        body=directory/(stem+'.html')
        if meta.get('status')!='checked' or meta.get('sourceUrl')!=robots_url or not body.exists():continue
        rp=urllib.robotparser.RobotFileParser(robots_url);raw=body.read_bytes()
        rp.parse(raw.decode('utf-8','replace').splitlines())
        if not rp.can_fetch('ResearchAtlasEvidenceBot/2.0',url):
            return {'sourceUrl':robots_url,'observedAt':meta['observedAt'],'bodySha256':hashlib.sha256(raw).hexdigest(),'decision':'robots_denied_from_cached_rules_no_request'}
    return None


def explicit_access_boundary(meta):
    """A reviewed route never overrides a known refusal, including robots."""
    if not isinstance(meta,dict):return False
    if meta.get('status') in {'robots_denied','authentication_required','access_challenge'} or meta.get('httpStatus') in {401,403} or meta.get('error')=='access_challenge':return True
    history=meta.get('attemptHistory',[])
    if not isinstance(history,list):return True
    return explicit_access_boundary(meta.get('robots')) or any(explicit_access_boundary(x) for x in history if isinstance(x,dict))


def same_fetch_metadata(left,right):
    # JSON types matter: e.g. actualPageRequestMade=true is not the number 1.
    return isinstance(left,dict) and isinstance(right,dict) and json.dumps(left,sort_keys=True)==json.dumps(right,sort_keys=True)


def original_uri_attempt_keys(ledger):
    """Durable attempt footprints close one-shot admission, not page proof."""
    observed={request_key(url) for url in ledger.get('originalUriObservationStarts',{})}
    for event in ledger.get('wireEvents',[]):
        observed.add(request_key(event.get('url')))
        observed.add(request_key(event.get('originalObservationUrl')))
    return observed


def original_uri_page_limit(entry,binding,ids):
    """Only a hash-bound, individually reviewed local size failure permits 8M."""
    limit=entry.get('maxPageBytes',DEFAULT_PAGE_MAX_BYTES)
    if type(limit) is not int:return None
    if limit==DEFAULT_PAGE_MAX_BYTES:return limit
    if limit!=REVIEWED_PAGE_MAX_BYTES or entry.get('observationOnly') is not True:return None
    if binding.get('status')!='fetch_error' or binding.get('httpStatus')!=200 or explicit_access_boundary(binding):return None
    if not re.search(r'curl:\s*\(63\)|response_exceeds_size_limit',binding.get('error','')):return None
    try:
        path=Path(entry['sizeLimitReviewPath']).resolve()
        if not path.is_relative_to(OUT.resolve()):return None
        proof=path.read_bytes()
        if hashlib.sha256(proof).hexdigest()!=entry['sizeLimitReviewSha256']:return None
        reviews=json.loads(proof)['items']
        for lid in ids:
            if not any(isinstance(x,dict) and x.get('labId')==lid and x.get('url')==entry['url'] and
                same_fetch_metadata(x.get('latestDestinationFetch'),binding) and type(x.get('maxPageBytes')) is int and x['maxPageBytes']==REVIEWED_PAGE_MAX_BYTES and
                x.get('metadataOnly') is True and valid_time(x.get('reviewedAt')) and
                x.get('decision')=='bounded_original_uri_once_8mb' for x in reviews):return None
    except (OSError,KeyError,ValueError,TypeError):return None
    return limit


def reviewed_original_uri_observations(captures):
    """Admit a frozen original route observation, never an entity acceptance."""
    entries=read(OUT/'reviewed-original-uri-observations.json',{}).get('items',[])
    if not entries:return []
    baseline_path=ROOT/'data/research-atlas.json'
    try:
        baseline_bytes=baseline_path.read_bytes()
        if hashlib.sha256(baseline_bytes).hexdigest()!=BASELINE_HASH:return []
        baseline={x['id']:x for x in json.loads(baseline_bytes)['labs']}
    except (OSError,KeyError,ValueError,TypeError):return []
    mismatches=read(OUT/'identity-decisions.json',{})
    excluded=set(mismatches.get('initialMismatchLabIds',[])) | {x['labId'] for x in mismatches.get('items',[])}
    # Any current-round original-URI metadata closes this one-shot admission,
    # even an access precheck with no page wire or a prior failed attempt.
    observed=original_uri_attempt_keys(read(OUT/'gap-results.json',{}));refused=set()
    for capture in captures:
        for meta in [capture.get('fetch',{})]+capture.get('attemptHistory',[]):
            observed.add(request_key(checked_url(meta)))
            observed.add(request_key(meta.get('blockedUrl')))
            observed.update(request_key(x.get('from')) for x in meta.get('redirects',[]))
            if explicit_access_boundary(meta):
                refused.add(request_key(checked_url(meta)))
                refused.add(request_key(meta.get('blockedUrl')))
    result=[]
    for entry in entries:
        if not isinstance(entry,dict) or entry.get('observationOnly') is not True or not valid_time(entry.get('reviewedAt')):continue
        url=entry.get('url')
        if not isinstance(url,str):continue
        original=request_key(url)
        ids=entry.get('labIds');binding=entry.get('latestDestinationFetch')
        if not original or original[0]!='http' or original in observed or entry.get('listedWebsite')!=url:continue
        if not isinstance(ids,list) or not ids or not all(isinstance(lid,str) and lid in baseline and lid not in excluded for lid in ids):continue
        if not isinstance(binding,dict) or not binding or not valid_time(binding.get('observedAt')) or explicit_access_boundary(binding):continue
        if not isinstance(checked_url(binding),str):continue
        related=request_key(checked_url(binding))
        if not related or related[0]!='https' or original[1:]!=related[1:]:continue
        roots={original,related}
        for target in (url,checked_url(binding)):
            parsed=urllib.parse.urlsplit(target)
            roots.add(request_key(urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,'/robots.txt','',''))))
        if roots & refused:continue
        valid=[]
        for lid in ids:
            packet=read(OUT/'packets'/(lid+'.json'));raw=read(OUT/'records'/(lid+'.json'))
            if not packet or not raw or packet.get('labId')!=lid or raw.get('labId')!=lid:continue
            if baseline[lid].get('labWebsiteUrl')!=url or packet.get('listedWebsite')!=url:continue
            if not same_fetch_metadata(packet.get('latestDestinationFetch'),binding):continue
            identity=raw.get('identity',{})
            if identity.get('status')=='mismatch' or identity.get('hasUnresolvedMismatch'):continue
            valid.append(lid)
        limit=original_uri_page_limit(entry,binding,valid) if valid else None
        if limit is not None:
            result.append(dict(entry,labIds=valid,kind='listed_url_direct_provenance_gap',priority=2,
                label='reviewed literal original URI observation only',
                notAnAcceptedCanonicalLabUrl=True,observationOnly=True,maxPageBytes=limit,
                originalURIObservationReviews=[dict(entry,labIds=valid)]))
    return result



PROFILE_LINK_KIND='reviewed_profile_lab_link_gap'
INDEPENDENT_PROFILE_LINK_KIND='reviewed_independently_dated_profile_lab_link_gap'
EXACT_REQUEST_KINDS={'listed_url_direct_provenance_gap',PROFILE_LINK_KIND,INDEPENDENT_PROFILE_LINK_KIND}



def profile_link_access_boundary(meta):
    """Legacy HTTP200 login destinations still close alternate route probes."""
    if not isinstance(meta,dict):return True
    if explicit_access_boundary(meta) or meta.get('transportStatus') in {'robots_denied','authentication_required','access_challenge'}:return True
    urls=[checked_url(meta),meta.get('finalUrl'),meta.get('blockedUrl')]
    urls += [hop.get(field) for hop in meta.get('redirects',[]) for field in ['from','to']]
    for url in urls:
        parsed=urllib.parse.urlsplit(url or '')
        # At least the authentication_target coverage of the audited A071
        # collector, including legacy .aspx routes and OAuth authorization.
        if (parsed.hostname or '').lower() in {'accounts.google.com','login.microsoftonline.com','login.ucsd.edu','sso.ucsd.edu','shibboleth.ucsd.edu'}:return True
        if re.search(r'/(?:login|logon|signin|sign-in|sso|saml|oauth2?|authorize|shibboleth)(?:[/.?]|$)',parsed.path,re.I):return True
    nested=meta.get('attemptHistory',[])
    if meta.get('robots') is not None:nested=list(nested)+[meta['robots']]
    return any(profile_link_access_boundary(x) for x in nested)


def profile_link_origin_unavailable(url,captures=()):
    """A known unavailable HTTP robots origin is not a new page opportunity."""
    parsed=urllib.parse.urlsplit(url)
    robots_url=urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,'/robots.txt','',''))
    stem='robots-'+hashlib.sha256(robots_url.encode()).hexdigest()
    observations=[]
    for directory in (OUT/'gap-cache',CACHE/'responses'):
        path=directory/(stem+'.json')
        if not path.exists():continue
        meta=read(path,{})
        if checked_url(meta)!=robots_url or not valid_time(meta.get('observedAt')):return True
        if profile_link_access_boundary(meta):return True
        observations.append(meta)
    def robot_observations(meta):
        if not isinstance(meta,dict):return
        if checked_url(meta)==robots_url:yield meta
        if isinstance(meta.get('robots'),dict):yield from robot_observations(meta['robots'])
        for previous in meta.get('attemptHistory',[]):yield from robot_observations(previous)
    for capture in captures:
        for meta in [capture.get('fetch',{})]+capture.get('attemptHistory',[]):
            for observation in robot_observations(meta):
                if not valid_time(observation.get('observedAt')) or profile_link_access_boundary(observation):return True
                observations.append(observation)
    if not observations:return False
    newest=max(dt.datetime.fromisoformat(x['observedAt']) for x in observations)
    latest=[x for x in observations if dt.datetime.fromisoformat(x['observedAt'])==newest]
    def usable(meta):
        code=meta.get('httpStatus')
        return not meta.get('error') and type(code) is int and (
            meta.get('status')=='checked' and code==200 or
            meta.get('status')=='not_found' and code in {404,410})
    return any(not usable(meta) for meta in latest)


def profile_lab_anchor(dom,url,label):
    """Only a visible main-profile Featured Content website anchor discovers."""
    for node in dom.main().walk():
        if node.tag!='a' or node.attrs.get('href')!=url or node.text()!=label:continue
        ancestors=[];parent=node
        while parent is not None:
            ancestors.append(parent);parent=parent.parent
        if any(n.excluded() or n.tag=='template' or 'hidden' in n.attrs or
                n.attrs.get('aria-hidden','').lower()=='true' or
                re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',n.attrs.get('style',''),re.I)
                for n in ancestors):continue
        if not any(n.attrs.get('id')=='ctl00_divProfilesContentMain' for n in ancestors):continue
        if not any(n.attrs.get('id')=='http://vivoweb.org/ontology/core#webpage' for n in ancestors):continue
        if not any(n.attrs.get('id')=='http://profiles.catalyst.harvard.edu/ontology/prns#PropertyGroupFeaturedContent' for n in ancestors):continue
        return True
    return False


def independent_profile_date_review(entry,proof,capture,dom):
    """Bind a distinct original capture without retiming its baseline proof.

    Both full primary-source review and route-boundary review are immutable
    owned inputs. Their declarations do not replace the live boundary checks.
    """
    if entry.get('sourceDateContract')!='independent_original_profile_capture':return False
    old_time=entry.get('historicalFieldObservedAt')
    if not valid_time(old_time) or proof.get('observedAt')!=old_time:return False
    if dt.datetime.fromisoformat(old_time.replace('Z','+00:00'))==dt.datetime.fromisoformat(capture['observedAt'].replace('Z','+00:00')):return False
    reports=[]
    for prefix in ('primaryReview','routeBoundaryReview'):
        path=Path(entry[prefix+'Path']).resolve()
        if not path.is_relative_to(OUT.resolve()):return False
        body=path.read_bytes()
        if hashlib.sha256(body).hexdigest()!=entry[prefix+'Sha256']:return False
        reports.append(json.loads(body))
    primary,boundary=reports
    def unique(rows):
        matches=[row for row in rows if row.get('labId')==entry['labId']]
        if len(matches)!=1:raise ValueError('Independent-date review needs exactly one target row')
        return matches[0]
    row=unique(primary['items']);route=unique(boundary['items'])
    if boundary['inputPrimaryReview']['sha256']!=entry['primaryReviewSha256']:return False
    for review in (row,route):
        if review.get('listedWebsite')!=entry['listedWebsite'] or review.get('oldFieldProof')!=proof or review.get('oldFieldProofSha256')!=entry['fieldProofSha256'] or review.get('oldFieldObservedAt')!=old_time:return False
        anchor=review.get('literalLabLink',{})
        if anchor.get('href')!=entry['url'] or anchor.get('label')!=entry['literalAnchor']['label']:return False
        if review.get('sameHostPathQueryDifferentScheme') is not True:return False
    if row.get('independentDatedSourceValid') is not True or row.get('isSameOriginalFieldObservation') is not False or row.get('oldFieldDateUnchanged') is not True or row.get('sameExactProfileSourceURL') is not True:return False
    if row.get('actualIndependentCaptureObservedAt')!=capture['observedAt'] or row.get('independentProfileBodySha256')!=capture['bodySha256']:return False
    if row.get('rawSha256AtReview')!=entry['rawSha256'] or row.get('packetSha256AtReview')!=entry['packetSha256'] or not same_fetch_metadata(row.get('currentRootFetchPreserved'),entry['latestDestinationFetch']):return False
    if not any(x.get('professorId')==entry['professorId'] and x.get('officialProfileUrl')==capture['sourceUrl'] for x in row.get('baselineProfessorRelations',[])):return False
    profiles=[x for x in primary['profiles'] if x.get('sourceUrl')==capture['sourceUrl'] and x.get('actualCaptureObservedAt')==capture['observedAt'] and x.get('bodySha256')==capture['bodySha256']]
    if len(profiles)!=1:return False
    profile=profiles[0]
    if profile.get('finalUrl')!=capture['sourceUrl'] or profile.get('originalMetadataSha256')!=capture['metadataSha256'] or profile.get('mainReadCompletely') is not True:return False
    if profile.get('mainTextSha256')!=hashlib.sha256(dom.main().text().encode()).hexdigest():return False
    actual=route.get('actualIndependentProfileCapture',{})
    if any(actual.get(k)!=value for k,value in {'sourceUrl':capture['sourceUrl'],'actualCaptureObservedAt':capture['observedAt'],'bodySha256':capture['bodySha256'],'originalMetadataSha256':capture['metadataSha256']}.items()):return False
    if route.get('rawSha256')!=entry['rawSha256'] or route.get('packetSha256')!=entry['packetSha256'] or not same_fetch_metadata(route.get('latestDestinationFetch'),entry['latestDestinationFetch']):return False
    if route.get('decision')!='unobserved_literal_related_route_requires_independent_date_contract':return False
    if any(route.get(k) is not False for k in ('literalOriginRobotsUnavailable','identityMismatchBoundary','externalTarget')):return False
    if any(route.get(k)!=[] for k in ('exactRequestKeyLogicalAttempts','exactRequestKeyPending','ownWireEvents','ownOneShotJournals','explicitAccessBoundaries','packetExactRequestKeyChecks')):return False
    return True


def reviewed_historical_profile_links(captures):
    """The original contract still requires the exact baseline capture date."""
    return reviewed_profile_link_entries(captures,read(OUT/'reviewed-profile-lab-links.json',{}).get('items',[]))


def reviewed_independently_dated_profile_links(captures):
    """Separate finite admission for independently reviewed original captures."""
    return reviewed_profile_link_entries(captures,read(OUT/'reviewed-independent-date-profile-links.json',{}).get('items',[]),independent_date=True)


def reviewed_profile_link_entries(captures,entries,*,independent_date=False):
    """Observe reviewed literal lab links, never upgrade a root URL.

    This independent admission cannot broaden the original-listed-URI contract.
    Every source byte, dated baseline relationship and target record is frozen.
    """
    if not entries:return []
    try:
        baseline_bytes=(ROOT/'data/research-atlas.json').read_bytes()
        if hashlib.sha256(baseline_bytes).hexdigest()!=BASELINE_HASH:return []
        atlas=json.loads(baseline_bytes);labs={x['id']:x for x in atlas['labs']}
        professors={x['id']:x for x in atlas['professors']}
    except (OSError,KeyError,ValueError,TypeError):return []
    decisions=read(OUT/'identity-decisions.json',{})
    excluded=set(decisions.get('initialMismatchLabIds',[]))|{x['labId'] for x in decisions.get('items',[])}
    observed=original_uri_attempt_keys(read(OUT/'gap-results.json',{}));refused=set()
    for capture in captures:
        # Pending exact targets also belong to the collector; do not duplicate.
        if capture.get('state') in {'pending','running'}:observed.add(request_key(capture.get('url')))
        for meta in [capture.get('fetch',{})]+capture.get('attemptHistory',[]):
            observed.add(request_key(checked_url(meta)));observed.add(request_key(meta.get('blockedUrl')))
            for hop in meta.get('redirects',[]):
                observed.add(request_key(hop.get('from')))
            if type(meta.get('httpStatus')) is int and 100<=meta['httpStatus']<=599:
                observed.add(request_key(meta.get('finalUrl')))
            if profile_link_access_boundary(meta):
                refused.update(request_key(u) for u in [capture.get('url'),checked_url(meta),meta.get('blockedUrl'),checked_url(meta.get('robots') or {})])
    result=[]
    for entry in entries:
        try:
            purpose='observe_literal_independently_dated_profile_lab_link' if independent_date else 'observe_literal_historical_profile_lab_link'
            if not isinstance(entry,dict) or entry.get('purpose')!=purpose or entry.get('observationOnly') is not True:continue
            if entry.get('baselineSha256')!=BASELINE_HASH or not valid_time(entry.get('reviewedAt')):continue
            if type(entry.get('maxPageBytes')) is not int or entry['maxPageBytes']!=DEFAULT_PAGE_MAX_BYTES:continue
            lid=entry['labId'];lab=labs[lid]
            if lid in excluded:continue
            # urlsplit discards some leading whitespace/control bytes. They
            # are not an observed literal wire URI and must never be repaired.
            if not isinstance(entry['url'],str) or any(c.isspace() or ord(c)<32 or ord(c)==127 for c in entry['url']) or '#' in entry['url']:continue
            target=request_key(entry['url']);listed=request_key(entry['listedWebsite'])
            if not target or not listed or target[0]!='http' or listed[0]!='https' or target[1:]!=listed[1:]:continue
            parsed=urllib.parse.urlsplit(entry['url'])
            if parsed.fragment or parsed.port is not None or not (parsed.hostname or '').endswith('.ucsd.edu'):continue
            if target in observed or lab.get('labWebsiteUrl')!=entry['listedWebsite']:continue
            packet_path=OUT/'packets'/(lid+'.json');raw_path=OUT/'records'/(lid+'.json')
            if hashlib.sha256(packet_path.read_bytes()).hexdigest()!=entry['packetSha256'] or hashlib.sha256(raw_path.read_bytes()).hexdigest()!=entry['rawSha256']:continue
            packet=read(packet_path);raw=read(raw_path);identity=raw.get('identity',{})
            if packet.get('labId')!=lid or raw.get('labId')!=lid or packet.get('listedWebsite')!=entry['listedWebsite']:continue
            if raw.get('status') not in {'partial','unresolved'} or identity.get('status')=='mismatch' or identity.get('hasUnresolvedMismatch'):continue
            if not same_fetch_metadata(packet.get('latestDestinationFetch'),entry.get('latestDestinationFetch')):continue
            metadata=[packet.get('latestDestinationFetch',{})]+packet.get('destinationAttemptHistory',[])
            metadata += [x.get('fetch',x) for field in ['relatedDestinationChecks','followupChecks'] for x in packet.get(field,[])]
            if any(profile_link_access_boundary(x) for x in metadata):continue
            roots={target,listed}
            for u in [entry['url'],entry['listedWebsite']]:
                p=urllib.parse.urlsplit(u);roots.add(request_key(urllib.parse.urlunsplit((p.scheme,p.netloc,'/robots.txt','',''))))
            if roots & refused or cached_robots_boundary(entry['url']) or profile_link_origin_unavailable(entry['url'],captures):continue
            capture=entry['profileCapture'];url=capture['sourceUrl'];profile=urllib.parse.urlsplit(url)
            if profile.scheme!='https' or profile.netloc!='profiles.ucsd.edu' or profile.query or profile.fragment or not profile.path.strip('/'):continue
            if entry['professorId'] not in lab.get('professorIds',[]) or professors[entry['professorId']].get('officialProfileUrl')!=url:continue
            body_path=Path(capture['bodyPath']).resolve();meta_path=Path(capture['metadataPath']).resolve()
            if not body_path.is_relative_to(OUT.resolve()) or not meta_path.is_relative_to(OUT.resolve()):continue
            body=body_path.read_bytes();meta_bytes=meta_path.read_bytes();meta=json.loads(meta_bytes)
            if hashlib.sha256(body).hexdigest()!=capture['bodySha256'] or hashlib.sha256(meta_bytes).hexdigest()!=capture['metadataSha256']:continue
            if meta.get('sourceUrl')!=url or meta.get('finalUrl')!=url or meta.get('observedAt')!=capture['observedAt'] or not valid_time(capture['observedAt']):continue
            if meta.get('sha256')!=capture['bodySha256'] or meta.get('status')!='ok' or type(meta.get('httpStatus')) is not int or meta['httpStatus']!=200 or profile_link_access_boundary(meta):continue
            label=entry['literalAnchor']['label']
            if entry['literalAnchor'].get('href')!=entry['url'] or not isinstance(label,str) or not label.strip():continue
            proofs=lab.get('fieldEvidence',{}).get('labWebsiteUrl',[])
            proof_time=entry.get('historicalFieldObservedAt') if independent_date else capture['observedAt']
            proofs=[proof for proof in proofs if proof.get('sourceUrl')==url and proof.get('observedAt')==proof_time and proof.get('status')=='verified' and
                    proof.get('method') in {'official_profile_explicit_lab_link','official_profile_generic_lab_link'} and
                    proof.get('evidence')==label+' → '+entry['listedWebsite'] and
                    hashlib.sha256(json.dumps(proof,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()==entry['fieldProofSha256']
                    ]
            if not proofs:continue
            dom=DOM(decode_cached_html(body)[0])
            if not profile_lab_anchor(dom,entry['url'],label):continue
            if independent_date and not independent_profile_date_review(entry,proofs[0],capture,dom):continue
        except (OSError,KeyError,ValueError,TypeError,AttributeError):continue
        result.append(dict(entry,labIds=[lid],kind=INDEPENDENT_PROFILE_LINK_KIND if independent_date else PROFILE_LINK_KIND,priority=2,
            discoveryMechanism='independently_dated_profile_literal_lab_anchor' if independent_date else 'historical_profile_literal_lab_anchor',
            label='reviewed literal historical profile lab link',
            notAnAcceptedCanonicalLabUrl=True,notAnOriginalListedURLCheck=True,
            observationScope='related_historical_profile_link_only'))
    return result


def reviewed_official_source_gaps(captures):
    """Check only curated historical field-source references, not new anchors."""
    entries=read(OUT/'reviewed-official-source-gaps.json',{}).get('items',[])
    if not entries:return []
    try:
        baseline_bytes=(ROOT/'data/research-atlas.json').read_bytes()
        if hashlib.sha256(baseline_bytes).hexdigest()!=BASELINE_HASH:return []
        baseline={lab['id']:lab for lab in json.loads(baseline_bytes)['labs']}
    except (OSError,KeyError,ValueError,TypeError):return []
    refused=set()
    for capture in captures:
        for meta in [capture.get('fetch',{})]+capture.get('attemptHistory',[]):
            if explicit_access_boundary(meta):
                refused.update(request_key(url) for url in [checked_url(meta),meta.get('blockedUrl')])
            robots=meta.get('robots') or {}
            if explicit_access_boundary(robots):refused.add(request_key(checked_url(robots)))
    result=[]
    for entry in entries:
        if not isinstance(entry,dict) or entry.get('baselineSha256')!=BASELINE_HASH or entry.get('purpose')!='verify_historical_lab_identity' or not valid_time(entry.get('reviewedAt')):continue
        lid=entry.get('labId');field=entry.get('field');url=entry.get('url')
        if not isinstance(lid,str) or lid not in baseline or not isinstance(field,str) or field not in {'labName','labWebsiteUrl'} or not isinstance(url,str):continue
        target=request_key(url)
        if not target or target[0]!='https' or target[2] not in {None,443}:continue
        parsed=urllib.parse.urlsplit(url);host=target[1]
        if not (host=='ucsd.edu' or host.endswith('.ucsd.edu')) or parsed.fragment or url!=url.strip():continue
        if host in {'sso.ucsd.edu','shibboleth.ucsd.edu'} or re.search(r'/(?:login|signin|sign-in|sso|saml|oauth2?|authorize|shibboleth)(?:[/.?]|$)',parsed.path,re.I):continue
        robots_url=urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,'/robots.txt','',''))
        if {target,request_key(robots_url)} & refused:continue
        raw=read(OUT/'records'/(lid+'.json'),{})
        if raw.get('labId')!=lid or raw.get('status') not in {'partial','unresolved'}:continue
        proofs=baseline[lid].get('fieldEvidence',{}).get(field,[])
        proof=next((p for p in proofs if isinstance(p,dict) and p.get('sourceUrl')==url and
            valid_time(p.get('observedAt')) and p['observedAt']==entry.get('fieldObservedAt') and
            hashlib.sha256(json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()==entry.get('fieldProofSha256')),None)
        if proof is None:continue
        result.append({'url':url,'labIds':[lid],'kind':'reviewed_official_identity_source_gap','priority':2,
            'purpose':entry['purpose'],'reviewedAt':entry['reviewedAt'],'baselineSha256':BASELINE_HASH,
            'historicalReferenceOnly':True,'notAnAcceptedCanonicalLabUrl':True,
            'discoveryMechanism':'reviewed_historical_field_source','maxPageBytes':DEFAULT_PAGE_MAX_BYTES,
            'historicalFieldReference':{'field':field,'sourceUrl':url,'observedAt':proof['observedAt'],'fieldProofSha256':entry['fieldProofSha256']},
            'label':'reviewed historical official identity source',
            'reason':entry.get('reason') or 'Finite historical field-source check; no current capture, anchor or entity acceptance inferred.'})
    return result


def plan():
    manifest=read(OUT/'manifest.json')
    items=[];seen={};available={};actual_available={}
    captures=list(read(CACHE/'queue.json')['items'].values())+list(read(OUT/'gap-results.json',{}).get('items',{}).values())
    for capture in captures:
        meta=capture.get('fetch',{});actual=request_key(checked_url(meta))
        if actual and meta.get('observedAt','') >= actual_available.get(actual,{}).get('fetch',{}).get('observedAt',''):
            actual_available[actual]=capture
        for url in [capture['url'],capture.get('fetch',{}).get('finalUrl','')]:
            k=key(url)
            if k and capture.get('fetch',{}).get('observedAt','') >= available.get(k,{}).get('fetch',{}).get('observedAt',''):
                available[k]=capture
    def add(entry):
        k=('listed_request',request_key(entry['url'])) if entry.get('kind') in EXACT_REQUEST_KINDS else key(entry['url'])
        if not k:return
        if k in seen:
            seen[k]['labIds']=list(dict.fromkeys(seen[k]['labIds']+entry['labIds']))
            if entry.get('observationOnly') is True:
                seen[k]['observationOnly']=True
                seen[k]['maxPageBytes']=min(seen[k].get('maxPageBytes',DEFAULT_PAGE_MAX_BYTES),entry.get('maxPageBytes',DEFAULT_PAGE_MAX_BYTES))
                reviews=seen[k].setdefault('originalURIObservationReviews',[])
                for review in entry.get('originalURIObservationReviews',[]):
                    if review not in reviews:reviews.append(review)
            return
        items.append(entry);seen[k]=entry
    for decision in read(OUT/'identity-decisions.json',{}).get('items',[]):
        for followup in decision.get('priorityFollowups',[]):
            add({'url':followup['url'],'labIds':[decision['labId']],'label':followup['kind'],'kind':'identity_review_followup','priority':1,'reason':decision['decision'],'notAnAcceptedCanonicalLabUrl':True})
    # Research can already be supported while its literal listed HTTP address
    # has never been requested. Only separately reviewed, unchanged captures
    # admit these gaps; a normalized HTTPS result cannot close them.
    for entry in read(OUT/'reviewed-listed-url-gaps.json',{}).get('items',[]):
        valid=[]
        for lid in entry['labIds']:
            packet=read(OUT/'packets'/(lid+'.json'));raw=read(OUT/'records'/(lid+'.json'))
            if not packet or not raw or packet.get('listedWebsite')!=entry['url']:continue
            meta=packet.get('latestDestinationFetch') or {};binding=entry.get('relatedCapture',{})
            if any(binding.get(k)!=v for k,v in {'requestedUrl':checked_url(meta),'sourceUrl':meta.get('finalUrl'),'observedAt':meta.get('observedAt'),'bodySha256':meta.get('sha256')}.items()):continue
            a=urllib.parse.urlsplit(entry['url']);b=urllib.parse.urlsplit(checked_url(meta) or '')
            if (a.hostname,(a.path or '/'),a.query)!=(b.hostname,(b.path or '/'),b.query):continue
            try:_,url=hydrate(raw,packet)
            except (AssertionError,KeyError,ValueError,TypeError):continue
            if url['listedUrlDirectlyChecked'] or url['transportStatus']!='ok' or url['pageIdentity']['status']!='confirmed' or url['entityAcceptanceStatus']!='accepted_lab_group':continue
            valid.append(lid)
        if valid:
            add(dict(entry,labIds=valid,kind='listed_url_direct_provenance_gap',priority=2,
                label='literal listed URL with only a related-address capture',
                reason='Separately reviewed original-address request gap; no HTTP redirect inferred from URL normalization.',
                notAnAcceptedCanonicalLabUrl=True))
    # This separate reviewed path also admits unresolved entities and HTTPS
    # transport failures. It cannot alter hydrate's science/identity gates.
    for entry in reviewed_original_uri_observations(captures):add(entry)
    for entry in reviewed_historical_profile_links(captures):add(entry)
    for entry in reviewed_independently_dated_profile_links(captures):add(entry)
    for entry in reviewed_official_source_gaps(captures):add(entry)
    # Explicitly reviewed same-site identity/research gaps may originate on a
    # personal page or an uncertain lab. Their purpose is to establish scope;
    # they do not require or imply prior entity acceptance.
    for entry in read(OUT/'reviewed-gap-additions.json',{}).get('items',[]):
        ids=entry['labIds']
        if not ids or any(read(OUT/'records'/(lid+'.json'))['status']=='supported' for lid in ids):continue
        if entry.get('discoveryMechanism') in {'html_frame_source','html_document_preload','html_image_map_area'} and (
            not entry.get('sourceId') or not valid_time(entry.get('sourceObservedAt')) or
            not valid_time(entry.get('reviewedAt')) or
            not isinstance(entry.get('sourceBodySha256'),str) or
            not re.fullmatch(r'[0-9a-f]{64}',entry['sourceBodySha256'])):continue
        packet=read(OUT/'packets'/(ids[0]+'.json'))
        source=next((s for s in packet['sources'] if s['sourceId']==entry['sourceId']),None)
        if not source or not source.get('cachePath') or source['observedAt']!=entry['sourceObservedAt']:
            continue
        if entry.get('sourceBodySha256') and entry['sourceBodySha256']!=source.get('bodySha256'):continue
        if (packet.get('latestDestinationFetch') or {}).get('status')!='ok':continue
        body=Path(source['cachePath']).read_bytes()
        if source.get('bodySha256') and hashlib.sha256(body).hexdigest()!=source['bodySha256']:continue
        dom=DOM(decode_cached_html(body)[0])
        def anchors(node):
            if node.tag=='a' and node.attrs.get('href'):yield urllib.parse.urljoin(source['sourceUrl'],node.attrs['href']).split('#',1)[0]
            for child in node.children:
                if hasattr(child,'tag'):yield from anchors(child)
        if entry.get('discoveryMechanism')=='html_meta_refresh':
            # Only a separately model-reviewed literal directive can admit a
            # cross-host target. It never rewrites canonical/HTTP observations.
            if not any(key(x['targetUrl'])==key(entry['url']) for x in html_meta_refreshes(dom,source['sourceUrl'])):continue
        elif entry.get('discoveryMechanism')=='html_frame_source':
            # A literal frame discovers another document; it proves neither an
            # HTTP redirect/canonical URL nor the target's research or identity.
            if explicit_access_boundary(packet.get('latestDestinationFetch')):continue
            target=request_key(entry['url']);origin=request_key(source['sourceUrl'])
            if not target or not origin or target[1]!=origin[1]:continue
            def frame_sources(node):
                if node.tag in {'frame','iframe'} and node.attrs.get('src'):yield node.attrs['src']
                for child in node.children:
                    if hasattr(child,'tag'):yield from frame_sources(child)
            if not any(('originalHtmlAttribute' not in entry or src==entry['originalHtmlAttribute']) and
                request_key(urllib.parse.urljoin(source['sourceUrl'],src))==target
                for src in frame_sources(dom.root)):continue
        elif entry.get('discoveryMechanism')=='html_document_preload':
            # A reviewed document preload is discovery only. Never evaluate a
            # script or turn this HTML declaration into a redirect/canonical.
            if explicit_access_boundary(packet.get('latestDestinationFetch')):continue
            target=request_key(entry['url']);origin=request_key(source['sourceUrl'])
            href=entry.get('originalHtmlAttribute')
            if not target or not origin or target[1]!=origin[1] or not isinstance(href,str) or not href:continue
            if not any(node.tag=='link' and 'preload' in node.attrs.get('rel','').lower().split() and
                node.attrs.get('as','').strip().lower()=='document' and node.attrs.get('href')==href and
                request_key(urllib.parse.urljoin(source['sourceUrl'],href))==target
                for node in dom.root.walk()):continue
        elif entry.get('discoveryMechanism')=='html_image_map_area':
            # Only an individually reviewed area in an actually referenced map
            # discovers a document. It is never a redirect or identity proof.
            if explicit_access_boundary(packet.get('latestDestinationFetch')):continue
            target=request_key(entry['url']);origin=request_key(source['sourceUrl'])
            href=entry.get('originalHtmlAttribute');map_name=entry.get('mapName')
            if not target or not origin or target[1]!=origin[1] or not isinstance(href,str) or not href or not isinstance(map_name,str) or not map_name:continue
            def map_nodes(node):
                if node.tag in {'script','style','noscript','template'}:return
                yield node
                for child in node.children:
                    if hasattr(child,'tag'):yield from map_nodes(child)
            nodes=list(map_nodes(dom.root))
            if not any(node.tag=='img' and node.attrs.get('usemap')=='#'+map_name for node in nodes):continue
            def reviewed_area(node):
                if node.tag!='area' or node.attrs.get('href')!=href:return False
                parent=node.parent
                while parent is not None and parent.tag!='map':parent=parent.parent
                return parent is not None and parent.attrs.get('name')==map_name and request_key(urllib.parse.urljoin(source['sourceUrl'],href))==target
            if not any(reviewed_area(node) for node in nodes):continue
        else:
            if urllib.parse.urlsplit(entry['url']).hostname!=urllib.parse.urlsplit(source['sourceUrl']).hostname:continue
            if not any(key(url)==key(entry['url']) for url in anchors(dom.root)):continue
        add(dict(entry,priority=2,notAnAcceptedCanonicalLabUrl=True))
    for item in manifest['items']:
        record=read(OUT/'records'/(item['labId']+'.json'))
        if not record or record['status']=='supported':continue
        packet=read(item['packetPath']);meta=packet.get('latestDestinationFetch') or {}
        if not meta and key(packet.get('listedWebsite')):
            add({'url':packet['listedWebsite'],'labIds':[item['labId']],'label':'listed URL with historical check only','linkedFrom':None,'sourceObservedAt':(packet.get('historicalWebsiteCheck') or {}).get('observedAt'),'kind':'historical_url_live_gap','priority':2,'reason':'Individually reviewed baseline record has no current-round destination capture.'})
        # Never turn a denied/login/challenge root into alternate-route probes.
        if meta.get('status')!='ok' or record['identity']['status']!='confirmed' or record['identity']['entityType'] not in {'lab','research_group','center_or_institute','facility'}:continue
        for source in packet['sources']:
            if source['role'] not in {'listed_lab_destination','related_destination_variant'} or not source.get('cachePath'):continue
            dom=DOM(decode_cached_html(Path(source['cachePath']).read_bytes())[0]);base=source['sourceUrl']
            candidates=[(0 if 'research' in label.lower() else 1,label,target) for label,target in research_links(dom,base)]
            for _,label,target in sorted(set(candidates))[:2]:
                add({'url':target,'labIds':[item['labId']],'label':label,'linkedFrom':base,'sourceObservedAt':source['observedAt'],'priority':3,'reason':'Individually reviewed record lacks sufficient research text; explicit same-site research/about link.'})
    for entry in items:
        capture=actual_available.get(request_key(entry['url'])) if entry.get('kind') in EXACT_REQUEST_KINDS else available.get(key(entry['url']))
        meta=(capture or {}).get('fetch',{})
        entry['availability']='not_captured' if not capture else 'awaiting_collection' if capture['state'] in {'pending','running'} else 'historical_evidence_only' if capture['state']=='retained_prior_evidence' and not meta else 'captured_reuse_only' if meta.get('status')=='ok' else 'access_boundary_do_not_bypass' if meta.get('status') in {'robots_denied','authentication_required','access_challenge'} else 'prior_attempt_unresolved'
        entry['requiresLiveFetch']=entry['availability']=='not_captured' or (entry['availability']=='historical_evidence_only' and entry.get('kind') in {'identity_review_followup','reviewed_identity_research_gap','reviewed_official_identity_source_gap'})
        if capture:entry['captureObservedAt']=meta.get('observedAt')
        boundary=cached_robots_boundary(entry['url']) if entry['requiresLiveFetch'] else None
        if boundary:
            entry.update(availability='access_boundary_do_not_bypass',requiresLiveFetch=False,cachedRobotsBoundary=boundary)
    output={'schemaVersion':1,'plannedAt':now(),'status':'coordinated_public_gaps' if coordination_ready() else 'awaiting_verified_shared_coordinator','urlCount':len(items),'liveCandidateCount':sum(x['requiresLiveFetch'] for x in items),'items':items,'policy':'Reuse fresh captures. Only genuine uncaptured public gaps use the verified shared gate; no global wait for Profiles queue. Candidate corrections are not canonical identity acceptance.'}
    atomic(OUT/'gap-plan.json',output);return output


def coordination_snapshot(probe=True):
    process=read(CACHE/'process.json',{});state=process.get('networkCoordination',{})
    if state.get('state')!='active' or state.get('protocolVersion')!=PROTOCOL or state.get('directory')!=str(SHARED) or not SHARED.is_dir() or not state.get('robotsAndRedirectsIncluded') or state.get('profilesMinimumSeconds',0)<10:
        raise RuntimeError('Network not started: active shared protocol receipt is absent or incompatible')
    hashes={};origins={};working={}
    for field,path in [('collectorCodeSha256',CODE),('coordinationCodeSha256',GATE_CODE)]:
        data,origin=verified_source(path,state.get(field,''))
        hashes[field]=hashlib.sha256(data).hexdigest();origins[field]=origin
        working[field]=hashlib.sha256(path.read_bytes()).hexdigest()
    required=state.get('requiredSourceFiles',{})
    if set(required)!=set(SOURCE_ORDER):
        raise RuntimeError('Network not started: complete loaded dependency hashes are absent')
    if required[CODE.name]!=hashes['collectorCodeSha256'] or required[GATE_CODE.name]!=hashes['coordinationCodeSha256'] or required['collection_scope.py']!=state.get('scopePolicyCodeSha256'):
        raise RuntimeError('Network not started: loaded dependency hash receipts disagree')
    required_origins={};required_working={}
    for name in SOURCE_ORDER:
        path=COLLECTION/'scripts'/name
        data,origin=verified_source(path,required[name])
        required_origins[name]=origin
        required_working[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    evidence=None
    if probe:
        result=subprocess.run(['ps','-p',str(int(process['pid'])),'-o','pid=,etime=,args='],capture_output=True,text=True,check=False)
        evidence=result.stdout.strip()
        if result.returncode or 'scripts/collect_ucsd_coverage.py' not in evidence or not evidence.startswith(str(process['pid'])):
            raise RuntimeError('Network not started: collector PID could not be verified live')
    return {'checkedAt':now(),'protocolVersion':PROTOCOL,'protocolDirectory':str(SHARED),'collectorPid':process['pid'],'collectorStartedAt':process['startedAt'],'activation':state,'sourceHashes':hashes,'sourceOrigins':origins,'currentWorkingFileHashes':working,'requiredSourceHashes':dict(required),'requiredSourceOrigins':required_origins,'currentRequiredWorkingFileHashes':required_working,'pidProbe':evidence}


def coordination_ready():
    receipt=read(OUT/'network-coordination.json',{})
    return receipt.get('status')=='ready' and receipt.get('protocolVersion')==PROTOCOL and receipt.get('adapterVerified') is True and receipt.get('collectorConnected') is True and receipt.get('liveRequestsEnabled') is True


def load_fetcher(expected_hashes=None,expected_sources=None):
    # Compile exact pinned source bytes; never create collector __pycache__.
    modules=[];previous=sys.dont_write_bytecode;sys.dont_write_bytecode=True
    try:
        state=read(CACHE/'process.json')['networkCoordination']
        if expected_hashes is not None and any(state.get(field)!=value for field,value in expected_hashes.items()):
            raise RuntimeError('Network not started: collector changed after the verified adapter snapshot')
        required=state.get('requiredSourceFiles',{})
        if expected_sources is not None and required!=expected_sources:
            raise RuntimeError('Network not started: collector dependencies changed after verification')
        if required:
            if set(required)!=set(SOURCE_ORDER) or required[CODE.name]!=state['collectorCodeSha256'] or required[GATE_CODE.name]!=state['coordinationCodeSha256'] or required['collection_scope.py']!=state.get('scopePolicyCodeSha256'):
                raise RuntimeError('Network not started: incomplete or inconsistent loaded dependency receipt')
            sources=[(Path(name).stem if name!=CODE.name else 'readonly_collection_fetcher',COLLECTION/'scripts'/name,required[name]) for name in SOURCE_ORDER]
        else:
            # Historical test fixtures retain their original collector source.
            # Live execution requires the complete seven-source receipt above.
            sources=[('collection_lock',COLLECTION/'scripts/collection_lock.py','06b3b4968f62e32f259c723c02637c701261b778814e387e5ad810b7afc72056'),
                     ('network_coordination',GATE_CODE,state['coordinationCodeSha256']),('readonly_collection_fetcher',CODE,state['collectorCodeSha256'])]
        # Verify every dependency before compiling any definitions. Queue and
        # scope classes are imported only; summary fetches never instantiate them.
        verified=[(name,path,verified_source(path,sha)[0]) for name,path,sha in sources]
        for name,path,source in verified:
            spec=importlib.util.spec_from_file_location(name,path)
            module=importlib.util.module_from_spec(spec);sys.modules[name]=module
            exec(compile(source,str(path),'exec'),module.__dict__)
            modules.append(module)
    finally:sys.dont_write_bytecode=previous
    module=modules[-1]
    discovery_normalizer=module.safe_url
    def preserve_wire_uri(raw):
        # Keep the pinned public-origin validation, then preserve the supplied
        # scheme/host/path. Collector discovery normalization upgrades UCSD
        # HTTP and drops some www prefixes without observing an HTTP redirect.
        if not discovery_normalizer(raw):return ''
        p=urllib.parse.urlsplit(raw)
        return urllib.parse.urlunsplit((p.scheme,p.netloc.lower(),urllib.parse.quote(p.path or '/',safe='/%:@-._~'),p.query,''))
    module.safe_url=preserve_wire_uri
    module.summaryUrlPolicy='preserve_wire_uri_after_pinned_public_origin_validation'
    return module


class RetryAfterDeferred(Exception):pass


def page_live_event(module,url,events):
    return next((event for event in events if event['kind']=='page_or_redirect' and event['url']==module.safe_url(url)),None)


def retry_pauses(ledger):
    pauses=ledger.setdefault('hostRetryAfter',{})
    for item in read(CACHE/'queue.json')['items'].values():
        meta=item.get('fetch',{})
        if meta.get('retryAfterEpoch'):
            for url in [item['url'],meta.get('finalUrl','')]:
                host=urllib.parse.urlsplit(url).hostname
                if host:pauses[host]=max(pauses.get(host,0),meta['retryAfterEpoch'])
    return pauses


def instrumented_fetcher(module,target,ledger):
    class TrackedFetcher(module.PublicFetcher):
        currentPageMaxBytes=DEFAULT_PAGE_MAX_BYTES
        currentOriginalObservationUrl=None

        def _wire(self,url,minimum=1,max_bytes=DEFAULT_PAGE_MAX_BYTES):
            # Robots explicitly pass 300,000; only the default page/redirect
            # cap can change, and only for this reviewed fetch lifecycle.
            if max_bytes==DEFAULT_PAGE_MAX_BYTES:max_bytes=self.currentPageMaxBytes
            return super()._wire(url,minimum,max_bytes)

        def _rules(self,url):
            rules,meta=super()._rules(url)
            # An explicit challenge takes precedence over an HTTP 404/410
            # classification. Keep the original robots cache, status code and
            # observation time intact; this copy records our access decision.
            if meta.get('error')=='access_challenge' and meta.get('status')!='unavailable':
                return None,dict(meta,status='unavailable',collectorClassifiedStatus=meta['status'],summaryAccessBoundaryEnforced=True)
            return rules,meta

        def _transport(self,url,max_bytes):
            # Called inside the shared host lock, including robots/redirects.
            host=urllib.parse.urlsplit(url).hostname
            pauses=retry_pauses(ledger)
            if pauses.get(host,0)>time.time():raise RetryAfterDeferred(url)
            event={'url':url,'startedAt':now(),'startedEpoch':time.time(),'kind':'robots' if urllib.parse.urlsplit(url).path.endswith('/robots.txt') else 'page_or_redirect','sharedProtocol':PROTOCOL,'maxResponseBytes':max_bytes}
            if self.currentOriginalObservationUrl:event['originalObservationUrl']=self.currentOriginalObservationUrl
            ledger.setdefault('wireEvents',[]).append(event)
            ledger['wireRequestsTotal']=len(ledger['wireEvents'])
            atomic(OUT/'gap-results.json',ledger)
            try:
                result=super()._transport(url,max_bytes)
                code,headers,_,error=result
                event.update(httpStatus=code,error=error,transportReturned=True)
                if code in {429,500,502,503,504}:
                    value=headers.get('retry-after','')
                    try:seconds=float(value)
                    except ValueError:
                        try:seconds=email.utils.parsedate_to_datetime(value).timestamp()-time.time()
                        except (ValueError,TypeError,OverflowError):seconds=60
                    pauses[host]=max(pauses.get(host,0),time.time()+max(60,seconds))
                return result
            except Exception as exc:
                event.update(transportExceptionType=type(exc).__name__,transportException=str(exc))
                raise
            finally:
                if not event.get('transportReturned'):event['requestOutcome']='transport_started_response_indeterminate'
                event['finishedAt']=now();atomic(OUT/'gap-results.json',ledger)
    return TrackedFetcher(target,timeout=18,delay=1)


def execute(limit):
    if not coordination_ready():raise RuntimeError('Network not started: shared protocol and adapter have not been verified')
    snapshot=coordination_snapshot()
    receipt=read(OUT/'network-coordination.json')
    if receipt.get('sourceHashes')!=snapshot['sourceHashes']:raise RuntimeError('Network not started: adapter receipt code hashes changed')
    if receipt.get('requiredSourceHashes')!=snapshot['requiredSourceHashes']:raise RuntimeError('Network not started: adapter dependency hashes changed')
    if receipt.get('adapterVerification',{}).get('adapterSha256')!=hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
        raise RuntimeError('Network not started: summary adapter changed after verification')
    p=plan();module=load_fetcher(snapshot['sourceHashes'],snapshot['requiredSourceHashes'])
    target=OUT/'gap-cache';target.mkdir(parents=True,exist_ok=True)
    wire_tmp=target/'wire-tmp';wire_tmp.mkdir(exist_ok=True)
    previous_temp=tempfile.tempdir;tempfile.tempdir=str(wire_tmp)
    # Fresh robots may be reused without changing their original observation.
    for source in (CACHE/'responses').glob('robots-*'):
        dest=target/source.name
        if not dest.exists():dest.write_bytes(source.read_bytes())
    ledger=read(OUT/'gap-results.json',{'schemaVersion':1,'items':{},'wireRequestsTotal':0,'wireEvents':[]})
    previous_coordination=ledger.get('coordination')
    if previous_coordination and previous_coordination!=snapshot:
        history=ledger.setdefault('coordinationHistory',[])
        if not history or history[-1]!=previous_coordination:history.append(previous_coordination)
    ledger.update(coordination=snapshot,fetcherSource=str(CODE),fetcherSourceSha256=snapshot['sourceHashes']['collectorCodeSha256'])
    fetcher=instrumented_fetcher(module,target,ledger);attempted=0
    try:
        for candidate in p['items']:
            if attempted>=limit:break
            url=candidate['url'];host=urllib.parse.urlsplit(url).hostname
            if not candidate['requiresLiveFetch'] or url in ledger['items'] or retry_pauses(ledger).get(host,0)>time.time():continue
            page_limit=DEFAULT_PAGE_MAX_BYTES
            if candidate.get('observationOnly') is True:
                if request_key(url) in original_uri_attempt_keys(ledger):continue
                page_limit=original_uri_page_limit(candidate,candidate.get('latestDestinationFetch',{}),candidate['labIds'])
                if page_limit is None:raise RuntimeError('Network not started: original URI page-size review no longer matches')
            start=len(ledger['wireEvents'])
            observation_start=None
            if candidate.get('observationOnly') is True:
                # Persist intent before robots/page transport. A hard stop may
                # leave only this journal; it must never become page proof.
                observation_start={'startedAt':now(),'maxPageBytes':page_limit,
                    'labIds':candidate['labIds'],'state':'started_not_completed',
                    'journalIsNotPageRequestProof':True,'wireEventStart':start,
                    'journalContextKind':candidate.get('kind'),
                    'notAnOriginalListedURLCheck':candidate.get('notAnOriginalListedURLCheck',False)}
                ledger.setdefault('originalUriObservationStarts',{})[url]=observation_start
                atomic(OUT/'gap-results.json',ledger)
            fetcher.currentPageMaxBytes=page_limit
            fetcher.currentOriginalObservationUrl=url if observation_start else None
            failure=None
            try:
                try:meta,body=fetcher.fetch(url)
                except RetryAfterDeferred as exc:
                    meta={'sourceUrl':url,'status':'deferred_retry_after','observedAt':now(),'blockedUrl':str(exc),'retryAfterEpoch':ledger['hostRetryAfter'].get(urllib.parse.urlsplit(str(exc)).hostname)}
                except Exception as exc:
                    failure=exc
                    meta={'sourceUrl':url,'status':'fetch_exception','observedAt':now(),
                        'error':str(exc),'exceptionType':type(exc).__name__,
                        'attemptState':'fetch_lifecycle_incomplete'}
            finally:
                fetcher.currentPageMaxBytes=DEFAULT_PAGE_MAX_BYTES
                fetcher.currentOriginalObservationUrl=None
            meta['summaryPageMaxBytes']=page_limit
            attempted+=1
            events=ledger['wireEvents'][start:]
            actual=page_live_event(module,url,events)
            # Starting a subprocess is indeterminate if it never returns a
            # response/error tuple. Only returned transport evidence proves an
            # original-page attempt, including a returned code-0 curl error.
            proven=actual if actual and type(actual.get('httpStatus')) is int and 0<=actual['httpStatus']<=599 else None
            meta['liveCheckedAt']=proven['startedAt'] if proven else None
            meta['actualPageRequestMade']=bool(proven)
            if actual and not proven:meta['pageRequestEvidence']='transport_started_response_indeterminate'
            if observation_start:
                observation_start.update(state='receipt_saved',finishedAt=now(),
                    outcome=meta['status'],wireEventRange=[start,len(ledger['wireEvents'])])
            ledger['items'][url]={'url':url,'state':'done' if meta['status']=='ok' else 'unresolved','fetch':meta,'contexts':candidate,'responseDirectory':str(target),'wireEventRange':[start,len(ledger['wireEvents'])],'protocolVersion':PROTOCOL,'loadedSourceHashes':snapshot['sourceHashes'],'loadedRequiredSourceHashes':snapshot['requiredSourceHashes']}
            ledger['updatedAt']=now();atomic(OUT/'gap-results.json',ledger)
            print(json.dumps({'url':url,'status':meta['status'],'liveCheckedAt':meta['liveCheckedAt'],'wireRequests':len(events),'labIds':candidate['labIds']},ensure_ascii=False),flush=True)
            if failure is not None:raise failure
    finally:tempfile.tempdir=previous_temp
    return {'attempted':attempted,'completedReceipts':len(ledger['items']),'wireRequestsTotal':ledger['wireRequestsTotal']}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['plan','execute','verify-coordination']);parser.add_argument('--limit',type=int,default=20);args=parser.parse_args()
    if args.limit<1 or args.limit>30:parser.error('--limit must be between 1 and 30')
    if args.action=='verify-coordination':
        result=coordination_snapshot();print(json.dumps(result,ensure_ascii=False))
    else:
        result=plan() if args.action=='plan' else execute(args.limit)
        print(json.dumps({k:v for k,v in result.items() if k!='items'},ensure_ascii=False))
