const DATA_URL = "data/research-atlas.json";
const REAL_PORTAL_DATA_URL = "data/ucsd/real-portal-resources.json";
const NOT_FOUND = "Not found";
const UNKNOWN = "Unknown";
const PAGE_SIZE = 80;
const DATA_FETCH_OPTIONS = { credentials: "same-origin", cache: "no-store" };
const REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";
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

const state = {
  data: null,
  records: [],
  index: [],
  query: "",
  type: "all",
  institution: "all",
  department: "all",
  area: "all",
  recruiting: "all",
  verifiedOnly: false,
  sort: "relevance",
  visibleLimit: PAGE_SIZE,
  saved: new Set(JSON.parse(localStorage.getItem("researchAtlasSaved") || "[]")),
  activeRecord: null,
};

const els = {
  form: document.querySelector("#searchForm"),
  hero: document.querySelector(".hero"),
  query: document.querySelector("#query"),
  typeButtons: [...document.querySelectorAll("[data-type-choice]")],
  smartFilterButtons: [...document.querySelectorAll("[data-smart-filter]")],
  recruiting: document.querySelector("#recruitingFilter"),
  institution: document.querySelector("#institutionFilter"),
  department: document.querySelector("#departmentFilter"),
  area: document.querySelector("#areaFilter"),
  sort: document.querySelector("#sortFilter"),
  clear: document.querySelector("#clearFilters"),
  results: document.querySelector("#results"),
  empty: document.querySelector("#emptyState"),
  heading: document.querySelector("#resultHeading"),
  updatedAt: document.querySelector("#updatedAt"),
  activeFilters: document.querySelector("#activeFilters"),
  resultSummary: document.querySelector("#resultSummary"),
  areaChips: document.querySelector("#areaChips"),
  loadMore: document.querySelector("#loadMore"),
  savedCount: document.querySelector("#savedCount"),
  savedList: document.querySelector("#savedList"),
  professorCount: document.querySelector("#professorCount"),
  labCount: document.querySelector("#labCount"),
  realResourceCount: document.querySelector("#realResourceCount"),
  sourceCount: document.querySelector("#sourceCount"),
  verifiedCount: document.querySelector("#verifiedCount"),
  template: document.querySelector("#resultTemplate"),
  drawer: document.querySelector("#detailDrawer"),
  drawerContent: document.querySelector("#drawerContent"),
};

const motion = {
  mm: null,
};

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^\p{L}\p{N}@.+-]+/gu, " ")
    .trim();
}

function valueOrFallback(value) {
  if (value === null || value === undefined || value === "") return NOT_FOUND;
  if (Array.isArray(value) && value.length === 0) return NOT_FOUND;
  return value;
}

