const DATA_URL = "data/research-atlas.json";
const REAL_PORTAL_DATA_URL = "data/ucsd/real-portal-resources.json";
const NOT_FOUND = "Not found";
const UNKNOWN = "Unknown";
const PAGE_SIZE = 40;
const AUTO_LOAD_LIMIT = PAGE_SIZE * 5;
const SEARCH_DEBOUNCE_MS = 140;
const SAVED_KEY = "researchAtlasSaved";
const DATA_FETCH_OPTIONS = { credentials: "same-origin", cache: "no-cache" };
const METRIC_STOPWORDS = new Set([
  "about",
  "across",
  "advanced",
  "analysis",
  "and",
  "array",
  "based",
  "california",
  "computer",
  "course",
  "data",
  "department",
  "diego",
  "effect",
  "engineering",
  "faculty",
  "for",
  "from",
  "learning",
  "machine",
  "methods",
  "model",
  "models",
  "profile",
  "public",
  "research",
  "san",
  "science",
  "signals",
  "study",
  "through",
  "ucsd",
  "university",
  "using",
  "with",
]);

const DEFAULT_FILTERS = {
  query: "",
  type: "all",
  division: "all",
  department: "all",
  field: "all",
  area: "all",
  recruiting: "all",
  evidence: "all",
  verifiedOnly: false,
  savedOnly: false,
  sort: "relevance",
};

// Short URL parameter names keep shared links readable.
const URL_KEYS = {
  query: "q",
  type: "type",
  division: "school",
  department: "dept",
  field: "field",
  area: "area",
  recruiting: "status",
  evidence: "evidence",
  verifiedOnly: "checked",
  savedOnly: "saved",
  sort: "sort",
};

const TYPE_KEYS = ["professor", "lab", "resource"];
const EVIDENCE_LABELS = {
  courses: "Official teaching records",
  ratings: "Any published rating",
  rateMyPI: "PI Review score",
  rateMyProfessors: "Rate My Professors score",
  needs_review: "Needs verification",
};
const RATING_PLATFORMS = [
  ["rateMyPI", "PI Review", "Mentoring opinions"],
  ["rateMyProfessors", "Rate My Professors", "Teaching opinions"],
];
const RATING_SHORT = { rateMyPI: "PI Review", rateMyProfessors: "RMP" };

const media = (query) => window.matchMedia(query);
const DESKTOP_DETAIL_QUERY = media("(min-width: 1280px)");
const DRAWER_QUERY = media("(max-width: 899px)");
const COMPACT_QUERY = media("(max-width: 639px)");
const REDUCED_MOTION_QUERY = media("(prefers-reduced-motion: reduce)");

const state = {
  ...DEFAULT_FILTERS,
  data: null,
  records: [],
  index: [],
  byId: new Map(),
  results: [],
  highlighter: null,
  vocabulary: null,
  departmentDivision: new Map(),
  facetCounts: null,
  suggestions: [],
  suggestionIndex: -1,
  visibleLimit: PAGE_SIZE,
  activeId: "",
  userSelected: false,
  saved: new Set(readStoredList(SAVED_KEY)),
};

const els = {
  form: document.querySelector("#searchForm"),
  query: document.querySelector("#query"),
  typeButtons: [...document.querySelectorAll("[data-type-choice]")],
  typeCounts: [...document.querySelectorAll("[data-count]")],
  quickButtons: [...document.querySelectorAll("[data-quick]")],
  division: document.querySelector("#divisionFilter"),
  department: document.querySelector("#departmentFilter"),
  field: document.querySelector("#fieldFilter"),
  area: document.querySelector("#areaFilter"),
  suggest: document.querySelector("#suggestions"),
  fieldStrip: document.querySelector("#fieldStrip"),
  searchNote: document.querySelector("#searchNote"),
  evidence: document.querySelector("#evidenceFilter"),
  verifiedOnly: document.querySelector("#verifiedOnly"),
  recruiting: document.querySelector("#recruitingFilter"),
  sort: document.querySelector("#sortFilter"),
  clear: document.querySelector("#clearFilters"),
  filtersButton: document.querySelector("#filtersButton"),
  filterCount: document.querySelector("#filterCount"),
  savedToggle: document.querySelector("#savedToggle"),
  savedCountTop: document.querySelector("#savedCountTop"),
  shareButton: document.querySelector("#shareButton"),
  rail: document.querySelector("#filterRail"),
  railClose: document.querySelector("#railClose"),
  railApply: document.querySelector("#railApply"),
  professorCount: document.querySelector("#professorCount"),
  labCount: document.querySelector("#labCount"),
  realResourceCount: document.querySelector("#realResourceCount"),
  courseCount: document.querySelector("#courseCount"),
  ratingCount: document.querySelector("#ratingCount"),
  updatedAt: document.querySelector("#updatedAt"),
  workspace: document.querySelector("#workspace"),
  resultHeading: document.querySelector("#resultHeading"),
  coverageLine: document.querySelector("#coverageLine"),
  activeFilters: document.querySelector("#activeFilters"),
  results: document.querySelector("#results"),
  loadMore: document.querySelector("#loadMore"),
  empty: document.querySelector("#emptyState"),
  emptyHint: document.querySelector("#emptyHint"),
  emptyReset: document.querySelector("#emptyReset"),
  savedCount: document.querySelector("#savedCount"),
  savedList: document.querySelector("#savedList"),
  detailPanel: document.querySelector("#detailPanel"),
  detailContent: document.querySelector("#detailContent"),
  detailClose: document.querySelector("#detailClose"),
  scrim: document.querySelector("#scrim"),
  toast: document.querySelector("#toast"),
};

/* ---------- Small utilities ---------- */

function readStoredList(key) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStoredList(key, values) {
  try {
    localStorage.setItem(key, JSON.stringify(values));
  } catch {
    // Private mode or blocked storage: saving still works for this visit.
  }
}

// Lower-case and drop diacritics, so "Halicioğlu" and "halicioglu" compare equal.
function foldText(value) {
  const text = String(value || "");
  return (/[^\x00-\x7f]/.test(text) ? text.normalize("NFKD").replace(/\p{M}+/gu, "") : text).toLowerCase();
}

function normalize(value) {
  return foldText(value).replace(/[^\p{L}\p{N}@.+-]+/gu, " ").trim();
}

function isKnown(value) {
  return value !== null && value !== undefined && value !== "" && value !== NOT_FOUND && value !== UNKNOWN;
}

function knownText(value) {
  return isKnown(value) ? String(value) : "";
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function uniqueByNormalized(values) {
  const seen = new Set();
  const out = [];
  for (const value of values.filter(isKnown)) {
    const key = normalize(value);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(value);
  }
  return out;
}

function uniqueLinks(links) {
  const seen = new Set();
  const out = [];
  for (const [label, url] of links) {
    if (!isKnown(url) || seen.has(url)) continue;
    seen.add(url);
    out.push([label, url]);
  }
  return out;
}

function numericMetric(value) {
  const numeric = Number(value);
  return isKnown(value) && Number.isFinite(numeric) && numeric >= 0;
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("en-US");
}

function slugLabel(value) {
  return String(value || "")
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function cleanText(value) {
  return String(value || "")
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function debounce(fn, wait) {
  let timer = 0;
  return (...args) => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => fn(...args), wait);
  };
}

function make(tag, className = "", content = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== "" && content !== null && content !== undefined) node.append(content);
  return node;
}

function makeExternal(label, url, className = "") {
  const anchor = make("a", className, label);
  anchor.href = url;
  anchor.target = "_blank";
  anchor.rel = "noreferrer";
  return anchor;
}

function prefersReducedMotion() {
  return REDUCED_MOTION_QUERY.matches;
}

/* ---------- Evidence model ---------- */

function coursesFor(record) {
  return Array.isArray(record.teaching?.courses) ? record.teaching.courses : [];
}

function courseTermOrder(course) {
  const term = String(course.term || "");
  const year = Number(term.match(/\b(?:19|20)\d{2}\b/)?.[0] || 0);
  const season = (term.match(/\b(winter|spring|summer|fall|autumn)\b/i)?.[1] || "").toLowerCase();
  return year * 10 + ({ winter: 1, spring: 2, summer: 3, fall: 4, autumn: 4 }[season] || 0);
}

function ratedPlatforms(record) {
  return Object.entries(record.ratings || {}).filter(([, rating]) => (
    rating.status === "verified" && numericMetric(rating.score) && Number(rating.reviewCount) > 0
  ));
}

function bestRating(record) {
  return ratedPlatforms(record).sort(([, a], [, b]) => Number(b.reviewCount) - Number(a.reviewCount))[0] || null;
}

function evidenceFields(record) {
  return Object.entries(record.fieldEvidence || {}).filter(([, items]) => (
    Array.isArray(items) && items.some((item) => item.sourceUrl && item.observedAt)
  ));
}

function profileLinkNeedsReview(record) {
  const review = record.profileLinkIdentityReview;
  return review?.captureVerified === true && review.status === "needs_review"
    && review.originalProfileUri === record.officialProfileUrl && review.captures?.length === 2;
}

function sourceChecked(record) {
  if (profileLinkNeedsReview(record)) return false;
  if (record.destinationIdentityAssessment?.identityStatus === "mismatch" || record.verification?.destinationIdentityStatus === "mismatch") return false;
  return record.verification?.status === "source_checked" || evidenceFields(record).length > 0;
}

function verificationLabel(record) {
  if (record.verification?.status === "needs_review") return "Needs review";
  if (record.verification?.status === "unavailable") return "Source unavailable";
  if (sourceChecked(record)) return "Partly source checked";
  return "Legacy · not reverified";
}

function facultyLabel(record) {
  const legacyRole = {
    emeritus: "Emeritus faculty",
    former: "Former faculty · directory",
    deceased: "Deceased · directory",
  }[record.facultyStatus];
  return legacyRole || ({
    listed_faculty: "Listed in official faculty directory",
    affiliate: "Affiliate · directory",
    emeritus: "Emeritus faculty",
    lecturer: "Lecturer · directory",
    adjunct: "Adjunct faculty · directory",
  })[record.appointmentStatus] || (record.facultyStatus === "listed_in_official_directory" ? "Listed in official directory" : "Status not verified");
}

function departmentNames(record) {
  return uniqueByNormalized([
    record.department,
    ...(record.departmentAffiliations || []).map((item) => typeof item === "string" ? item : item.department || item.name),
    ...(Array.isArray(record.directoryListings) ? record.directoryListings.map((item) => item.department) : []),
  ]);
}

function dateLabel(value) {
  if (!isKnown(value)) return "Not checked";
  if (/^\d{4}-\d{2}-\d{2}$/.test(String(value))) return String(value);
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) return "Date unavailable";
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Los_Angeles", year: "numeric", month: "2-digit", day: "2-digit",
  }).format(date);
}

function ratingStatusLabel(rating) {
  return ({
    no_reviews: "No reviews on matched profile",
    not_found: "No exact match in checked source",
    unavailable: "Source unavailable",
    needs_review: "Identity needs review",
    not_checked: "Not checked",
  })[rating?.status] || "Not verified";
}

function hasScholarProfile(record) {
  if (!isKnown(record.googleScholarUrl)) return false;
  try {
    const url = new URL(record.googleScholarUrl);
    return /^scholar\.google\.[a-z.]+$/.test(url.hostname) && url.pathname === "/citations" && Boolean(url.searchParams.get("user"));
  } catch {
    return false;
  }
}

function tokenSet(value) {
  return new Set(
    normalize(cleanText(value))
      .split(/\s+/)
      .filter((token) => token.length > 2 && !/^\d+$/.test(token) && !METRIC_STOPWORDS.has(token)),
  );
}

function relevantPublications(record) {
  const recordTokens = tokenSet([record.department, record.summary, record.labAffiliation, ...(record.researchAreas || [])].join(" "));
  const publications = record.academicProfile?.recentPublications || [];
  return publications
    .map((paper) => {
      let score = 0;
      for (const token of tokenSet([paper.title, paper.venue].join(" "))) {
        if (recordTokens.has(token)) score += 1;
      }
      return { paper, score };
    })
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score || String(b.paper.publicationDate || b.paper.year || "").localeCompare(String(a.paper.publicationDate || a.paper.year || "")))
    .map(({ paper }) => paper);
}

function hasAcademicMetrics(record) {
  const profile = record.academicProfile || {};
  return numericMetric(profile.citationCount) || numericMetric(profile.worksCount) || numericMetric(profile.hIndex);
}

