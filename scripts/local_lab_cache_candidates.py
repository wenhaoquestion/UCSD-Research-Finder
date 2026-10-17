"""Find already-captured evidence candidates for individually unresolved labs.

Read-only source discovery, never evidence/identity acceptance or network work.
Candidates require an actual same-site anchor, an existing professor relation,
or a URL in that professor's preserved field evidence. No name/slug guessing.
"""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path
import urllib.parse

from lab_summary_content import ContentDOM, EXTRACTION_VERSION, decode_cached_html
from local_lab_summaries import OUT, CACHE, ROOT, BASELINE_HASH, atomic, key, now, read, research_links, html_meta_refreshes, checked_url


def official(url):
    host=urllib.parse.urlsplit(url).hostname or ''
    return host=='ucsd.edu' or host.endswith('.ucsd.edu')


def all_anchors(node,base):
    if node.tag=='a' and node.attrs.get('href'):
        target=urllib.parse.urljoin(base,node.attrs['href']).split('#',1)[0]
        if key(target):yield node.text().strip(),target
    for child in node.children:
        if hasattr(child,'tag'):yield from all_anchors(child,base)


def source_from_capture(candidate, queue=None):
    """Extract an exact existing capture; admission requires a model review.

    The original queue URL/time/hash must match the bytes. This function never
    substitutes another observation or writes into a collection directory.
    """
    queue=queue or read(CACHE/'queue.json')
    requested=candidate['requestedUrl'];expected=candidate['bodySha256']
    item=next((x for x in queue['items'].values() if x['url']==requested),{})
    attempts=[item.get('fetch',{})]+item.get('attemptHistory',[])
    meta=next((x for x in attempts if x.get('status')=='ok' and x.get('observedAt')==candidate['observedAt'] and x.get('sha256')==expected),None)
    if not meta:raise ValueError('Candidate no longer has its original queue capture: '+requested)
    path=CACHE/'responses'/(hashlib.sha256(requested.encode()).hexdigest()+'.html')
    if path.resolve()!=Path(candidate['cachePath']).resolve():raise ValueError('Unexpected candidate cache path')
    body=path.read_bytes()
    if hashlib.sha256(body).hexdigest()!=expected:raise ValueError('Candidate body changed: '+requested)
    markup,decoding,warning=decode_cached_html(body);dom=ContentDOM(markup);node=dom.main()
    text=node.text();url=meta.get('finalUrl',requested)
    if key(url)!=key(candidate['sourceUrl']):raise ValueError('Candidate final URL changed')
    nodes=list(dom.root.walk())
    source={'sourceUrl':url,'queueUrl':requested,'requestedUrl':checked_url(meta),'checkedUrl':checked_url(meta),'observedAt':meta['observedAt'],
        'text':text,'title':next((n.text() for n in nodes if n.tag=='title'),''),
        'headings':[n.text() for n in node.walk() if n.tag in {'h1','h2','h3'}][:25],
        'sourceContentDates':[{'value':n.attrs.get('content'),'kind':n.attrs.get('property') or n.attrs.get('name')} for n in nodes if n.tag=='meta' and (n.attrs.get('property') or n.attrs.get('name')) in {'article:published_time','article:modified_time','date','datePublished','dateModified','DC.date.issued','dcterms.date'}],
        'textTruncated':False,'bodySha256':expected,'collectorSha256':meta['sha256'],
        'canonicalLinkUrls':[urllib.parse.urljoin(url,n.attrs.get('href','')) for n in nodes if n.tag=='link' and 'canonical' in n.attrs.get('rel','').split()],
        'cachePath':str(path),'captureOrigin':'collection_cache_reuse',
        'redirectChain':meta.get('redirects',[]),'httpStatus':meta.get('httpStatus'),
        'textExtractionVersion':EXTRACTION_VERSION,'sourceDecodingMethod':decoding,
        'sourceDecodingWarning':warning,'role':'reviewed_cached_followup_requires_entity_match'}
    source['sourceId']='src-'+hashlib.sha256((url+'\n'+source['observedAt']+'\n'+text).encode()).hexdigest()[:16]
    source['htmlMetaRefreshes']=html_meta_refreshes(dom,url)
    return source


