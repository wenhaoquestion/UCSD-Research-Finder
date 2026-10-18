const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const dummy = { addEventListener() {} };
const context = vm.createContext({
  document: { querySelector: () => dummy, querySelectorAll: () => [], addEventListener() {},
    createElement: tag => ({ tag, children: [], append(...items) { this.children.push(...items); } }) },
  localStorage: { getItem: () => null },
  window: { matchMedia: () => ({ matches: true }) },
  fetch: () => new Promise(() => {}),
  URL,
});
for (const file of ['../assets/taxonomy.js', '../assets/app.js']) {
  vm.runInContext(fs.readFileSync(path.join(__dirname, file), 'utf8'), context);
}
const evaluate = expression => vm.runInContext(expression, context);

assert.equal(evaluate('buildRecords({professors:[{id:"one",name:"One Professor",email:"department@ucsd.edu"},{id:"two",name:"Another Professor",email:"department@ucsd.edu"}]}).length'), 2,
  'shared department email must not merge different people');
assert.equal(evaluate('buildRecords({professors:[{id:"one",name:"Same Name",email:"same@ucsd.edu",department:"Physics"},{id:"two",name:"Same Name",email:"same@ucsd.edu",department:"Mathematics"}]}).length'), 2,
  'matching names and contacts cannot silently combine unreviewed department or identity claims');
assert.equal(evaluate('makeRecordIndex([{id:"canonical",aliasIds:["retired"]}]).get("retired").id'), 'canonical',
  'explicit retained stable IDs continue to resolve old person and lab links');
assert.throws(() => evaluate('makeRecordIndex([{id:"one",aliasIds:["retired"]},{id:"two",aliasIds:["retired"]}])'), /Ambiguous record ID/);
assert.equal(evaluate('sourceChecked({ sourceUrls: ["https://ucsd.edu"], lastVerified: "2026-10-02" })'), false,
  'source links and legacy timestamps do not verify a record');
assert.equal(evaluate('sourceChecked({verification:{status:"source_checked",destinationIdentityStatus:"mismatch"},fieldEvidence:{labName:[{sourceUrl:"http://example.ucsd.edu",observedAt:"2026-10-01"}]}})'), false,
  'historical field evidence cannot make a mismatched lab destination pass the source-checked filter');
assert.equal(evaluate('ratedPlatforms({ ratings: { rateMyPI: { status: "no_reviews", score: 0, reviewCount: 0 } } }).length'), 0,
  'unreviewed profiles cannot become zero-star ratings');
assert.equal(evaluate('ratingStatusLabel({status: "no_reviews"})'), 'No reviews on matched profile');
assert.equal(evaluate('hasScholarProfile({ googleScholarUrl: "https://scholar.google.com/citations?view_op=search_authors&mauthors=Example" })'), false,
  'Scholar search pages are not verified author profiles');
assert.equal(evaluate('hasScholarProfile({ googleScholarUrl: "https://scholar.google.ch/citations?user=ExampleID" })'), true);
assert.equal(evaluate('dateLabel("2026-10-03T01:00:00Z")'), '2026-10-02', 'timestamps use the campus Pacific calendar date');
assert.equal(evaluate('dateLabel("2026-10-03")'), '2026-10-03', 'date-only source dates must not shift timezones');
assert(evaluate('courseTermOrder({term:"Fall 2026"}) > courseTermOrder({term:"Winter 2025"})'), 'teaching terms sort by year and season, not alphabetically');
assert.equal(evaluate('coursesFor({ teaching: { courses: [], candidates: [{courseCode:"ASTR 1"}] } }).length'), 0,
  'surname-only teaching leads cannot count as verified courses');
assert.equal(evaluate('buildIndex([{ displayName: "Example", links: [], teaching: { candidates: [{courseCode:"ASTR 1"}] } }])[0].haystack.includes("astr")'), false,
  'unverified leads cannot enter the normal course search index');
