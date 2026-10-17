"""Read a named subject's explicit UCSD appointment in their own overview.

This supplements a missing Profiles title table. It does not replace a stated
table role, read publications or infer a department from a school or hospital.
"""
import hashlib
import re

from faculty_profile_bindings import profile_metadata
from faculty_scoped_titles import same_named_subject
from refresh_labs import DOM, evidence

OVERVIEW = 'http://vivoweb.org/ontology/core#overview'
GROUP = 'http://profiles.catalyst.harvard.edu/ontology/prns#PropertyGroupOverview'
ROLE = (r'(?:(?:Assistant|Associate|Adjunct|Clinical|Research|Teaching|Distinguished|Emeritus|Visiting|Acting|Senior|HS|Health Sciences)\s+)*'
        r'(?:Professor|Lecturer)(?:\s+Emerit(?:us|a))?')
CLAUSE = re.compile(r'^(?P<subject>[^;:!?]{3,150}?)\s+is\s+(?:a|an|the)\s+'
                    r'(?P<role>'+ROLE+r')\s+at\s+'
                    r'(?P<institution>UC\s+San\s+Diego|University of California,?\s+San Diego)\b', re.I)


def own_overview_listing(item, cache):
    try:
        base, markup = profile_metadata(item, cache)
    except (ValueError, KeyError):
        return None
    dom = DOM(markup); nodes = list(dom.main().walk())
    # A table role remains independently dated and authoritative as listed;
    # a different biography must not silently qualify or replace it.
    for node in nodes:
        cells = [c for c in node.children if hasattr(c,'tag') and c.tag in {'th','td'}]
        if node.tag=='tr' and len(cells)==2 and cells[0].tag=='th' and cells[0].text()=='Title(s)' and cells[1].text():
            return None
    overviews = [n for n in nodes if n.tag=='div' and n.attrs.get('id')==OVERVIEW]
    if len(overviews)!=1 or 'PropertyGroupData' not in overviews[0].parent.attrs.get('class','').split():
        return None
    ancestor = overviews[0].parent
    while ancestor is not None and ancestor.attrs.get('id')!=GROUP:
        ancestor=ancestor.parent
    if ancestor is None or 'PropertyGroupItem' not in ancestor.attrs.get('class','').split():
        return None
    text=overviews[0].text(); match=CLAUSE.match(text)
    if not match:
        return None
    subject=re.sub(r',?\s+(?:(?:Ph\.?D\.?|M\.?D\.?|MD|PhD)\s*,?\s*)+$','',match['subject']).strip(' ,')
    if not same_named_subject(base['nameAsDisplayed'],subject):
        return None
    role,quote=match['role'],text[:match.end()]
    proof={**evidence(item['fetch'],'official_profiles_own_overview_explicit_ucsd_appointment',quote),
           **base,'evidenceType':'main_text_quote','overviewId':OVERVIEW,
           'overviewSubjectAsListed':subject,'academicRoleAsListed':role,'institutionAsListed':match['institution']}
    qualification={'nameAsDisplayed':base['nameAsDisplayed'],'roleAsListed':role,'unitAsListed':'',
        'scope':'Explicit named present-tense UCSD appointment in the subject’s own overview; no department mapping or current HR verification.',
        'evidence':proof,'fieldEvidence':{'nameAsDisplayed':proof,'roleAsListed':proof}}
    return {'name':base['nameAsDisplayed'],'department':'Unknown','departmentExplicitlyListed':False,
        'departmentAsListed':'','departmentMappingStatus':'unit_not_stated','profileDiscovery':True,
        'discoveryId':'ucsd-profile-faculty-'+hashlib.sha256(base['sourceUrl'].encode()).hexdigest()[:14],
        'listedRole':role,'appointmentStatus':'emeritus' if 'emerit' in role.lower() else 'listed_faculty',
        'directorySection':'UCSD Profiles named own overview appointment','sourceUrl':base['sourceUrl'],
        'observedAt':base['observedAt'],'evidence':proof,'profileUrl':base['sourceUrl'],
        'namedLinkUrl':base['sourceUrl'],'email':'','personalWebsiteUrl':'','googleScholarUrl':'','researchAreas':[],
        'academicQualification':qualification}