// Citation numbers are shown only when the author match itself carries verification evidence.
function academicMetrics(record) {
  const profile = record.academicProfile || {};
  const hasMetrics = hasAcademicMetrics(record);
  const source = isKnown(profile.source) ? profile.source : (isKnown(profile.openAlexUrl) ? "OpenAlex" : UNKNOWN);
  const verified = hasMetrics && (
    profile.verificationStatus === "verified"
    || (record.fieldEvidence?.academicProfile || []).some((evidence) => evidence.sourceUrl && evidence.observedAt && evidence.status === "verified")
  );
  return {
    profile,
    hasMetrics,
    verified,
    source,
    citationCount: verified && numericMetric(profile.citationCount) ? Number(profile.citationCount) : -1,
    status: verified ? `${source} verified` : (hasMetrics ? `${source} needs review` : "Not verified"),
  };
}

/* ---------- Record model ---------- */

function primaryAffiliationLabel(record) {
  return (record.labAffiliations || []).some((item) => item.recordSubtype === "ngo" && item.url === record.labAffiliationUrl)
    ? "Organization affiliation" : "Lab affiliation";
}

function professorLinks(professor) {
  const reviewedLink = profileLinkNeedsReview(professor);
  return [
    [reviewedLink ? "Original profile link (identity review)" : "Faculty profile", professor.officialProfileUrl],
    ["Personal website", professor.personalWebsiteUrl],
    ["Google Scholar profile", hasScholarProfile(professor) ? professor.googleScholarUrl : null],
    ["Google Scholar search", professor.googleScholarSearchUrl],
    ["OpenAlex author", professor.academicProfile?.openAlexUrl],
    ["LinkedIn search", professor.linkedinSearchUrl],
    [primaryAffiliationLabel(professor), professor.labAffiliationUrl],
    ...(professor.labAffiliations || []).filter((lab) => lab.url !== professor.labAffiliationUrl).map((lab) => [lab.labName || "Related lab", lab.url]),
  ].filter(([, url]) => isKnown(url));
}

function unverifiedOwnershipPi(record) {
  return record.unverifiedFields?.includes("principalInvestigator")
    && (record.labOwnershipReviews || []).some((review) => review.captureVerified === true
      && review.kind === "existing_lab_own_contact_institution");
}

function labLinks(lab) {
  return [
    [lab.destinationIdentityAssessment?.identityStatus === "mismatch" || lab.verification?.destinationIdentityStatus === "mismatch" ? "Original listed website (identity mismatch)" : lab.recordSubtype === "ngo" ? "Organization website" : "Lab website", lab.labWebsiteUrl],
    ["PI profile", lab.principalInvestigatorProfileUrl],
    ...(lab.sharedResourceReviews || []).filter((review) => review.captureVerified && review.action === "register_shared_lab_resource" && review.resourceKind === "shared_landing_page" && review.memberLabIds?.includes(lab.id)).map((review) => ["Shared landing page", review.resourceUri]),
  ].filter(([, url]) => isKnown(url));
}

function resourceLinks(resource) {
  return [
    ["REAL Portal listing", resource.sourceUrl],
    ...(resource.externalUrls || []).map((url, index) => [`External link ${index + 1}`, url]),
  ].filter(([, url]) => isKnown(url));
}

function resourceAreas(resource) {
  const areas = ["Experiential learning"];
  const text = normalize(`${resource.title} ${resource.description} ${resource.resourceType}`);
  if (text.includes("research")) areas.push("Research");
  if (text.includes("intern")) areas.push("Internship");
  if (text.includes("volunteer")) areas.push("Volunteer");
  if (text.includes("co curricular") || resource.resourceType === "Co-curricular") areas.push("Co-curricular");
  return unique(areas);
}

/* ---------- Taxonomy: broad groups with detailed entries (assets/taxonomy.js) ---------- */

const OTHER_DIVISION = { id: "other", label: "Other units", aliases: [], departments: [] };
const CJK_PATTERN = /[\u3400-\u9fff]/;

// Matching key for department and organization names: "Department of Physics" and
// "Electrical and Computer Engineering (ECE)" reduce to their plain names.
function departmentKey(value) {
  return foldText(value)
    .replace(/\([^)]*\)/g, " ")
    .replace(/&/g, " and ")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim()
    .replace(/^(the )?department of /, "")
    .replace(/ department$/, "");
}

function buildTaxonomy() {
  const divisions = new Map([...DIVISIONS, OTHER_DIVISION].map((division) => [division.id, division]));
  const departments = new Map();
  for (const division of DIVISIONS) {
    for (const department of division.departments) {
      const entry = { ...department, division: division.id };
      for (const alias of [department.name, ...(department.aliases || [])]) departments.set(departmentKey(alias), entry);
    }
  }
  const fields = new Map();
  const subfields = new Map();
  for (const field of RESEARCH_FIELDS) {
    fields.set(field.id, field);
    for (const sub of field.subfields) {
      subfields.set(sub.id, { ...sub, field: field.id, pattern: new RegExp(`\\b(?:${sub.patterns.join("|")})`, "i") });
    }
  }
  // Campus units are checked first so "Student Health" is not filed under Medicine.
  const divisionOrder = [...DIVISIONS].sort((a, b) => (b.id === "campus") - (a.id === "campus"));
  // Chinese names translate to the English label they belong to; the search index stays
  // English-only because CJK text would make every indexed string slower to scan.
  const cjk = {};
  const addCjk = (key, values) => { cjk[key] = unique([...(cjk[key] || []), ...values]); };
  for (const entry of [...fields.values(), ...subfields.values(), ...DIVISIONS]) {
    for (const alias of entry.aliases || []) if (CJK_PATTERN.test(alias)) addCjk(alias, [entry.label]);
  }
  for (const [key, values] of Object.entries(CJK_SYNONYMS)) addCjk(key, values);
  return { divisions, departments, fields, subfields, divisionOrder, cjk };
}

const TAXONOMY = buildTaxonomy();

function resolveDepartment(raw, fallbackDivision = OTHER_DIVISION.id) {
  const key = departmentKey(raw);
  if (!key) return null;
  const known = TAXONOMY.departments.get(key);
  if (known) return known;
  const division = TAXONOMY.divisionOrder.find((item) => item.match?.test(key));
  return { name: cleanText(raw), division: division?.id || fallbackDivision };
}

function divisionLabel(id) {
  return TAXONOMY.divisions.get(id)?.label || slugLabel(id);
}

function fieldLabel(id) {
  return TAXONOMY.fields.get(id)?.label || slugLabel(id);
}

function subfieldLabel(id) {
  return TAXONOMY.subfields.get(id)?.label || slugLabel(id);
}

// Raw area lists mix "Physical Chemistry|Materials Chemistry", trailing commas and case variants.
function cleanAreas(values) {
  return uniqueByNormalized((values || [])
    .flatMap((value) => String(value).split("|"))
    .map((value) => value.replace(/[\s,;:.]+$/, "").trim())
    .filter((value) => value.length > 2));
}

function subfieldsForText(text) {
  const folded = foldText(text);
  if (!folded.trim()) return [];
  return [...TAXONOMY.subfields.values()].filter((sub) => sub.pattern.test(folded)).map((sub) => sub.id);
}

// Fields come from sourced topic text plus the field each department implies, so records
// without a captured summary still appear under their broad field.
function classifyRecord(record) {
  const text = [
    ...(record.researchAreas || []),
    ...(record.researchKeywords || []),
    record.summary,
    record.recordType === "professor" ? "" : record.displayName,
    ...(record.labAffiliations || []).map((lab) => lab.labName),
  ].filter(isKnown).join(" · ");
  const subfields = new Set(subfieldsForText(text));
  const fields = new Set();
  for (const name of record.departments || []) {
    const department = TAXONOMY.departments.get(departmentKey(name));
    if (department?.sub) subfields.add(department.sub);
    if (department?.field) fields.add(department.field);
  }
  for (const id of subfields) fields.add(TAXONOMY.subfields.get(id).field);
  record.subfieldIds = [...subfields];
  record.fieldIds = RESEARCH_FIELDS.map((field) => field.id).filter((id) => fields.has(id));
  return record;
}

function assignDepartments(record, names, fallbackDivision) {
  const resolved = names.map((name) => resolveDepartment(name, fallbackDivision)).filter(Boolean);
  for (const { name, division } of resolved) {
    if (!state.departmentDivision.has(name)) state.departmentDivision.set(name, division);
  }
  record.departments = uniqueByNormalized(resolved.map((item) => item.name));
  record.divisions = unique(resolved.map((item) => item.division));
  return record;
}

function professorKind(item) {
  const flagged = ["emeritus", "former", "deceased"].includes(item.facultyStatus)
    || ["affiliate", "emeritus", "lecturer", "adjunct"].includes(item.appointmentStatus);
  return flagged ? facultyLabel(item).split(" · ")[0] : "Professor";
}

// Derived facts are computed once so filtering and sorting stay cheap on every keystroke.
function withFacts(record) {
  classifyRecord(record);
  const rating = bestRating(record);
  record.facts = {
    courses: coursesFor(record).length,
    ratings: ratedPlatforms(record).map(([key]) => key),
    rating,
    checked: sourceChecked(record),
    needsReview: record.verification?.status === "needs_review",
    metrics: academicMetrics(record),
  };
  return record;
}

function buildRecords(data, realPortalData = null) {
  const professors = (data.professors || []).map((item) => ({
    ...item,
    recordType: "professor",
    displayName: knownText(item.name) || NOT_FOUND,
    displayKind: professorKind(item),
    summary: knownText(item.researchSummary),
    email: knownText(item.email),
    researchAreas: cleanAreas(item.researchAreas),
    sourceUrls: item.sourceUrls || [],
    links: professorLinks(item),
  })).map((record) => withFacts(assignDepartments({ ...record }, departmentNames(record))));

  const labs = (data.labs || []).map((item) => withFacts(assignDepartments({
    ...item,
    recordType: "lab",
    displayName: knownText(item.labName) || NOT_FOUND,
    displayKind: item.recordSubtype === "ngo" ? "NGO" : item.recordSubtype === "research_group" ? "Research group" : "Lab",
    summary: knownText(item.description),
    email: knownText(item.contactEmail),
    researchAreas: cleanAreas(item.researchAreas),
    sourceUrls: item.sourceUrls || [],
    links: labLinks(item),
  }, departmentNames(item))));

  const resources = (realPortalData?.resources || []).map((item) => withFacts(assignDepartments({
    ...item,
    id: item.id || `real-${item.title}`,
    recordType: "resource",
    displayName: knownText(item.title) || NOT_FOUND,
    displayKind: "REAL resource",
    institution: "University of California San Diego",
    department: knownText(item.organization),
    summary: knownText(item.description),
    email: knownText(item.contactEmails?.[0]),
    researchAreas: resourceAreas(item),
    sourceUrls: [item.sourceUrl || realPortalData.sourceUrl].filter(isKnown),
    links: resourceLinks(item),
    recruitingStatus: UNKNOWN,
    recruitingEvidence: { text: "", url: "" },
  }, uniqueByNormalized([item.organization]), "campus")));

  return [...professors, ...labs, ...resources];
}

// Person identities are resolved by the source-reviewed data build. The UI
// preserves separate records and resolves only explicitly retained stable IDs.
function makeRecordIndex(records) {
  const index = new Map();
  for (const record of records) {
    for (const id of [record.id, ...(record.aliasIds || [])]) {
      if (!id) continue;
      if (index.has(id) && index.get(id) !== record) throw new Error(`Ambiguous record ID: ${id}`);
      index.set(id, record);
    }
  }
  return index;
}

function programConnections(record) {
  return (record.campusProgramRelationships || []).filter((entry) => entry.captureVerified === true && entry.relationship === "program_listing_and_own_rotation_guidance");
}

function taxonomyTerms(record) {
  const named = (map, ids) => ids.flatMap((id) => {
    const entry = map.get(id);
    return entry ? [entry.label, ...(entry.aliases || []).filter((alias) => !CJK_PATTERN.test(alias))] : [];
  });
  return [
    ...named(TAXONOMY.fields, record.fieldIds || []),
    ...named(TAXONOMY.subfields, record.subfieldIds || []),
    ...named(TAXONOMY.divisions, record.divisions || []),
  ];
}