function isKnown(value) {
  return value !== null && value !== undefined && value !== "" && value !== NOT_FOUND && value !== UNKNOWN;
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

function gsapCore() {
  return window.gsap || null;
}

function prefersReducedMotion() {
  return window.matchMedia(REDUCED_MOTION_QUERY).matches;
}

function option(value, label) {
  const node = document.createElement("option");
  node.value = value;
  node.textContent = label;
  return node;
}

function slugLabel(value) {
  return value
    .split(/[\s_-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function professorLinks(professor) {
  return [
    ["Faculty profile", professor.officialProfileUrl],
    ["Personal website", professor.personalWebsiteUrl],
    ["Google Scholar profile", professor.googleScholarUrl],
    ["Google Scholar search", professor.googleScholarSearchUrl],
    ["OpenAlex author", professor.academicProfile?.openAlexUrl],
    ["LinkedIn search", professor.linkedinSearchUrl],
    ["Lab affiliation", professor.labAffiliationUrl],
  ].filter(([, url]) => isKnown(url));
}

function labLinks(lab) {
  return [
    ["Lab website", lab.labWebsiteUrl],
    ["PI profile", lab.principalInvestigatorProfileUrl],
  ].filter(([, url]) => isKnown(url));
}

function resourceLinks(resource) {
  return [
    ["REAL Portal", resource.sourceUrl],
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

function buildRecords(data, realPortalData = null) {
  const professors = mergeProfessorDuplicates((data.professors || []).map((item) => {
    const displayName = valueOrFallback(item.name);
    return {
      ...item,
      recordType: "professor",
      displayName,
      displayKind: "Professor",
      affiliationLine: [item.institution, item.department].filter(isKnown).join(" / "),
      summary: valueOrFallback(item.researchSummary),
      email: valueOrFallback(item.email),
      researchAreas: item.researchAreas || [],
      sourceUrls: item.sourceUrls || [],
      links: professorLinks(item),
    };
  }));

  const labs = (data.labs || []).map((item) => {
    const displayName = valueOrFallback(item.labName);
    return {
      ...item,
      recordType: "lab",
      displayName,
      displayKind: slugLabel(item.recordSubtype || "lab"),
      affiliationLine: [item.institution, item.department].filter(isKnown).join(" / "),
      summary: valueOrFallback(item.description),
      email: valueOrFallback(item.contactEmail),
      researchAreas: item.researchAreas || [],
      sourceUrls: item.sourceUrls || [],
      links: labLinks(item),
    };
  });

  const resources = (realPortalData?.resources || []).map((item) => {
    const displayName = valueOrFallback(item.title);
    return {
      ...item,
      id: item.id || `real-${displayName}`,
      recordType: "resource",
      displayName,
      displayKind: "REAL Resource",
      institution: "University of California San Diego",
      department: valueOrFallback(item.organization),
      affiliationLine: [item.resourceType, item.organization].filter(isKnown).join(" / "),
      summary: valueOrFallback(item.description),
      email: valueOrFallback(item.contactEmails?.[0]),
      researchAreas: resourceAreas(item),
      sourceUrls: [item.sourceUrl || realPortalData.sourceUrl].filter(isKnown),
      links: resourceLinks(item),
      recruitingStatus: UNKNOWN,
      recruitingEvidence: { text: "", url: "" },
      lastVerified: item.lastVerified,
    };
  });

  return [...professors, ...labs, ...resources];
}

function professorMergeKey(record) {
  if (isKnown(record.email)) return `email:${String(record.email).toLowerCase()}`;
  if (hasScholarProfile(record)) return `scholar:${record.googleScholarUrl}`;
  return "";
}

function academicScore(record) {
  const profile = record.academicProfile || {};
  let score = 0;
  if (isKnown(profile.citationCount)) score += 10;
  if (isKnown(profile.worksCount)) score += 8;
  if (isKnown(profile.openAlexUrl)) score += 6;
  score += Math.min((profile.recentPublications || []).length, 5);
  return score;
}

function summaryScore(record) {
  const text = String(record.summary || "");
  let score = Math.min(text.length, 400);
  if (/public .*faculty profile/i.test(text)) score -= 80;
  if (/catalog|listing/i.test(text)) score -= 45;
  if (/research on|research in|focus/i.test(text)) score += 80;
  return score;
}

function bestBy(records, scorer) {
  return [...records].sort((a, b) => scorer(b) - scorer(a))[0];
}

function mergeProfessorGroup(records) {
  if (records.length === 1) return records[0];

  const base = { ...bestBy(records, (record) => summaryScore(record) + academicScore(record)) };
  const academicRecord = bestBy(records, academicScore);
  const summaryRecord = bestBy(records, summaryScore);
  const departments = uniqueByNormalized(records.map((record) => record.department));
  const institutions = uniqueByNormalized(records.map((record) => record.institution));
  const profileIds = records.map((record) => record.id).filter(Boolean);

  base.id = profileIds[0] || base.id;
  base.mergedProfileIds = profileIds;
  base.mergedProfileCount = records.length;
  base.department = departments.join(" + ");
  base.institution = institutions[0] || base.institution;
  base.affiliationLine = [base.institution, base.department].filter(isKnown).join(" / ");
  base.summary = summaryRecord.summary;
  base.researchSummary = summaryRecord.summary;
  base.email = records.find((record) => isKnown(record.email))?.email || base.email;
  base.personalWebsiteUrl = records.find((record) => isKnown(record.personalWebsiteUrl))?.personalWebsiteUrl || base.personalWebsiteUrl;
  base.officialProfileUrl = records.find((record) => isKnown(record.officialProfileUrl))?.officialProfileUrl || base.officialProfileUrl;
  base.googleScholarUrl = records.find((record) => hasScholarProfile(record))?.googleScholarUrl || base.googleScholarUrl;
  base.googleScholarSearchUrl = records.find((record) => isKnown(record.googleScholarSearchUrl))?.googleScholarSearchUrl || base.googleScholarSearchUrl;
  base.linkedinSearchUrl = records.find((record) => isKnown(record.linkedinSearchUrl))?.linkedinSearchUrl || base.linkedinSearchUrl;
  base.labAffiliation = uniqueByNormalized(records.map((record) => record.labAffiliation)).join(" + ") || base.labAffiliation;
  base.labAffiliationUrl = records.find((record) => isKnown(record.labAffiliationUrl))?.labAffiliationUrl || base.labAffiliationUrl;
  base.researchAreas = uniqueByNormalized(records.flatMap((record) => record.researchAreas || []));
  base.sourceUrls = unique(records.flatMap((record) => record.sourceUrls || []).filter(isKnown));
  base.links = uniqueLinks(records.flatMap((record) => record.links || []));
  base.academicProfile = academicRecord.academicProfile || base.academicProfile;
  base.recruitingStatus = records.find((record) => record.recruitingStatus === "Recruiting")?.recruitingStatus
    || records.find((record) => record.recruitingStatus === "Not recruiting")?.recruitingStatus
    || base.recruitingStatus;
  base.recruitingEvidence = records.find((record) => record.recruitingEvidence?.text)?.recruitingEvidence || base.recruitingEvidence;
  return base;
}

function mergeProfessorDuplicates(professors) {
  const groups = new Map();
  const singles = [];
  for (const professor of professors) {
    const key = professorMergeKey(professor);
    if (!key) {
      singles.push(professor);
      continue;
    }
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(professor);
  }

  return [...groups.values()].map(mergeProfessorGroup).concat(singles);
}

function buildIndex(records) {
  return records.map((record) => {
    const linkText = record.links.flatMap(([label, url]) => [label, url]);
    const sourceText = record.sourceUrls || [];
    const fields = [
      record.displayName,
      record.displayKind,
      record.institution,
      record.department,
      record.summary,
      record.email,
      record.labAffiliation,
      record.principalInvestigator,
      record.organization,
      record.resourceType,
      record.applicationProcedure,
      record.academicProfile?.matchedName,
      record.academicProfile?.openAlexUrl,
      ...(record.academicProfile?.recentPublications || []).flatMap((paper) => [
        paper.title,
        paper.venue,
        paper.year,
      ]),
      record.recruitingStatus,
      record.recruitingEvidence?.text,
      ...(record.researchAreas || []),
      ...linkText,
      ...sourceText,
    ];

    return {
      haystack: normalize(fields.join(" ")),
      name: normalize(record.displayName),
      department: normalize(record.department),
      areas: (record.researchAreas || []).map(normalize),
      sourceCount: (record.sourceUrls || []).length,
    };
  });
}

function setSelectOptions(select, values, allLabel) {
  const current = select.value || "all";
  select.replaceChildren(option("all", allLabel), ...values.map((value) => option(value, value)));
  select.value = values.includes(current) ? current : "all";
}

function renderFacets() {
  const institutions = unique(state.records.map((record) => record.institution).filter(isKnown)).sort();
  const departments = unique(state.records.map((record) => record.department).filter(isKnown)).sort();
  const areas = unique(state.records.flatMap((record) => record.researchAreas || [])).sort();

  setSelectOptions(els.institution, institutions, "All universities");
  setSelectOptions(els.department, departments, "All departments");
  setSelectOptions(els.area, areas, "All research areas");

  const topAreas = [...areas]
    .sort((a, b) => areaCount(b) - areaCount(a) || a.localeCompare(b))
    .slice(0, 10);

  els.areaChips.replaceChildren(
    ...topAreas.map((area) => {
      const button = document.createElement("button");
      button.className = `chip${state.area === area ? " is-active" : ""}`;
      button.type = "button";
      button.textContent = area;
      button.addEventListener("click", () => {
        state.area = state.area === area ? "all" : area;
        state.visibleLimit = PAGE_SIZE;
        els.area.value = state.area;
        renderFacets();
        render();
      });
      return button;
    }),
  );
}

function updateTypeButtons() {
  els.typeButtons.forEach((button) => {
    const isActive = button.dataset.typeChoice === state.type;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function updateSmartFilterButtons() {
  els.smartFilterButtons.forEach((button) => {
    const key = button.dataset.smartFilter;
    const isActive = (
      (key === "recruiting" && state.recruiting === "Recruiting") ||
      (key === "verified" && state.verifiedOnly) ||
      (key === "professor" && state.type === "professor" && !state.verifiedOnly) ||
      (key === "lab" && state.type === "lab") ||
      (key === "resource" && state.type === "resource")
    );
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function areaCount(area) {
  return state.records.filter((record) => (record.researchAreas || []).includes(area)).length;
}

function compileTerms() {
  return normalize(state.query).split(/\s+/).filter(Boolean);
}

function scoreRecord(record, indexed, terms) {
  if (!terms.length) return 0;
  let score = 0;
  for (const term of terms) {
    if (indexed.name.includes(term)) score += 8;
    if (indexed.department.includes(term)) score += 4;
    if (indexed.areas.some((area) => area.includes(term))) score += 5;
    if (indexed.haystack.includes(term)) score += 1;
  }
  if (record.recruitingStatus === "Recruiting") score += 2;
  return score;
}

function filteredRecords() {
  const terms = compileTerms();
  const rows = [];

  state.records.forEach((record, index) => {
    const indexed = state.index[index];

    if (state.type !== "all" && record.recordType !== state.type) return;
    if (state.institution !== "all" && record.institution !== state.institution) return;
    if (state.department !== "all" && record.department !== state.department) return;
    if (state.area !== "all" && !(record.researchAreas || []).includes(state.area)) return;
    if (state.recruiting !== "all" && record.recruitingStatus !== state.recruiting) return;
    if (state.verifiedOnly && !academicMetrics(record).verified) return;
    if (terms.length && !terms.every((term) => indexed.haystack.includes(term))) return;

    rows.push({ record, index, score: scoreRecord(record, indexed, terms) });
  });

  rows.sort((a, b) => {
    if (state.sort === "name") return a.record.displayName.localeCompare(b.record.displayName);
    if (state.sort === "department") {
      return (
        (a.record.department || "").localeCompare(b.record.department || "") ||
        a.record.displayName.localeCompare(b.record.displayName)
      );
    }
    if (state.sort === "citations") {
      return citationSortValue(b.record) - citationSortValue(a.record) || a.record.displayName.localeCompare(b.record.displayName);
    }
    if (state.sort === "sources") {
      return b.record.sourceUrls.length - a.record.sourceUrls.length || a.record.displayName.localeCompare(b.record.displayName);
    }
    return b.score - a.score || a.record.displayName.localeCompare(b.record.displayName);
  });

  return rows.map((row) => row.record);
}

function citationSortValue(record) {
  const metrics = academicMetrics(record);
  const value = metrics.verified ? metrics.profile.citationCount : UNKNOWN;
  if (!isKnown(value)) return -1;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : -1;
}

function statusClass(status) {
  if (status === "Recruiting") return "recruiting";
  if (status === "Not recruiting") return "not-recruiting";
  return "unknown";
}

function makeTag(text) {
  const tag = document.createElement("span");
  tag.textContent = text;
  return tag;
}

function makeLink(label, url, className = "") {
  const anchor = document.createElement("a");
  anchor.className = `link-button ${className}`.trim();
  anchor.href = url;
  anchor.target = "_blank";
  anchor.rel = "noreferrer";
  anchor.textContent = label;
  return anchor;
}

function cardLinks(record) {
  if (record.recordType === "professor") {
    return [
      ["Personal website", record.personalWebsiteUrl],
      ["Faculty profile", record.officialProfileUrl],
    ]
      .filter(([, url]) => isKnown(url))
      .map(([label, url], index) => [label, url, index === 0 ? "primary-link" : ""]);
  }
  return record.links.slice(0, 1).map(([label, url]) => [label, url, "primary-link"]);
}

function makeEmail(record) {
  const row = document.createDocumentFragment();
  if (!isKnown(record.email)) {
    const missing = document.createElement("span");
    missing.className = "email-pill";
    missing.textContent = "Email not found";
    row.appendChild(missing);
    return row;
  }

  const email = document.createElement("a");
  email.className = "email-pill";
  email.href = `mailto:${record.email}`;
  email.textContent = record.email;
  row.appendChild(email);

  const copy = document.createElement("button");
  copy.className = "email-copy";
  copy.type = "button";
  copy.textContent = "Copy";
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(record.email);
      copy.textContent = "Copied";
      window.setTimeout(() => {
        copy.textContent = "Copy";
      }, 1200);
    } catch {
      copy.textContent = "Select email";
    }
  });
  row.appendChild(copy);
  return row;
}

function numberLabel(value) {
  if (!isKnown(value)) return "";
  if (typeof value === "number") return value.toLocaleString();
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toLocaleString() : String(value);
}

function numericMetric(value) {
  const numeric = Number(value);
  return isKnown(value) && Number.isFinite(numeric) && numeric >= 0;
}

function cleanText(value) {
  return String(value || "")
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenSet(value) {
  return new Set(
    normalize(cleanText(value))
      .split(/\s+/)
      .filter((token) => token.length > 2 && !/^\d+$/.test(token) && !METRIC_STOPWORDS.has(token)),
  );
}

function recordEvidenceTokens(record) {
  return tokenSet([
    record.department,
    record.summary,
    record.labAffiliation,
    ...(record.researchAreas || []),
  ].join(" "));
}

function paperEvidenceTokens(paper) {
  return tokenSet([
    paper.title,
    paper.venue,
  ].join(" "));
}

function publicationRelevanceScore(record, paper) {
  const recordTokens = recordEvidenceTokens(record);
  const paperTokens = paperEvidenceTokens(paper);
  let score = 0;

  for (const token of paperTokens) {
    if (recordTokens.has(token)) score += 1;
  }

  return score;
}

function relevantPublications(record) {
  const publications = record.academicProfile?.recentPublications || [];
  return publications
    .map((paper) => ({ paper, score: publicationRelevanceScore(record, paper) }))
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score || String(b.paper.publicationDate || b.paper.year || "").localeCompare(String(a.paper.publicationDate || a.paper.year || "")))
    .map(({ paper }) => paper);
}

function hasAcademicMetrics(record) {
  const profile = record.academicProfile || {};
  return numericMetric(profile.citationCount) || numericMetric(profile.worksCount) || numericMetric(profile.hIndex);
}

function academicProfileLooksRelevant(record) {
  const profile = record.academicProfile || {};
  if (!hasAcademicMetrics(record)) return false;

  const confidence = Number(profile.matchConfidence);
  if (Number.isFinite(confidence) && confidence < 0.95) return false;

  const publications = profile.recentPublications || [];
  if (!publications.length) return Number.isFinite(confidence) && confidence >= 0.98;

  return relevantPublications(record).length > 0;
}

function academicMetrics(record) {
  const profile = record.academicProfile || {};
  const hasMetrics = hasAcademicMetrics(record);
  const source = isKnown(profile.source) ? profile.source : (isKnown(profile.openAlexUrl) ? "OpenAlex" : UNKNOWN);
  const verified = hasMetrics && academicProfileLooksRelevant(record);
  return {
    profile,
    hasMetrics,
    verified,
    source,
    status: verified ? `${source} verified` : (hasMetrics ? `${source} needs review` : "Not verified"),
  };
}

function initials(name) {
  const parts = cleanText(name).split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  return parts.slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function scholarUrl(record) {
  if (hasScholarProfile(record)) {
    return record.googleScholarUrl;
  }
  if (isKnown(record.googleScholarSearchUrl)) return record.googleScholarSearchUrl;
  const query = encodeURIComponent(`${record.displayName} ${record.institution || "UC San Diego"}`);
  return `https://scholar.google.com/citations?view_op=search_authors&mauthors=${query}&hl=en`;
}

function hasScholarProfile(record) {
  return isKnown(record.googleScholarUrl) && record.googleScholarUrl.includes("scholar.google.");
}

function bestRecentPublication(record) {
  return relevantPublications(record).find((paper) => isKnown(paper.title))
    || (record.academicProfile?.recentPublications || []).find((paper) => isKnown(paper.title));
}

function makeMetric(label, value, emptyLabel = "N/A") {
  const item = document.createElement("span");
  const number = document.createElement("strong");
  number.textContent = isKnown(value) ? numberLabel(value) : emptyLabel;
  const text = document.createElement("span");
  text.textContent = label;
  item.append(number, text);
  return item;
}

function renderScholarPreview(record) {
  if (record.recordType !== "professor") return null;

  const metrics = academicMetrics(record);
  const academic = metrics.profile;
  const paper = metrics.verified ? bestRecentPublication(record) : null;
  const wrapper = document.createElement("div");
  wrapper.className = "scholar-preview";

  const header = document.createElement("div");
  header.className = "scholar-preview-head";
  const label = document.createElement("span");
  label.className = "metric-title";
  label.textContent = "Academic metrics";
  const source = document.createElement("em");
  source.className = `metric-source${metrics.verified ? " is-verified" : metrics.hasMetrics ? " is-review" : ""}`;
  source.textContent = metrics.status;
  label.appendChild(source);

  const scholar = makeLink(hasScholarProfile(record) ? "Scholar profile" : "Scholar search", scholarUrl(record), "scholar-link");
  header.append(label, scholar);

  if (!metrics.verified) {
    const notice = document.createElement("p");
    notice.className = "metrics-review";
    notice.textContent = metrics.hasMetrics
      ? "Citation numbers are hidden because the publication match needs review."
      : "Citation metrics are not verified in the local metadata yet.";
    wrapper.append(header, notice);
    return wrapper;
  }

  const stats = document.createElement("div");
  stats.className = "scholar-stats";
  stats.append(
    makeMetric("citations", academic.citationCount),
    makeMetric("works", academic.worksCount),
  );

  const recent = document.createElement("p");
  recent.className = "recent-paper";
  if (paper) {
    recent.textContent = `Recent: ${cleanText(paper.title)}`;
    const paperMeta = [paper.publicationDate || paper.year, isKnown(paper.citationCount) ? `${numberLabel(paper.citationCount)} citations` : ""]
      .filter(isKnown)
      .join(" / ");
    if (paperMeta) {
      const meta = document.createElement("span");
      meta.textContent = paperMeta;
      recent.appendChild(meta);
    }
  } else {
    recent.textContent = "Recent papers not available in the local metadata yet.";
  }

  wrapper.append(header, stats, recent);
  return wrapper;
}

function metricBadgeText(record) {
  if (record.recordType !== "professor") return record.displayKind;
  const metrics = academicMetrics(record);
  if (metrics.verified) return `${metrics.source} verified`;
  if (metrics.hasMetrics) return "Metrics need review";
  return "Metrics pending";
}

function makeInsight(label, value, className = "") {
  const item = document.createElement("span");
  item.className = `insight-pill ${className}`.trim();
  const key = document.createElement("span");
  key.textContent = label;
  const body = document.createElement("strong");
  body.textContent = value;
  item.append(key, body);
  return item;
}

function renderCardInsights(record) {
  const row = document.createElement("div");
  row.className = "card-insights";
  row.append(
    makeInsight("Sources", numberLabel(record.sourceUrls?.length || 0)),
    makeInsight("Contact", isKnown(record.email) ? "Email" : "Missing", isKnown(record.email) ? "good" : "muted"),
    makeInsight("Evidence", metricBadgeText(record)),
  );
  if (record.recordType === "resource" && isKnown(record.applicationProcedure)) {
    row.append(makeInsight("Apply", record.applicationProcedure));
  }
  return row;
}

function renderTags(tags, limit = 4) {
  const visible = (tags || []).slice(0, limit).map(makeTag);
  const remaining = Math.max((tags || []).length - limit, 0);
  if (remaining > 0) {
    const more = makeTag(`+${remaining}`);
    more.className = "more-tag";
    visible.push(more);
  }
  return visible;
}

function recordMetaLine(record) {
  const parts = [];
  if (record.recordType === "professor") {
    return null;
  } else if (record.recordType === "resource") {
    if (isKnown(record.yearOfActivity)) parts.push(record.yearOfActivity);
    if (isKnown(record.applicationProcedure)) parts.push(record.applicationProcedure);
  }
  if (!parts.length) return null;
  const meta = document.createElement("p");
  meta.className = "record-meta-line";
  meta.textContent = parts.join(" / ");
  return meta;
}

function renderCard(record, position) {
  const fragment = els.template.content.cloneNode(true);
  const card = fragment.querySelector(".result-card");
  const typeBadge = fragment.querySelector(".type-badge");
  const statusBadge = fragment.querySelector(".status-badge");
  const topline = fragment.querySelector(".card-topline");
  const titleRow = fragment.querySelector(".card-title-row");
  const title = fragment.querySelector("h3");
  const affiliation = fragment.querySelector(".card-affiliation");
  const save = fragment.querySelector(".save-button");
  const summary = fragment.querySelector(".summary");
  const email = fragment.querySelector(".email-row");
  const tags = fragment.querySelector(".tag-list");
  const actions = fragment.querySelector(".card-actions");

  card.dataset.interactiveCard = "";
  typeBadge.textContent = record.displayKind;
  statusBadge.textContent = record.recruitingStatus || UNKNOWN;
  statusBadge.classList.add(statusClass(record.recruitingStatus));
  if (record.mergedProfileCount > 1) {
    const mergeBadge = document.createElement("span");
    mergeBadge.className = "merge-badge";
    mergeBadge.textContent = `${record.mergedProfileCount} merged`;
    topline.appendChild(mergeBadge);
  }

  const avatar = document.createElement("span");
  avatar.className = `record-avatar ${record.recordType}`;
  avatar.textContent = initials(record.displayName);
  titleRow.insertBefore(avatar, titleRow.firstElementChild);

  title.textContent = record.displayName;
  affiliation.textContent = record.affiliationLine || record.institution || NOT_FOUND;
  summary.textContent = record.summary;

  save.textContent = state.saved.has(record.id) ? "Saved" : "Save";
  save.classList.toggle("is-saved", state.saved.has(record.id));
  save.addEventListener("click", () => toggleSaved(record.id));

  const scholarPreview = renderScholarPreview(record);
  if (scholarPreview) summary.after(scholarPreview);

  email.replaceChildren(makeEmail(record));
  const meta = recordMetaLine(record);
  if (meta) email.after(meta);
  email.after(renderCardInsights(record));
  tags.replaceChildren(...renderTags(record.researchAreas || []));

  const actionNodes = [];
  const seenActionUrls = new Set();
  for (const [label, url, className] of cardLinks(record)) {
    if (seenActionUrls.has(url)) continue;
    seenActionUrls.add(url);
    actionNodes.push(makeLink(label, url, className));
  }

  const details = document.createElement("button");
  details.className = "details-button";
  details.type = "button";
  details.textContent = `Sources (${record.sourceUrls.length})`;
  details.addEventListener("click", () => openDrawer(record.id));
  actionNodes.push(details);

  actions.replaceChildren(...actionNodes);
  return fragment;
}

function initGsapMotion() {
  const gsap = gsapCore();
  if (!gsap) return;

  gsap.defaults({ duration: 0.6, ease: "power3.out", overwrite: "auto" });
  motion.mm = gsap.matchMedia();
  motion.mm.add(
    {
      isDesktop: "(min-width: 900px)",
      isMobile: "(max-width: 899px)",
      reduceMotion: REDUCED_MOTION_QUERY,
    },
    (context) => {
      const { isDesktop, isMobile, reduceMotion } = context.conditions;
      if (reduceMotion) {
        gsap.set(
          [
            ".topbar",
            ".brand-mark",
            ".top-links a",
            ".hero-frame",
            ".hero-ambient span",
            ".hero-copy .eyebrow-label",
            ".hero-copy h1",
            ".hero-subtitle",
            ".hero-metrics span",
            ".search-panel",
            ".quick-actions button",
            ".filter-panel",
            ".results-toolbar",
            ".result-summary span",
            ".active-filters",
            ".chip-row",
            ".accuracy-note",
          ],
          { clearProps: "all" },
        );
        return;
      }

      gsap.from(".topbar", { y: -18, autoAlpha: 0, duration: 0.5, ease: "power2.out" });
      gsap.from(".brand-mark", { scale: 0.82, rotation: -4, autoAlpha: 0, duration: 0.58, ease: "back.out(1.7)" });
      gsap.from(".top-links a", { y: -8, autoAlpha: 0, duration: 0.42, stagger: 0.05, delay: 0.08 });
      gsap.from(".hero-frame", { scale: isDesktop ? 0.985 : 1, autoAlpha: 0, duration: 0.78, ease: "power2.out" });
      gsap.from(".hero-ambient span", {
        x: (index) => (index % 2 === 0 ? 28 : -18),
        y: (index) => (index % 2 === 0 ? 12 : -10),
        scale: 0.96,
        autoAlpha: 0,
        duration: 0.9,
        stagger: 0.08,
        ease: "power3.out",
      });
      gsap.from(".hero-copy .eyebrow-label, .hero-copy h1, .hero-subtitle, .hero-metrics span", {
        y: isMobile ? 16 : 28,
        autoAlpha: 0,
        duration: 0.72,
        stagger: { each: 0.07, from: "start" },
      });
      gsap.from(".search-panel", {
        y: isMobile ? 18 : 30,
        scale: isDesktop ? 0.985 : 1,
        autoAlpha: 0,
        duration: 0.78,
        delay: 0.12,
        ease: "back.out(1.18)",
      });
      gsap.from(".quick-actions button", {
        y: 8,
        autoAlpha: 0,
        duration: 0.42,
        stagger: 0.04,
        delay: 0.22,
      });
      gsap.from(".filter-panel", {
        x: isDesktop ? -24 : 0,
        y: isDesktop ? 0 : 18,
        autoAlpha: 0,
        duration: 0.68,
        delay: 0.18,
      });
      gsap.from(".results-toolbar, .result-summary span, .active-filters, .chip-row, .accuracy-note", {
        y: 14,
        autoAlpha: 0,
        duration: 0.5,
        stagger: 0.05,
        delay: 0.24,
      });

      if (isDesktop) {
        gsap.to(".ambient-line-a", { x: "+=34", duration: 7, repeat: -1, yoyo: true, ease: "sine.inOut" });
        gsap.to(".ambient-line-b", { x: "-=24", duration: 8, repeat: -1, yoyo: true, ease: "sine.inOut" });
        gsap.to(".ambient-plate-a, .ambient-plate-b, .ambient-plate-c", {
          y: (index) => [10, -8, 12][index] || 8,
          duration: 5.5,
          repeat: -1,
          yoyo: true,
          stagger: 0.28,
          ease: "sine.inOut",
        });
      }
    },
  );
}

function animateResults() {
  const gsap = gsapCore();
  if (!gsap || prefersReducedMotion()) return;

  const cards = [...els.results.querySelectorAll(".result-card")].slice(0, 24);
  if (!cards.length) return;

  gsap.killTweensOf(cards);
  gsap.fromTo(
    cards,
    { y: 18, scale: 0.985, autoAlpha: 0 },
    {
      y: 0,
      scale: 1,
      autoAlpha: 1,
      duration: 0.46,
      ease: "power2.out",
      stagger: { each: 0.025, from: "start" },
      clearProps: "transform,opacity,visibility",
    },
  );
}

function animateMetricCount(element, targetValue) {
  const gsap = gsapCore();
  const target = Number(targetValue) || 0;
  const current = Number(String(element.textContent || "0").replace(/,/g, "")) || 0;

  if (!gsap || prefersReducedMotion()) {
    element.textContent = target.toLocaleString();
    return;
  }

  const proxy = { value: current };
  gsap.to(proxy, {
    value: target,
    duration: 1,
    ease: "power2.out",
    onUpdate: () => {
      element.textContent = Math.round(proxy.value).toLocaleString();
    },
    onComplete: () => {
      element.textContent = target.toLocaleString();
    },
  });
}

function animateSearchFeedback() {
  const gsap = gsapCore();
  if (!gsap || prefersReducedMotion()) return;

  gsap.fromTo(
    els.form,
    { scale: 0.992 },
    { scale: 1, duration: 0.32, ease: "back.out(2.2)", clearProps: "transform" },
  );
}

function render() {
  const records = filteredRecords();
  const visible = records.slice(0, state.visibleLimit);
  const shown = Math.min(visible.length, records.length);
  els.heading.textContent = records.length
    ? `${records.length} ${records.length === 1 ? "match" : "matches"} - showing ${shown}`
    : "0 matches";
  els.empty.hidden = records.length !== 0;
  els.loadMore.hidden = shown >= records.length;
  els.loadMore.textContent = `Load more (${records.length - shown} remaining)`;
  renderResultSummary(records);
  renderActiveFilters();
  updateTypeButtons();
  updateSmartFilterButtons();

  if (!records.length) {
    els.results.replaceChildren();
    renderSaved();
    return;
  }

  const fragment = document.createDocumentFragment();
  visible.forEach((record, index) => fragment.appendChild(renderCard(record, index)));
  els.results.replaceChildren(fragment);
  els.results.classList.remove("is-refreshing");
  window.requestAnimationFrame(() => {
    els.results.classList.add("is-refreshing");
    animateResults();
  });
  renderSaved();
}

function renderResultSummary(records) {
  const professors = records.filter((record) => record.recordType === "professor").length;
  const labs = records.filter((record) => record.recordType === "lab").length;
  const resources = records.filter((record) => record.recordType === "resource").length;
  const recruiting = records.filter((record) => record.recruitingStatus === "Recruiting").length;
  const verified = records.filter((record) => academicMetrics(record).verified).length;

  els.resultSummary.replaceChildren(
    makeResultSummaryItem("Professors", professors),
    makeResultSummaryItem("Labs", labs),
    makeResultSummaryItem("REAL", resources),
    makeResultSummaryItem("Recruiting", recruiting),
    makeResultSummaryItem("Verified", verified),
  );
}

function makeResultSummaryItem(label, value) {
  const item = document.createElement("span");
  const number = document.createElement("strong");
  number.textContent = numberLabel(value);
  const text = document.createElement("span");
  text.textContent = label;
  item.append(number, text);
  return item;
}

function renderActiveFilters() {
  const filters = [];
  if (state.type !== "all") filters.push(["Type", slugLabel(state.type)]);
  if (state.department !== "all") filters.push(["Department", state.department]);
  if (state.area !== "all") filters.push(["Area", state.area]);
  if (state.recruiting !== "all") filters.push(["Recruiting", state.recruiting]);
  if (state.institution !== "all") filters.push(["University", state.institution]);
  if (state.verifiedOnly) filters.push(["Metrics", "Verified only"]);
  if (state.sort !== "relevance") filters.push(["Sort", slugLabel(state.sort)]);

  els.activeFilters.hidden = !filters.length;
  els.activeFilters.replaceChildren(
    ...filters.map(([label, value, key]) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.dataset.filterKey = key || label.toLowerCase();
      chip.textContent = `${label}: ${value}`;
      return chip;
    }),
  );
}

function syncControlsFromState() {
  els.query.value = state.query;
  els.recruiting.value = state.recruiting;
  els.institution.value = state.institution;
  els.department.value = state.department;
  els.area.value = state.area;
  els.sort.value = state.sort;
}

function clearFilter(key) {
  if (key === "type") state.type = "all";
  if (key === "department") state.department = "all";
  if (key === "area") state.area = "all";
  if (key === "recruiting") state.recruiting = "all";
  if (key === "university") state.institution = "all";
  if (key === "metrics") state.verifiedOnly = false;
  if (key === "sort") state.sort = "relevance";
  state.visibleLimit = PAGE_SIZE;
  syncControlsFromState();
  if (key === "area") renderFacets();
  render();
}

function renderMetrics() {
  const professors = state.records.filter((record) => record.recordType === "professor").length;
  const labs = state.records.filter((record) => record.recordType === "lab").length;
  const resources = state.records.filter((record) => record.recordType === "resource").length;
  const sources = unique(state.records.flatMap((record) => record.sourceUrls || [])).length;
  const verified = state.records.reduce((sum, record) => sum + Number(record.sourceUrls?.length || 0), 0);

  animateMetricCount(els.professorCount, professors);
  animateMetricCount(els.labCount, labs);
  animateMetricCount(els.realResourceCount, resources);
  animateMetricCount(els.sourceCount, sources);
  animateMetricCount(els.verifiedCount, verified);

  const date = state.data?.generatedAt ? new Date(state.data.generatedAt) : null;
  els.updatedAt.textContent = date && !Number.isNaN(date.valueOf())
    ? `Updated ${date.toLocaleDateString()}`
    : "Using bundled sample data";
}

function toggleSaved(id) {
  if (state.saved.has(id)) state.saved.delete(id);
  else state.saved.add(id);
  localStorage.setItem("researchAtlasSaved", JSON.stringify([...state.saved]));
  render();
}

function renderSaved() {
  const savedRecords = [...state.saved]
    .map((id) => state.records.find((record) => record.id === id))
    .filter(Boolean);

  els.savedCount.textContent = savedRecords.length;
  if (!savedRecords.length) {
    const empty = document.createElement("p");
    empty.className = "updated-at";
    empty.textContent = "No saved entries yet.";
    els.savedList.replaceChildren(empty);
    return;
  }

  els.savedList.replaceChildren(
    ...savedRecords.map((record) => {
      const item = document.createElement("a");
      item.className = "saved-item";
      item.href = "#";
      item.innerHTML = "<strong></strong><span></span>";
      item.querySelector("strong").textContent = record.displayName;
      item.querySelector("span").textContent = record.displayKind;
      item.addEventListener("click", (event) => {
        event.preventDefault();
        openDrawer(record.id);
      });
      return item;
    }),
  );
}

function field(label, value) {
  const wrapper = document.createElement("div");
  wrapper.className = "drawer-field";
  const labelNode = document.createElement("span");
  labelNode.textContent = label;
  wrapper.appendChild(labelNode);

  if (isKnown(value) && /^https?:\/\//.test(String(value))) {
    const link = document.createElement("a");
    link.href = value;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = value;
    wrapper.appendChild(link);
  } else {
    const strong = document.createElement("strong");
    strong.textContent = Array.isArray(value) ? value.join(", ") : valueOrFallback(value);
    wrapper.appendChild(strong);
  }

  return wrapper;
}

function section(title, child) {
  const wrapper = document.createElement("section");
  wrapper.className = "drawer-section";
  const heading = document.createElement("h3");
  heading.textContent = title;
  wrapper.append(heading, child);
  return wrapper;
}

function linkList(items) {
  const list = document.createElement("ul");
  list.className = "link-list";
  list.replaceChildren(
    ...items.map(([label, url]) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = url;
      a.target = "_blank";
      a.rel = "noreferrer";
      a.textContent = `${label}: ${url}`;
      li.appendChild(a);
      return li;
    }),
  );
  return list;
}

function sourceList(urls) {
  const list = document.createElement("ul");
  list.className = "source-list";
  list.replaceChildren(
    ...urls.map((url) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = url;
      a.target = "_blank";
      a.rel = "noreferrer";
      a.textContent = url;
      li.appendChild(a);
      return li;
    }),
  );
  return list;
}

function publicationList(publications) {
  const list = document.createElement("ul");
  list.className = "publication-list";
  list.replaceChildren(
    ...(publications.length ? publications : [{ title: NOT_FOUND }]).map((paper) => {
      const li = document.createElement("li");
      const title = isKnown(paper.url) ? document.createElement("a") : document.createElement("strong");
      if (isKnown(paper.url)) {
        title.href = paper.url;
        title.target = "_blank";
        title.rel = "noreferrer";
      }
      title.textContent = cleanText(paper.title) || NOT_FOUND;
      const meta = document.createElement("span");
      meta.textContent = [
        paper.publicationDate || paper.year,
        paper.venue,
        isKnown(paper.citationCount) ? `${numberLabel(paper.citationCount)} citations` : "",
      ]
        .filter(isKnown)
        .join(" / ");
      li.append(title, meta);
      return li;
    }),
  );
  return list;
}

function detailFieldList(fields) {
  const list = document.createElement("div");
  list.className = "detail-field-list";
  const entries = Object.entries(fields || {});
  list.replaceChildren(
    ...(entries.length ? entries : [["Details", NOT_FOUND]]).map(([label, value]) => {
      const item = document.createElement("div");
      item.className = "drawer-field";
      const key = document.createElement("span");
      key.textContent = label;
      const body = document.createElement("p");
      body.textContent = value;
      item.append(key, body);
      return item;
    }),
  );
  return list;
}

function animateDrawerOpen() {
  const gsap = gsapCore();
  if (!gsap || prefersReducedMotion()) return;

  const panel = els.drawer.querySelector(".drawer-panel");
  const scrim = els.drawer.querySelector(".drawer-scrim");
  const content = [...els.drawerContent.children];
  gsap.killTweensOf([panel, scrim, ...content]);
  gsap.fromTo(scrim, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.22, ease: "power1.out" });
  gsap.fromTo(panel, { x: 44, autoAlpha: 0 }, { x: 0, autoAlpha: 1, duration: 0.42, ease: "power3.out" });
  gsap.fromTo(
    content,
    { y: 12, autoAlpha: 0 },
    { y: 0, autoAlpha: 1, duration: 0.34, delay: 0.1, stagger: 0.035, ease: "power2.out" },
  );
}

function finishDrawerClose() {
  const gsap = gsapCore();
  const panel = els.drawer.querySelector(".drawer-panel");
  const scrim = els.drawer.querySelector(".drawer-scrim");
  els.drawer.classList.remove("is-open");
  els.drawer.hidden = true;
  if (gsap) gsap.set([panel, scrim, ...els.drawerContent.children], { clearProps: "all" });
}

function openDrawer(id) {
  const record = state.records.find((item) => item.id === id);
  if (!record) return;
  state.activeRecord = record;

  const root = document.createDocumentFragment();
  const heading = document.createElement("div");
  heading.className = "drawer-heading";
  const label = document.createElement("p");
  label.className = "eyebrow-label";
  label.textContent = `${record.displayKind} - ${record.recruitingStatus || UNKNOWN}`;
  const title = document.createElement("h2");
  title.id = "drawerTitle";
  title.textContent = record.displayName;
  const summary = document.createElement("p");
  summary.className = "summary";
  summary.textContent = record.summary;
  heading.append(label, title, summary);

  const grid = document.createElement("div");
  grid.className = "drawer-grid";
  if (record.recordType === "professor") {
    const metrics = academicMetrics(record);
    const academic = metrics.profile;
    grid.append(
      field("University", record.institution),
      field("Department", record.department),
      field("Email", record.email),
      field("Lab affiliation", record.labAffiliation),
      field("Faculty profile", record.officialProfileUrl),
      field("Personal website", record.personalWebsiteUrl),
      field("Google Scholar", record.googleScholarUrl),
      field("Scholar search", record.googleScholarSearchUrl),
      field("OpenAlex", academic.openAlexUrl),
      field("Metric status", metrics.status),
      field("Citations", metrics.verified ? academic.citationCount : (metrics.hasMetrics ? "Hidden until match is reviewed" : UNKNOWN)),
      field("Works", metrics.verified ? academic.worksCount : (metrics.hasMetrics ? "Hidden until match is reviewed" : UNKNOWN)),
      field("h-index", metrics.verified ? academic.hIndex : (metrics.hasMetrics ? "Hidden until match is reviewed" : UNKNOWN)),
      field("Last verified", record.lastVerified),
    );
  } else if (record.recordType === "lab") {
    grid.append(
      field("University", record.institution),
      field("Department", record.department),
      field("Principal investigator", record.principalInvestigator),
      field("Contact email", record.email),
      field("Lab website", record.labWebsiteUrl),
      field("Last verified", record.lastVerified),
    );
  } else {
    grid.append(
      field("University", record.institution),
      field("Organization", record.organization),
      field("Resource type", record.resourceType),
      field("Year", record.yearOfActivity),
      field("Application", record.applicationProcedure),
      field("Contact email", record.email),
      field("REAL Portal", record.sourceUrl),
      field("Last verified", record.lastVerified),
    );
  }

  const recruitment = document.createElement("p");
  recruitment.className = "summary";
  recruitment.textContent = record.recruitingEvidence?.text
    ? `${record.recruitingStatus}: ${record.recruitingEvidence.text}`
    : `${record.recruitingStatus || UNKNOWN}: no explicit public recruiting statement is captured for this entry.`;

  root.append(
    heading,
    grid,
    section("Research areas", linkFreeList(record.researchAreas || [])),
  );

  if (record.recordType === "professor") {
    const metrics = academicMetrics(record);
    const publications = metrics.verified ? relevantPublications(record) : [];
    root.appendChild(section("Recent publications", publicationList(publications)));
    root.appendChild(section("Recruitment evidence", recruitment));
  } else if (record.recordType === "resource") {
    root.appendChild(section("REAL Portal details", detailFieldList(record.detailFields || { Description: record.summary })));
  } else {
    root.appendChild(section("Recruitment evidence", recruitment));
  }

  if (record.links.length) root.appendChild(section("Useful links", linkList(record.links)));
  root.appendChild(section("Source URLs", sourceList(record.sourceUrls || [])));

  els.drawerContent.replaceChildren(root);
  els.drawer.hidden = false;
  els.drawer.classList.add("is-open");
  els.drawer.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
  animateDrawerOpen();
}

function linkFreeList(items) {
  const tags = document.createElement("div");
  tags.className = "tag-list";
  tags.replaceChildren(...(items.length ? items : [NOT_FOUND]).map(makeTag));
  return tags;
}

function closeDrawer() {
  const gsap = gsapCore();
  const panel = els.drawer.querySelector(".drawer-panel");
  const scrim = els.drawer.querySelector(".drawer-scrim");
  els.drawer.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  state.activeRecord = null;

  if (gsap && !prefersReducedMotion()) {
    gsap.killTweensOf([panel, scrim]);
    gsap.to(panel, { x: 38, autoAlpha: 0, duration: 0.26, ease: "power2.in" });
    gsap.to(scrim, { autoAlpha: 0, duration: 0.2, ease: "power1.out", onComplete: finishDrawerClose });
    return;
  }

  els.drawer.classList.remove("is-open");
  window.setTimeout(() => {
    if (!els.drawer.classList.contains("is-open")) els.drawer.hidden = true;
  }, 220);
}

function addRipple(target, event) {
  const rect = target.getBoundingClientRect();
  const ripple = document.createElement("span");
  ripple.className = "ripple";
  ripple.style.left = `${event.clientX - rect.left}px`;
  ripple.style.top = `${event.clientY - rect.top}px`;
  target.appendChild(ripple);
  ripple.addEventListener("animationend", () => ripple.remove(), { once: true });
}

function resetCardMotion(card) {
  const gsap = gsapCore();
  if (gsap && !prefersReducedMotion()) {
    gsap.to(card, {
      "--card-x": "50%",
      "--card-y": "50%",
      duration: 0.34,
      ease: "power2.out",
    });
    return;
  }

  card.style.setProperty("--card-x", "50%");
  card.style.setProperty("--card-y", "50%");
}

function initMotionInteractions() {
  const reduceMotion = prefersReducedMotion();
  if (reduceMotion) return;
  const gsap = gsapCore();

  let pointerTimer = 0;
  document.addEventListener("pointermove", (event) => {
    if (event.pointerType === "touch") return;

    document.documentElement.style.setProperty("--pointer-x", `${event.clientX}px`);
    document.documentElement.style.setProperty("--pointer-y", `${event.clientY}px`);
    document.body.classList.add("is-pointer-active");
    window.clearTimeout(pointerTimer);
    pointerTimer = window.setTimeout(() => document.body.classList.remove("is-pointer-active"), 900);

    if (els.hero?.contains(event.target)) {
      const rect = els.hero.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      if (gsap) {
        gsap.to(els.hero, {
          "--hero-pan-x": `${x * 22}px`,
          "--hero-pan-y": `${y * 14}px`,
          duration: 0.45,
          ease: "power2.out",
        });
      } else {
        els.hero.style.setProperty("--hero-pan-x", `${x * 18}px`);
        els.hero.style.setProperty("--hero-pan-y", `${y * 12}px`);
      }
    }

    const card = event.target.closest("[data-interactive-card]");
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const xPercent = (x / rect.width) * 100;
    const yPercent = (y / rect.height) * 100;
    if (gsap) {
      gsap.to(card, {
        "--card-x": `${xPercent}%`,
        "--card-y": `${yPercent}%`,
        duration: 0.24,
        ease: "power2.out",
      });
    } else {
      card.style.setProperty("--card-x", `${xPercent}%`);
      card.style.setProperty("--card-y", `${yPercent}%`);
    }
  });

  els.hero?.addEventListener("pointerleave", () => {
    if (gsap) {
      gsap.to(els.hero, { "--hero-pan-x": "0px", "--hero-pan-y": "0px", duration: 0.5, ease: "power2.out" });
    } else {
      els.hero.style.setProperty("--hero-pan-x", "0px");
      els.hero.style.setProperty("--hero-pan-y", "0px");
    }
  });

  document.addEventListener("pointerout", (event) => {
    const card = event.target.closest?.("[data-interactive-card]");
    if (card && !card.contains(event.relatedTarget)) resetCardMotion(card);
  });

  document.addEventListener("click", (event) => {
    const target = event.target.closest(
      ".primary-action, .quick-actions button, .panel-head button, .drawer-close, .save-button, .link-button, .details-button, .chip, .segment, .load-more, .top-links a, .active-filters button",
    );
    if (!target) return;
    addRipple(target, event);
  });
}

function applyStateFromControls() {
  state.query = els.query.value;
  state.recruiting = els.recruiting.value;
  state.institution = els.institution.value;
  state.department = els.department.value;
  state.area = els.area.value;
  state.sort = els.sort.value;
}

function applySmartFilter(key) {
  if (key === "recruiting") {
    state.recruiting = state.recruiting === "Recruiting" ? "all" : "Recruiting";
  }
  if (key === "verified") {
    const nextVerified = !state.verifiedOnly;
    state.verifiedOnly = nextVerified;
    if (nextVerified) {
      state.type = "professor";
      state.sort = "citations";
    } else if (state.sort === "citations") {
      state.sort = "relevance";
    }
  }
  if (["professor", "lab", "resource"].includes(key)) {
    state.type = state.type === key && !state.verifiedOnly ? "all" : key;
    if (key !== "professor") state.verifiedOnly = false;
  }
  state.visibleLimit = PAGE_SIZE;
  syncControlsFromState();
  render();
}

async function loadData() {
  const response = await fetch(DATA_URL, DATA_FETCH_OPTIONS);
  if (!response.ok) throw new Error(`Could not load ${DATA_URL}: ${response.status}`);
  const data = await response.json();
  const realResponse = await fetch(REAL_PORTAL_DATA_URL, DATA_FETCH_OPTIONS).catch(() => null);
  const realPortalData = realResponse?.ok ? await realResponse.json() : null;
  state.data = data;
  state.records = buildRecords(data, realPortalData);
  state.index = buildIndex(state.records);
  renderFacets();
  renderMetrics();
  render();
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  animateSearchFeedback();
  applyStateFromControls();
  state.visibleLimit = PAGE_SIZE;
  renderFacets();
  render();
});

[els.query, els.recruiting, els.institution, els.department, els.area, els.sort].forEach((control) => {
  control.addEventListener(control === els.query ? "input" : "change", () => {
    applyStateFromControls();
    state.visibleLimit = PAGE_SIZE;
    if (control === els.area) renderFacets();
    render();
  });
});

els.typeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    state.type = button.dataset.typeChoice || "all";
    if (state.type !== "professor") state.verifiedOnly = false;
    state.visibleLimit = PAGE_SIZE;
    render();
  });
});

els.smartFilterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    applySmartFilter(button.dataset.smartFilter);
  });
});

els.activeFilters.addEventListener("click", (event) => {
  const chip = event.target.closest("[data-filter-key]");
  if (!chip) return;
  clearFilter(chip.dataset.filterKey);
});

els.clear.addEventListener("click", () => {
  state.query = "";
  state.type = "all";
  state.institution = "all";
  state.department = "all";
  state.area = "all";
  state.recruiting = "all";
  state.verifiedOnly = false;
  state.sort = "relevance";
  state.visibleLimit = PAGE_SIZE;
  syncControlsFromState();
  renderFacets();
  render();
});

els.loadMore.addEventListener("click", () => {
  state.visibleLimit += PAGE_SIZE;
  render();
});

document.querySelectorAll("[data-close-drawer]").forEach((node) => {
  node.addEventListener("click", closeDrawer);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && state.activeRecord) closeDrawer();
});

initGsapMotion();
initMotionInteractions();

loadData().catch((error) => {
  els.heading.textContent = "Data unavailable";
  els.updatedAt.textContent = error.message;
  els.results.replaceChildren();
  els.empty.hidden = false;
  els.empty.textContent = "The data file could not be loaded. Run a local server and check data/research-atlas.json.";
});