assert(evaluate('buildIndex([{displayName: "Example Professor", links: [], teaching: {courses: [{courseCode:"CSE 151A", title:"Machine Learning", term:"Fall 2026"}]}}])[0].haystack.includes("cse151a")'),
  'compact course-code queries must be searchable');
assert(evaluate('buildIndex([{displayName: "Example", links: [], researchKeywords: ["Zika virus"]}])[0].haystack.includes("zika")'),
  'official profile keywords must be searchable');
assert.equal(evaluate('buildRecords({professors: [], labs: [{id:"a",labName:"Flow Control Lab",labWebsiteUrl:"https://example.ucsd.edu"},{id:"b",labName:"Coordinated Robotics Lab",labWebsiteUrl:"https://example.ucsd.edu"}]}).filter(r => r.recordType === "lab").length'), 2,
  'separately named labs sharing a homepage remain separate frontend records');
const unresolvedDetail = evaluate('JSON.stringify(labAffiliationDetails({unresolvedLabLinks:[{labName:"Lab website",url:"https://example.ucsd.edu/",fieldEvidence:{sourceUrl:"https://ucsd.edu/profile",observedAt:"2026-10-01",evidence:"Original named lab link"}}]}))');
assert(unresolvedDetail.includes('Shared website; named lab unresolved'));
assert(unresolvedDetail.includes('Original named lab link'), 'unresolved associations retain their original source quote in the detail view');
assert(unresolvedDetail.includes('https://ucsd.edu/profile'));
assert.equal(evaluate('validExternalUrl("https://sebatlab.org /")'), false, 'invalid source strings must not become repaired clickable links');
assert.equal(evaluate('labLinks({labWebsiteUrl:"http://old.ucsd.edu/",destinationIdentityAssessment:{identityStatus:"mismatch"}})[0][0]'), 'Original listed website (identity mismatch)');
assert.equal(evaluate('buildRecords({labs:[{id:"ngo",labName:"Example Foundation",recordSubtype:"ngo"}]}).find(r=>r.id==="ngo").displayKind'), 'NGO',
  'an explicitly classified NGO is displayed as an organization');
assert.equal(evaluate('labLinks({recordSubtype:"ngo",labWebsiteUrl:"https://foundation.example/"})[0][0]'), 'Organization website');
assert.equal(evaluate('primaryAffiliationLabel({labAffiliationUrl:"https://foundation.example/",labAffiliations:[{recordSubtype:"ngo",url:"https://foundation.example/"}]})'), 'Organization affiliation');
assert.equal(evaluate('primaryAffiliationLabel({labAffiliationUrl:"https://lab.example/",labAffiliations:[{recordSubtype:"ngo",url:"https://foundation.example/"}]})'), 'Lab affiliation');
assert(evaluate('JSON.stringify(labAffiliationDetails({labAffiliations:[{labName:"Example Foundation",recordSubtype:"ngo",url:"https://foundation.example/",relationship:"faculty_organization_link"}]})).includes("Documented organization association")'));
assert(evaluate('labLinks({id:"lab-a",labWebsiteUrl:"https://example.ucsd.edu/",sharedResourceReviews:[{captureVerified:true,action:"register_shared_lab_resource",resourceKind:"shared_landing_page",memberLabIds:["lab-a","lab-b"],resourceUri:"http://group.ucsd.edu/"}]}).some(link=>link[0]==="Shared landing page" && link[1]==="http://group.ucsd.edu/")'));
assert.equal(evaluate('labLinks({id:"unrelated",labWebsiteUrl:"https://example.ucsd.edu/",sharedResourceReviews:[{captureVerified:true,action:"register_shared_lab_resource",resourceKind:"shared_landing_page",memberLabIds:["lab-a","lab-b"],resourceUri:"http://group.ucsd.edu/"}]}).length'),1);
assert.equal(evaluate('validExternalUrl("http://example.ucsd.edu/?a=1&amp;b=2")'), true, 'valid literal query strings remain usable');
assert.equal(evaluate('validExternalUrl("javascript:alert(1)")'), false);
assert.equal(evaluate('validExternalUrl("https://user:secret@example.ucsd.edu/")'), false);