function buildIndex(records) {
  return records.map((record) => {
    const departments = record.departments || departmentNames(record);
    const topics = taxonomyTerms(record);
    const fields = [
      record.displayName,
      record.displayKind,
      record.institution,
      record.facultyStatus,
      record.directorySection,
      record.appointmentStatus,
      ...(record.aliasNames || []),
      ...departments,
      record.summary,
      record.email,
      record.labAffiliation,
      ...(record.labAffiliations || []).flatMap((lab) => [lab.labName, lab.url]),
      record.principalInvestigator,
      ...(record.relatedProfessorNames || []),
      ...programConnections(record).map((entry) => entry.programName),
      record.organization,
      record.resourceType,
      record.applicationProcedure,
      record.academicProfile?.matchedName,
      record.academicProfile?.openAlexUrl,
      ...(record.academicProfile?.recentPublications || []).flatMap((paper) => [paper.title, paper.venue, paper.year]),
      record.recruitingStatus,
      record.recruitingEvidence?.text,
      // Compact codes ("cse151a") are indexed so course searches work without the space.
      ...coursesFor(record).flatMap((course) => [course.courseCode, String(course.courseCode || "").replace(/\s+/g, ""), course.title, course.term, course.status]),
      ...Object.values(record.ratings || {}).map((rating) => rating.platform),
      ...(record.researchAreas || []),
      ...(record.researchKeywords || []),
      // Field and school names let "neuroscience" or "engineering" find records whose own text never says so.
      ...topics,
      ...(record.links || []).flatMap(([label, url]) => [label, url]),
      ...(record.sourceUrls || []),
    ];

    // Leading spaces let short terms match at word starts only (" ai" but not "email").
    return {
      haystack: ` ${normalize(fields.filter(isKnown).join(" "))} `,
      name: ` ${normalize([record.displayName, ...(record.aliasNames || [])].join(" "))} `,
      departments: departments.map(normalize),
      areas: [...(record.researchAreas || []), ...(record.researchKeywords || [])].map(normalize),
      topics: ` ${normalize(topics.join(" "))} `,
    };
  });
}

// Word -> record count, used only to widen a misspelled term to the words it was meant to be.
// Built on the first query that needs it, so page load doesn't pay for it.
function buildVocabulary(index) {
  const vocabulary = new Map();
  for (const indexed of index) {
    for (const token of new Set(indexed.haystack.split(" "))) {
      if (token.length > 2 && /^\p{L}+$/u.test(token)) vocabulary.set(token, (vocabulary.get(token) || 0) + 1);
    }
  }
  return vocabulary;
}

/* ---------- Search & filtering ---------- */

const fuzzyCache = new Map();

// Optimal string alignment distance (a transposition counts as one edit), abandoned past `max`.
function editDistance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let before = null;
  let previous = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i += 1) {
    const row = [i];
    let rowMin = i;
    for (let j = 1; j <= b.length; j += 1) {
      let value = Math.min(previous[j] + 1, row[j - 1] + 1, previous[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) value = Math.min(value, before[j - 2] + 1);
      row[j] = value;
      rowMin = Math.min(rowMin, value);
    }
    if (rowMin > max) return max + 1;
    before = previous;
    previous = row;
  }
  return previous[b.length];
}

// A term that already occurs somewhere is taken literally; only unknown words get spelling help.
// Whole-word corrections ("cancr" -> "cancer") win over prefix ones, which keep half-typed
// words useful ("nuerosci" -> "neurosci"). Corrections then match like typed text.
function spellingCorrections(term) {
  if (fuzzyCache.has(term)) return fuzzyCache.get(term);
  let result = [];
  if (/^\p{L}{5,}$/u.test(term) && !state.index.some((indexed) => indexed.haystack.includes(term))) {
    state.vocabulary ||= buildVocabulary(state.index);
    const max = term.length >= 8 ? 2 : 1;
    const candidates = [];
    for (const [token, weight] of state.vocabulary) {
      if (token[0] !== term[0] && token[1] !== term[1]) continue;
      const whole = editDistance(term, token, max);
      if (whole <= max) candidates.push({ text: token, rank: whole * 2, weight });
      else if (token.length > term.length && editDistance(term, token.slice(0, term.length), max) <= max) {
        candidates.push({ text: token.slice(0, term.length), rank: max * 2 + 1, weight });
      }
    }
    const best = Math.min(...candidates.map((candidate) => candidate.rank));
    const weights = new Map();
    for (const candidate of candidates.filter((item) => item.rank === best)) {
      weights.set(candidate.text, (weights.get(candidate.text) || 0) + candidate.weight);
    }
    result = [...weights].sort((a, b) => b[1] - a[1]).slice(0, 4).map(([text]) => text);
  }
  fuzzyCache.set(term, result);
  return result;
}

function makeTerm(raw, alternatives) {
  return { raw, alts: unique(alternatives.map(normalize)), fuzzyTokens: spellingCorrections(raw) };
}

// Chinese has no spaces, so known words inside a query become separate required terms.
function cjkKeys(word) {
  const keys = Object.keys(TAXONOMY.cjk).filter((key) => word.includes(key));
  return keys.filter((key) => !keys.some((other) => other !== key && other.includes(key)));
}

function compileQuery(query) {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  const terms = [];
  for (const word of words) {
    if (CJK_PATTERN.test(word)) {
      const keys = cjkKeys(word);
      if (keys.length > 1) keys.forEach((key) => terms.push(makeTerm(key, [key, ...TAXONOMY.cjk[key]])));
      else terms.push(makeTerm(word, [word, ...keys.flatMap((key) => TAXONOMY.cjk[key])]));
    } else {
      terms.push(makeTerm(word, [word, ...(SEARCH_SYNONYMS[word] || [])]));
    }
  }
  return { terms, phrase: words.length > 1 ? words.join(" ") : "" };
}

// Indexed text is padded with spaces. Terms of three or more letters match anywhere, as
// before; one- and two-letter terms must start a word ("wu" finds "Wuerthwein", not every
// "would"), and known abbreviations ("ai", "ml") must be whole words so "html" stays out.
function isAbbreviation(alt) {
  return alt.length <= 2 && Object.hasOwn(SEARCH_SYNONYMS, alt);
}

function textHas(text, alt) {
  if (CJK_PATTERN.test(alt) || alt.length > 2) return text.includes(alt);
  return text.includes(isAbbreviation(alt) ? ` ${alt} ` : ` ${alt}`);
}

function termMatches(term, indexed) {
  return term.alts.some((alt) => textHas(indexed.haystack, alt)) || term.fuzzyTokens.some((alt) => indexed.haystack.includes(alt));
}

function matchesFilters(record) {
  const { facts } = record;
  if (state.savedOnly && !state.saved.has(record.id)) return false;
  if (state.division !== "all" && !record.divisions.includes(state.division)) return false;
  if (state.department !== "all" && !record.departments.includes(state.department)) return false;
  if (state.recruiting !== "all" && (record.recruitingStatus || UNKNOWN) !== state.recruiting) return false;
  if (state.verifiedOnly && !facts.checked) return false;
  if (state.evidence === "courses" && !facts.courses) return false;
  if (state.evidence === "ratings" && !facts.ratings.length) return false;
  if (["rateMyPI", "rateMyProfessors"].includes(state.evidence) && !facts.ratings.includes(state.evidence)) return false;
  if (state.evidence === "needs_review" && facts.checked && !facts.needsReview) return false;
  return true;
}

// Where a word appears decides its weight: a name beats a research area beats body text.
function placementScore(indexed, alt) {
  if (indexed.name.startsWith(` ${alt}`)) return 18;
  if (textHas(indexed.name, alt) && indexed.name.includes(` ${alt}`)) return 14;
  if (indexed.name.includes(alt) && alt.length > 3) return 8;
  if (indexed.areas.some((area) => area.includes(alt))) return 7;
  if (textHas(indexed.topics, alt)) return 6;
  if (indexed.departments.some((department) => department.includes(alt))) return 5;
  return textHas(indexed.haystack, alt) ? 2 : 0;
}

function scoreRecord(record, indexed, matched, query) {
  const { facts } = record;
  // Without a query, records with more checked evidence surface first.
  let score = (facts.checked ? 4 : 0) + (facts.courses ? 3 : 0) + (facts.ratings.length ? 2 : 0) + (facts.metrics.verified ? 2 : 0);
  for (const term of matched) {
    // Spelling-corrected words count, but below anything the reader typed exactly.
    const best = Math.max(
      ...term.alts.map((alt) => placementScore(indexed, alt)),
      ...term.fuzzyTokens.map((alt) => placementScore(indexed, alt) * 0.75),
    );
    score += best || 1;
  }
  if (query.phrase) {
    if (indexed.name.includes(query.phrase)) score += 25;
    else if (indexed.haystack.includes(query.phrase)) score += 8;
  }
  score += matched.length * 20;
  if (record.recruitingStatus === "Recruiting") score += 3;
  return score;
}

function ratingSortValue(record) {
  const rating = record.facts.rating?.[1];
  return rating ? Number(rating.score) * 1000 + Math.min(Number(rating.reviewCount), 999) : -1;
}

const byName = (a, b) => a.record.displayName.localeCompare(b.record.displayName);
const SORTERS = {
  relevance: (a, b) => b.score - a.score || byName(a, b),
  name: byName,
  department: (a, b) => (a.record.departments[0] || "").localeCompare(b.record.departments[0] || "") || byName(a, b),
  courses: (a, b) => b.record.facts.courses - a.record.facts.courses || byName(a, b),
  rating: (a, b) => ratingSortValue(b.record) - ratingSortValue(a.record) || byName(a, b),
  citations: (a, b) => b.record.facts.metrics.citationCount - a.record.facts.metrics.citationCount || byName(a, b),
  sources: (a, b) => b.record.sourceUrls.length - a.record.sourceUrls.length || byName(a, b),
};

function increment(map, key) {
  map.set(key, (map.get(key) || 0) + 1);
}

// One pass computes the visible rows, the per-type counts under every other filter (so the
// type tabs show what each tab would reveal), and field counts for the browse strip.
function collectRows(query, required) {
  const counts = { all: 0, professor: 0, lab: 0, resource: 0 };
  const fieldCounts = new Map();
  const areaCounts = new Map();
  const rows = [];
  state.records.forEach((record, position) => {
    if (!matchesFilters(record)) return;
    const indexed = state.index[position];
    const matched = query.terms.filter((term) => termMatches(term, indexed));
    if (matched.length < required) return;
    const inField = state.field === "all" || record.fieldIds.includes(state.field);
    const inArea = state.area === "all" || record.subfieldIds.includes(state.area);
    const inType = state.type === "all" || record.recordType === state.type;
    if (inType) {
      record.fieldIds.forEach((id) => increment(fieldCounts, id));
      if (inField) record.subfieldIds.forEach((id) => increment(areaCounts, id));
    }
    if (!inField || !inArea) return;
    counts.all += 1;
    counts[record.recordType] += 1;
    if (!inType) return;
    rows.push({ record, score: state.sort === "relevance" ? scoreRecord(record, indexed, matched, query) : 0 });
  });
  return { rows, counts, fieldCounts, areaCounts };
}

function computeResults() {
  const query = compileQuery(state.query);
  let result = collectRows(query, query.terms.length);
  let relaxed = false;
  // Nothing has every word: fall back to records with most of them, ranked by how many.
  if (!result.counts.all && query.terms.length > 1) {
    const partial = collectRows(query, Math.ceil(query.terms.length / 2));
    if (partial.counts.all) {
      result = partial;
      relaxed = true;
    }
  }
  result.rows.sort(SORTERS[state.sort] || SORTERS.relevance);
  const corrections = query.terms.filter((term) => term.fuzzyTokens.length).map((term) => [term.raw, term.fuzzyTokens.slice(0, 3)]);
  return { ...result, records: result.rows.map((row) => row.record), query, relaxed, corrections };
}

function buildHighlighter(query) {
  const words = query.terms.flatMap((term) => [...term.alts, ...term.fuzzyTokens]);
  const usable = unique(words).filter((word) => word.length > 1).sort((a, b) => b.length - a.length);
  const source = usable.map((word) => {
    if (word.length > 2 || CJK_PATTERN.test(word)) return escapeRegExp(word);
    return isAbbreviation(word) ? `\\b${escapeRegExp(word)}\\b` : `\\b${escapeRegExp(word)}`;
  });
  return source.length ? new RegExp(source.join("|"), "gi") : null;
}

function highlight(value) {
  const source = String(value || "");
  const fragment = document.createDocumentFragment();
  if (!state.highlighter) {
    fragment.append(source);
    return fragment;
  }
  let last = 0;
  for (const match of source.matchAll(state.highlighter)) {
    fragment.append(source.slice(last, match.index), make("mark", "", match[0]));
    last = match.index + match[0].length;
  }
  fragment.append(source.slice(last));
  return fragment;
}

/* ---------- URL state ---------- */

function readUrl() {
  const params = new URL(window.location.href).searchParams;
  for (const [key, param] of Object.entries(URL_KEYS)) {
    if (!params.has(param)) continue;
    const value = params.get(param);
    state[key] = typeof DEFAULT_FILTERS[key] === "boolean" ? value === "1" : value;
  }
  if (!["all", ...TYPE_KEYS].includes(state.type)) state.type = "all";
  if (!SORTERS[state.sort]) state.sort = "relevance";
  if (state.evidence !== "all" && !EVIDENCE_LABELS[state.evidence]) state.evidence = "all";
  if (params.has("id")) {
    state.activeId = params.get("id");
    state.userSelected = true;
  }
}