def scan():
    baseline=(ROOT/'data/research-atlas.json').read_bytes()
    if hashlib.sha256(baseline).hexdigest()!=BASELINE_HASH:raise ValueError('Baseline atlas changed')
    atlas=json.loads(baseline)
    labs={x['id']:x for x in atlas['labs']}
    professors={x['id']:x for x in atlas['professors']}
    queue=read(CACHE/'queue.json')
    by_url=collections.defaultdict(list);by_professor=collections.defaultdict(list)
    for item in queue['items'].values():
        if item.get('fetch',{}).get('status')!='ok':continue
        for url in {item['url'],item['fetch'].get('finalUrl',item['url'])}:
            by_url[key(url)].append(item)
        for context in item.get('contexts',[]):
            if context.get('professorId') and official(item['url']):
                by_professor[context['professorId']].append(item)
    rows=[];parsed={};candidate_total=0
    for entry in read(OUT/'manifest.json')['items']:
        lid=entry['labId'];raw=read(OUT/'records'/(lid+'.json'))
        if raw['status']=='supported':continue
        packet=read(entry['packetPath']);known={key(s['sourceUrl']) for s in packet['sources'] if s.get('cachePath') and s.get('bodySha256')}
        candidates={}
        def add(item,reason):
            meta=item['fetch'];url=meta.get('finalUrl',item['url'])
            if key(url) in known:return
            path=CACHE/'responses'/(hashlib.sha256(item['url'].encode()).hexdigest()+'.html')
            if not path.exists():return
            body=path.read_bytes();digest=hashlib.sha256(body).hexdigest()
            if digest!=meta.get('sha256'):return
            ident=(item['url'],meta['observedAt'],digest)
            if ident not in candidates:
                candidates[ident]={'sourceUrl':url,'requestedUrl':item['url'],
                    'observedAt':meta['observedAt'],'bodySha256':digest,'cachePath':str(path),
                    'discoveryReasons':[],'notAcceptedAsLabResearch':True}
            if reason not in candidates[ident]['discoveryReasons']:
                candidates[ident]['discoveryReasons'].append(reason)
        for pid in labs.get(lid,{}).get('professorIds',[]):
            for item in by_professor[pid]:
                add(item,{'kind':'existing_baseline_professor_relation','professorId':pid,
                    'professorName':professors.get(pid,{}).get('name'),
                    'scopeWarning':'Associated faculty research requires explicit lab/group scope.'})
            for field,proofs in professors.get(pid,{}).get('fieldEvidence',{}).items():
                for proof in proofs if isinstance(proofs,list) else []:
                    url=proof.get('sourceUrl','')
                    if official(url):
                        for item in by_url.get(key(url),[]):
                            add(item,{'kind':'existing_professor_field_evidence_url',
                                'professorId':pid,'field':field,'originalEvidenceTime':proof.get('observedAt')})
        for source in packet['sources']:
            if not source.get('cachePath') or source.get('role','').startswith('historical'):continue
            path=Path(source['cachePath'])
            if not path.exists():continue
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if digest!=source.get('bodySha256'):continue
            if digest not in parsed:parsed[digest]=ContentDOM(decode_cached_html(path.read_bytes())[0])
            dom=parsed[digest];base=source['sourceUrl']
            anchors=list(research_links(dom,base))
            anchors.extend((label,url) for label,url in all_anchors(dom.root,base)
                if official(url) and urllib.parse.urlsplit(url).hostname=='profiles.ucsd.edu')
            for label,url in dict.fromkeys(anchors):
                for item in by_url.get(key(url),[]):
                    add(item,{'kind':'actual_captured_anchor','anchorLabel':label,
                        'linkedFrom':base,'sourceId':source['sourceId'],
                        'sourceObservedAt':source['observedAt']})
        values=list(candidates.values());candidate_total+=len(values)
        rows.append({'labId':lid,'ordinal':entry['ordinal'],'labName':packet['labName'],
            'currentStatus':raw['status'],'entityType':raw['identity']['entityType'],
            'blockers':raw['blockers'],'candidates':values})
    result={'schemaVersion':1,'scannedAt':now(),'collectorUpdatedAt':queue['updatedAt'],
        'collectorCounts':queue['counts'],'baselineSha256':BASELINE_HASH,'recordsExamined':len(rows),
        'recordsWithUnpacketizedCandidates':sum(bool(x['candidates']) for x in rows),
        'candidateCaptureRelationships':candidate_total,'networkRequestsMade':0,'items':rows,
        'policy':'Read-only candidate inventory, no automatic lab scope or identity acceptance. Existing packet sources are excluded; no URL guessing or unrelated organization expansion.'}
    atomic(OUT/'unpacketized-cache-candidates.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='items'}))


if __name__=='__main__':scan()