const affiliate = {recordType:"lab",displayKind:"Lab",institution:"Partner Institute",campusProgramRelationships:[{captureVerified:true,relationship:"program_listing_and_own_rotation_guidance",programName:"Example Graduate Program",facultyNameAsListed:"Jane Example",facultyRoleAsListed:"Assistant Professor, Partner Institute",programSourceUrl:"https://program.ucsd.edu/faculty",studentAccessStatement:{text:"For UCSD graduate students, we consider rotation students.",url:"https://example.org/",observedAt:"2026-10-16T01:00:00Z"}}]};
context.affiliate = affiliate;
assert(evaluate('JSON.stringify(detailFields(affiliate))').includes('UCSD graduate program connections'));
assert(evaluate('JSON.stringify(detailFields(affiliate))').includes('Assistant Professor, Partner Institute'));
assert(evaluate('buildIndex([{...affiliate,displayName:"Example Lab",links:[]}])[0].haystack.includes("example graduate program")'));
context.affiliate.campusProgramRelationships[0].captureVerified = false;
assert.equal(evaluate('JSON.stringify(detailFields(affiliate))').includes('UCSD graduate program connections'),false);
assert.equal(evaluate('buildIndex([{...affiliate,displayName:"Example Lab",links:[]}])[0].haystack.includes("example graduate program")'),false);

context.ownershipLab = {recordType:"lab",displayKind:"Lab",principalInvestigator:"Daniel W. Example",
  unverifiedFields:["principalInvestigator"],labOwnershipReviews:[{captureVerified:true,kind:"existing_lab_own_contact_institution"}]};
assert(evaluate('JSON.stringify(detailFields(ownershipLab))').includes('Earlier PI label (unverified)'));
assert.equal(evaluate('unverifiedOwnershipPi(ownershipLab)'),true,
  'result rows and detail fields share the same verified ownership/unverified PI scope');
context.ownershipLab.labOwnershipReviews[0].captureVerified = false;
assert.equal(evaluate('JSON.stringify(detailFields(ownershipLab))').includes('Earlier PI label (unverified)'),false);
context.ownershipLab.labOwnershipReviews[0].captureVerified = true;
context.ownershipLab.unverifiedFields = [];
assert.equal(evaluate('JSON.stringify(detailFields(ownershipLab))').includes('Earlier PI label (unverified)'),false,
  'an independently verified PI is not relabeled by an institution-only review');


// Departments: variant names collapse to one entry inside a broad school/division.
assert.equal(evaluate('resolveDepartment("Department of Physics").name'), 'Physics');
assert.equal(evaluate('resolveDepartment("Electrical and Computer Engineering (ECE)").division'), 'engineering');
assert.equal(evaluate('resolveDepartment("Halicioglu Data Science Institute (HDSI)").name'), 'Halicioğlu Data Science Institute');
assert.equal(evaluate('resolveDepartment("Student Health and Well-Being", "campus").division'), 'campus',
  'campus services are not filed under Medicine because their name says health');
assert.equal(evaluate('resolveDepartment("Psychiatry").division'), 'health');

// Research fields: raw area strings are cleaned and classified into broad + detailed fields.
assert.equal(evaluate('JSON.stringify(cleanAreas(["Physical Chemistry|Materials Chemistry", "Biochemistry|BB", "International Economics,"]))'),
  JSON.stringify(['Physical Chemistry', 'Materials Chemistry', 'Biochemistry', 'International Economics']));