function writeUrl() {
  const params = new URLSearchParams();
  for (const [key, param] of Object.entries(URL_KEYS)) {
    const value = state[key];
    if (value === DEFAULT_FILTERS[key] || value === "") continue;
    params.set(param, typeof value === "boolean" ? "1" : value);
  }
  if (state.userSelected && state.activeId) params.set("id", state.activeId);
  const query = params.toString();
  const next = `${window.location.pathname}${query ? `?${query}` : ""}`;
  if (next !== `${window.location.pathname}${window.location.search}`) {
    window.history.replaceState(null, "", next);
  }
}

/* ---------- Facets & controls ---------- */

function countMap(values) {
  const counts = new Map();
  for (const value of values) if (isKnown(value)) increment(counts, value);
  return counts;
}

function option(label, value, count) {
  return new Option(count === undefined ? label : `${label} (${formatNumber(count)})`, value);
}

function optionGroup(label, options) {
  const group = document.createElement("optgroup");
  group.label = label;
  group.append(...options);
  return group;
}

// Each pair of selects is broad -> detailed: the detailed list follows the broad choice,
// and picking a detailed entry also sets its broad group.
function renderFacets() {
  const counts = state.facetCounts;
  const divisionIds = [...TAXONOMY.divisions.keys()].filter((id) => counts.divisions.get(id));
  els.division.replaceChildren(
    option("All schools & divisions", "all"),
    ...divisionIds.map((id) => option(divisionLabel(id), id, counts.divisions.get(id))),
  );
  const divisions = state.division === "all" ? divisionIds : [state.division];
  const departmentGroups = divisions.map((division) => {
    const names = [...counts.departments.keys()]
      .filter((name) => state.departmentDivision.get(name) === division)
      .sort((a, b) => a.localeCompare(b));
    return [division, names.map((name) => option(name, name, counts.departments.get(name)))];
  }).filter(([, options]) => options.length);
  els.department.replaceChildren(
    option(state.division === "all" ? "All departments" : `All of ${divisionLabel(state.division)}`, "all"),
    ...(state.division === "all" ? departmentGroups.map(([division, options]) => optionGroup(divisionLabel(division), options)) : departmentGroups.flatMap(([, options]) => options)),
  );

  els.field.replaceChildren(
    option("All research fields", "all"),
    ...RESEARCH_FIELDS.filter((field) => counts.fields.get(field.id)).map((field) => option(field.label, field.id, counts.fields.get(field.id))),
  );
  const fields = RESEARCH_FIELDS.filter((field) => state.field === "all" || field.id === state.field);
  const areaGroups = fields.map((field) => [field, field.subfields
    .filter((sub) => counts.areas.get(sub.id))
    .map((sub) => option(sub.label, sub.id, counts.areas.get(sub.id)))]).filter(([, options]) => options.length);
  els.area.replaceChildren(
    option(state.field === "all" ? "All specific areas" : `Any area in ${fieldLabel(state.field)}`, "all"),
    ...(state.field === "all" ? areaGroups.map(([field, options]) => optionGroup(field.label, options)) : areaGroups.flatMap(([, options]) => options)),
  );
}

function computeFacetCounts() {
  state.facetCounts = {
    divisions: countMap(state.records.flatMap((record) => record.divisions)),
    departments: countMap(state.records.flatMap((record) => record.departments)),
    fields: countMap(state.records.flatMap((record) => record.fieldIds)),
    areas: countMap(state.records.flatMap((record) => record.subfieldIds)),
  };
}

// Shared links from before the taxonomy used raw names ("dept=Department of Physics",
// "area=Machine learning"); map them onto the current entries instead of dropping them.
function normalizeTaxonomyState() {
  const counts = state.facetCounts;
  if (state.department !== "all" && !counts.departments.has(state.department)) {
    const resolved = resolveDepartment(state.department);
    state.department = resolved && counts.departments.has(resolved.name) ? resolved.name : "all";
  }
  if (state.department !== "all") state.division = state.departmentDivision.get(state.department) || state.division;
  if (state.division !== "all" && !counts.divisions.has(state.division)) state.division = "all";
  if (state.area !== "all" && !TAXONOMY.subfields.has(state.area)) {
    const [match] = subfieldsForText(state.area);
    if (!match && !state.query) state.query = state.area;
    state.area = match || "all";
  }
  if (state.area !== "all") state.field = TAXONOMY.subfields.get(state.area).field;
  if (state.field !== "all" && !TAXONOMY.fields.has(state.field)) state.field = "all";
}

function setDivision(value) {
  state.division = value;
  if (value !== "all" && state.department !== "all" && state.departmentDivision.get(state.department) !== value) state.department = "all";
}

function setDepartment(value) {
  state.department = value;
  if (value !== "all") state.division = state.departmentDivision.get(value) || state.division;
}

function setField(value) {
  state.field = value;
  if (value !== "all" && state.area !== "all" && TAXONOMY.subfields.get(state.area)?.field !== value) state.area = "all";
}

function setArea(value) {
  state.area = value;
  if (value !== "all") state.field = TAXONOMY.subfields.get(value)?.field || state.field;
}

function syncStateFromControls(changed = null) {
  state.query = els.query.value.trim();
  if (changed === els.division) setDivision(els.division.value);
  if (changed === els.department) setDepartment(els.department.value);
  if (changed === els.field) setField(els.field.value);
  if (changed === els.area) setArea(els.area.value);
  state.evidence = els.evidence.value;
  state.verifiedOnly = els.verifiedOnly.checked;
  state.recruiting = els.recruiting.value;
  state.sort = els.sort.value;
}

function syncControls() {
  if (els.query.value.trim() !== state.query) els.query.value = state.query;
  if (state.facetCounts) renderFacets();
  els.division.value = state.division;
  els.department.value = state.department;
  els.field.value = state.field;
  els.area.value = state.area;
  els.evidence.value = state.evidence;
  els.verifiedOnly.checked = state.verifiedOnly;
  els.recruiting.value = state.recruiting;
  els.sort.value = state.sort;
  for (const select of [els.division, els.department, els.field, els.area, els.evidence, els.recruiting]) {
    select.classList.toggle("is-set", select.value !== "all");
  }
  els.savedToggle.setAttribute("aria-pressed", String(state.savedOnly));
  els.quickButtons.forEach((button) => {
    const key = button.dataset.quick;
    const active = key === "checked" ? state.verifiedOnly : state.evidence === key;
    button.setAttribute("aria-pressed", String(active));
  });
}

function activeFilterEntries() {
  const entries = [];
  if (state.savedOnly) entries.push(["savedOnly", "Saved", "only"]);
  if (state.field !== "all" && state.area === "all") entries.push(["field", "Field", fieldLabel(state.field)]);
  if (state.area !== "all") entries.push(["area", "Area", subfieldLabel(state.area)]);
  if (state.division !== "all" && state.department === "all") entries.push(["division", "School", divisionLabel(state.division)]);
  if (state.department !== "all") entries.push(["department", "Dept", state.department]);
  if (state.evidence !== "all") entries.push(["evidence", "Evidence", EVIDENCE_LABELS[state.evidence]]);
  if (state.verifiedOnly) entries.push(["verifiedOnly", "Data", "source checked"]);
  if (state.recruiting !== "all") entries.push(["recruiting", "Status", state.recruiting]);
  return entries;
}

function renderActiveFilters() {
  const entries = activeFilterEntries();
  els.activeFilters.hidden = entries.length === 0;
  const chips = entries.map(([key, label, value]) => {
    const chip = make("button", "chip");
    chip.type = "button";
    chip.dataset.filterKey = key;
    chip.setAttribute("aria-label", `Remove filter ${label}: ${value}`);
    chip.append(make("small", "", label), value);
    return chip;
  });
  if (entries.length > 1) {
    const clearAll = make("button", "text-button chip-clear", "Clear all");
    clearAll.type = "button";
    clearAll.dataset.filterKey = "*";
    chips.push(clearAll);
  }
  els.activeFilters.replaceChildren(...chips);
  const railFilters = entries.filter(([key]) => key !== "savedOnly").length;
  els.filterCount.hidden = railFilters === 0;
  els.filterCount.textContent = railFilters;
}

function resetFilters({ keepQuery = false } = {}) {
  const query = state.query;
  Object.assign(state, DEFAULT_FILTERS);
  if (keepQuery) state.query = query;
  syncControls();
  update({ scroll: true });
}

// Removing a detailed chip steps back to its broad group; removing a broad chip clears both.
function clearFilter(key) {
  if (key === "*") {
    resetFilters({ keepQuery: true });
    return;
  }
  state[key] = DEFAULT_FILTERS[key];
  if (key === "field") state.area = "all";
  if (key === "division") state.department = "all";
  syncControls();
  update({ scroll: true });
}

/* ---------- Browse by field ---------- */

function stripButton(label, count, data, pressed = false) {
  const button = make("button", "", label);
  button.type = "button";
  Object.assign(button.dataset, data);
  button.setAttribute("aria-pressed", String(pressed));
  if (count !== null) button.append(make("span", "", formatNumber(count)));
  return button;
}

// Field counts follow the current query and filters, so after typing "imaging" the strip shows
// which fields those results fall into; a broad field then opens its detailed areas.
function renderFieldStrip(fieldCounts, areaCounts) {
  const items = [];
  if (state.field === "all") {
    const fields = RESEARCH_FIELDS.filter((field) => fieldCounts.get(field.id));
    if (state.query) fields.sort((a, b) => fieldCounts.get(b.id) - fieldCounts.get(a.id));
    items.push(...fields.map((field) => stripButton(field.label, fieldCounts.get(field.id), { stripField: field.id })));
  } else {
    const field = TAXONOMY.fields.get(state.field);
    items.push(stripButton("All fields", null, { stripField: "all" }));
    items[0].classList.add("strip-back");
    items.push(stripButton(field.label, fieldCounts.get(field.id) || 0, { stripField: field.id }, state.area === "all"));
    const subs = field.subfields.filter((sub) => areaCounts.get(sub.id) || sub.id === state.area);
    items.push(...subs.map((sub) => stripButton(sub.label, areaCounts.get(sub.id) || 0, { stripArea: sub.id }, sub.id === state.area)));
  }
  els.fieldStrip.hidden = items.length === 0;
  els.fieldStrip.replaceChildren(...(items.length ? [make("span", "strip-label", state.field === "all" ? "Fields" : "Areas"), ...items] : []));
}

function applyQuickFilter(key) {
  if (key === "checked") state.verifiedOnly = !state.verifiedOnly;
  else state.evidence = state.evidence === key ? "all" : key;
  syncControls();
  update({ scroll: true });
}

/* ---------- Result rows ---------- */

const BOOKMARK_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h11v17L12 16.2l-5.5 4.3z"/></svg>';

function rowMetric(label, value, known = true) {
  const cell = make("div", `row-metric${known ? "" : " is-empty"}`);
  cell.append(make("dt", "", label), make("dd", "", known ? value : "—"));
  return cell;
}

function rowMetrics(record) {
  const list = make("dl", "row-metrics");
  const { facts } = record;
  if (record.recordType === "professor") {
    if (facts.metrics.verified) list.append(rowMetric("Citations", formatNumber(facts.metrics.citationCount)));
    list.append(rowMetric("Courses", formatNumber(facts.courses), facts.courses > 0));
    if (facts.rating) {
      const [key, rating] = facts.rating;
      list.append(rowMetric(`${RATING_SHORT[key] || rating.platform} · ${formatNumber(rating.reviewCount)}`, `${rating.score}`));
    } else {
      list.append(rowMetric("Rating", "", false));
    }
  } else if (record.recordType === "lab") {
    list.append(rowMetric("Sources", formatNumber(record.sourceUrls.length)));
  } else if (isKnown(record.yearOfActivity)) {
    list.append(rowMetric("Year", String(record.yearOfActivity)));
  }
  return list;
}

function rowTags(record) {
  const departments = new Set(record.departments.map(normalize));
  const tags = record.researchAreas.filter((area) => !departments.has(normalize(area)));
  // Profile keywords fill in for records whose prose matched no controlled area.
  if (tags.length < 3) tags.push(...(record.researchKeywords || []).slice(0, 4 - tags.length));
  if (!tags.length && record.recordType !== "resource") tags.push(...record.subfieldIds.slice(0, 2).map(subfieldLabel));
  if (record.recordType === "lab" && isKnown(record.principalInvestigator)) {
    tags.unshift(`${unverifiedOwnershipPi(record) ? "Earlier PI label (unverified):" : "PI"} ${record.principalInvestigator}`);
  }
  if (record.recordType === "professor" && record.facts.courses) {
    tags.unshift(...unique(coursesFor(record).map((course) => course.courseCode)).slice(0, 3));
  }
  if (!tags.length) return null;
  const row = make("p", "row-tags");
  row.append(...tags.slice(0, 6).map((tag) => make("span", "", highlight(tag))));
  return row;
}

