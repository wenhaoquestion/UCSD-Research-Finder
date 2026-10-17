#!/usr/bin/env python3
"""Check the dated candidate atlas in a local browser, including shared lab IDs.

Serve .cache/coverage-20261016/candidate-site-preview on loopback first. This is
an optional browser check; the normal offline test suite needs no Playwright.
Redirect server access logs to a file when using with_server.py: its unread
stderr pipe fills during this many navigations and blocks HTTP responses.
"""
from pathlib import Path
import argparse, hashlib, json, datetime as dt
from urllib.parse import urlsplit, parse_qs
from playwright.sync_api import sync_playwright, expect
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('--port', type=int, default=8765)
cli.add_argument('--browser-executable')
cli.add_argument('--faculty-before', type=Path, help='Also check every new professor and every archived prior candidate against this complete earlier atlas')
cli.add_argument('--candidate-quarantine', type=Path)
args=cli.parse_args()
origin=f'http://127.0.0.1:{args.port}'
root=Path(__file__).resolve().parents[1];out=root/'.cache/coverage-20261016/browser-site-preview';out.mkdir(exist_ok=True)
candidate=root/'.cache/coverage-20261016/faculty-assembly-preview/research-atlas.json'
served=root/'.cache/coverage-20261016/candidate-site-preview/data/research-atlas.json'
assert candidate.read_bytes()==served.read_bytes(), 'Loopback candidate copy must match the reviewed snapshot'
candidate_data=json.loads(candidate.read_text())
person_reviews=json.loads((root/'data/ucsd/person-identity-review-20261016.json').read_text())['entries']
profile_bindings=list({row['professorId']:row for row in json.loads((root/'data/ucsd/faculty-profile-identity-review-20261016.json').read_text())['entries']}.values())
candidate_people={person['id']:person for person in candidate_data['professors']}
qualification_people=[person for person in candidate_data['professors']
                      if any(entry.get('academicQualification',{}).get('evidence',{}).get('method') in {'identity_matched_jacobs_primary_appointment','identity_matched_official_profile_title_field'}
                             for entry in person.get('directoryListings',[]))]
bound_candidate_aliases=[(person,review) for person in candidate_data['professors']
                         for review in person.get('candidateObservationAliases',[])]
before_people={person['id']:person for person in json.loads(args.faculty_before.read_text())['professors']} if args.faculty_before else {}
new_people=[person for person in candidate_data['professors'] if person['id'] not in before_people] if args.faculty_before else []
def visible_professor_state(person):
 fields=['name','department','departmentAffiliations','officialProfileUrl','personalWebsiteUrl','email',
         'researchSummary','researchAreas','teaching','ratings','verification','labAffiliations','aliasNames','sourceUrls']
 return {**{key:person.get(key) for key in fields},'directoryListings':[
  {key:row.get(key) for key in ['name','department','listedRole','sourceUrl','observedAt','evidence','academicQualification']}
  for row in person.get('directoryListings',[])]}
changed_people=[person for person in candidate_data['professors'] if person['id'] in before_people
                and visible_professor_state(person)!=visible_professor_state(before_people[person['id']])]
changed_professor_ids={person['id'] for person in changed_people}
held_people=[row['record'] for row in json.loads(args.candidate_quarantine.read_text())
             if row.get('candidateHistoryVerified') and row.get('record',{}).get('id') in before_people
             and row['record']['id'] not in candidate_people] if args.candidate_quarantine else []
faculty_review_path=root/'.cache/coverage-20261016/profile-qualification-preview/faculty-review.json'
qualified_initial_holds=[row for row in json.loads(faculty_review_path.read_text())['uncertainListings']
                         if row.get('reason')=='qualified_title_legacy_initial_alias_requires_identity_review'] if faculty_review_path.exists() else []