assert(evaluate('subfieldsForText("deep learning for robot navigation").includes("ml")'));
assert(evaluate('subfieldsForText("deep learning for robot navigation").includes("robotics")'));
assert.equal(evaluate('subfieldsForText("laboratory techniques").includes("economics")'), false, '"labor" must not match "laboratory"');
assert.equal(evaluate('subfieldsForText("macrophages in tumor surveillance").includes("economics")'), false, '"macro" must not match "macrophages"');
assert.equal(evaluate('subfieldsForText("thin films for neural circuits").includes("arts")'), false, 'thin films are not cinema');
assert.equal(evaluate('classifyRecord({ departments: ["Psychiatry"], researchAreas: [], summary: "" }).fieldIds.join()'), 'health',
  'a department alone still places a record in its broad field');

// Search: typos, abbreviations and Chinese field names.
assert.equal(evaluate('editDistance("nueroscience", "neuroscience", 2)'), 1, 'a transposition is one edit');
assert(evaluate('compileQuery("ml").terms[0].alts.includes("machine learning")'));
assert(evaluate('compileQuery("机器学习").terms[0].alts.includes("machine learning")'));
assert.equal(evaluate('compileQuery("机器学习实验室").terms.length'), 2, 'known Chinese words become separate required terms');
assert.equal(evaluate('textHas(" email maintained", "ai")'), false, 'abbreviations match whole words only');
assert.equal(evaluate('textHas(" ai safety", "ai")'), true);
assert.equal(evaluate('textHas(" frank wuerthwein", "wu")'), true, 'two letters still find names that start with them');
assert.equal(evaluate('textHas(" danna zhang", "ang")'), true, 'three-letter terms match inside words, as before');

// Recovered archives keep stable links and whole snapshots without becoming people,
// active labs, REAL Portal resources, or sources of current contact/ratings claims.
const oldSnapshot = { id: 'old-directory', email: 'old@ucsd.edu', ratings: { rateMyPI: { score: 4.8 } }, lastVerified: '2020-01-01' };
context.recoveryFixture = {
  professors: [{ id: 'active-professor', name: 'Active Professor', department: 'Physics' }],
  labs: [{ id: 'active-lab', labName: 'Active Lab', department: 'Physics' }],
  recovery: {
    directorySources: [{ id: 'old-directory', label: 'Faculty Emeriti', department: 'Physics', sourceUrl: 'https://physics.ucsd.edu/faculty',
      previousProfessorObservations: ['original_record', 'previous_candidate', 'assembled_record'].map(scope => ({ scope, record: oldSnapshot })) }],
    retiredLabResources: [{ id: 'old-lab', aliasIds: ['older-lab'], label: 'Old Resource', department: 'Physics', sourceUrl: 'https://physics.ucsd.edu/resources',
      classification: 'historical_record_not_active_lab', reason: 'Historical resource; not an active lab.',
      previousLabObservations: [{ scope: 'original_record', record: { id: 'old-lab', contactEmail: 'old-lab@ucsd.edu', principalInvestigator: 'Earlier PI' } }] }],
  },
};
context.recoveryRealFixture = { resources: [{ id: 'real-entry', title: 'REAL Entry' }] };
evaluate('state.records = buildRecords(recoveryFixture, recoveryRealFixture); state.index = buildIndex(state.records); state.byId = makeRecordIndex(state.records)');
assert.equal(evaluate('state.byId.get("old-directory").recordType'), 'archive');
assert.equal(evaluate('state.byId.get("older-lab").id'), 'old-lab');
assert.equal(evaluate('state.byId.get("old-lab").displayKind'), 'Retired resource');
assert.equal(evaluate('state.byId.get("old-directory").email'), '');
assert.equal(evaluate('state.byId.get("old-directory").facts.ratings.length'), 0);
assert.equal(evaluate('sourceChecked(state.byId.get("old-directory"))'), false);
assert.deepEqual(JSON.parse(evaluate('JSON.stringify(collectRows(compileQuery(""), 0).counts)')),
  { all: 5, professor: 1, lab: 1, resource: 1, archive: 2 });