function makeSaveToggle(record) {
  const saved = state.saved.has(record.id);
  const button = make("button", "save-toggle");
  button.type = "button";
  button.dataset.saveId = record.id;
  button.innerHTML = BOOKMARK_SVG;
  button.setAttribute("aria-pressed", String(saved));
  button.setAttribute("aria-label", `${saved ? "Remove" : "Save"} ${record.displayName}`);
  button.title = saved ? "Saved (S)" : "Save (S)";
  return button;
}

function renderRow(record, position, animateIndex) {
  const row = make("li", "row");
  row.dataset.id = record.id;
  if (record.id === state.activeId) row.classList.add("is-selected");
  if (animateIndex !== null && !prefersReducedMotion()) {
    row.classList.add("is-entering");
    row.style.setProperty("--i", animateIndex);
    row.addEventListener("animationend", () => row.classList.remove("is-entering"), { once: true });
  }

  const meta = make("p", "row-meta");
  meta.append(make("span", "row-kind", record.displayKind));
  const departmentLine = record.recordType === "resource"
    ? [record.resourceType, record.organization].filter(isKnown).join(" · ")
    : record.departments.join(" · ");
  if (departmentLine) meta.append(make("span", "row-dept", departmentLine));
  if (record.recruitingStatus === "Recruiting") meta.append(make("span", "row-flag", "Recruiting"));
  if (record.facts.needsReview) meta.append(make("span", "row-flag is-warn", "Needs review"));

  const title = make("button", "row-title", highlight(record.displayName));
  title.type = "button";
  title.dataset.openId = record.id;

  const main = make("div", "row-main");
  main.append(meta, title);
  if (record.summary) main.append(make("p", "row-summary", highlight(record.summary)));
  const tags = rowTags(record);
  if (tags) main.append(tags);

  const side = make("div", "row-side");
  side.append(rowMetrics(record), makeSaveToggle(record));

  row.append(make("span", "row-index", String(position + 1).padStart(3, "0")), main, side);
  return row;
}

function appendRows(from, to, animate) {
  const fragment = document.createDocumentFragment();
  state.results.slice(from, to).forEach((record, offset) => {
    fragment.append(renderRow(record, from + offset, animate && offset < 14 ? offset : null));
  });
  els.results.append(fragment);
}

function renderCounts(counts) {
  els.typeCounts.forEach((node) => {
    node.textContent = formatNumber(counts[node.dataset.count] || 0);
  });
  els.typeButtons.forEach((button) => {
    const type = button.dataset.typeChoice;
    button.setAttribute("aria-pressed", String(type === state.type));
    button.classList.toggle("is-empty", !counts[type]);
  });
}

function renderHeading(total) {
  els.resultHeading.textContent = `${formatNumber(total)} ${total === 1 ? "record" : "records"}`;
  if (state.query) els.coverageLine.textContent = `matching “${state.query}”`;
  else if (state.savedOnly) els.coverageLine.textContent = "in your saved list";
  else els.coverageLine.textContent = "across UC San Diego";
}

// Says plainly when results rely on spelling correction or on only some of the words.
function renderSearchNote({ relaxed, corrections, query }) {
  const parts = [];
  if (corrections.length) {
    parts.push(`Including similar spellings: ${corrections.map(([raw, tokens]) => `${raw} → ${tokens.join(", ")}`).join("; ")}.`);
  }
  if (relaxed) {
    parts.push(`No record contains all ${query.terms.length} words, so these match most of them.`);
  }
  els.searchNote.hidden = parts.length === 0;
  els.searchNote.textContent = parts.join(" ");
}

function renderEmpty(total) {
  els.empty.hidden = total !== 0;
  if (total !== 0) return;
  const filters = activeFilterEntries().length + (state.type !== "all" ? 1 : 0);
  if (state.savedOnly && !state.saved.size) {
    els.emptyHint.textContent = "You haven’t saved anything yet. Use the bookmark on any record, or press S.";
  } else if (state.query && filters) {
    els.emptyHint.textContent = `No records match “${state.query}” with ${filters} filter${filters > 1 ? "s" : ""} applied. Try removing a filter.`;
  } else if (state.query) {
    els.emptyHint.textContent = `No records contain “${state.query}”. Try a shorter or broader term, or browse a research field — course codes work with or without the space.`;
  } else {
    els.emptyHint.textContent = "The current filters exclude every record. Remove one to widen the search.";
  }
}

function renderLoadMore() {
  const remaining = state.results.length - Math.min(state.visibleLimit, state.results.length);
  els.loadMore.hidden = remaining <= 0;
  els.loadMore.textContent = `Show ${formatNumber(Math.min(remaining, PAGE_SIZE))} more — ${formatNumber(remaining)} remaining`;
}

function render() {
  const result = computeResults();
  const { records, counts } = result;
  state.results = records;
  state.resultsQuery = state.query;
  state.highlighter = buildHighlighter(result.query);

  renderHeading(records.length);
  renderSearchNote(result);
  renderCounts(counts);
  renderFieldStrip(result.fieldCounts, result.areaCounts);
  renderActiveFilters();
  renderEmpty(records.length);

  els.results.replaceChildren();
  els.results.setAttribute("aria-busy", "false");
  appendRows(0, Math.min(state.visibleLimit, records.length), true);
  renderLoadMore();

  const activeVisible = records.some((record) => record.id === state.activeId);
  if (!activeVisible && !state.userSelected && DESKTOP_DETAIL_QUERY.matches && records.length) {
    showDetail(records[0].id);
  } else {
    highlightSelectedRow();
  }
  renderSaved();
  if (document.activeElement === els.query) renderSuggestions();
  writeUrl();
}

function loadMore() {
  const from = Math.min(state.visibleLimit, state.results.length);
  state.visibleLimit += PAGE_SIZE;
  appendRows(from, Math.min(state.visibleLimit, state.results.length), true);
  renderLoadMore();
}

function scrollToResults() {
  const top = els.workspace.getBoundingClientRect().top + window.scrollY - els.form.offsetHeight;
  if (window.scrollY > top + 4) {
    window.scrollTo({ top, behavior: prefersReducedMotion() ? "auto" : "smooth" });
  }
}

function update({ scroll = false } = {}) {
  state.visibleLimit = PAGE_SIZE;
  render();
  if (scroll) scrollToResults();
}

/* ---------- Saved ---------- */

function toggleSaved(id) {
  if (!id) return;
  const record = state.byId.get(id);
  if (state.saved.has(id)) state.saved.delete(id);
  else state.saved.add(id);
  writeStoredList(SAVED_KEY, [...state.saved]);
  const saved = state.saved.has(id);
  document.querySelectorAll(`[data-save-id="${CSS.escape(id)}"]`).forEach((button) => {
    button.setAttribute("aria-pressed", String(saved));
    if (button.classList.contains("save-toggle")) {
      button.setAttribute("aria-label", `${saved ? "Remove" : "Save"} ${record?.displayName || "record"}`);
      button.title = saved ? "Saved (S)" : "Save (S)";
    } else {
      button.textContent = saved ? "Saved" : "Save";
    }
  });
  showToast(saved ? `Saved ${record?.displayName || ""}` : "Removed from saved");
  if (state.savedOnly) update();
  else renderSaved();
}

function renderSaved() {
  const saved = [...state.saved].map((id) => state.byId.get(id)).filter(Boolean);
  els.savedCount.textContent = saved.length;
  els.savedCountTop.textContent = saved.length;
  if (!saved.length) {
    els.savedList.replaceChildren(make("p", "saved-empty", "Bookmark records to keep a shortlist here."));
    return;
  }
  els.savedList.replaceChildren(
    ...saved.slice(0, 8).map((record) => {
      const item = make("button", "saved-item");
      item.type = "button";
      item.dataset.openId = record.id;
      item.append(make("strong", "", record.displayName), make("span", "", record.displayKind));
      return item;
    }),
  );
  if (saved.length > 8) {
    const more = make("button", "text-button", `View all ${saved.length} saved`);
    more.type = "button";
    more.addEventListener("click", () => {
      state.savedOnly = true;
      syncControls();
      closeRail();
      update({ scroll: true });
    });
    els.savedList.append(more);
  }
}

/* ---------- Detail ---------- */

function highlightSelectedRow() {
  els.results.querySelectorAll(".row").forEach((row) => {
    row.classList.toggle("is-selected", row.dataset.id === state.activeId);
  });
}

function showDetail(id) {
  const record = state.byId.get(id);
  if (!record) return false;
  state.activeId = record.id;
  const view = renderDetail(record);
  if (!prefersReducedMotion()) {
    view.classList.add("is-entering");
    view.addEventListener("animationend", () => view.classList.remove("is-entering"), { once: true });
  }
  els.detailContent.replaceChildren(view);
  els.detailPanel.scrollTop = 0;
  highlightSelectedRow();
  return true;
}

// Explicit selection: records the choice in the URL and, on narrow screens, opens the sheet.
function openDetail(id, { reveal = true } = {}) {
  if (!showDetail(id)) return;
  state.userSelected = true;
  writeUrl();
  if (reveal && !DESKTOP_DETAIL_QUERY.matches) openSheet();
}

function detailSection(title, ...children) {
  const section = make("section", "detail-section");
  section.append(make("h3", "", title), ...children.filter(Boolean));
  return section;
}

function note(text) {
  return make("p", "note", text);
}

function fieldGrid(fields) {
  const grid = make("dl", "field-grid");
  for (const [label, value, url] of fields) {
    const known = Array.isArray(value) ? value.length > 0 : isKnown(value);
    const display = Array.isArray(value) ? value.join(", ") : String(value);
    const cell = make("div");
    const dd = make("dd", known ? "" : "is-empty");
    if (known && isKnown(url)) dd.append(makeExternal(display, url, "inline-link"));
    else dd.textContent = known ? display : "—";
    cell.append(make("dt", "", label), dd);
    grid.append(cell);
  }
  return grid;
}

function evidenceItem(title, meta, excerpt, links) {
  const item = make("li");
  item.append(make("strong", "", title));
  if (meta) item.append(make("span", "evidence-meta", meta));
  if (excerpt) item.append(make("p", "evidence-quote", excerpt));
  const actions = links.filter(([, url]) => validExternalUrl(url));
  if (actions.length) {
    const row = make("p", "evidence-links");
    row.append(...actions.map(([label, url]) => makeExternal(label, url)));
    item.append(row);
  }
  return item;
}

function validExternalUrl(value) {
  if (typeof value !== "string" || /\s/.test(value)) return false;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password;
  } catch {
    return false;
  }
}

function detailHead(record) {
  const head = make("header", "detail-head");
  const kind = make("p", "detail-kind");
  kind.append(make("span", "", record.displayKind));
  if (record.recruitingStatus === "Recruiting") kind.append(make("span", "is-recruiting", "Recruiting"));
  else if (record.recruitingStatus === "Not recruiting") kind.append(make("span", "is-muted", "Not recruiting"));
  kind.append(make("span", record.facts.needsReview ? "is-warn" : "is-muted", verificationLabel(record)));

  const affiliation = [record.departments.join(" / "), record.institution].filter(isKnown).join(" — ");
  head.append(kind, make("h2", "detail-title", record.displayName), make("p", "detail-affiliation", affiliation || NOT_FOUND));

  const quick = make("div", "detail-quick");
  const save = make("button", "line-button", state.saved.has(record.id) ? "Saved" : "Save");
  save.type = "button";
  save.dataset.saveId = record.id;
  save.setAttribute("aria-pressed", String(state.saved.has(record.id)));
  quick.append(save);
  if (record.email) {
    const mail = make("a", "line-button", "Email");
    mail.href = `mailto:${record.email}`;
    const copy = make("button", "line-button", "Copy email");
    copy.type = "button";
    copy.dataset.copy = record.email;
    copy.dataset.copyLabel = `Copied ${record.email}`;
    quick.append(mail, copy);
  }
  const share = make("button", "line-button", "Copy link");
  share.type = "button";
  share.dataset.copyRecordLink = record.id;
  quick.append(share);
  head.append(quick);
  return head;
}

