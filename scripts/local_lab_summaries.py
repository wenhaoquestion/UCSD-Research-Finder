#!/usr/bin/env python3
"""Offline, resumable lab-summary workspace. Never fetches or edits collection data.

prepare builds inspectable source packets; checkpoint validates model-authored
per-lab records and atomically materializes the public review files. Source
timestamps always come from the capture, never packet construction time.
"""
from __future__ import annotations
import argparse
import collections
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.parse
from refresh_labs import Node, links
from lab_summary_content import ContentDOM as DOM,EXTRACTION_VERSION,decode_cached_html

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/local-lab-summaries'
COLLECTION = Path('/tmp/ucsd-research-20261016')
CACHE = COLLECTION / '.cache/coverage-20261016'
BASELINE_HASH = 'ed451d2888bdbd34024ea16b951e5ae1d3a81262c75aa42a35531f2814ddc44e'
STATES = {'supported', 'partial', 'awaiting_collection', 'unresolved'}
ENTITY_TYPES = {'lab','research_group','center_or_institute','facility','personal_research_site','unconfirmed','educational_resource','departmental_division','research_field_directory','course','clinical_trials_overview'}

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')

def read(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default

def atomic(path, value, jsonl=False):
    path = Path(path)
    assert path.resolve().is_relative_to(ROOT.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=path.name + '.')
    try:
        with os.fdopen(fd, 'w') as f:
            if jsonl:
                for row in value:
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
            else:
                json.dump(value, f, ensure_ascii=False, indent=2)
                f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def key(url):
    p = urllib.parse.urlsplit(url or '')
    if p.scheme not in {'http','https'} or not p.hostname:
        return ''
    return (p.hostname.lower().removeprefix('www.'), p.path.rstrip('/') or '/', p.query)

def request_key(url):
    """Actual request identity; content reuse's scheme/host folding is unsafe here."""
    try:
        p=urllib.parse.urlsplit(url or '')
        if p.scheme not in {'http','https'} or not p.hostname or p.username or p.password:return None
        path=urllib.parse.quote(p.path or '/',safe='/%:@-._~')
        path=re.sub(r'%[0-9a-fA-F]{2}',lambda m:m.group().upper(),path)
        return (p.scheme.lower(),p.hostname.lower(),p.port,path,p.query)
    except ValueError:return None

def checked_url(meta):
    return meta.get('sourceUrl') or meta.get('requestedUrl') or meta.get('url')

def page_request_proven(meta):
    """A fetch target alone is not proof that robots allowed a page request."""
    code=meta.get('httpStatus')
    if meta.get('actualPageRequestMade') is True or (type(code) is int and 0<=code<=599):return True
    actual=request_key(checked_url(meta))
    return bool(actual and any(x.get('httpStatus') in {301,302,303,307,308} and
        request_key(x.get('from'))==actual for x in meta.get('redirects',[])))

def request_scope(meta,listed_url):
    target=checked_url(meta)
    if not request_key(target):return 'unknown_request_provenance'
    matches=request_key(target)==request_key(listed_url)
    if page_request_proven(meta):return 'listed_url_direct_request' if matches else 'related_url_request_only'
    return 'listed_url_access_precheck_only' if matches else 'related_url_access_precheck_only'

def destination_captures(listed_url,items):
    """Prefer an actual listed-URL request over arrival through another URL."""
    direct=[];related=[];seen=set();expected=request_key(listed_url)
    for item in sorted(items,key=lambda x:x.get('fetch',{}).get('observedAt',''),reverse=True):
        meta=item.get('fetch',{});ident=(item['url'],meta.get('observedAt'),meta.get('status'))
        if ident in seen:continue
        seen.add(ident)
        (direct if expected and request_key(checked_url(meta) or item['url'])==expected else related).append(item)
    return direct,related

def source_matches_fetch(source,meta):
    actual=request_key(checked_url(meta))
    captured=request_key(source.get('checkedUrl') or source.get('requestedUrl'))
    digest=meta.get('sha256')
    return bool(page_request_proven(meta) and actual and captured==actual and
        isinstance(digest,str) and re.fullmatch(r'[0-9a-f]{64}',digest) and source.get('bodySha256')==digest and
        source.get('observedAt')==meta.get('observedAt') and
        request_key(source.get('sourceUrl'))==request_key(meta.get('finalUrl')))

def research_links(dom,base):
    """Navigation may discover a source but never becomes research evidence."""
    def every(node):
        yield node
        for child in node.children:
            if isinstance(child,Node):
                yield from every(child)
    choices=[]
    basepath=urllib.parse.urlsplit(base).path
    parts=[x for x in basepath.split('/') if x]
    prefix=basepath.rsplit('/',1)[0]+'/' if '.' in (parts[-1] if parts else '') else basepath.rstrip('/')+'/' if len(parts)>=2 and parts[-1] not in {'home','contact','about','research'} else '/'
    for node in every(dom.root):
        if node.tag!='a' or not node.attrs.get('href'):
            continue
        label=node.text().strip()
        target=urllib.parse.urljoin(base,node.attrs['href']).split('#',1)[0]
        if not key(target) or key(target)[0]!=key(base)[0] or key(target)==key(base):
            continue
        path=urllib.parse.urlsplit(target).path
        if not path.startswith(prefix):
            continue
        descriptive=bool(re.fullmatch(r'(?:our |the |explore our |learn about our |about (?:the |our )?)?(?:research(?: projects| overview| themes| areas| area| interests| program| focus)?|projects?|science|focus|about(?: us| the lab| our lab| the laboratory)?)',label,re.I))
        research_path=bool(re.search(r'/(?:research|science|focus)(?:/|\.|$)',path,re.I))
        if (descriptive or research_path) and not re.search(r'/(?:login|signin|accounts|search)(?:/|$|\?)|\.pdf(?:$|\?)|publications|news|events',target,re.I):
            choices.append((label,target))
    return list(dict.fromkeys(choices))

def html_meta_refreshes(dom,base):
    """Advertised client navigation only; never an observed HTTP redirect."""
    def every(node):
        yield node
        for child in node.children:
            if isinstance(child,Node):yield from every(child)
    result=[]
    for node in every(dom.root):
        if node.tag!='meta' or node.attrs.get('http-equiv','').strip().lower()!='refresh':continue
        content=node.attrs.get('content','')
        match=re.fullmatch(r'\s*(\d+(?:\.\d+)?)\s*;\s*url\s*=\s*(.+?)\s*',content,re.I)
        if not match:continue
        value=match.group(2).strip()
        if len(value)>1 and value[0]==value[-1] and value[0] in {'"',"'"}:value=value[1:-1]
        target=urllib.parse.urljoin(base,value)
        parsed=urllib.parse.urlsplit(target)
        if not key(target) or parsed.username or parsed.password:continue
        item={'content':content,'targetUrl':target,'isObservedHTTPRedirect':False}
        if item not in result:result.append(item)
    return result

def load_labs():
    raw = (ROOT / 'data/research-atlas.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != BASELINE_HASH:
        raise ValueError('Baseline atlas changed')
    baseline = json.loads(raw)
    labs = copy.deepcopy(baseline['labs'])
    known = {x['id'] for x in labs}
    imports = []
    # This frozen, separately audited incremental batch is authorized before
    # global collection completion. It does not widen the completed-export
    # glob or apply aliases, updates, or faculty changes.
    from lab_summary_handoff import load_reviewed_handoff
    additions, receipt = load_reviewed_handoff(baseline, collection=COLLECTION)
    for lab in additions:
        if lab['id'] not in known:
            labs.append(copy.deepcopy(lab));known.add(lab['id'])
            imports.append({'labId':lab['id'],'sourceFile':receipt['sourceFile'],
                'generatedAt':receipt['generatedAt'],'collectionState':'reviewed_incremental',
                'isFinalExport':False,'reviewedHandoff':receipt})
    for path in sorted((COLLECTION/'data/ucsd').glob('coverage*evidence*.json')):
        d = read(path)
        # Only an explicit completed export, with an accepted review decision,
        # can add an ID. Never import discovery/reviewable candidates.
        if d.get('collectionState') != 'completed':
            continue
        approved = {x.get('labId') for x in d.get('reviewedLabDecisions', d.get('review', [])) if x.get('decision',{}).get('action') == 'accept'}
        for lab in d.get('labs', []):
            if lab['id'] not in known and lab['id'] in approved:
                labs.append(lab)
                known.add(lab['id'])
                imports.append({'labId':lab['id'],'sourceFile':str(path),'generatedAt':d.get('generatedAt')})
    return labs, imports

def prepare(*, append_only=False):
    labs, imports = load_labs()
    prior_manifest=read(OUT/'manifest.json',{}) if append_only else {}
    prior_items={item['labId']:item for item in prior_manifest.get('items',[])}
    if append_only:
        # A newly pinned reviewed batch must not re-extract or re-date the
        # existing reviewed packets. Keep their order and provenance intact.
        by_id={lab['id']:lab for lab in labs}
        assert len(prior_items)==len(prior_manifest.get('items',[]))
        for lid,item in prior_items.items():
            assert lid in by_id and item['labName']==by_id[lid]['labName']
            assert item['listedWebsite']==by_id[lid].get('labWebsiteUrl')
            assert (OUT/'packets'/(lid+'.json')).is_file()
        labs=[by_id[lid] for lid in prior_items]+[lab for lab in labs if lab['id'] not in prior_items]
        imports=[item for item in prior_manifest.get('imports',[]) if item['labId'] in prior_items]+[item for item in imports if item['labId'] not in prior_items]
    imports_by_id={item['labId']:item for item in imports}
    professors={p['id']:p for p in read(ROOT/'data/research-atlas.json')['professors']}
    queue = read(CACHE/'queue.json')
    index = {}
    gap_results=read(OUT/'gap-results.json',{})
    review_references=collections.defaultdict(set)
    for receipt_path in OUT.glob('extraction-review-*.json'):
        for review in read(receipt_path,{}).get('items',[]):
            review_references[review.get('labId')].update(review.get('sourceIdsRead',[]))
    all_items=list(gap_results.get('items',{}).values())+list(queue['items'].values())
    for item in all_items:
        index.setdefault(key(item['url']), []).append(item)
        if item.get('fetch',{}).get('finalUrl'):
            index.setdefault(key(item['fetch']['finalUrl']), []).append(item)
    page_cache = {}
    def page(item):
        u = item['url']
        meta = item.get('fetch', {})
        cache_key=(u,item.get('responseDirectory',''),meta.get('observedAt'),meta.get('status'))
        if cache_key in page_cache:
            return page_cache[cache_key]
        cache_url=meta.get('sourceUrl',u) if item.get('responseDirectory') else u
        path = Path(item.get('responseDirectory',CACHE/'responses'))/(hashlib.sha256(cache_url.encode()).hexdigest()+'.html')
        if meta.get('status') != 'ok' or not path.exists():
            page_cache[cache_key] = None
            return None
        body = path.read_bytes()
        digest=hashlib.sha256(body).hexdigest()
        if meta.get('sha256') and meta['sha256']!=digest:
            raise ValueError('Cached body changed under its original observation metadata: '+u)
        markup,decoding_method,decoding_warning = decode_cached_html(body)
        dom = DOM(markup)
        node = dom.main()
        text = node.text()
        title = next((n.text() for n in dom.root.walk() if n.tag == 'title'), '')
        headings = [n.text() for n in node.walk() if n.tag in {'h1','h2','h3'}]
        canonical = [urllib.parse.urljoin(meta.get('finalUrl',u),n.attrs.get('href','')) for n in dom.root.walk() if n.tag=='link' and 'canonical' in n.attrs.get('rel','').split()]
        dates = [{'value':n.attrs.get('content'), 'kind':n.attrs.get('property') or n.attrs.get('name')} for n in dom.root.walk() if n.tag=='meta' and (n.attrs.get('property') or n.attrs.get('name')) in {'article:published_time','article:modified_time','date','datePublished','dateModified','DC.date.issued','dcterms.date'}]
        source = {'sourceUrl':meta.get('finalUrl',u),'queueUrl':u,'requestedUrl':checked_url(meta),'checkedUrl':checked_url(meta),'observedAt':meta.get('observedAt'), 'sourceContentDates':dates, 'title':title,'headings':headings[:25], 'text':text[:18000], 'textTruncated':len(text)>18000,'bodySha256':digest,'collectorSha256':meta.get('sha256'), 'canonicalLinkUrls':canonical,'cachePath':str(path),'captureOrigin':'summary_gap_live_fetch' if item.get('responseDirectory') else 'collection_cache_reuse','redirectChain':meta.get('redirects',[]),'httpStatus':meta.get('httpStatus'), 'links':research_links(dom,meta.get('finalUrl',u))}
        source['textExtractionVersion']=EXTRACTION_VERSION
        source['htmlMetaRefreshes']=html_meta_refreshes(dom,meta.get('finalUrl',u))
        source.update(sourceDecodingMethod=decoding_method,sourceDecodingWarning=decoding_warning)
        page_cache[cache_key] = source
        return source
    manifest=[]
    for n,lab in enumerate(labs):
        if lab['id'] in prior_items:
            assert prior_items[lab['id']]['ordinal']==n
            # Packet bytes/date/order stay fixed; targeted followup imports may
            # have increased their source count since the previous manifest.
            retained=copy.deepcopy(prior_items[lab['id']])
            retained['sourceCount']=len(read(OUT/'packets'/(lab['id']+'.json'))['sources'])
            manifest.append(retained)
            continue
        sources=[]
        seen=set()
        def add_source(source, role):
            if not source or source['sourceUrl'] in seen:
                return
            seen.add(source['sourceUrl'])
            source = dict(source)
            source['role']=role
            source['sourceId']='s'+str(len(sources)+1)
            sources.append(source)
        direct_items,related_items=destination_captures(lab.get('labWebsiteUrl'),index.get(key(lab.get('labWebsiteUrl')),[]))
        primary_items=direct_items+related_items
        for item in primary_items[:2]:
            add_source(page(item),'listed_lab_destination' if item in direct_items else 'related_destination_variant')
        # Only follow explicit links already captured by the collection task.
        for source in list(sources):
            for label,url in source['links']:
                for item in index.get(key(url),[])[:1]:
                    if len(sources)<5:
                        add_source(page(item),'explicit_linked_research_subpage')
        # Preserve field-specific historical provenance; no borrowed timestamps.
        for field,proofs in lab.get('fieldEvidence',{}).items():
            for proof in proofs if isinstance(proofs,list) else [proofs]:
                if not isinstance(proof,dict) or not proof.get('evidence') or not proof.get('observedAt'):
                    continue
                text=proof['evidence']
                source={'sourceUrl':proof['sourceUrl'],'observedAt':proof['observedAt'],'text':text,'title':'Historical field evidence: '+field,'headings':[],'sourceContentDates':[], 'sourceId':'s'+str(len(sources)+1),'role':'historical_field_'+field,'originalMethod':proof.get('method'), 'textTruncated':False}
                if not any(s['sourceUrl']==source['sourceUrl'] and text in s['text'] for s in sources):
                    sources.append(source)
        # Other listed official sources are used for identity/affiliation, with
        # their full captured content available for the research reviewer.
        for url in lab.get('sourceUrls',[]):
            if key(url) and key(url)[0].endswith('ucsd.edu'):
                for item in index.get(key(url),[])[:1]:
                    if len([s for s in sources if not s['role'].startswith('historical')])<8:
                        add_source(page(item),'listed_official_source_requires_entity_localization')
        faculty_urls=[lab.get('principalInvestigatorProfileUrl','')]
        for pid in lab.get('professorIds',[]):
            person=professors.get(pid,{})
            faculty_urls.append(person.get('officialProfileUrl',''))
            # These remain faculty-scoped excerpts. Reviewers must find an
            # explicit lab/group connection before using them for lab claims.
            for proof in person.get('fieldEvidence',{}).get('researchSummary',[]):
                if not proof.get('evidence') or not proof.get('observedAt'):
                    continue
                source={'sourceUrl':proof['sourceUrl'],'observedAt':proof['observedAt'],
                    'text':proof['evidence'],'title':'Associated faculty research: '+person.get('name',''),
                    'headings':[],'sourceContentDates':[],'role':'associated_faculty_research_requires_lab_scope_check',
                    'associatedProfessorId':pid,'associatedProfessorName':person.get('name'),
                    'scopeWarning':'Personal research alone does not prove this lab conducts it.',
                    'originalMethod':proof.get('method'),'textTruncated':False}
                if not any(s['sourceUrl']==source['sourceUrl'] and source['text'] in s['text'] for s in sources):
                    sources.append(source)
        for url in faculty_urls:
            if key(url) and (key(url)[0]=='ucsd.edu' or key(url)[0].endswith('.ucsd.edu')):
                for item in index.get(key(url),[])[:1]:
                    add_source(page(item),'associated_faculty_profile_requires_lab_scope_check')
        for source in read(OUT/'supplemental-sources'/(lab['id']+'.json'),[]):
            # Manually reviewed cross-record captures can corroborate a stable
            # ID without merging IDs or changing the served dataset.
            if not source.get('identityReview'):
                raise ValueError('Supplemental capture requires explicit identity review: '+lab['id'])
            if not any(s['sourceUrl']==source['sourceUrl'] and source['text'] in s['text'] for s in sources):
                sources.append(dict(source))
        # Reviewed identity-followup URLs are evidence candidates only. They do
        # not replace the listed destination or silently change a stable ID.
        followup_urls=[]
        for decision in read(OUT/'identity-decisions.json',{}).get('items',[]):
            if decision['labId']==lab['id']:
                followup_urls.extend(x['url'] for x in decision.get('priorityFollowups',[]))
        for item in gap_results.get('items',{}).values():
            if lab['id'] in item.get('contexts',{}).get('labIds',[]):
                followup_urls.append(item['url'])
        followup_checks=[]
        for followup_url in dict.fromkeys(followup_urls):
            followup_direct,followup_related=destination_captures(followup_url,index.get(key(followup_url),[]))
            matches=followup_direct+followup_related
            if matches:
                item=matches[0];meta=item.get('fetch',{})
                add_source(page(item),'reviewed_followup_requires_entity_match')
                followup_checks.append({'discoveryUrl':followup_url,'checkedUrl':checked_url(meta),'requestedUrl':checked_url(meta) if page_request_proven(meta) else None,'pageRequestProven':page_request_proven(meta),'checkMatchesDiscoveryUrl':bool(request_key(checked_url(meta)) and request_key(checked_url(meta))==request_key(followup_url)),'finalUrl':meta.get('finalUrl'),'redirectChain':meta.get('redirects',[]),'transportStatus':meta.get('status','not_captured'),'observedAt':meta.get('observedAt'),'liveCheckedAt':meta.get('liveCheckedAt') if item.get('responseDirectory') else None,'checkOrigin':'summary_task_live_request' if item.get('responseDirectory') and meta.get('actualPageRequestMade') else 'summary_task_cache_reuse' if item.get('responseDirectory') and meta.get('status')=='ok' else 'summary_task_access_precheck' if item.get('responseDirectory') else 'reused_collection_capture','notAnAcceptedCanonicalLabUrl':True})
        for s in sources:
            s.pop('links',None)
            s['sourceId']='src-'+hashlib.sha256((s['sourceUrl']+'\n'+s['observedAt']+'\n'+s['text']).encode()).hexdigest()[:16]
        # A new capture must not invalidate previously reviewed historical
        # evidence. Retain referenced packet sources under the same stable ID.
        old_packet=read(OUT/'packets'/(lab['id']+'.json'),{})
        record=read(OUT/'records'/(lab['id']+'.json'),{})
        referenced={e['sourceId'] for e in record.get('evidence',[])}
        referenced.update(review_references.get(lab['id'],set()))
        current_ids={s['sourceId'] for s in sources}
        for s in old_packet.get('sources',[]):
            if s['sourceId'] in referenced and s['sourceId'] not in current_ids:
                sources.append(s)
        latest_item=next((x for x in primary_items if x.get('fetch')),None)
        latest=latest_item.get('fetch') if latest_item else None
        packet={'schemaVersion':1,'ordinal':n,'labId':lab['id'],'labName':lab['labName'],'listedWebsite':lab.get('labWebsiteUrl'),'listedDepartment':lab.get('department'),'listedInstitution':lab.get('institution'),'listedSubtype':lab.get('recordSubtype'),'sources':sources,'latestDestinationFetch':latest,'latestDestinationCheckOrigin':'summary_task_live_request' if latest_item and latest_item.get('responseDirectory') else 'reused_collection_capture' if latest_item else 'preserved_historical_check','destinationQueueStates':sorted({x['state'] for x in primary_items}),'historicalWebsiteCheck':lab.get('websiteCheck'),'preparedAt':now()}
        packet['latestDestinationCheckScope']=request_scope(latest,packet['listedWebsite']) if latest else 'historical_or_unchecked'
        packet['latestDestinationPageRequestProven']=bool(latest and page_request_proven(latest))
        packet['latestDestinationRequestMatchesListed']=bool(latest and request_key(checked_url(latest)) and request_key(checked_url(latest))==request_key(packet['listedWebsite']))
        packet['relatedDestinationChecks']=[{'queueUrl':x['url'],'checkedUrl':checked_url(x.get('fetch',{})),
            'fetch':x.get('fetch',{}),'checkOrigin':'summary_task_live_request' if x.get('responseDirectory') else 'reused_collection_capture',
            'notADirectListedUrlCheck':True} for x in related_items if x.get('fetch')]
        if lab['id'] in imports_by_id:
            packet['importProvenance']=imports_by_id[lab['id']]
            packet['importedUnknownsAndDateBoundaries']={field:copy.deepcopy(lab[field]) for field in ['principalInvestigator','principalInvestigatorProfileUrl','principalInvestigatorIdentityScope','department','departmentAssessment','unverifiedFields','contentDateNote','relatedProfessorNames','relationshipScope','relationshipType','websiteSharing','professorIds'] if field in lab}
        packet['followupChecks']=followup_checks
        attempts={}
        for item in direct_items:
            for attempt in item.get('attemptHistory',[]) or [item.get('fetch',{})]:
                if attempt:
                    attempts[(attempt.get('sourceUrl'),attempt.get('observedAt'),attempt.get('status'))]=attempt
        packet['destinationAttemptHistory']=sorted(attempts.values(),key=lambda x:x.get('observedAt',''))
        atomic(OUT/'packets'/(lab['id']+'.json'),packet)
        manifest.append({k:packet[k] for k in ['ordinal','labId','labName','listedWebsite','destinationQueueStates'] }|{'sourceCount':len(sources),'packetPath':str(OUT/'packets'/(lab['id']+'.json'))})
    active_hosts=sorted({urllib.parse.urlsplit(x['url']).hostname for x in queue['items'].values() if x['state'] in {'pending','running'}})
    atomic(OUT/'manifest.json',{'baselineCount':868,'eligibleCount':len(labs),'imports':imports,'collectorUpdatedAt':queue.get('updatedAt'),'collectorCounts':queue.get('counts'),'collectorActiveHosts':active_hosts,'items':manifest})
    checkpoint()
    print(json.dumps({'eligible':len(labs),'sourcePackets':sum(x['sourceCount']>0 for x in manifest),'collector':queue.get('counts')}))

def valid_time(value):
    if not isinstance(value,str):
        return False
    try:
        return dt.datetime.fromisoformat(value.replace('Z','+00:00')).tzinfo is not None
    except ValueError:
        return False

def extraction_review_state():
    """Recovered prose requires actual model review, never automatic acceptance."""
    impact=read(OUT/'extraction-impact.json',{})
    groups=collections.defaultdict(list)
    for item in impact.get('items',[]):groups[item['labId']].append(item)
    reviews={}
    for path in sorted(OUT.glob('extraction-review-*.json')):
        for item in read(path,{}).get('items',[]):
            if item.get('labId') in groups and valid_time(item.get('reviewedAt')):
                reviews[item['labId']]=item
    completed=[];pending=[];errors=[]
    for lid,changes in groups.items():
        review=reviews.get(lid,{})
        packet=read(OUT/'packets'/(lid+'.json'),{})
        sources={s['sourceId']:s for s in packet.get('sources',[])}
        read_ids=review.get('sourceIdsRead',[])
        if any(sid not in sources for sid in read_ids):errors.append('Unknown recovered review source ID: '+lid)
        recovered=[sources[sid] for sid in read_ids if sid in sources and sources[sid].get('textExtractionVersion')==EXTRACTION_VERSION]
        covered=all(any(key(s['sourceUrl'])==key(change['sourceUrl']) for s in recovered) for change in changes)
        if review.get('decision') in {'changed','unchanged'} and covered:
            completed.append(lid)
        else:pending.append(lid)
    return {'affectedRecordCount':len(groups),'reviewedRecordCount':len(completed),'pendingRecordCount':len(pending),'pendingLabIds':pending,'reviewErrors':errors,'extractionVersion':EXTRACTION_VERSION}

def audit_outputs():
    """Check an actual saved projection, not only the generation code path."""
    m=read(OUT/'manifest.json');cp=read(OUT/'checkpoint.json');q=read(OUT/'queue.json')
    summaries=[json.loads(line) for line in (OUT/'summaries.jsonl').read_text().splitlines()]
    urls=[json.loads(line) for line in (OUT/'url-verification.jsonl').read_text().splitlines()]
    expected=[x['labId'] for x in q['items'] if x['status'] not in {'unprocessed','validation_error'}]
    errors=[];cache_warnings=[]
    for label,rows in [('summary',summaries),('url',urls)]:
        ids=[r['labId'] for r in rows]
        if ids!=expected or len(ids)!=len(set(ids)):
            errors.append(label+' IDs do not equal the complete processed queue snapshot')
    inputs={x['labId']:x for x in m['items']};summary_by_id={x['labId']:x for x in summaries}
    for row in urls:
        entry=inputs.get(row['labId'])
        if not entry:continue
        packet=read(entry['packetPath']);meta=packet.get('latestDestinationFetch') or packet.get('historicalWebsiteCheck') or {}
        summary=summary_by_id.get(row['labId'],{});packet_sources={s['sourceId']:s for s in packet['sources']}
        expected_checked=checked_url(meta);page_proven=page_request_proven(meta)
        if row.get('listedUrl')!=packet['listedWebsite'] or row.get('requestedUrl')!=(expected_checked if page_proven else None) or row.get('checkedUrl')!=expected_checked or row.get('pageRequestProven')!=page_proven:
            errors.append('Projected listed/actual request URL provenance differs from packet: '+row['labId'])
        direct=bool(page_proven and request_key(expected_checked) and request_key(expected_checked)==request_key(packet['listedWebsite']))
        expected_scope=request_scope(meta,packet['listedWebsite'])
        if row.get('listedUrlDirectlyChecked')!=direct or (row.get('canCountAsVerifiedLabGroupURL') and not direct):
            errors.append('Related URL incorrectly counted as a direct listed URL check: '+row['labId'])
        if row.get('checkScope')!=expected_scope or summary.get('lastCheckScope')!=expected_scope or row.get('evidence')!=summary.get('evidence'):
            errors.append('Serialized URL/summary check scopes or evidence disagree: '+row['labId'])
        expected_final=meta.get('finalUrl') if page_proven and meta.get('status') in {'ok','reachable'} else None
        if row.get('lastCheckedAt')!=meta.get('observedAt') or row.get('redirectChain')!=meta.get('redirects',[]) or row.get('canonicalUrl')!=expected_final:
            errors.append('Projected destination time/redirect/final URL differs from actual capture: '+row['labId'])
        if row.get('redirectTargetNormalizationPolicy')!=packet.get('latestDestinationUrlPolicy','collector_discovery_normalization') or row.get('redirectLocationHeadersPreserved') is not False:
            errors.append('Projected redirect normalization/header provenance differs from packet: '+row['labId'])
        if summary.get('lastCheckedAt')!=meta.get('observedAt') or summary.get('lastCheckedUrl')!=expected_checked or summary.get('listedUrlDirectlyChecked')!=direct:
            errors.append('Summary check scope/time differs from actual capture: '+row['labId'])
        history=packet.get('destinationAttemptHistory',[])
        if row.get('attemptHistory')!=history or any(request_key(checked_url(x))!=request_key(packet['listedWebsite']) for x in history):
            errors.append('Original URL attempt history contains unrelated or altered requests: '+row['labId'])
        for proof in summary.get('evidence',[]):
            source=packet_sources.get(proof.get('sourceId'),{});location=proof.get('evidenceLocation','body')
            text=source.get('title','') if location=='title' else ' '.join(source.get('headings',[])) if location=='headings' else source.get('text','')
            if (not proof.get('evidence') or proof['evidence'] not in text or
                any(proof.get(field)!=source.get(field) for field in ['sourceUrl','observedAt','bodySha256'])):
                errors.append('Saved evidence quote/source/time/hash differs from source packet: '+row['labId'])
    if len(q['items'])!=m['eligibleCount'] or sum(cp['counts'].values())!=m['eligibleCount']:
        errors.append('Queue accounting does not equal eligible count')
    eligible={x['labId'] for x in m['items']}
    extras={p.stem for p in (OUT/'records').glob('*.json')}-eligible
    if extras:errors.append('Unexpected record IDs: '+str(sorted(extras)))
    digests={}
    for row in summaries:
        for e in row['evidence']:
            p=urllib.parse.urlsplit(e['sourceUrl'])
            if not key(e['sourceUrl']) or p.username or p.password or not valid_time(e['observedAt']):
                errors.append('Invalid evidence URL/time: '+row['labId'])
            path=e.get('cachePath')
            if path and e.get('bodySha256'):
                if path not in digests:
                    digests[path]=hashlib.sha256(Path(path).read_bytes()).hexdigest() if Path(path).exists() else None
                if digests[path]!=e['bodySha256']:
                    cache_warnings.append({'labId':row['labId'],'cachePath':path,'reason':'Referenced cache is missing or changed; exact historical packet text and original hash remain preserved.'})
    decisions=read(OUT/'identity-decisions.json',{})
    byid={x['labId']:x for x in summaries};url_byid={x['labId']:x for x in urls}
    accepted_mismatches=[]
    for row in summaries:
        if row['identity']['status']=='mismatch' or row['identity'].get('hasUnresolvedMismatch'):
            if row['entityAcceptanceStatus'] in {'accepted','accepted_lab_group','source_supported_other_entity'} or row['status']=='supported':
                accepted_mismatches.append(row['labId'])
    for decision in decisions.get('items',[]):
        lid=decision['labId'];row=byid.get(lid);url=url_byid.get(lid)
        if decision.get('unresolvedMismatch') and (not row or row['status']=='supported' or url.get('canCountAsVerifiedLabGroupURL') or row['entityAcceptanceStatus'] in {'accepted','accepted_lab_group','source_supported_other_entity'}):
            errors.append('Reviewed mismatch improperly accepted: '+lid)
        packet=read(OUT/'packets'/(lid+'.json'));sources={s['sourceId']:s for s in packet['sources']}
        for evidence in decision.get('evidence',[]):
            source=sources.get(evidence['sourceId'],{})
            location=evidence.get('evidenceLocation','body')
            text=source.get('title','') if location=='title' else ' '.join(source.get('headings',[])) if location=='headings' else source.get('text','')
            if evidence['evidence'] not in text or evidence['observedAt']!=source.get('observedAt'):
                errors.append('Identity decision evidence missing/changed: '+lid)
    if accepted_mismatches:errors.append('Unresolved mismatches in accepted counts: '+str(accepted_mismatches))
    gaps=read(OUT/'gap-results.json',{})
    wire_events=gaps.get('wireEvents',[])
    if gaps and gaps.get('wireRequestsTotal')!=len(wire_events):
        errors.append('Own wire total differs from actual event ledger')
    for event in wire_events:
        if not valid_time(event.get('startedAt')) or event.get('sharedProtocol') not in {'fcntl-host-clock-v1','fcntl-host-clock-v2'}:
            errors.append('Own wire event lacks actual time/shared protocol')
    for item in gaps.get('items',{}).values():
        meta=item['fetch'];start,end=item['wireEventRange']
        events=wire_events[start:end]
        if meta.get('actualPageRequestMade'):
            if not any(event['kind']=='page_or_redirect' and event['startedAt']==meta.get('liveCheckedAt') for event in events):
                errors.append('Own page liveCheckedAt does not match a real wire event: '+item['url'])
        elif meta.get('liveCheckedAt'):
            errors.append('Cache/robots-only check falsely has page liveCheckedAt: '+item['url'])
    extraction=extraction_review_state()
    errors.extend(extraction['reviewErrors'])
    integrity=not errors and not cp['validationErrors']
    result={'schemaVersion':1,'checkedAt':now(),'eligibleCount':m['eligibleCount'],'processedSnapshotCount':len(summaries),'uniqueEvidenceCacheFilesChecked':len(digests),'projectionSha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['summaries.jsonl','url-verification.jsonl','queue.json','checkpoint.json']},'errors':errors,'sourceCacheDigestWarnings':cache_warnings,'integrityPassed':integrity,'extractionReview':extraction,'passed':integrity and not extraction['pendingRecordCount']}
    result.update(identityDecisionsReviewed=len(decisions.get('items',[])),unresolvedMismatchAcceptedCount=len(accepted_mismatches))
    atomic(OUT/'validation.json',result)
    return result

def hydrate(raw,packet):
    assert raw['labId']==packet['labId']
    assert raw['status'] in STATES
    assert valid_time(raw.get('reviewedAt')), 'missing actual review time'
    assert raw['identity']['status'] in {'confirmed','uncertain','mismatch'}
    assert raw['identity']['entityType'] in ENTITY_TYPES
    assert raw['affiliation']['status'] in {'source_reported','uncertain','external'}
    for field in ['researchQuestions','topics','methods','uncertainty','blockers']:
        assert isinstance(raw.get(field,[]),list) and all(isinstance(x,str) and x.strip() for x in raw.get(field,[])), field
    sources={s['sourceId']:s for s in packet['sources']}
    evidence=[]
    for e in raw.get('evidence',[]):
        s=sources[e['sourceId']]
        quote=e['quote']
        location=e.get('quoteLocation','body')
        assert location in {'body','title','headings'}
        quoted_source=s.get('title','') if location=='title' else ' '.join(s.get('headings',[])) if location=='headings' else s['text']
        assert len(quote.strip())>=3 and quote in quoted_source, (raw['labId'],'unsupported quote',quote)
        assert valid_time(s.get('observedAt'))
        assert key(s.get('sourceUrl'))
        evidence.append({'sourceId':e['sourceId'],'sourceUrl':s['sourceUrl'],'requestedUrl':s.get('checkedUrl') or s.get('requestedUrl'),'queueUrl':s.get('queueUrl'),'observedAt':s['observedAt'],'captureOrigin':s.get('captureOrigin','preserved_historical_field_evidence'),'sourceContentDates':s.get('sourceContentDates',[]),'sourceTitle':s.get('title'),'sourceHeadings':s.get('headings',[]),'evidence':quote,'evidenceLocation':location,'originalExtractionMethod':s.get('originalMethod'),'supports':e.get('supports',[]),'sourceRole':s['role'],'cachePath':s.get('cachePath'),'bodySha256':s.get('bodySha256'),'collectorSha256':s.get('collectorSha256')})
        evidence[-1]['textExtractionVersion']=s.get('textExtractionVersion','preserved_legacy_extraction_or_field_evidence')
        evidence[-1].update(sourceDecodingMethod=s.get('sourceDecodingMethod'),sourceDecodingWarning=s.get('sourceDecodingWarning'))
        for provenance_field in ['evidenceNature','literalOfficialPageProse','provenanceNote']:
            if provenance_field in e:evidence[-1][provenance_field]=e[provenance_field]
    if raw['status']=='supported':
        assert raw.get('summaryZh') and raw.get('topics') and evidence
        assert raw['identity']['status']=='confirmed'
        assert any('research' in e['supports'] or 'topics' in e['supports'] for e in evidence)
    if raw.get('summaryZh'):
        assert evidence, 'summary requires source evidence'
    if raw.get('methods'):
        assert any('methods' in e['supports'] for e in evidence), 'methods require explicit method evidence'
    if raw['status']!='supported':
        assert raw.get('blockers'), 'non-supported records require concrete blockers'
    if raw['identity']['status']=='confirmed':
        assert any('identity' in e['supports'] for e in evidence), 'confirmed entity needs identity evidence'
    if raw['affiliation']['status']=='source_reported':
        assert any('affiliation' in e['supports'] for e in evidence), 'source-reported affiliation needs evidence'
    acceptance=raw['identity'].get('acceptanceStatus') or ('accepted_lab_group' if raw['status']=='supported' and raw['identity']['entityType'] in {'lab','research_group'} else 'source_supported_other_entity' if raw['status']=='supported' else 'provisional_or_unresolved')
    review=next((x for x in read(OUT/'identity-decisions.json',{}).get('items',[]) if x['labId']==raw['labId'] and x.get('unresolvedMismatch')),None)
    if review:
        assert acceptance not in {'accepted','accepted_lab_group','source_supported_other_entity'} and raw['status']!='supported', 'reviewed unresolved mismatch cannot be accepted by changing a record status'
    if raw['identity']['status']=='mismatch' or raw['identity'].get('hasUnresolvedMismatch'):
        assert acceptance not in {'accepted','accepted_lab_group','source_supported_other_entity'}, 'unresolved identity mismatch cannot be accepted'
        assert raw['status']!='supported', 'mismatch research must remain provisional/partial'
    if acceptance in {'accepted','accepted_lab_group'}:
        assert raw['identity']['status']=='confirmed' and raw['status']=='supported'
    fetch=packet.get('latestDestinationFetch')
    historical=False
    if not fetch:
        fetch=packet.get('historicalWebsiteCheck') or {}
        historical=True
    actual_checked_url=checked_url(fetch)
    matches_listed=bool(request_key(actual_checked_url) and request_key(actual_checked_url)==request_key(packet['listedWebsite']))
    page_proven=page_request_proven(fetch);direct_page=bool(matches_listed and page_proven)
    check_scope=request_scope(fetch,packet['listedWebsite'])
    destination_quotes=[e for e in evidence if e['sourceRole'] in {'listed_lab_destination','related_destination_variant'} and 'identity' in e['supports'] and source_matches_fetch(sources[e['sourceId']],fetch)]
    page_identity={**raw['identity']}
    if fetch.get('status') not in {'ok','reachable'} or not destination_quotes:
        page_identity={'status':'uncertain','entityType':raw['identity']['entityType'],'reason':'本次目的页未取得可匹配身份的正文引证；实体的历史身份结论另列。'}
    url={'labId':raw['labId'],'requestedUrl':packet['listedWebsite'],'canonicalUrl':fetch.get('finalUrl') if fetch.get('status') in {'ok','reachable'} else None,'canonicalBasis':'observed_final_destination_only','canonicalLinkUrls':next((s.get('canonicalLinkUrls',[]) for s in packet['sources'] if s['role']=='listed_lab_destination'),[]),'redirectChain':fetch.get('redirects',[]),'transportStatus':fetch.get('status','not_captured'),'httpStatus':fetch.get('httpStatus'),'lastCheckedAt':fetch.get('observedAt'),'historicalCheckOnly':historical,'robots':fetch.get('robots'),'error':fetch.get('error'),'blockedUrl':fetch.get('blockedUrl'),'queueStates':packet['destinationQueueStates'],'pageIdentity':page_identity,'entityIdentity':raw['identity'],'affiliation':raw['affiliation'],'reviewedAt':raw['reviewedAt'],'evidence':evidence}
    url.update(listedUrl=packet['listedWebsite'],requestedUrl=actual_checked_url if page_proven else None,checkedUrl=actual_checked_url,
        pageRequestProven=page_proven,requestMatchesListedUrl=matches_listed,listedUrlDirectlyChecked=direct_page,checkScope=check_scope,
        canonicalUrl=fetch.get('finalUrl') if page_proven and fetch.get('status') in {'ok','reachable'} else None,
        canonicalBasis='observed_final_destination_only' if direct_page else 'observed_final_destination_of_related_checked_url_only' if page_proven else 'no_page_request_proven',
        relatedDestinationChecks=packet.get('relatedDestinationChecks',[]),
        verificationLimitations=[] if direct_page else ['仅有访问前置检查，未证明实际请求过页面。'] if not page_proven else ['实际检查地址与原列表地址不同或缺少请求地址证明；未据此声称原地址已直接检查或发生HTTP重定向。'])
    url['canonicalLinkUrls']=next((s.get('canonicalLinkUrls',[]) for s in packet['sources'] if s['role'] in {'listed_lab_destination','related_destination_variant'} and source_matches_fetch(s,fetch)),[])
    own_live=packet.get('latestDestinationCheckOrigin')=='summary_task_live_request' and fetch.get('actualPageRequestMade',True)
    own_precheck=packet.get('latestDestinationCheckOrigin')=='summary_task_live_request' and not own_live
    url.update(checkOrigin='summary_task_live_request' if own_live else 'summary_task_cache_reuse' if own_precheck and fetch.get('status')=='ok' else 'summary_task_access_precheck' if own_precheck else 'preserved_historical_check' if historical else 'reused_collection_capture',liveCheckedByThisTask=own_live)
    url.update(observedFinalUrl=fetch.get('finalUrl'),attemptHistory=packet.get('destinationAttemptHistory',[]),preservedHistoricalWebsiteCheck=packet.get('historicalWebsiteCheck'))
    url['liveCheckedAt']=fetch.get('liveCheckedAt',fetch.get('observedAt')) if own_live else None
    url['listedUrlLiveCheckedByThisTask']=bool(own_live and direct_page)
    url['redirectTargetNormalizationPolicy']=packet.get('latestDestinationUrlPolicy','collector_discovery_normalization')
    url['redirectLocationHeadersPreserved']=False
    if url['redirectChain'] and url['redirectTargetNormalizationPolicy']=='collector_discovery_normalization':
        url['verificationLimitations'].append('旧采集器对跳转目标执行发现用URL规范化，且未保留原始Location头；to表示后续实际请求目标，不能完整证明服务器原始跳转指令。')
    url['followupChecks']=packet.get('followupChecks',[])
    url['htmlMetaRefreshes']=[{'sourceId':source['sourceId'],'sourceUrl':source['sourceUrl'],
        'sourceObservedAt':source['observedAt'],'sourceBodySha256':source.get('bodySha256'),**directive}
        for source in packet['sources'] if source['role'] in {'listed_lab_destination','related_destination_variant'} and source_matches_fetch(source,fetch)
        for directive in source.get('htmlMetaRefreshes',[])]
    url['entityAcceptanceStatus']=acceptance
    url['canCountAsVerifiedLabGroupURL']=bool(direct_page and acceptance=='accepted_lab_group' and page_identity['status']=='confirmed' and raw['identity']['entityType'] in {'lab','research_group'} and not raw['identity'].get('hasUnresolvedMismatch'))
    error=' '.join([str(fetch.get('error','')),str((fetch.get('robots') or {}).get('error',''))]).lower()
    url['failureCategory']='dns_error' if 'resolve host' in error else 'timeout' if 'timed out' in error or 'timeout' in error else 'tls_error' if 'certificate' in error or 'ssl' in error else fetch.get('status') if fetch.get('status') not in {'ok','reachable'} else None
    result={'schemaVersion':1,'labId':raw['labId'],'labName':packet['labName'],'status':raw['status'],'summaryZh':raw.get('summaryZh'),'researchQuestions':raw.get('researchQuestions',[]),'topics':raw.get('topics',[]),'methods':raw.get('methods',[]),'evidence':evidence,'lastCheckedAt':url['lastCheckedAt'],'observedAt':sorted({e['observedAt'] for e in evidence}),'sourceContentDates':[{'sourceUrl':e['sourceUrl'],'dates':e['sourceContentDates']} for e in evidence if e['sourceContentDates']],'uncertainty':raw.get('uncertainty',[]),'identity':raw['identity'],'affiliation':raw['affiliation'],'reviewedAt':raw['reviewedAt'],'blockers':raw.get('blockers',[]),'packetPreparedAt':packet['preparedAt']}
    result['entityAcceptanceStatus']=acceptance
    result.update(lastCheckedUrl=actual_checked_url,lastCheckScope=check_scope,listedUrl=packet['listedWebsite'],listedUrlDirectlyChecked=direct_page,pageRequestProven=page_proven)
    result['researchContentSupport']=raw.get('researchContentSupport',{'status':'supported' if raw['status']=='supported' else 'limited_or_not_captured','scope':'identity_matched_entity' if raw['status']=='supported' else 'see_record_uncertainty'})
    if packet.get('importProvenance'):
        for projection in [result,url]:
            projection['importProvenance']=packet['importProvenance']
            projection['importedUnknownsAndDateBoundaries']=packet.get('importedUnknownsAndDateBoundaries',{})
    return result,url

def checkpoint():
    m=read(OUT/'manifest.json')
    if not m:
        return
    summaries=[];urls=[];items=[];errors=[]
    for item in m['items']:
        path=OUT/'records'/(item['labId']+'.json')
        if path.exists():
            try:
                raw=read(path)
                summary,url=hydrate(raw,read(item['packetPath']))
                summaries.append(summary);urls.append(url)
                state=raw['status']
            except (ValueError,KeyError,AssertionError,TypeError) as exc:
                errors.append({'labId':item['labId'],'error':str(exc)})
                state='validation_error'
        else:
            state='unprocessed'
        items.append({'labId':item['labId'],'ordinal':item['ordinal'],'status':state,'recordPath':str(path)})
    ids=[x['labId'] for x in items]
    assert len(ids)==len(set(ids))==m['eligibleCount']
    counts=dict(collections.Counter(x['status'] for x in items))
    urlcounts=dict(collections.Counter(x['transportStatus'] for x in urls))
    collection_pending=sum(m['collectorCounts'].get(k,0) for k in ['pending','running'])
    checkpoint={'schemaVersion':1,'updatedAt':now(),'baselineCount':868,'eligibleCount':len(items),'processedCount':len(summaries),'counts':counts,'entityTypeCounts':dict(collections.Counter(x['identity']['entityType'] for x in summaries)),'supportedLabOrGroupSummaries':sum(x['status']=='supported' and x['identity']['entityType'] in {'lab','research_group'} for x in summaries),'urlTransportCounts':urlcounts,'urlPageIdentityCounts':dict(collections.Counter(x['pageIdentity']['status'] for x in urls)),'urlCheckOriginCounts':dict(collections.Counter(x['checkOrigin'] for x in urls)),'collectorUpdatedAt':m['collectorUpdatedAt'],'collectorCounts':m['collectorCounts'],'imports':m['imports'],'validationErrors':errors,'networkRequestsByThisTask':read(OUT/'gap-results.json',{}).get('wireRequestsTotal',0),'model':'gpt-6.1-sol (confirmed by summary-goal-receipt.jsonl; model-authored synthesis, no external model API)','goalStatusLastRead':'not queried by this offline projection; historical setup is not current Goal proof','baselineReviewComplete':len([x for x in summaries if next(i['ordinal'] for i in items if i['labId']==x['labId'])<868])==868 and not errors,'eligibleReviewComplete':len(summaries)==len(items) and not errors,'collectionStillAwaited':collection_pending>0,'outputsAreComplete':len(summaries)==len(items) and not errors and not collection_pending}
    coordination=read(OUT/'network-coordination.json',{'status':'pending','adapterVerified':False,'collectorConnected':False})
    coordinator_ready=coordination.get('status')=='ready' and coordination.get('adapterVerified') and coordination.get('collectorConnected')
    checkpoint['networkCoordination']=coordination
    checkpoint['entityAcceptanceCounts']=dict(collections.Counter(x['entityAcceptanceStatus'] for x in summaries))
    checkpoint['verifiedAcceptedLabGroupURLCount']=sum(x['canCountAsVerifiedLabGroupURL'] for x in urls)
    checkpoint['urlRequestScopeCounts']=dict(collections.Counter(x['checkScope'] for x in urls))
    checkpoint['listedUrlDirectRequestCount']=sum(x['listedUrlDirectlyChecked'] for x in urls)
    own_gaps=read(OUT/'gap-results.json',{})
    checkpoint['actualPageURLChecksByThisTask']=sum(bool(item.get('fetch',{}).get('actualPageRequestMade')) for item in own_gaps.get('items',{}).values())
    checkpoint['ownGapTransportCounts']=dict(collections.Counter(item['fetch']['status'] for item in own_gaps.get('items',{}).values()))
    checkpoint['urlRootChecksByThisTask']=sum(url['listedUrlLiveCheckedByThisTask'] for url in urls)
    checkpoint['extractionReview']=extraction_review_state()
    checkpoint['baselineInitialReviewComplete']=checkpoint['baselineReviewComplete']
    if checkpoint['extractionReview']['pendingRecordCount'] or checkpoint['extractionReview']['reviewErrors']:
        checkpoint.update(baselineReviewComplete=False,eligibleReviewComplete=False,outputsAreComplete=False)
    followups=[]
    byid={x['labId']:x for x in summaries}
    for url in urls:
        row=byid[url['labId']]
        reasons=[]
        if row['status']!='supported':reasons.append('insufficient_entity_scoped_research')
        if url['pageIdentity']['status']!='confirmed':reasons.append('destination_identity_'+url['pageIdentity']['status'])
        if url['historicalCheckOnly']:reasons.append('only_historical_url_check_available')
        if not reasons:continue
        boundary=url['transportStatus'] in {'robots_denied','authentication_required','access_challenge'}
        followups.append({'labId':url['labId'],'requestedUrl':url['requestedUrl'],'reasons':reasons,'currentTransportStatus':url['transportStatus'],'lastCheckedAt':url['lastCheckedAt'],'checkOrigin':url['checkOrigin'],'modelReviewedAt':row['reviewedAt'],'specificBlockers':row['blockers'],'nextAction':'do_not_bypass_access_boundary' if boundary else 'await_verified_shared_host_coordinator_then_bounded_public_gap_check' if not coordinator_ready else 'reuse_new_capture_or_coordinated_public_gap_check','networkMayStartNow':bool(not boundary and coordinator_ready and urllib.parse.urlsplit(url['requestedUrl']).hostname not in m.get('collectorActiveHosts',[])),'preserveHistoricalEvidence':True})
    checkpoint['followupCount']=len(followups)
    # Record files are the atomic source of truth. Aggregates are replaceable
    # snapshots; checkpoint is replaced last, after both JSONL projections.
    atomic(OUT/'summaries.jsonl',summaries,True)
    atomic(OUT/'url-verification.jsonl',urls,True)
    atomic(OUT/'queue.json',{'schemaVersion':1,'updatedAt':checkpoint['updatedAt'],'items':items})
    atomic(OUT/'followups.json',{'schemaVersion':1,'updatedAt':checkpoint['updatedAt'],'items':followups,'policy':'A follow-up is not a new live verification. Access boundaries remain stopping points.'})
    atomic(OUT/'checkpoint.json',checkpoint)
    review=['# Lab research review\n','This file is a projection of individually reviewed records. Source capture times and model review times are separate. A source link is evidence, not proof of a new live request by this task.\n',f"Reviewed {len(summaries)} / {len(items)} eligible records. Supported lab/group summaries: {checkpoint['supportedLabOrGroupSummaries']}. Live wire requests by this summary task: {checkpoint['networkRequestsByThisTask']}.\n"]
    for row in summaries:
        review += [f"## {row['labName']}\n",f"`{row['labId']}` · {row['status']} · {row['identity']['entityType']}\n",(row['summaryZh'] or '尚无足够来源可写研究总结。')+'\n']
        if row['methods']:review.append('方法：'+'；'.join(row['methods'])+'。\n')
        review.append('不确定性：'+'；'.join(row['uncertainty'])+'\n')
        seen=set()
        for e in row['evidence']:
            ident=(e['sourceUrl'],e['observedAt'])
            if ident not in seen:
                review.append(f"- [官方来源]({e['sourceUrl']}) · 原观察时间 `{e['observedAt']}` · {e['captureOrigin']}")
                seen.add(ident)
        review.append('\n模型审阅时间：`'+row['reviewedAt']+'`。\n')
    (OUT/'REVIEW.md').write_text('\n'.join(review))
    report=ROOT/'docs/operations/LAB-SUMMARY-PROGRESS-20261016.md'
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text('# Local lab summary progress — 2026-10-15 PDT\n\n'+
        'Updated: '+checkpoint['updatedAt']+'\n\n'+
        'Execution: local Mac; configured model GPT-6.1 sol confirmed by setup receipt; formal Goal last read active. '+
        'Worktree `/tmp/ucsd-lab-summaries-20261016`, branch `codex/ucsd-lab-summaries-20261016`. '+
        'Baseline `df18bbed255211fc6bc9b7d6fbec3092306f8afd`; 868 stable lab IDs. No served atlas changes.\n\n'+
        '## Accounting\n\n'+
        '| State | Count |\n|---|---:|\n'+''.join('| '+k+' | '+str(v)+' |\n' for k,v in sorted(counts.items()))+
        '\nEligible: '+str(len(items))+'. Valid processed: '+str(len(summaries))+'. '+
        'Supported lab/group research summaries: '+str(checkpoint['supportedLabOrGroupSummaries'])+'. Other supported entity types are counted separately. '+
        'Entity types: '+json.dumps(checkpoint['entityTypeCounts'])+'. '+
        'Actually checked page identity: '+json.dumps(checkpoint['urlPageIdentityCounts'])+'. '+
        'Verified listed lab/group URLs: '+str(checkpoint['verifiedAcceptedLabGroupURLCount'])+'. '+
        'Actual request scopes: '+json.dumps(checkpoint['urlRequestScopeCounts'])+'. '+
        'Transport: '+json.dumps(urlcounts)+'.\n\n'+
        'Recovered cached-text review: '+str(checkpoint['extractionReview']['reviewedRecordCount'])+' / '+str(checkpoint['extractionReview']['affectedRecordCount'])+' affected records reviewed; '+str(checkpoint['extractionReview']['pendingRecordCount'])+' pending. '+
        'Newly parsed text never counts as model-reviewed automatically. Original capture dates and hashes are retained.\n\n'+
        '## Evidence and boundaries\n\n'+
        'Sources come from read-only collection captures, preserved field evidence, or explicitly coordinated summary-task gap captures. '+
        'Each quotation is checked against the exact source packet. `observedAt` and `lastCheckedAt` preserve actual capture times; `reviewedAt` is the synthesis review time. '+
        'Undated page text remains undated. HTTP 200 does not establish entity identity, current affiliation, or continued operation. '+
        'Failures never erase historical evidence or imply closure. Personal faculty research is not automatically lab research. '+
        'Entity type and affiliation are separate reviewed checks.\n\n'+
        'Collection snapshot: '+str(m['collectorUpdatedAt'])+'; '+json.dumps(m['collectorCounts'])+'. '+
        'This task wire requests: '+str(checkpoint['networkRequestsByThisTask'])+'. Cached URL checks: '+json.dumps(checkpoint['urlCheckOriginCounts'])+'. Cache reads are not new live checks. '+
        ('Live follow-up uses the verified shared host-lock/clock protocol, including robots and every redirect hop. The collector remains active; genuine gaps do not wait for the entire Profiles queue. ' if coordinator_ready else 'Live follow-up is pending verified shared host-lock/clock coordination. ')+
        'New IDs require either a completed collection export with explicit acceptance or the separately audited, hash-pinned reviewed incremental handoff. Only labs are appended; aliases and updates are ignored. Incremental admission does not finalize collection.\n\n'+
        'Network coordination receipt: `data/local-lab-summaries/network-coordination.json`; status '+(str(coordination.get('status'))+'. '+str(coordination.get('reason',''))).rstrip()+'\n\n'+
        '## Resume and validate\n\n'+
        '```sh\ncd /tmp/ucsd-lab-summaries-20261016\npython3 scripts/local_lab_summaries.py prepare --append-reviewed\npython3 scripts/local_lab_summaries.py checkpoint\npython3 scripts/local_lab_summaries.py validate\n```\n\n'+
        'Review `data/local-lab-summaries/queue.json` for unprocessed IDs and individual record blockers. '+
        'Per-record files are atomically replaced; JSONL/checkpoint files are rebuildable projections. '+
        'Refresh packets between batches to consume new captures, then retry awaiting records. '+
        'Local commits only; no push, merge, or deployment.\n\n'+
        'Validation errors: '+json.dumps(errors,ensure_ascii=False)+'.\n')
    return checkpoint

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','checkpoint','validate']);p.add_argument('--append-reviewed',action='store_true');args=p.parse_args()
    if args.append_reviewed and args.action!='prepare':p.error('--append-reviewed applies only to prepare')
    if args.action=='prepare':
        prepare(append_only=args.append_reviewed)
    else:
        cp=checkpoint()
        print(json.dumps({k:cp[k] for k in ['eligibleCount','processedCount','counts','supportedLabOrGroupSummaries','verifiedAcceptedLabGroupURLCount','validationErrors','outputsAreComplete']}
            |{'checkpointPath':str(OUT/'checkpoint.json')},ensure_ascii=False))
        if args.action=='validate':
            audit=audit_outputs()
            print(json.dumps({'passed':audit['passed'],'validationPath':str(OUT/'validation.json')},ensure_ascii=False))
            if not audit['passed']:raise SystemExit(1)

if __name__=='__main__':
    main()