assert(evaluate('JSON.stringify(archiveDetails(state.byId.get("old-directory")))').includes('old@ucsd.edu'));
assert(evaluate('JSON.stringify(archiveDetails(state.byId.get("old-directory")))').includes('Previous reviewed record'));
assert(evaluate('JSON.stringify(archiveDetails(state.byId.get("old-directory")))').includes('Record at archive time'));
assert(evaluate('JSON.stringify(archiveDetails(state.byId.get("old-lab")))').includes('Earlier PI'));
assert(evaluate('state.index.find(row => row.name.includes("faculty emeriti")).haystack.includes("physics")'), 'archives retain the current taxonomy/search model');

context.pendingIdentityData = { professors: [], labs: [], recovery: { pendingProfileResources: [{
  id: 'possible-person', label: 'Possible existing person', classification: 'pending_person_identity',
  department: 'Physics', sourceUrl: 'https://profiles.ucsd.edu/possible.person',
  previousProfessorObservations: [{ scope: 'source_observation', record: oldSnapshot }],
}] } };
assert.equal(evaluate('buildRecords(pendingIdentityData)[0].recordType'), 'archive');
assert.equal(evaluate('buildRecords(pendingIdentityData)[0].displayKind'), 'Profile observation');
assert.equal(evaluate('sourceChecked(buildRecords(pendingIdentityData)[0])'), false);
assert(evaluate('JSON.stringify(archiveDetails(buildRecords(pendingIdentityData)[0]))').includes('Captured source record'));

context.historicalAppointmentFixture = {
  historicalAppointmentAsListed: { titleAsListed: 'Associate Professor, Physics' },
  historicalFieldEvidence: { appointmentStatus: [{ sourceUrl: 'https://profiles.ucsd.edu/example', observedAt: '2020-01-01', evidence: 'Earlier appointment quote' }] },
  verification: { status: 'needs_review', rawUnavailable: true },
  fieldEvidence: { name: [{ sourceUrl: 'https://profiles.ucsd.edu/example', observedAt: '2020-01-01' }] },
};
const historicalAppointment = evaluate('JSON.stringify(recoveryAppointmentDetails(historicalAppointmentFixture))');
assert(historicalAppointment.includes('Historical appointment'));
assert(historicalAppointment.includes('Associate Professor, Physics'));
assert(historicalAppointment.includes('2020-01-01'));
assert(historicalAppointment.includes('not freshly verified'));
assert.equal(evaluate('sourceChecked(historicalAppointmentFixture)'), false);
context.freshAppointmentFixture = { appointmentAsListed: { titleAsListed: 'Assistant Professor', sourceUrl: 'https://profiles.ucsd.edu/fresh', observedAt: '2026-10-17' } };
assert(evaluate('JSON.stringify(recoveryAppointmentDetails(freshAppointmentFixture))').includes('Captured appointment'));
context.freshAppointmentFixture = { appointmentAsListed: { namedFacultyListing: { listedRole: 'Lecturer', sourceUrl: 'https://physics.ucsd.edu/faculty', observedAt: '2026-10-17' } } };
assert(evaluate('JSON.stringify(recoveryAppointmentDetails(freshAppointmentFixture))').includes('Lecturer'));
context.freshAppointmentFixture = { appointmentAsListed: { namedFacultyListing: { listedRole: 'Assistant Professor', capture: { sourceUrl: 'https://physics.ucsd.edu/faculty', observedAt: '2026-10-17' } } } };
assert(evaluate('JSON.stringify(recoveryAppointmentDetails(freshAppointmentFixture))').includes('https://physics.ucsd.edu/faculty'));
assert.equal(evaluate('recoveryAppointmentDetails({appointmentAsListed:{titleAsListed:"Professor"},fieldEvidence:{appointmentStatus:[{sourceUrl:"https://other.ucsd.edu/",observedAt:"2026-10-17"}]}})'), null,
  'a role without its own source metadata cannot borrow unrelated field evidence');