function detailLinks(record) {
  if (!record.links.length) return null;
  const list = make("ul", "link-list");
  for (const [label, url] of record.links) {
    const item = make("li");
    item.append(makeExternal(label, url));
    list.append(item);
  }
  const section = detailSection("Links", list);
  const review = record.profileLinkIdentityReview;
  if (record.recordType === "professor" && profileLinkNeedsReview(record)) {
    const [destination, separate] = review.captures;
    const issue = make("div", "profile-link-review");
    const observations = make("ul", "evidence-list");
    issue.append(make("p", "rating-warn", `Profile link needs review: the stored link opens a page headed ${destination.nameAsDisplayed}. Its relationship to ${record.displayName} is unresolved.`));
    observations.append(evidenceItem(
      `Captured destination: ${destination.nameAsDisplayed}`, `Observed ${dateLabel(destination.observedAt)}`,
      "This is the captured destination of the stored profile link.", [["Destination source", destination.sourceUrl]],
    ));
    observations.append(evidenceItem(
      `Separate named page: ${separate.nameAsDisplayed} · identity unresolved`, `Observed ${dateLabel(separate.observedAt)}`,
      "A matching display name on a separately captured page does not establish its relationship to this record.",
      [["Separate page for review", separate.sourceUrl]],
    ));
    issue.append(observations);
    section.append(issue);
  }
  return section;
}

function detailOverview(record) {
  const body = record.summary ? make("p", "", record.summary) : note("No public summary was captured for this record.");
  let tags = null;
  if (record.fieldIds.length) {
    tags = make("div", "tag-list");
    const covered = new Set(record.subfieldIds.map((id) => TAXONOMY.subfields.get(id).field));
    for (const id of record.subfieldIds) {
      const tag = make("button", "", subfieldLabel(id));
      tag.type = "button";
      tag.dataset.areaFilter = id;
      tag.title = `Show all records in ${subfieldLabel(id)}`;
      tags.append(tag);
    }
    for (const id of record.fieldIds.filter((field) => !covered.has(field))) {
      const tag = make("button", "", fieldLabel(id));
      tag.type = "button";
      tag.dataset.fieldFilter = id;
      tag.title = `Show all records in ${fieldLabel(id)}`;
      tags.append(tag);
    }
  }
  let keywords = null;
  const terms = uniqueByNormalized([...record.researchAreas, ...(record.researchKeywords || [])]);
  if (terms.length && record.recordType !== "resource") {
    keywords = make("div", "keyword-list");
    keywords.append(make("span", "keyword-label", "Research areas & keywords"));
    for (const keyword of terms.slice(0, 20)) {
      const button = make("button", "", keyword);
      button.type = "button";
      button.dataset.searchKeyword = keyword;
      button.title = `Search for ${keyword}`;
      keywords.append(button);
    }
  }
  return detailSection("Overview", body, tags, keywords);
}

function teachingDetails(record) {
  const courses = coursesFor(record);
  const candidates = record.teaching?.candidates || [];
  const parts = [];
  if (!courses.length) {
    const status = candidates.length
      ? "candidate assignments need identity verification"
      : record.teaching?.status === "not_found" ? "not found in checked sources" : "not yet checked";
    parts.push(note(`No verified teaching records captured. Status: ${status}.`));
  } else {
    const list = make("ul", "evidence-list");
    [...courses].sort((a, b) => courseTermOrder(b) - courseTermOrder(a)).forEach((course) => {
      const status = { historical: "Teaching history", current: "Current term", planned: "Planned", tentative: "Tentative", scheduled: "Scheduled", unknown: "Term not classified" }[course.status] || course.status || "Term not classified";
      list.append(evidenceItem(
        [course.courseCode, course.title].filter(isKnown).join(" · "),
        `${course.term || "Term not specified"} · ${course.isTentative ? `${status} (tentative)` : status} · observed ${dateLabel(course.observedAt)}`,
        "",
        [["Official course source", course.sourceUrl], ["Published schedule", course.dataUrl !== course.sourceUrl ? course.dataUrl : null]],
      ));
    });
    parts.push(list, note("Official teaching records. Historical assignments do not promise a future offering; planned assignments may change."));
  }
  if (candidates.length) {
    const details = make("details", "candidate-details");
    details.append(make("summary", "", `Unverified teaching leads (${candidates.length})`));
    details.append(note("These assignments need an identity check. A surname-only match does not establish that this professor teaches the course. Leads are excluded from verified course counts and the official teaching filter."));
    const list = make("ul", "evidence-list");
    [...candidates].sort((a, b) => courseTermOrder(b) - courseTermOrder(a)).forEach((course) => {
      const identity = `Listed instructor: ${course.instructorName || "Not captured"} · ${String(course.matchMethod || "").includes("surname") ? "Surname-only match" : "Identity match needs review"}`;
      list.append(evidenceItem(
        [course.courseCode, course.title].filter(isKnown).join(" · "),
        `${course.term || "Term not specified"}${course.isTentative ? " · tentative schedule" : ""} · observed ${dateLabel(course.observedAt)} · ${identity}`,
        course.evidence || "",
        [["Official teaching source", course.sourceUrl], ["Published schedule", course.dataUrl !== course.sourceUrl ? course.dataUrl : null]],
      ));
    });
    details.append(list);
    parts.push(details);
  }
  return detailSection("Courses & teaching", ...parts);
}

function ratingDetails(record) {
  const grid = make("div", "rating-grid");
  const verifiedKeys = record.facts.ratings;
  for (const [key, label, purpose] of RATING_PLATFORMS) {
    const rating = record.ratings?.[key];
    const verified = verifiedKeys.includes(key);
    const panel = make("article", `rating-panel${verified ? "" : " is-empty"}`);
    panel.append(make("h4", "", rating?.platform || label), make("p", "rating-purpose", purpose));
    if (verified) {
      const score = make("p", "rating-score");
      score.append(String(rating.score), make("small", "", ` / ${rating.scale || 5}`));
      panel.append(score, make("p", "rating-count", `${formatNumber(rating.reviewCount)} ${Number(rating.reviewCount) === 1 ? "review" : "reviews"}`));
      if (Number(rating.reviewCount) < 5) panel.append(make("p", "rating-warn", "Small sample: fewer than five reviews."));
      if (key === "rateMyProfessors") {
        const extra = [
          numericMetric(rating.difficulty) ? `Difficulty ${rating.difficulty}/5` : "",
          numericMetric(rating.wouldTakeAgainPercent) ? `${rating.wouldTakeAgainPercent}% would take again` : "",
        ].filter(Boolean).join(" · ");
        if (extra) panel.append(make("p", "rating-extra", extra));
      }
    } else {
      panel.append(make("p", "rating-status", ratingStatusLabel(rating)));
    }
    panel.append(make("p", "evidence-meta", rating?.observedAt
      ? `Retrieved ${dateLabel(rating.observedAt)}${rating.latestReviewAt ? ` · latest review ${dateLabel(rating.latestReviewAt)}` : " · review dates: see source"}`
      : "Not checked for this professor"));
    const fallback = key === "rateMyPI"
      ? ["Browse PI Review UCSD directory", "https://pi-review.com/universities/158"]
      : ["Search Rate My Professors", `https://www.ratemyprofessors.com/search/professors/1079?q=${encodeURIComponent(record.displayName)}`];
    const [linkLabel, linkUrl] = rating?.sourceUrl ? [verified ? "Open rating source" : "Open platform search", rating.sourceUrl] : fallback;
    panel.append(makeExternal(linkLabel, linkUrl, "inline-link"));
    grid.append(panel);
  }
  return detailSection(
    "Student ratings",
    grid,
    note("Separate platforms and measures. PI Review (pi-review.com) is the mentoring source used here. Reviews are self-selected opinions; a freshly retrieved score can still be based on old reviews."),
  );
}

function labAffiliationDetails(record) {
  const affiliations = record.labAffiliations || [];
  const unresolved = record.unresolvedLabLinks || [];
  if (!affiliations.length && !unresolved.length) return detailSection("Labs & research groups", note("No lab relationship has been reverified for this professor yet."));
  const relationLabels = {
    faculty_lab_link: "Lab linked from faculty profile",
    faculty_organization_link: "Documented organization association",
    official_directory_same_record: "Listed together in official directory",
    principal_investigator: "Listed as principal investigator",
  };
  const list = make("ul", "evidence-list");
  for (const lab of affiliations) {
    const evidence = Array.isArray(lab.fieldEvidence) ? lab.fieldEvidence[0] || {} : (lab.fieldEvidence || {});
    list.append(evidenceItem(
      lab.labName || "Research group",
      `${relationLabels[lab.relationship] || "Documented lab association"} · observed ${dateLabel(evidence.observedAt)}`,
      evidence.evidence || "",
      [[lab.recordSubtype === "ngo" ? "Organization website" : "Lab website", lab.url], ["Relationship source", evidence.sourceUrl]],
    ));
  }
  for (const lab of unresolved) {
    const evidence = Array.isArray(lab.fieldEvidence) ? lab.fieldEvidence[0] || {} : (lab.fieldEvidence || {});
    list.append(evidenceItem(
      lab.labName || "Lab link awaiting identity review",
      `Shared website; named lab unresolved · observed ${dateLabel(evidence.observedAt)}`,
      evidence.evidence || "",
      [["Shared website", lab.url], ["Relationship source", evidence.sourceUrl]],
    ));
  }
  return detailSection(
    "Labs, groups & organizations",
    list,
    note("An associated lab or organization link alone does not establish a leadership role. The relationship and original wording are shown above."),
  );
}

function academicDetails(record) {
  const { verified, hasMetrics, status, profile } = record.facts.metrics;
  if (!verified) {
    return detailSection("Academic metrics", note(hasMetrics
      ? `${status}. Citation numbers are hidden because the publication match needs review.`
      : "Citation metrics are not verified in the local metadata yet."));
  }
  const grid = make("dl", "metric-grid");
  for (const [label, value] of [["Citations", profile.citationCount], ["Works", profile.worksCount], ["h-index", profile.hIndex], ["i10-index", profile.i10Index]]) {
    const cell = make("div", numericMetric(value) ? "" : "is-empty");
    cell.append(make("dt", "", label), make("dd", "", numericMetric(value) ? formatNumber(value) : "—"));
    grid.append(cell);
  }
  const list = make("ol", "publication-list");
  const publications = relevantPublications(record).slice(0, 5);
  if (!publications.length) list.append(make("li", "is-placeholder", "No relevant recent publications in the local metadata."));
  for (const paper of publications) {
    const item = make("li");
    item.append(
      isKnown(paper.url) ? makeExternal(cleanText(paper.title), paper.url, "paper-title") : make("span", "paper-title", cleanText(paper.title)),
      make("span", "", [paper.publicationDate || paper.year, paper.venue].filter(isKnown).join(" · ") || "Venue not listed"),
      make("small", "", numericMetric(paper.citationCount) ? `${formatNumber(paper.citationCount)} citations` : ""),
    );
    list.append(item);
  }
  return detailSection("Academic metrics", grid, note(status), make("h4", "sub-heading", "Recent publications"), list);
}

function facultyDirectoryDetails(record) {
  const fields = [
    ["Directory status", facultyLabel(record)],
    ["Department affiliations", record.departments],
  ];
  if (record.aliasNames?.length) fields.push(["Also listed as", record.aliasNames]);
  if (record.directorySection) fields.push(["Directory section", record.directorySection]);
  const parts = [fieldGrid(fields)];
  const listings = Array.isArray(record.directoryListings) ? record.directoryListings : [];
  if (listings.length) {
    const list = make("ul", "evidence-list");
    const qualifications = new Set();
    for (const entry of listings) {
      const excerpt = typeof entry.evidence === "string" ? entry.evidence : entry.evidence?.evidence || "";
      list.append(evidenceItem(
        [entry.department, entry.listedRole].filter(isKnown).join(" · ") || "Official directory listing",
        `Observed ${dateLabel(entry.observedAt)}`,
        excerpt,
        [["Directory source", entry.sourceUrl]],
      ));
      const qualification = entry.academicQualification;
      const proof = qualification?.evidence;
      const key = JSON.stringify([proof?.sourceUrl, proof?.observedAt, qualification?.roleAsListed]);
      if (isKnown(qualification?.roleAsListed) && isKnown(proof?.sourceUrl) && proof?.observedAt && !qualifications.has(key)) {
        qualifications.add(key);
        const item = evidenceItem(
          `Profile academic title · ${qualification.roleAsListed}`,
          `Observed ${dateLabel(proof.observedAt)}`,
          proof.evidence || "",
          [["Profile source", proof.sourceUrl]],
        );
        item.classList.add("academic-qualification");
        list.append(item);
      }
    }
    parts.push(list);
  }
  const normalization = record.departmentLabelNormalization;
  if (normalization?.captureVerified) {
    const unitList = make("ul", "evidence-list unit-label-normalization");
    unitList.append(evidenceItem(
      `Published unit: ${normalization.sourceUnitAsPublished}`,
      `Appointment observed ${dateLabel(normalization.ownAppointmentObservedAt)} · Unit page observed ${dateLabel(normalization.unitObservedAt)}`,
      `Normalized to ${normalization.canonicalDepartment} using the registered official unit page (${normalization.unitNameAsPublished}). This category may be a school, institute or umbrella unit.`,
      [["Own appointment source", normalization.ownAppointmentSourceUrl], ["Official unit page", normalization.unitSourceUrl]],
    ));
    parts.push(unitList);
  }
  parts.push(note("These roles describe how official directories list this person. A directory listing alone does not confirm current employment."));
  return detailSection("Faculty roles & affiliations", ...parts);
}

