"""Correct an existing lab's unsupported campus ownership from its own contact.

The original positive named resource, current named home and literal Contact Us
link establish the document scope. Institutional contact is independent of a
person's appointment, identity, PI role or a campus program connection.
"""
import copy
import hashlib
import re
import urllib.parse
from pathlib import Path

from atlas_urls import valid_url
from lab_entities import LabIndex, named_lab_key
from lab_identity_merges import verify_capture_proofs
from lab_resource_reviews import record_sha256
from refresh_labs import DOM, every_node, evidence_items, normalized, unique_values

KIND = 'existing_lab_own_contact_institution'
UCSD = 'University of California San Diego'


def _resource(uri):
    p = urllib.parse.urlsplit(uri)
    # Empty HTTP root paths are the actual / request target; preserve all other
    # path, scheme, query and hostname distinctions (including www).
    return p.scheme.lower(), p.netloc.lower(), p.path or '/', p.query


def verified_lab_ownership_reviews(review, queue, cache, labs):
    index = LabIndex(labs)
    items = {i['url']: i for i in queue['items'].values()}
    rows, seen = copy.deepcopy(review.get('entries', [])), set()
    for row in rows:
        lab = index.by_id.get(row.get('labId'))
        original = row.get('originalLabRecord', {})
        institution = row.get('institution', '')
        displayed = row.get('institutionAsDisplayed', '')
        if (lab is None or lab['id'] != row['labId'] or lab['id'] in seen
                or row.get('kind') != KIND or not row.get('reason')
                or original != lab or row.get('originalLabRecordSha256') != record_sha256(original)
                or lab.get('websiteSharing') or lab.get('institution') != UCSD
                or any(evidence_items(lab.get('fieldEvidence', {}).get(f)) for f in ['institution', 'department'])
                or not isinstance(institution, str) or not 5 <= len(institution) <= 200
                or institution in {UCSD, 'Unknown', 'Not found'}
                or not isinstance(displayed, str)
                or normalized(displayed).removeprefix('the ') != normalized(institution)
                or row.get('departmentContextReview') != {
                    'action':'retain_unverified_routing_context', 'previousDepartment':lab.get('department')}):
            raise ValueError('Lab ownership requires one unchanged existing record and unsupported campus routing')
        seen.add(lab['id'])
        home, contact = row.get('primaryRequestedUri'), row.get('contactRequestedUri')
        if (not valid_url(home) or not valid_url(contact) or _resource(home) != _resource(lab['labWebsiteUrl'])
                or {x['id'] for x in index.candidates(home)} != {lab['id']}):
            raise ValueError('Own institution requires the uniquely owned actual original primary resource')
        proofs = row.get('evidence', [])
        verify_capture_proofs(proofs, queue, cache, lab['id'])
        keys = ['ownIdentityEvidence', 'ownTitleEvidence', 'contactLinkEvidence',
                'contactTitleEvidence', 'institutionEvidence']
        if any(row.get(k) not in proofs for k in keys):
            raise ValueError('Own institution requires all five separately scoped captured proofs')
        identity, title, link, contact_title, claim = [row[k] for k in keys]
        name = row.get('ownLabNameAsDisplayed', '')
        tokens = set(named_lab_key(name).split()) - {'lab', 'laboratory', 'group', 'research'}
        if (not tokens or not any(len(t) >= 4 for t in tokens)
                or not tokens <= set(named_lab_key(lab['labName']).split())
                or identity.get('evidenceType') != 'document_heading' or identity.get('evidence') != name
                or title.get('evidenceType') != 'document_title' or name not in title.get('evidence', '')
                or not title['evidence'].endswith(' - '+institution)
                or lab.get('websiteCheck', {}).get('status') != 'reachable'
                or lab['websiteCheck'].get('title') != title['evidence']
                or any(p['requestedUrl'] != home for p in [identity, title, link])
                or any(p['requestedUrl'] != contact for p in [contact_title, claim])
                or contact_title.get('evidenceType') != 'document_title'
                or contact_title.get('evidence') != 'Contact | '+name+' - '+institution):
            raise ValueError('Institution must belong to the same specifically named original lab and Contact document')
        sources = []
        for uri in [home, contact]:
            item = items[uri]; meta = item['fetch']; visited = uri
            for hop in meta.get('redirects', []):
                if hop.get('from') != visited or hop.get('httpStatus') not in {301,302,303,307,308}:
                    raise ValueError('Own institution requires actual continuous transport observations')
                visited = hop.get('to')
            if visited != meta['finalUrl']:
                raise ValueError('Own institution requires its actual captured destination')
            sources.append(urllib.parse.urlsplit(visited))
        root, child = sources
        prefix = root.path.rstrip('/')
        if ((root.scheme, root.netloc) != (child.scheme, child.netloc)
                or root.query or child.query or child.path.rstrip('/') == prefix
                or not child.path.startswith(prefix+'/')
                or any(p['sourceUrl'] != items[home]['fetch']['finalUrl'] for p in [identity, title, link])
                or any(p['sourceUrl'] != items[contact]['fetch']['finalUrl'] for p in [contact_title, claim])):
            raise ValueError('Contact institution requires the exact own entity path, not a shared host or department page')
        home_dom = DOM((Path(cache)/'responses'/(hashlib.sha256(home.encode()).hexdigest()+'.html')).read_text())
        anchors = [n for n in every_node(home_dom.root) if n.tag == 'a'
                   and n.attrs.get('href') == link.get('attributeValue') and n.text() == 'Contact Us']
        def own_navigation(node):
            parent = node.parent
            while parent:
                if parent.tag == 'nav':
                    return True
                parent = parent.parent
            return False
        if (link.get('evidenceType') != 'html_attribute' or link.get('elementTag') != 'a'
                or link.get('attributeName') != 'href'
                or urllib.parse.urljoin(items[home]['fetch']['finalUrl'], link['attributeValue']) != contact
                or not any(own_navigation(n) for n in anchors)):
            raise ValueError('Own institution requires the named primary Contact Us navigation field')
        contact_dom = DOM((Path(cache)/'responses'/(hashlib.sha256(contact.encode()).hexdigest()+'.html')).read_text()).main()
        text = claim.get('evidence', '')
        if (claim.get('evidenceType') != 'main_text_quote'
                or claim.get('method') != 'reviewed_own_lab_contact_institution'
                or not 20 <= len(text) <= 800 or displayed not in text
                or not re.search(r'\b\d{5}(?:-\d{4})?\b', text)
                or not any(n.tag in {'h1','h2','h3','h4','h5','h6'} and n.text() == 'Contact Us' for n in every_node(contact_dom))
                or not any(n.tag in {'p','address','div','section'} and n.text() == text for n in every_node(contact_dom))):
            raise ValueError('Institution requires its explicit own lab institutional contact/address block')
        row['captureVerified'] = True
    return rows