assert.equal(evaluate('sourceChecked({ verification: { status: "source_checked", rawUnavailable: false } })'), true);

// Rail evidence toggles combine, and older single-value links still parse.
assert.equal(evaluate('state.evidence = "courses"; evidenceKeys().join()'), 'courses');
assert.equal(evaluate('setEvidenceKeys(["ratings", "courses", "bogus"]); state.evidence'), 'courses,ratings',
  'evidence keys are stored in a stable order and unknown keys are dropped');
assert.equal(evaluate('state.evidence = "courses,ratings"; matchesFilters({ facts: { courses: 2, ratings: [], checked: true } })'), false,
  'selected evidence filters must all hold');
assert.equal(evaluate('matchesFilters({ facts: { courses: 2, ratings: ["rateMyPI"], checked: true } })'), true);
evaluate('state.evidence = "all"');

// Unknown reviewed departments fall back to the unit in the record's own captured listing.
assert.equal(evaluate('unitFromTitle("Lecturer - Academic Year, Provost - Muir")'), 'Provost - Muir');
assert.equal(evaluate('resolveDepartment("Provost - Muir").name'), 'John Muir College');
assert.equal(evaluate('resolveDepartment("Ob/Gyn & Reproductive sciences").name'), 'Obstetrics, Gynecology & Reproductive Sciences');
const listed = evaluate(`JSON.stringify(buildRecords({ professors: [{ id: "u1", name: "Example Person", department: "Unknown",
  appointmentAsListed: { namedFacultyListing: { titleAsListed: "Assistant Clinical Professor",
    evidence: { sourceUrl: "https://pediatrics.ucsd.edu/faculty/index.html", observedAt: "2026-10-17T00:00:00Z" } } } }] })[0])`);
assert(JSON.parse(listed).departments.includes('Pediatrics'), 'a verified department roster listing names the department');
assert.equal(JSON.parse(listed).department, 'Unknown', 'the reviewed department field itself is left unchanged');
assert.equal(evaluate('buildRecords({ professors: [{ id: "u2", name: "No Evidence", department: "Unknown" }] })[0].departments.length'), 0,
  'without captured evidence no department is invented');

// Labs with an Unknown reviewed department use their own site's statement, or a PI named there.
const labObs = { entries: [
  { labId: "l1", basis: "lab_site_statement", unitsAsPublished: ["Department: MAE"].map(() => "MAE"), sourceUrl: "https://lab.ucsd.edu/", observedAt: "2026-10-18", evidence: ["Department: MAE, UCSD"] },
  { labId: "l2", basis: "named_principal_investigator", principalInvestigatorId: "p1", sourceUrl: "https://lab2.ucsd.edu/", observedAt: "2026-10-18", evidence: ["Jane Doe"] },
] };
context.labObs = labObs;
const labRows = JSON.parse(evaluate(`JSON.stringify(buildRecords({ professors: [{ id: "p1", name: "Jane Doe", department: "Physics" }],
  labs: [{ id: "l1", labName: "One Lab", department: "Unknown" }, { id: "l2", labName: "Two Lab", department: "Unknown" }, { id: "l3", labName: "Three Lab", department: "Unknown" }] }, null, labObs))`));
const labById = Object.fromEntries(labRows.map((r) => [r.id, r]));
assert.equal(labById.l1.departments.join(), 'Mechanical & Aerospace Engineering', 'a lab site naming its unit maps to the department');
assert.equal(labById.l2.departments.join(), 'Physics', 'a PI named on the lab site lends the department from their record');
assert.equal(labById.l3.departments.length, 0, 'labs without an observation stay unassigned');
assert.equal(labById.l1.department, 'Unknown', 'the reviewed lab department field is unchanged');

console.log('PASS: person/lab identity, recovered archives and appointments, field verification, missing scores, course indexing, taxonomy, and fuzzy search');