original_people={person['id']:person for person in json.loads((root/'.cache/coverage-20261016/baseline/research-atlas.json').read_text())['professors']}
errors=[];local_errors=[];blocked=[];results=[]
with sync_playwright() as p:
 options={'headless':True}
 if args.browser_executable:
  options['executable_path']=args.browser_executable
 else:
  options['channel']='chrome'
 browser=p.chromium.launch(**options)
 for viewport in [{'width':1440,'height':1000},{'width':390,'height':844}]:
  page=browser.new_page(viewport=viewport)
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('response',lambda r:local_errors.append({'url':r.url,'status':r.status}) if r.url.startswith(origin+'/') and r.status>=400 else None)
  def route_request(route):
   if route.request.url.startswith(origin+'/'):
    route.continue_()
   else:
    blocked.append(route.request.url);route.abort()
  page.route('**/*',route_request)
  for name,lab_id in [('Sunil K. Sinha Research Group','ucsd-physics-research-site-sunil-k-sinha'),('Flow Control Lab','ucsd-live-lab-802bc4f0642435'),('Coordinated Robotics Lab','ucsd-live-lab-7df54236890322'),('The Sebat Lab','ucsd-cellular-molecular-medicine-lab-sebat-lab'),('Kleinfeld Lab','ucsd-physics-lab-kleinfeld-lab'),('Allen Lab (Quantum Devices and Imaging)','ucsd-physics-lab-allen-lab-quantum-devices-and-imaging')]:
   page.goto(origin+'/',wait_until='networkidle')
   expect(page.locator('#labCount')).to_have_text('873')
   page.locator('#query').fill(name)
   button=page.locator(f'#results .row[data-id="{lab_id}"] .row-title')
   expect(button).to_have_text(name)
   button.click()
   expect(page.locator('#detailContent h2.detail-title')).to_have_text(name)
   expect(page.locator('#detailPanel')).to_have_css('transform','none')
   bounds=page.locator('#detailPanel').bounding_box()
   assert bounds and bounds['x']>=-1 and bounds['x']+bounds['width']<=viewport['width']+1
   if lab_id == 'ucsd-physics-research-site-sunil-k-sinha':
    expect(page.locator('#detailContent')).to_contain_text('Needs review')
    expect(page.locator('#detailContent')).to_contain_text('Original listed website (identity mismatch)')
    expect(page.locator('#detailContent')).not_to_contain_text('Monica Allen')
    expect(page.locator('#detailContent a[href="http://sinhagroup.ucsd.edu/"]').first).to_be_visible()
    if viewport['width'] >= 1280:
     page.locator('#verifiedOnly').check()
     expect(page.locator(f'#results .row[data-id="{lab_id}"]')).to_have_count(0)
   elif lab_id == 'ucsd-cellular-molecular-medicine-lab-sebat-lab':
    expect(page.locator('#detailContent a[href="https://sebatlab.org/"]').first).to_be_visible()
    expect(page.locator('#detailContent')).to_contain_text('Jonathan Sebat')
    expect(page.locator('#detailContent a[href="https://profiles.ucsd.edu/jonathan.sebat"]').first).to_be_visible()
    expect(page.locator('#detailContent')).to_contain_text('sebatlab@health.ucsd.edu')
    expect(page.locator('#detailContent')).to_contain_text('jsebat@health.ucsd.edu')
    assert not page.locator('#detailContent a').evaluate_all('(links) => links.some(a => /\\s/.test(a.getAttribute("href")))')
   elif lab_id == 'ucsd-physics-lab-kleinfeld-lab':
    expect(page.locator('#detailContent')).to_contain_text('David Kleinfeld')
    expect(page.locator('#detailContent a[href="https://biology.ucsd.edu/research/faculty/dkleinfeld"]').first).to_be_visible()
   elif lab_id == 'ucsd-physics-lab-allen-lab-quantum-devices-and-imaging':
    expect(page.locator('#detailContent a[href="https://allen.physics.ucsd.edu/"]').first).to_be_visible()
    expect(page.locator('#detailContent')).to_contain_text('Monica Allen')
    expect(page.locator('#detailContent')).not_to_contain_text('Sunil K. Sinha')
   else:
    expect(page.locator('#detailContent')).to_contain_text('Shared by separately named labs')
    expect(page.locator('#detailContent')).to_contain_text('Thomas Bewley')
    expect(page.locator('#detailContent a[href="https://jacobsschool.ucsd.edu/faculty/profile?id=64"]').first).to_be_visible()
    expect(page.locator('#detailContent a[href="https://www.ucsdrobotics.org/"]').first).to_be_visible()
    expect(page.locator('#detailContent a[href="http://robotics.ucsd.edu/"]').first).to_be_visible()
    expect(page.locator('#detailContent')).to_contain_text('Shared landing page')
    page.screenshot(animations='disabled',path=str(out/f'shared-resource-{viewport["width"]}.png'),full_page=viewport['width']>=1280)
   assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
   results.append({'viewport':viewport,'labId':lab_id,'labName':name,'details':'passed'})
  page.screenshot(animations='disabled',path=str(out/f'shared-labs-{viewport["width"]}.png'),full_page=viewport['width']>=1280)
  for review in person_reviews:
   source_id,target_id=review['sourceProfessorId'],review['targetProfessorId']
   page.goto(origin+'/?id='+source_id,wait_until='networkidle')
   expect(page.locator('#professorCount')).to_have_text(f'{len(candidate_data["professors"]):,}')
   expect(page.locator('#detailContent h2.detail-title')).to_have_text(review['name'])
   expect(page.locator('#detailPanel')).to_have_css('transform','none')
   assert parse_qs(urlsplit(page.url).query).get('id')==[target_id], 'Old stable ID must resolve to the reviewed canonical record'
   if review['name']=='James McKernan':
    expect(page.locator('#detailContent .detail-affiliation')).to_contain_text('Mathematics')
    expect(page.locator('#detailContent .detail-affiliation')).not_to_contain_text('Biochemistry')
    if viewport['width'] < 1280:
     page.screenshot(animations='disabled',path=str(out/f'reviewed-person-{viewport["width"]}.png'))
     page.locator('#detailClose').click()
    page.locator('#query').fill(review['name'])
    if viewport['width'] < 1280:
     page.locator('#filtersButton').click()
    page.locator('#departmentFilter').select_option('Mathematics')
    if viewport['width'] < 1280:
     page.locator('#railApply').click()
    expect(page.locator(f'#results .row[data-id="{target_id}"]')).to_have_count(1)
    expect(page.locator(f'#results .row[data-id="{source_id}"]')).to_have_count(0)
    if viewport['width'] >= 1280:
     page.screenshot(animations='disabled',path=str(out/f'reviewed-person-{viewport["width"]}.png'),full_page=True)
   if review['name']=='Daniel Grier':
    expect(page.locator('#detailContent')).to_contain_text('CSE 291T')
    expect(page.locator('#detailContent')).to_contain_text('MATH 277A')
   if review['identityBasis']['type']=='misparsed_research_link_in_named_faculty_card':
    person=candidate_people[target_id]
    for field in ['name','department','officialProfileUrl']:
     assert person[field]==review['originalTargetRecord'][field]
    assert review['originalSourceRecord']['name'] not in person.get('aliasNames',[])
    expect(page.locator('#detailContent a[href="'+person['officialProfileUrl']+'"]').first).to_be_visible()
    expect(page.locator('#results .row[data-id="'+source_id+'"]')).to_have_count(0)
    assert 'ucsd-bioengineering-k-king' in candidate_people, 'Initial-only catalog record needs a separate review'
    separate_id='ucsd-medicine-kevin-robert-king'
    assert separate_id in candidate_people or any(
     r['sourceProfessorId']==separate_id and r['targetProfessorId']==target_id
     and r['identityBasis']['type']=='explicit_named_roster_personal_identifier_chain' for r in person_reviews
    ), 'Different retained name needs its separate verified source-chain review'
    page.screenshot(animations='disabled',path=str(out/f'resolved-research-label-{viewport["width"]}.png'))
   if review['identityBasis']['type']=='explicit_named_roster_personal_identifier_chain':
    person=candidate_people[target_id]
    for field in ['name','department','officialProfileUrl']:
     assert person[field]==review['originalTargetRecord'][field]
    published_name=review['originalSourceRecord']['name']
    assert published_name in person['aliasNames']
    expect(page.locator('#detailContent a[href="'+person['officialProfileUrl']+'"]').first).to_be_visible()
    expect(page.locator('#detailContent')).to_contain_text('Medicine')
    expect(page.locator('#detailContent .detail-affiliation')).not_to_contain_text('Interdisciplinary')
    expect(page.locator('#detailContent')).to_contain_text('BENG 294A')
    expect(page.locator('#detailContent')).to_contain_text('MED 238')
    page.screenshot(animations='disabled',path=str(out/f'reviewed-profile-chain-{viewport["width"]}.png'))
    if viewport['width'] < 1280:
     page.locator('#detailClose').click()
    page.locator('#query').fill(published_name)
    expect(page.locator('#results .row[data-id="'+target_id+'"]')).to_have_count(1)
    expect(page.locator('#results .row[data-id="'+source_id+'"]')).to_have_count(0)
   assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
   results.append({'viewport':viewport,'sourceProfessorId':source_id,'canonicalProfessorId':target_id,'name':review['name'],'aliasAndDetails':'passed'})
  for binding in profile_bindings:
   person=candidate_people[binding['professorId']]
   assert person['officialProfileUrl']==binding['originalProfileUri'], 'An identity binding must preserve the original primary profile URI'
   page.goto(origin+'/?id='+person['id'],wait_until='networkidle')
   expect(page.locator('#detailContent h2.detail-title')).to_have_text(person['name'])
   expect(page.locator('#detailPanel')).to_have_css('transform','none')
   hrefs=page.locator('#detailContent a').evaluate_all('(links) => links.map(a => a.getAttribute("href"))')
   assert binding['originalProfileUri'] in hrefs
   if person['id'] in changed_professor_ids:
    expect(page.locator('#detailContent')).to_contain_text(binding['qualificationAsListed']['titleAsListed'])
    assert binding['captures'][1]['sourceUrl'] in hrefs
    if person['id'] in {'ucsd-pharmacology-joann-trejo','ucsd-electrical-and-computer-engineering-kenneth-a-zeger'}:
     page.locator('#detailContent').get_by_text('Faculty roles & affiliations',exact=True).scroll_into_view_if_needed()
     page.screenshot(animations='disabled',path=str(out/f'new-identity-binding-{viewport["width"]}.png'))
   assert parse_qs(urlsplit(page.url).query).get('id')==[person['id']]
   assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
   results.append({'viewport':viewport,'professorId':person['id'],'name':person['name'],'retainedPrimaryUri':binding['originalProfileUri'],'capturedMetadataBinding':'passed'})
  for person in qualification_people:
   page.goto(origin+'/?id='+person['id'],wait_until='networkidle')
   expect(page.locator('#detailContent h2.detail-title')).to_have_text(person['name'])
   expect(page.locator('#detailPanel')).to_have_css('transform','none')
   roles=[]
   for listing in person['directoryListings']:
    if listing.get('academicQualification',{}).get('evidence',{}).get('method') in {'identity_matched_jacobs_primary_appointment','identity_matched_official_profile_title_field'}:
     label=' · '.join(value for value in [listing['department'],listing['listedRole']] if value not in {'Unknown','Not found',''})
     expect(page.locator('#detailContent')).to_contain_text(label)
     qualification=listing['academicQualification']
     expect(page.locator('#detailContent .academic-qualification').filter(has_text=qualification['roleAsListed']).first).to_be_visible()
     assert qualification['evidence']['sourceUrl'] in page.locator('#detailContent .academic-qualification a').evaluate_all('(links) => links.map(a => a.getAttribute("href"))')
     roles.append(label)
   assert parse_qs(urlsplit(page.url).query).get('id')==[person['id']]
   assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
   if person['id']=='ucsd-economics-melissa-famulari':
    page.locator('#detailContent .academic-qualification').first.scroll_into_view_if_needed()
    page.screenshot(animations='disabled',path=str(out/f'own-title-field-{viewport["width"]}.png'))
   results.append({'viewport':viewport,'professorId':person['id'],'name':person['name'],'retainedRosterRoles':roles,'ownQualificationWithOriginalRosterWording':'passed'})
  for person,review in bound_candidate_aliases:
   source_id=review['sourceProposedProfessorId']
   page.goto(origin+'/?id='+source_id,wait_until='networkidle')
   expect(page.locator('#detailContent h2.detail-title')).to_have_text(person['name'])
   expect(page.locator('#detailPanel')).to_have_css('transform','none')
   published=review['observationBinding']['nameReview']
   expect(page.locator('#detailContent')).to_contain_text(published['profileNameAsDisplayed'])
   hrefs=page.locator('#detailContent a').evaluate_all('(links) => links.map(a => a.getAttribute("href"))')
   assert person['officialProfileUrl'] in hrefs
   assert parse_qs(urlsplit(page.url).query).get('id')==[person['id']]
   expect(page.locator(f'#results .row[data-id="{source_id}"]')).to_have_count(0)
   assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
   results.append({'viewport':viewport,'previousProposedProfessorId':source_id,'retainedOriginalProfessorId':person['id'],
                   'nameAsRetained':person['name'],'profileNameAsPublished':published['profileNameAsDisplayed'],
                   'verifiedCandidateAliasResolution':'passed'})
  # Search and select the full changed/new cohort through real UI controls.
  # Keep the loaded atlas for these interactions instead of re-fetching its
  # complete JSON on every selection. Independent deep-link checks above and
  # all held-candidate links below still exercise fresh document navigation.
  if new_people or changed_people:
   page.goto(origin+'/',wait_until='networkidle')
  new_ids={person['id'] for person in new_people}
  for person in new_people+changed_people:
   if viewport['width'] < 1280 and 'is-open' in (page.locator('#detailPanel').get_attribute('class') or '').split():
    page.locator('#detailClose').click()
   page.locator('#query').fill(person['name'])
   button=page.locator(f'#results .row[data-id="{person["id"]}"] .row-title')
   expect(button).to_have_text(person['name'])
   button.click()
   expect(page.locator('#professorCount')).to_have_text(f'{len(candidate_data["professors"]):,}')
   expect(page.locator('#detailContent h2.detail-title')).to_have_text(person['name'])
   expect(page.locator('#detailPanel')).to_have_css('transform','none')
   hrefs=page.locator('#detailContent a').evaluate_all('(links) => links.map(a => a.getAttribute("href"))')
   assert person['officialProfileUrl'] in hrefs
   for area in person.get('researchAreas',[])[:14]:
    expect(page.locator('#detailContent')).to_contain_text(area)
   if person.get('email') and person['email']!='Not found':
    assert 'mailto:'+person['email'] in hrefs
   for review in person.get('professorFieldReviews',[]):
    assert review['sourceObservation']['capture']['sourceUrl'] in hrefs
   if person['name'] in {'Efim Zelmanov','Audrey A. Terras','Aaron Pollack'} and person.get('professorFieldReviews'):
    page.locator('#detailContent .tag-list').first.scroll_into_view_if_needed()
    page.screenshot(animations='disabled',path=str(out/f'own-math-fields-{viewport["width"]}.png'))
   for listing in person.get('directoryListings',[]):
    expect(page.locator('#detailContent')).to_contain_text(listing['listedRole'])
   context_rows=[row for row in person.get('directoryListings',[]) if row.get('departmentMappingStatus')=='unverified_source_context_only']
   for listing in context_rows:
    assert listing['department']=='Unknown' and listing.get('sourceDepartmentContext')=='Interdisciplinary'
   if context_rows and 'Interdisciplinary' not in person.get('departmentAffiliations',[]) and person['department']!='Interdisciplinary':
    expect(page.locator('#detailContent .detail-affiliation')).not_to_contain_text('Interdisciplinary')
   assert parse_qs(urlsplit(page.url).query).get('id')==[person['id']]
   assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
   results.append({'viewport':viewport,'professorId':person['id'],'name':person['name'],
                   'newQualifiedProfessorDetails' if person['id'] in new_ids else 'changedProfessorDetails':'passed',
                   'interaction':'search_and_select','sourceContextRowsChecked':len(context_rows)})
  # The teaching-course artifact is archived; the explicitly named research
  # lab retains its own ID and the original professor's separately proved PI link.
  digi=candidate_data['labs'] and next((lab for lab in candidate_data['labs'] if lab['id']=='ucsd-live-lab-db372d05c77570'),None)
  if digi:
   page.goto(origin+'/?id='+digi['id'],wait_until='networkidle')
   expect(page.locator('#labCount')).to_have_text(f'{len(candidate_data["labs"]):,}')
   expect(page.locator('#detailContent h2.detail-title')).to_have_text(digi['labName'])
   expect(page.locator('#detailContent')).to_contain_text('Edward Jay Wang')
   assert digi['professorIds']==['ucsd-faculty-edward-wang']
   hrefs=page.locator('#detailContent a').evaluate_all('(links)=>links.map(a=>a.getAttribute("href"))')
   assert digi['labWebsiteUrl'] in hrefs and digi['principalInvestigatorProfileUrl'] in hrefs
   page.locator('#detailContent .detail-section').filter(has=page.get_by_role('heading',name='Lab details',exact=True)).screenshot(animations='disabled',path=str(out/f'digihealth-lab-{viewport["width"]}.png'))
   person=candidate_people['ucsd-faculty-edward-wang']
   page.goto(origin+'/?id='+person['id'],wait_until='networkidle')
   expect(page.locator('#detailContent h2.detail-title')).to_have_text('Edward Wang')
   labs_section=page.locator('#detailContent .detail-section').filter(has=page.get_by_role('heading',name='Labs & research groups',exact=True))
   expect(labs_section).to_contain_text(digi['labName'])
   expect(labs_section).not_to_contain_text('Biosignals Processing Lab')
   assert person['officialProfileUrl'] in page.locator('#detailContent a').evaluate_all('(links)=>links.map(a=>a.getAttribute("href"))')
   labs_section.screenshot(animations='disabled',path=str(out/f'digihealth-professor-link-{viewport["width"]}.png'))
   old_course='ucsd-live-lab-97139595f4c472'
   assert old_course not in {lab['id'] for lab in candidate_data['labs']}
   page.goto(origin+'/?id='+old_course,wait_until='networkidle')
   assert parse_qs(urlsplit(page.url).query).get('id')!=[old_course]
   expect(page.locator(f'#results .row[data-id="{old_course}"]')).to_have_count(0)
   results.append({'viewport':viewport,'newLabId':digi['id'],'retainedProfessorId':person['id'],'archivedCourseArtifactId':old_course,'labAndPiIdentityAndCourseIsolation':'passed'})
  ideker=next((lab for lab in candidate_data['labs'] if lab['id']=='ucsd-medicine-lab-trey-ideker-lab'),None)
  if ideker and 'https://idekerlab.org/' in ideker.get('alternateWebsiteUrls',[]):
   page.goto(origin+'/?id='+ideker['id'],wait_until='networkidle')
   expect(page.locator('#detailContent h2.detail-title')).to_have_text(ideker['labName'])
   hrefs=page.locator('#detailContent a').evaluate_all('(links)=>links.map(a=>a.getAttribute("href"))')
   assert ideker['labWebsiteUrl']=='https://gpm.ucsd.edu/research/ideker/index.html'
   assert ideker['labWebsiteUrl'] in hrefs and 'https://idekerlab.org/' in hrefs
   results.append({'viewport':viewport,'labId':ideker['id'],'originalCampusPrimaryAndActualExternalAlias':'passed'})
  for person in held_people:
   page.goto(origin+'/?id='+person['id'],wait_until='networkidle')
   expect(page.locator('#professorCount')).to_have_text(f'{len(candidate_data["professors"]):,}')
   assert parse_qs(urlsplit(page.url).query).get('id')!=[person['id']], 'An archived unresolved candidate must not resolve as a published person or an inferred alias'
   expect(page.locator(f'#results .row[data-id="{person["id"]}"]')).to_have_count(0)
   results.append({'viewport':viewport,'heldProposedProfessorId':person['id'],'name':person['name'],'unresolvedCandidateNotPublished':'passed'})
  for hold in qualified_initial_holds:
   for pid in hold['candidateProfessorIds']:
    person=candidate_people[pid]
    assert pid in original_people
    assert all(person[key]==original_people[pid][key] for key in ['name','officialProfileUrl'])
    page.goto(origin+'/?id='+pid,wait_until='networkidle')
    expect(page.locator('#detailContent h2.detail-title')).to_have_text(person['name'])
    expect(page.locator('#detailPanel')).to_have_css('transform','none')
    assert person['officialProfileUrl'] in page.locator('#detailContent a').evaluate_all('(links) => links.map(a => a.getAttribute("href"))')
    assert parse_qs(urlsplit(page.url).query).get('id')==[pid]
    results.append({'viewport':viewport,'retainedOriginalProfessorId':pid,'name':person['name'],
                    'qualifiedSourceNameHeld':hold['listing']['name'],'initialNameAndPrimaryUriPreserved':'passed'})
  page.close()
 browser.close()