def apply_lab_ownership_reviews(data, reviews):
    index = LabIndex(data['labs'])
    for row in reviews:
        lab = index.by_id.get(row.get('labId'))
        old = row.get('originalLabRecord', {})
        if (not row.get('captureVerified') or lab is None or lab['id'] != row['labId']
                or any(lab.get(k) != old.get(k) for k in ['labName','labWebsiteUrl'])
                or lab.get('institution') not in {old.get('institution'),row['institution']}
                or lab.get('department') not in {old.get('department'),'Unknown'}
                or evidence_items(lab.get('fieldEvidence', {}).get('department'))
                or (lab.get('institution') != row['institution']
                    and evidence_items(lab.get('fieldEvidence', {}).get('institution')))):
            raise ValueError('Own institution correction cannot overwrite another verified affiliation or identity')
    for row in reviews:
        lab = index.by_id[row['labId']]
        for field, value in [('institution',row['institution']),('department','Unknown')]:
            if lab.get(field) != value:
                observation = {'field':field, 'value':copy.deepcopy(lab.get(field)),
                    'fieldEvidence':copy.deepcopy(lab.get('fieldEvidence', {}).get(field, [])),
                    'reason':row['reason']}
                lab['previousFieldObservations'] = unique_values(lab.get('previousFieldObservations', [])+[observation])
            lab[field] = value
        proofs = lab.setdefault('fieldEvidence', {})
        proofs['institution'] = unique_values(evidence_items(proofs.get('institution'))+[row['institutionEvidence'],row['contactTitleEvidence']])
        lab['relationshipScope'] = 'reviewed_own_lab_institution'
        proofs['relationshipScope'] = copy.deepcopy(proofs['institution'])
        lab['departmentAssessment'] = {'status':'unresolved',
            'sourceDepartmentContext':row['originalLabRecord'].get('department'),
            'reason':'Earlier campus faculty/topic routing is not a verified department of this separately owned lab. Retain that context without an absence or appointment claim.'}
        lab['labOwnershipReviews'] = unique_values(lab.get('labOwnershipReviews', [])+[row])
        lab['sourceUrls'] = unique_values(lab.get('sourceUrls', [])+[p['sourceUrl'] for p in row['evidence']])
