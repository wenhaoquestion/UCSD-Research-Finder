"""Reverify an original own leadership resource without inventing a new lab.

An old record may list a failed directory-label URI as its website while
already retaining a separate own URI for leadership. Its new named own title,
scoped PI section and independent campus listing establish resource continuity.
This registers only the exact observed URI;it creates no canonical person edge.
"""
import copy
from urllib.parse import urlsplit

from atlas_urls import url_key
from faculty_profile_bindings import captured_source
from lab_entities import LabIndex,named_lab_key
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256,verified_alias_reviews
from refresh_labs import DOM,every_node,evidence_items

KIND='retained_original_own_leadership_resource_reverified'


def classes(node):
    return set(node.attrs.get('class','').split())


def verified_existing_own_resources(review,queue,cache,labs):
    index=LabIndex(labs);items={i['url']:i for i in queue['items'].values()}
    rows=copy.deepcopy(review.get('entries',[]));seen=set()
    for row in rows:
        lab=index.by_id.get(row.get('labId'));original=row.get('originalLabRecord',{})
        uri=row.get('ownResourceUri','');part=urlsplit(uri);name=(lab or {}).get('labName','')
        if (row.get('kind')!=KIND or lab is None or lab['id'] in seen or not row.get('reason')
                or original!=lab or row.get('originalLabRecordSha256')!=record_sha256(lab)
                or lab.get('websiteSharing') or lab.get('professorIds') or lab.get('relatedProfessorNames')
                or lab.get('institution')!='University of California San Diego'
                or part.scheme!='https' or not (part.hostname or '').endswith('.ucsd.edu')
                or part.path!='/' or part.query or part.fragment or uri==lab['labWebsiteUrl']
                or uri not in lab.get('sourceUrls',[]) or len(named_lab_key(name).split())<4
                or {r['id'] for r in index.by_id.values() if named_lab_key(r['labName'])==named_lab_key(name)}!={lab['id']}
                or {r['id'] for r in index.candidates(uri)}-{lab['id']}):
            raise ValueError('Existing own resource requires one unchanged specific original lab and retained campus own URI')
        seen.add(lab['id']);pi=lab.get('principalInvestigator')
        old=evidence_items(lab.get('fieldEvidence',{}).get('principalInvestigator'))
        retained=[p for p in old if p.get('sourceUrl')==uri and p.get('status')=='verified'
                  and p.get('method')=='manual_review_explicit_lab_leadership'
                  and p.get('evidence')=='The research group is directed by Prof. '+str(pi)+'.']
        if (len(retained)!=1 or row.get('retainedLeadershipSourceProof')!=retained[0]
                or pi in {None,'','Not found','Unknown'}):
            raise ValueError('A source URL alone cannot establish original own leadership-resource continuity')
        previous=items.get(lab['labWebsiteUrl'],{}).get('fetch',{})
        if (previous.get('status')!='http_error' or previous.get('httpStatus')!=404
                or row.get('previousPrimaryObservation')!=previous):
            raise ValueError('An existing positive individual resource cannot be replaced by this failed-directory resource scope')
        proofs=row.get('evidence',[]);verify_capture_proofs(proofs,queue,cache,lab['id'])
        keys=['ownTitleEvidence','ownGroupHeadingEvidence','ownMembersTitleEvidence','ownPiSectionEvidence',
              'ownMembersLinkEvidence','campusRosterTitleEvidence','campusNamedGroupEvidence','namedPublisherLinkEvidence']
        if any(row.get(k) not in proofs for k in keys):
            raise ValueError('Resource continuity requires every independently scoped original/own/campus proof')
        title,group,team,role,memberlink,roster_title,roster,publisher=[row[k] for k in keys]
        def document(proof):
            item=items.get(proof.get('requestedUrl'))
            if item is None:raise ValueError('Resource continuity requires the actual original request')
            capture,html=captured_source(item,cache);visited=capture['requestedUrl']
            for hop in item['fetch'].get('redirects',[]):
                if hop.get('from')!=visited or hop.get('httpStatus') not in {301,302,303,307,308}:
                    raise ValueError('Resource continuity requires an actual continuous transport chain')
                visited=hop.get('to')
            if item['fetch'].get('httpStatus')!=200 or visited!=capture['sourceUrl']:
                raise ValueError('Resource continuity requires successful actual captures')
            return DOM(html)
        for p in proofs:document(p)
        own=document(title);members=document(team)
        if (title.get('requestedUrl')!=uri or title.get('sourceUrl')!=uri
                or title.get('evidenceType')!='document_title' or title.get('evidence')!=name
                or [n.text() for n in every_node(own.root) if n.tag=='title']!=[name]
                or group.get('requestedUrl')!=uri or group.get('sourceUrl')!=uri
                or group.get('evidenceType')!='document_heading' or group.get('headingTag')!='h1'
                or group.get('evidence')!=name+' at UC San Diego'
                or team.get('requestedUrl')!=uri+'members' or team.get('sourceUrl')!=uri+'members'
                or team.get('evidenceType')!='document_title' or team.get('evidence')!=name+' - Members'
                or [n.text() for n in every_node(members.root) if n.tag=='title']!=[name+' - Members']
                or role.get('requestedUrl')!=team['requestedUrl'] or role.get('sourceUrl')!=team['sourceUrl']
                or role.get('evidenceType')!='main_text_quote'
                or role.get('evidence')!='Principal Investigator Prof. '+pi):
            raise ValueError('The retained own URI must independently name the same lab and same source-reported PI')
        headings=[n for n in every_node(members.main()) if n.tag=='h1']
        selected=[n for n in headings if n.text()=='Principal Investigator']
        if len(selected)!=1 or not any(n.text()=='Graduate Students' for n in headings):
            raise ValueError('Own leadership requires one explicit PI section before student names')
        # Native Google Sites uses nested section wrappers;scope the heading
        # and subsequent text to the next h1 without changing global parsing.
        content=list(members.main().walk());start=content.index(selected[0])
        end=next((i for i in range(start+1,len(content)) if content[i].tag=='h1'),len(content))
        paragraphs=[n.text() for n in content[start+1:end] if n.tag=='p' and n.text()]
        if paragraphs!=['Prof. '+pi]:
            raise ValueError('Only the sole published PI name before the student section establishes leadership continuity')
        if (memberlink.get('requestedUrl')!=uri or memberlink.get('sourceUrl')!=uri
                or memberlink.get('evidenceType')!='html_attribute' or memberlink.get('elementTag')!='a'
                or memberlink.get('attributeName')!='href' or memberlink.get('attributeValue')!='/members'
                or memberlink.get('linkUrl')!=team['sourceUrl']):
            raise ValueError('Own members page requires the literal published navigation reference')
        ruri=roster.get('sourceUrl','');rp=urlsplit(ruri)
        if (rp.scheme!='https' or rp.hostname!='ece.ucsd.edu' or rp.path!='/faculty-research/ece-laboratories'
                or rp.query or rp.fragment or roster_title.get('sourceUrl')!=ruri
                or roster_title.get('evidenceType')!='document_title'
                or roster_title.get('evidence')!='ECE Laboratories | '+lab['department']
                or roster.get('evidenceType')!='main_text_quote'
                or not roster.get('evidence','').startswith(name+' (Professor ')
                or roster.get('evidence') not in [p.get('evidence') for p in evidence_items(lab.get('fieldEvidence',{}).get('labName'))]):
            raise ValueError('The current named campus department listing must retain the original exact lab declaration')
        lis=[n for n in every_node(document(roster).main()) if n.tag=='li' and n.text()==roster['evidence']
             and [a.text() for a in every_node(n) if a.tag=='a']==[name]]
        if len(lis)!=1:
            raise ValueError('The scientific group must occupy one specifically named campus lab-list row')
        pp=urlsplit(publisher.get('sourceUrl',''))
        named=[n for n in every_node(document(publisher).main()) if n.tag=='h3' and 'faculty_profile_name' in classes(n)]
        if (pp.hostname!='jacobsschool.ucsd.edu' or pp.path!='/faculty/profile'
                or publisher.get('evidenceType')!='named_link' or publisher.get('linkText')!='Website'
                or publisher.get('linkUrl')!=uri or len(named)!=1
                or named[0].text()!=row.get('publisherNameAsPublished')):
            raise ValueError('An independently named original official faculty profile must literally publish the own root')
        alias={'labId':lab['id'],'url':uri,'fieldEvidence':proofs,'reason':row['reason']}
        alias_review={'labId':lab['id'],'url':uri,'originalAliasRecord':alias,
            'originalAliasRecordSha256':record_sha256(alias),'reason':row['reason'],'evidence':proofs}
        row['resourceAlias']=alias
        row['resourceAliasReview']=verified_alias_reviews({'entries':[alias_review]},[alias],queue,cache)[0]
        row['captureVerified']=True
    return rows


def attach_existing_own_resources(coverage,reviews):
    occupied={url_key(a['url']) for a in coverage['labAliases']}
    for row in reviews:
        if not row.get('captureVerified') or not row.get('resourceAliasReview',{}).get('captureVerified'):
            raise ValueError('Existing own resource registration requires its complete capture review')
        if (row.get('resourceAlias',{}).get('labId')!=row.get('labId')
                or row.get('resourceAlias',{}).get('url')!=row.get('ownResourceUri')
                or url_key(row['ownResourceUri']) in occupied):
            raise ValueError('Existing own resource cannot replace or duplicate another reviewed alias')
        occupied.add(url_key(row['ownResourceUri']))
    for row in reviews:
        coverage['labAliases'].append(copy.deepcopy(row['resourceAlias']))
        coverage['labAliasResourceReviews'].append(copy.deepcopy(row['resourceAliasReview']))