function detailFields(record) {
  if (record.recordType === "professor") {
    return detailSection("Contact", fieldGrid([
      ["Email", record.email],
      [primaryAffiliationLabel(record), record.labAffiliation, record.labAffiliationUrl],
      ["Legacy verification date", record.lastVerified],
    ]));
  }
  if (record.recordType === "lab") {
    const fields = fieldGrid([
      [unverifiedOwnershipPi(record) ? "Earlier PI label (unverified)" : "Principal investigator", record.principalInvestigator, record.principalInvestigatorProfileUrl],
      ["Associated professors", record.relatedProfessorNames || []],
      ["Contact", record.email],
      ...(record.additionalContactEmails?.length ? [["Other published contacts", record.additionalContactEmails]] : []),
      ["Type", record.displayKind],
      ...(record.websiteSharing?.kind === "distinct_named_labs" ? [["Website", "Shared by separately named labs"]] : []),
      ["Legacy verification date", record.lastVerified],
    ]);
    const parts = [fields];
    const connections = programConnections(record);
    if (connections.length) {
      const list = make("ul", "evidence-list");
      for (const entry of connections) {
        list.append(evidenceItem(entry.programName,
          `Program directory lists ${entry.facultyNameAsListed} as ${entry.facultyRoleAsListed}. Rotation guidance observed ${dateLabel(entry.studentAccessStatement?.observedAt)}.`,
          entry.studentAccessStatement?.text || "",
          [["UCSD program source", entry.programSourceUrl], ["Lab rotation guidance", entry.studentAccessStatement?.url]]));
      }
      parts.push(make("h4", "sub-heading", "UCSD graduate program connections"), list);
    }
    const resources = (record.campusResearchRelationships || []).filter((entry) =>
      entry.captureVerified === true && entry.relationship === "named_directory_resource_link");
    if (resources.length) {
      const list = make("ul", "evidence-list");
      for (const entry of resources) {
        list.append(evidenceItem(entry.directoryNameAsPublished,
          `The directory card for ${entry.listedNameAsPublished} links this group as “${entry.linkLabelAsPublished}”. Observed ${dateLabel(entry.observedAt)}.`,
          "The directory link establishes a research resource connection. The group’s institution, department and PI remain unverified.",
          [["UCSD directory source", entry.directorySourceUrl]]));
      }
      parts.push(make("h4", "sub-heading", "UCSD research resource listing"), list);
    }
    return detailSection(record.recordSubtype === "ngo" ? "Organization details" : "Lab details", ...parts);
  }
  const fields = [
    ["Organization", record.organization],
    ["Type", record.resourceType],
    ["Year", record.yearOfActivity],
    ["Contact", record.email],
    ["How to apply", record.applicationProcedure],
  ];
  for (const [label, value] of Object.entries(record.detailFields || {})) {
    if (!fields.some(([existing]) => existing === label)) fields.push([label, value]);
  }
  return detailSection("REAL Portal details", fieldGrid(fields));
}

function detailRecruitment(record) {
  const evidence = record.recruitingEvidence || {};
  const status = record.recruitingStatus || UNKNOWN;
  const body = isKnown(evidence.text)
    ? make("p", "", `${status}: “${cleanText(evidence.text)}”`)
    : make("p", "", status === UNKNOWN
      ? "No explicit public recruiting statement was captured. That doesn’t mean the group is closed — a short, specific email is usually the best way to ask."
      : status);
  const link = isKnown(evidence.url) ? makeExternal("View evidence source", evidence.url, "inline-link") : null;
  return detailSection("Recruiting", body, link);
}

function verificationDetails(record) {
  const parts = [note(`${verificationLabel(record)}. Last source attempt: ${dateLabel(record.verification?.lastAttemptedAt)}. Each item applies only to the named field.`)];
  const issues = record.verification?.issues || [];
  if (issues.length) {
    parts.push(make("p", "rating-warn", issues.map((issue) => typeof issue === "string" ? issue : (issue.message || issue.reason || issue.code || "Review needed")).join(" · ")));
  }
  const list = make("ul", "evidence-list");
  for (const [key, items] of evidenceFields(record)) {
    for (const evidence of items) {
      if (!evidence.sourceUrl || !evidence.observedAt) continue;
      list.append(evidenceItem(
        slugLabel(key.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/\./g, " ")),
        dateLabel(evidence.observedAt),
        evidence.evidence || evidence.text || "",
        [["Field source", evidence.sourceUrl]],
      ));
    }
  }
  if (list.children.length) {
    const details = make("details", "candidate-details");
    details.append(make("summary", "", `Field evidence (${list.children.length})`), list);
    parts.push(details);
  } else {
    parts.push(note("No field-level evidence recorded. Existing source links and legacy dates do not establish that this entry was reverified."));
  }
  return detailSection("Verification", ...parts);
}

function detailSources(record) {
  const section = make("section", "detail-section");
  const details = make("details", "source-details");
  const summary = make("summary", "", "Source URLs");
  summary.append(make("span", "", String(record.sourceUrls.length)));
  const list = make("ul", "source-list");
  for (const url of record.sourceUrls) {
    const item = make("li");
    item.append(makeExternal(url.replace(/^https?:\/\/(www\.)?/, ""), url));
    list.append(item);
  }
  if (!record.sourceUrls.length) list.append(make("li", "", "No source URLs recorded."));
  details.append(summary, list);
  section.append(details);
  return section;
}

function renderDetail(record) {
  const root = make("article", "detail-record");
  root.append(detailHead(record));
  const sections = [detailLinks(record), detailOverview(record)];
  if (record.recordType === "professor") {
    sections.push(
      teachingDetails(record),
      ratingDetails(record),
      labAffiliationDetails(record),
      academicDetails(record),
      facultyDirectoryDetails(record),
    );
  }
  sections.push(detailFields(record));
  if (record.recordType !== "resource") sections.push(detailRecruitment(record));
  sections.push(verificationDetails(record), detailSources(record));
  root.append(...sections.filter(Boolean));
  return root;
}

/* ---------- Search suggestions ---------- */

const SUGGESTION_GROUPS = [
  ["topic", "Research fields", 5],
  ["place", "Schools & departments", 3],
  ["record", "Top matches", 4],
];

function buildSuggestionEntries() {
  const counts = state.facetCounts;
  const entries = [];
  for (const field of RESEARCH_FIELDS) {
    if (counts.fields.get(field.id)) {
      entries.push({ group: "topic", kind: "field", value: field.id, label: field.label, meta: "All areas", count: counts.fields.get(field.id), keys: [field.label, ...field.aliases] });
    }
    for (const sub of field.subfields) {
      if (!counts.areas.get(sub.id)) continue;
      entries.push({ group: "topic", kind: "area", value: sub.id, label: sub.label, meta: field.label, count: counts.areas.get(sub.id), keys: [sub.label, ...sub.aliases] });
    }
  }
  for (const [id, count] of counts.divisions) {
    const division = TAXONOMY.divisions.get(id);
    entries.push({ group: "place", kind: "division", value: id, label: division.label, meta: "School / division", count, keys: [division.label, ...(division.aliases || [])] });
  }
  for (const [name, count] of counts.departments) {
    const known = TAXONOMY.departments.get(departmentKey(name));
    entries.push({ group: "place", kind: "department", value: name, label: name, meta: divisionLabel(state.departmentDivision.get(name)), count, keys: [name, ...(known?.aliases || [])] });
  }
  return entries.map((entry) => ({ ...entry, keys: unique(entry.keys.map(normalize)) }));
}

function suggestionScore(entry, q, synonyms) {
  let best = 0;
  for (const key of entry.keys) {
    if (key === q) best = Math.max(best, 10);
    else if (q.length <= 2 && !CJK_PATTERN.test(q)) best = Math.max(best, ` ${key} `.includes(` ${q} `) ? 6 : 0);
    else if (key.startsWith(q)) best = Math.max(best, 8);
    else if (` ${key}`.includes(` ${q}`)) best = Math.max(best, 6);
    else if (q.length >= 3 && key.includes(q)) best = Math.max(best, 4);
    else if (CJK_PATTERN.test(q) && key.length > 1 && q.includes(key)) best = Math.max(best, 5);
    if (synonyms.some((synonym) => ` ${key}`.includes(` ${synonym}`))) best = Math.max(best, 7);
  }
  if (!best && /^\p{L}{4,}$/u.test(q)) {
    const words = entry.keys.flatMap((key) => key.split(" "));
    if (words.some((word) => editDistance(q, word, 1) <= 1 || editDistance(q, word.slice(0, q.length), 1) <= 1)) best = 3;
  }
  return best;
}

function suggestionOption(entry, index) {
  const item = make("div", "suggest-item");
  item.id = `suggest-${index}`;
  item.setAttribute("role", "option");
  item.setAttribute("aria-selected", "false");
  item.dataset.suggestIndex = index;
  const text = make("span", "suggest-text");
  text.append(make("span", "suggest-label", entry.label), make("span", "suggest-meta", entry.meta));
  item.append(text);
  if (entry.count !== undefined) item.append(make("span", "suggest-count", formatNumber(entry.count)));
  return item;
}

function renderSuggestions() {
  const q = normalize(els.query.value);
  if (q.length < 2 || !state.suggestionEntries) {
    closeSuggestions();
    return;
  }
  const synonyms = [...(SEARCH_SYNONYMS[q] || []), ...cjkKeys(q).flatMap((key) => TAXONOMY.cjk[key])].map(normalize);
  const scored = state.suggestionEntries
    .map((entry) => [entry, suggestionScore(entry, q, synonyms)])
    .filter(([, score]) => score > 0)
    .sort((a, b) => b[1] - a[1] || b[0].count - a[0].count)
    .map(([entry]) => entry);
  const records = state.resultsQuery === state.query
    ? state.results.map((record) => ({
      group: "record", kind: "record", value: record.id, label: record.displayName,
      meta: [record.displayKind, record.departments[0]].filter(Boolean).join(" · "),
    }))
    : [];
  const groups = SUGGESTION_GROUPS
    .map(([key, label, limit]) => [label, (key === "record" ? records : scored.filter((entry) => entry.group === key)).slice(0, limit)])
    .filter(([, entries]) => entries.length);
  state.suggestions = groups.flatMap(([, entries]) => entries);
  state.suggestionIndex = -1;
  if (!state.suggestions.length) {
    closeSuggestions();
    return;
  }
  let index = 0;
  els.suggest.replaceChildren(...groups.flatMap(([label, entries]) => [
    make("p", "suggest-group", label),
    ...entries.map((entry) => suggestionOption(entry, index++)),
  ]));
  els.suggest.hidden = false;
  els.query.setAttribute("aria-expanded", "true");
  els.query.removeAttribute("aria-activedescendant");
}

function closeSuggestions() {
  els.suggest.hidden = true;
  state.suggestionIndex = -1;
  els.query.setAttribute("aria-expanded", "false");
  els.query.removeAttribute("aria-activedescendant");
}

function moveSuggestion(delta) {
  const total = state.suggestions.length;
  if (!total) return;
  state.suggestionIndex = state.suggestionIndex === -1 && delta < 0 ? total - 1 : (state.suggestionIndex + delta + total) % total;
  els.suggest.querySelectorAll("[role=option]").forEach((item) => {
    const active = Number(item.dataset.suggestIndex) === state.suggestionIndex;
    item.setAttribute("aria-selected", String(active));
    if (active) {
      els.query.setAttribute("aria-activedescendant", item.id);
      item.scrollIntoView({ block: "nearest" });
    }
  });
}

// Picking a field or department turns the typed words into a filter, so the query is cleared.
function chooseSuggestion(entry) {
  closeSuggestions();
  if (!entry) return;
  if (entry.kind === "record") {
    openDetail(entry.value);
    return;
  }
  state.query = "";
  if (entry.kind === "field") {
    state.field = entry.value;
    state.area = "all";
  } else if (entry.kind === "area") {
    setArea(entry.value);
  } else if (entry.kind === "division") {
    state.division = entry.value;
    state.department = "all";
  } else if (entry.kind === "department") {
    setDepartment(entry.value);
  }
  syncControls();
  update({ scroll: true });
  if (DRAWER_QUERY.matches) els.query.blur();
}

/* ---------- Overlays (filter drawer, detail sheet) ---------- */

let lastFocus = null;

