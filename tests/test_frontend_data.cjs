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

console.log('PASS: person and lab identity, field verification, missing scores, course-code indexing, taxonomy, and fuzzy search');