assert not errors and not local_errors, (errors,local_errors)
receipt={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'isFinalValidation':False,'servedAtlasModified':False,'candidateAtlas':'faculty-assembly-preview/research-atlas.json','candidateAtlasSha256':hashlib.sha256((root/'.cache/coverage-20261016/faculty-assembly-preview/research-atlas.json').read_bytes()).hexdigest(), 'checkScriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'browser':'headless Chromium / installed Chrome, fresh contexts','checks':results,'pageErrors':errors,'localHttpErrors':local_errors,'externalRequestsBlocked':sorted(set(blocked)),'screenshots':[str(out/name) for name in ['shared-labs-1440.png','shared-labs-390.png','shared-resource-1440.png','shared-resource-390.png']],'limitation':'Candidate snapshot UI checks only; full eligible collection and final export/site checks remain required.'}
receipt['servedAssetSha256']={name:hashlib.sha256((root/'.cache/coverage-20261016/candidate-site-preview'/name).read_bytes()).hexdigest() for name in ['assets/app.js','assets/styles.css']}
receipt['screenshots'].extend(str(out/f'own-title-field-{width}.png') for width in [1440,390] if (out/f'own-title-field-{width}.png').exists())
receipt['screenshots'].extend(str(out/f'new-identity-binding-{width}.png') for width in [1440,390] if (out/f'new-identity-binding-{width}.png').exists())
receipt['screenshots'].extend(str(out/f'own-math-fields-{width}.png') for width in [1440,390] if (out/f'own-math-fields-{width}.png').exists())
receipt['screenshots'].extend(str(out/f'{label}-{width}.png') for label in ['digihealth-lab','digihealth-professor-link'] for width in [1440,390] if (out/f'{label}-{width}.png').exists())
(root/'docs/operations/shared-lab-site-preview-20261016.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checked':len(results),'pageErrors':errors,'localHttpErrors':local_errors}))