function syncOverlay() {
  const open = els.rail.classList.contains("is-open") || els.detailPanel.classList.contains("is-open");
  els.scrim.hidden = !open;
  document.body.classList.toggle("is-locked", open);
}

function openSheet() {
  lastFocus = document.activeElement;
  els.detailPanel.classList.add("is-open");
  els.detailPanel.setAttribute("role", "dialog");
  els.detailPanel.setAttribute("aria-modal", "true");
  syncOverlay();
  els.detailPanel.focus({ preventScroll: true });
}

function closeSheet() {
  if (!els.detailPanel.classList.contains("is-open")) return;
  els.detailPanel.classList.remove("is-open");
  els.detailPanel.removeAttribute("role");
  els.detailPanel.removeAttribute("aria-modal");
  syncOverlay();
  const row = els.results.querySelector(`[data-open-id="${CSS.escape(state.activeId)}"]`);
  (row || lastFocus)?.focus?.({ preventScroll: true });
}

function openRail() {
  els.rail.classList.add("is-open");
  els.filtersButton.setAttribute("aria-expanded", "true");
  syncOverlay();
  els.rail.querySelector("button, select")?.focus({ preventScroll: true });
}

function closeRail() {
  if (!els.rail.classList.contains("is-open")) return;
  els.rail.classList.remove("is-open");
  els.filtersButton.setAttribute("aria-expanded", "false");
  syncOverlay();
  els.filtersButton.focus({ preventScroll: true });
}

function resetOverlaysForLayout() {
  if (DESKTOP_DETAIL_QUERY.matches) {
    els.detailPanel.classList.remove("is-open");
    els.detailPanel.removeAttribute("role");
    els.detailPanel.removeAttribute("aria-modal");
    if (!state.activeId && state.results.length) showDetail(state.results[0].id);
  }
  if (!DRAWER_QUERY.matches) {
    els.rail.classList.remove("is-open");
    els.filtersButton.setAttribute("aria-expanded", "false");
  }
  syncOverlay();
}

/* ---------- Keyboard navigation ---------- */

function moveSelection(delta) {
  const current = state.results.findIndex((record) => record.id === state.activeId);
  selectIndex(current === -1 ? 0 : current + delta);
}

function selectIndex(index) {
  if (!state.results.length) return;
  const next = Math.max(0, Math.min(state.results.length - 1, index));
  if (next >= state.visibleLimit) loadMore();
  const record = state.results[next];
  openDetail(record.id, { reveal: false });
  const button = els.results.querySelector(`[data-open-id="${CSS.escape(record.id)}"]`);
  button?.focus({ preventScroll: true });
  button?.closest(".row")?.scrollIntoView({ block: "nearest", behavior: prefersReducedMotion() ? "auto" : "smooth" });
}

function isTypingTarget(target) {
  return target instanceof HTMLElement && (target.matches("input, select, textarea") || target.isContentEditable);
}

function focusSearch() {
  els.query.focus();
  els.query.select();
}

function handleKeydown(event) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    focusSearch();
    return;
  }
  if (event.target === els.query && !els.suggest.hidden) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      moveSuggestion(event.key === "ArrowDown" ? 1 : -1);
      return;
    }
    if (event.key === "Enter" && state.suggestionIndex >= 0) {
      event.preventDefault();
      chooseSuggestion(state.suggestions[state.suggestionIndex]);
      return;
    }
    if (event.key === "Escape") {
      closeSuggestions();
      return;
    }
  }
  if (event.key === "Escape") {
    if (els.detailPanel.classList.contains("is-open")) closeSheet();
    else if (els.rail.classList.contains("is-open")) closeRail();
    else if (document.activeElement === els.query) els.query.blur();
    return;
  }
  if (event.target === els.query && event.key === "ArrowDown") {
    event.preventDefault();
    selectIndex(0);
    return;
  }
  if (isTypingTarget(event.target) || event.metaKey || event.ctrlKey || event.altKey) return;
  const inResults = els.results.contains(event.target);
  const key = event.key;
  if (key === "/") {
    event.preventDefault();
    focusSearch();
  } else if (key === "j" || (inResults && key === "ArrowDown")) {
    event.preventDefault();
    moveSelection(1);
  } else if (key === "k" || (inResults && key === "ArrowUp")) {
    event.preventDefault();
    moveSelection(-1);
  } else if (key === "s" && state.activeId) {
    event.preventDefault();
    toggleSaved(state.activeId);
  }
}

/* ---------- Feedback ---------- */

let toastTimer = 0;

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("is-visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => els.toast.classList.remove("is-visible"), 1800);
}

async function copyText(value, message) {
  try {
    await navigator.clipboard.writeText(value);
  } catch {
    const field = make("textarea");
    field.value = value;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.append(field);
    field.select();
    document.execCommand("copy");
    field.remove();
  }
  showToast(message);
}

function recordLink(id) {
  const url = new URL(window.location.href);
  url.search = "";
  url.searchParams.set("id", id);
  return url.toString();
}

/* ---------- Hero numbers ---------- */

function animateNumber(element, target) {
  const value = Number(target) || 0;
  if (prefersReducedMotion()) {
    element.textContent = formatNumber(value);
    return;
  }
  const start = performance.now();
  const duration = 900;
  const step = (now) => {
    const progress = Math.min(1, (now - start) / duration);
    const eased = 1 - (1 - progress) ** 3;
    element.textContent = formatNumber(Math.round(value * eased));
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function renderStats() {
  const count = (predicate) => state.records.filter(predicate).length;
  animateNumber(els.professorCount, count((record) => record.recordType === "professor"));
  animateNumber(els.labCount, count((record) => record.recordType === "lab"));
  animateNumber(els.realResourceCount, count((record) => record.recordType === "resource"));
  animateNumber(els.courseCount, count((record) => record.facts.courses > 0));
  animateNumber(els.ratingCount, count((record) => record.facts.ratings.length > 0));
  els.updatedAt.textContent = state.data?.generatedAt
    ? `Dataset built ${dateLabel(state.data.generatedAt)} · field dates vary`
    : "Bundled dataset";
}

/* ---------- Data loading ---------- */

async function loadData() {
  const [data, realPortalData] = await Promise.all([
    fetch(DATA_URL, DATA_FETCH_OPTIONS).then((response) => {
      if (!response.ok) throw new Error(`Could not load ${DATA_URL} (HTTP ${response.status}).`);
      return response.json();
    }),
    fetch(REAL_PORTAL_DATA_URL, DATA_FETCH_OPTIONS)
      .then((response) => (response.ok ? response.json() : null))
      .catch(() => null),
  ]);
  state.data = data;
  state.records = buildRecords(data, realPortalData);
  state.index = buildIndex(state.records);
  state.vocabulary = null;
  fuzzyCache.clear();
  state.byId = makeRecordIndex(state.records);
  state.saved = new Set([...state.saved].map((id) => state.byId.get(id)?.id || id));
  computeFacetCounts();
  normalizeTaxonomyState();
  state.suggestionEntries = buildSuggestionEntries();

  syncControls();
  renderStats();
  render();

  if (state.userSelected && state.byId.has(state.activeId)) {
    openDetail(state.activeId, { reveal: true });
  } else if (state.userSelected) {
    state.userSelected = false;
    state.activeId = "";
    writeUrl();
  }
}

/* ---------- Wiring ---------- */

function bindEvents() {
  const debouncedUpdate = debounce(() => update({ scroll: true }), SEARCH_DEBOUNCE_MS);

  els.form.addEventListener("submit", (event) => {
    event.preventDefault();
    closeSuggestions();
    syncStateFromControls();
    update({ scroll: true });
    if (DRAWER_QUERY.matches) els.query.blur();
  });

  els.query.addEventListener("input", () => {
    syncStateFromControls();
    renderSuggestions();
    debouncedUpdate();
  });
  els.query.addEventListener("focus", renderSuggestions);
  els.query.addEventListener("blur", closeSuggestions);
  // Keep focus in the field while an option is clicked, so blur doesn't close the list first.
  els.suggest.addEventListener("pointerdown", (event) => event.preventDefault());
  els.suggest.addEventListener("click", (event) => {
    const item = event.target.closest("[data-suggest-index]");
    if (item) chooseSuggestion(state.suggestions[Number(item.dataset.suggestIndex)]);
  });

  for (const control of [els.division, els.department, els.field, els.area, els.evidence, els.verifiedOnly, els.recruiting, els.sort]) {
    control.addEventListener("change", () => {
      syncStateFromControls(control);
      syncControls();
      update({ scroll: true });
    });
  }

  els.fieldStrip.addEventListener("click", (event) => {
    const button = event.target.closest("[data-strip-field], [data-strip-area]");
    if (!button) return;
    if (button.dataset.stripArea) setArea(state.area === button.dataset.stripArea ? "all" : button.dataset.stripArea);
    else if (button.dataset.stripField === "all") setField("all");
    else {
      setField(button.dataset.stripField);
      state.area = "all";
    }
    syncControls();
    update({ scroll: true });
  });

  els.typeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.type = button.dataset.typeChoice || "all";
      update({ scroll: true });
    });
  });

  els.quickButtons.forEach((button) => {
    button.addEventListener("click", () => applyQuickFilter(button.dataset.quick));
  });

  els.activeFilters.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-filter-key]");
    if (chip) clearFilter(chip.dataset.filterKey);
  });

  els.clear.addEventListener("click", () => resetFilters({ keepQuery: true }));
  els.emptyReset.addEventListener("click", () => resetFilters());
  els.loadMore.addEventListener("click", loadMore);

  els.savedToggle.addEventListener("click", () => {
    state.savedOnly = !state.savedOnly;
    syncControls();
    update({ scroll: true });
  });

  els.shareButton.addEventListener("click", () => copyText(window.location.href, "Search link copied"));
  els.filtersButton.addEventListener("click", openRail);
  els.railClose.addEventListener("click", closeRail);
  els.railApply.addEventListener("click", closeRail);
  els.detailClose.addEventListener("click", closeSheet);
  els.scrim.addEventListener("click", () => {
    closeSheet();
    closeRail();
  });

  // Delegated clicks: row titles, saved list, save toggles, tags, copy buttons.
  document.addEventListener("click", (event) => {
    const target = event.target.closest("[data-open-id], [data-save-id], [data-area-filter], [data-field-filter], [data-search-keyword], [data-copy], [data-copy-record-link]");
    if (!target) return;
    if (target.dataset.saveId) {
      toggleSaved(target.dataset.saveId);
    } else if (target.dataset.openId) {
      closeRail();
      openDetail(target.dataset.openId);
    } else if (target.dataset.areaFilter || target.dataset.fieldFilter) {
      if (target.dataset.areaFilter) setArea(target.dataset.areaFilter);
      else setField(target.dataset.fieldFilter);
      syncControls();
      closeSheet();
      update({ scroll: true });
    } else if (target.dataset.searchKeyword) {
      state.query = target.dataset.searchKeyword;
      syncControls();
      closeSheet();
      update({ scroll: true });
    } else if (target.dataset.copy) {
      copyText(target.dataset.copy, target.dataset.copyLabel || "Copied");
    } else if (target.dataset.copyRecordLink) {
      copyText(recordLink(target.dataset.copyRecordLink), "Record link copied");
    }
  });

  document.addEventListener("keydown", handleKeydown);
  DESKTOP_DETAIL_QUERY.addEventListener("change", resetOverlaysForLayout);
  DRAWER_QUERY.addEventListener("change", resetOverlaysForLayout);

  const syncPlaceholder = () => {
    els.query.placeholder = COMPACT_QUERY.matches ? "Search people, labs, fields" : "Search a professor, lab, course, or field — e.g. machine learning";
  };
  COMPACT_QUERY.addEventListener("change", syncPlaceholder);
  syncPlaceholder();

  // Auto-load the first few pages as the reader nears the end of the list; after that the button stays manual.
  if ("IntersectionObserver" in window) {
    new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting) && !els.loadMore.hidden && state.visibleLimit < AUTO_LOAD_LIMIT) {
        loadMore();
      }
    }, { rootMargin: "0px 0px 600px 0px" }).observe(els.loadMore);
  }
}

function boot() {
  bindEvents();
  readUrl();
  syncControls();
  loadData().catch((error) => {
    els.resultHeading.textContent = "Data unavailable";
    els.coverageLine.textContent = error.message;
    els.results.replaceChildren();
    els.results.setAttribute("aria-busy", "false");
    els.empty.hidden = false;
    els.emptyHint.textContent = "The dataset could not be loaded. If you opened index.html directly, serve the folder with `python3 -m http.server` instead.";
  });
}

// tests/test_frontend_data.cjs evaluates this file in a bare VM to exercise the data helpers;
// only a real page (which has a document.readyState) boots the UI.
if (document.readyState) boot();
