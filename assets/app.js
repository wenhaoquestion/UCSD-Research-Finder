const DATA_URL = "data/research-atlas.json";
const REAL_PORTAL_DATA_URL = "data/ucsd/real-portal-resources.json";
const NOT_FOUND = "Not found";
const UNKNOWN = "Unknown";
const PAGE_SIZE = 80;

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
  sort: "relevance",
  visibleLimit: PAGE_SIZE,
  saved: new Set(JSON.parse(localStorage.getItem("researchAtlasSaved") || "[]")),
  activeRecord: null,
};

const els = {
  form: document.querySelector("#searchForm"),
  query: document.querySelector("#query"),
  type: document.querySelector("#typeFilter"),
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
  return Boolean(value && value !== NOT_FOUND && value !== UNKNOWN);
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
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
  const professors = (data.professors || []).map((item) => {
    const displayName = valueOrFallback(item.name);
    return {
      ...item,
      recordType: "professor",
      displayName,
      displayKind: "Professor",
      affiliationLine: [item.institution, item.department].filter(isKnown).join(" · "),
      summary: valueOrFallback(item.researchSummary),
      email: valueOrFallback(item.email),
      researchAreas: item.researchAreas || [],
      sourceUrls: item.sourceUrls || [],
      links: professorLinks(item),
    };
  });

  const labs = (data.labs || []).map((item) => {
    const displayName = valueOrFallback(item.labName);
    return {
      ...item,
      recordType: "lab",
      displayName,
      displayKind: slugLabel(item.recordSubtype || "lab"),
      affiliationLine: [item.institution, item.department].filter(isKnown).join(" · "),
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
      affiliationLine: [item.resourceType, item.organization].filter(isKnown).join(" · "),
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
    .slice(0, 14);

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
    if (state.sort === "sources") {
      return b.record.sourceUrls.length - a.record.sourceUrls.length || a.record.displayName.localeCompare(b.record.displayName);
    }
    return b.score - a.score || a.record.displayName.localeCompare(b.record.displayName);
  });

  return rows.map((row) => row.record);
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

function recordMetaLine(record) {
  const parts = [];
  if (record.recordType === "professor") {
    const academic = record.academicProfile || {};
    if (isKnown(academic.citationCount)) parts.push(`${numberLabel(academic.citationCount)} citations`);
    if (isKnown(academic.worksCount)) parts.push(`${numberLabel(academic.worksCount)} works`);
    if (isKnown(academic.hIndex)) parts.push(`h-index ${numberLabel(academic.hIndex)}`);
  } else if (record.recordType === "resource") {
    if (isKnown(record.yearOfActivity)) parts.push(record.yearOfActivity);
    if (isKnown(record.applicationProcedure)) parts.push(record.applicationProcedure);
  }
  if (!parts.length) return null;
  const meta = document.createElement("p");
  meta.className = "record-meta-line";
  meta.textContent = parts.join(" · ");
  return meta;
}

function renderCard(record, position) {
  const fragment = els.template.content.cloneNode(true);
  const card = fragment.querySelector(".result-card");
  const typeBadge = fragment.querySelector(".type-badge");
  const statusBadge = fragment.querySelector(".status-badge");
  const title = fragment.querySelector("h3");
  const affiliation = fragment.querySelector(".card-affiliation");
  const save = fragment.querySelector(".save-button");
  const summary = fragment.querySelector(".summary");
  const email = fragment.querySelector(".email-row");
  const tags = fragment.querySelector(".tag-list");
  const actions = fragment.querySelector(".card-actions");

  card.style.animationDelay = `${Math.min(position, 10) * 24}ms`;
  typeBadge.textContent = record.displayKind;
  statusBadge.textContent = record.recruitingStatus || UNKNOWN;
  statusBadge.classList.add(statusClass(record.recruitingStatus));
  title.textContent = record.displayName;
  affiliation.textContent = record.affiliationLine || record.institution || NOT_FOUND;
  summary.textContent = record.summary;

  save.textContent = state.saved.has(record.id) ? "Saved" : "Save";
  save.classList.toggle("is-saved", state.saved.has(record.id));
  save.addEventListener("click", () => toggleSaved(record.id));

  email.replaceChildren(makeEmail(record));
  const meta = recordMetaLine(record);
  if (meta) email.after(meta);
  tags.replaceChildren(...(record.researchAreas || []).slice(0, 7).map(makeTag));

  const primary = record.links[0];
  const actionNodes = [];
  if (primary) actionNodes.push(makeLink(primary[0], primary[1], "primary-link"));

  const details = document.createElement("button");
  details.className = "details-button";
  details.type = "button";
  details.textContent = `Sources (${record.sourceUrls.length})`;
  details.addEventListener("click", () => openDrawer(record.id));
  actionNodes.push(details);

  actions.replaceChildren(...actionNodes);
  return fragment;
}

function render() {
  const records = filteredRecords();
  const visible = records.slice(0, state.visibleLimit);
  const shown = Math.min(visible.length, records.length);
  els.heading.textContent = records.length
    ? `${records.length} ${records.length === 1 ? "match" : "matches"} · showing ${shown}`
    : "0 matches";
  els.empty.hidden = records.length !== 0;
  els.loadMore.hidden = shown >= records.length;
  els.loadMore.textContent = `Load more (${records.length - shown} remaining)`;

  if (!records.length) {
    els.results.replaceChildren();
    renderSaved();
    return;
  }

  const fragment = document.createDocumentFragment();
  visible.forEach((record, index) => fragment.appendChild(renderCard(record, index)));
  els.results.replaceChildren(fragment);
  renderSaved();
}

function renderMetrics() {
  const professors = state.records.filter((record) => record.recordType === "professor").length;
  const labs = state.records.filter((record) => record.recordType === "lab").length;
  const resources = state.records.filter((record) => record.recordType === "resource").length;
  const sources = unique(state.records.flatMap((record) => record.sourceUrls || [])).length;
  const verified = state.records.reduce((sum, record) => sum + Number(record.sourceUrls?.length || 0), 0);

  els.professorCount.textContent = professors;
  els.labCount.textContent = labs;
  els.realResourceCount.textContent = resources;
  els.sourceCount.textContent = sources;
  els.verifiedCount.textContent = verified;

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
      title.textContent = paper.title || NOT_FOUND;
      const meta = document.createElement("span");
      meta.textContent = [
        paper.publicationDate || paper.year,
        paper.venue,
        isKnown(paper.citationCount) ? `${numberLabel(paper.citationCount)} citations` : "",
      ]
        .filter(isKnown)
        .join(" · ");
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

function openDrawer(id) {
  const record = state.records.find((item) => item.id === id);
  if (!record) return;
  state.activeRecord = record;

  const root = document.createDocumentFragment();
  const heading = document.createElement("div");
  heading.className = "drawer-heading";
  const label = document.createElement("p");
  label.className = "eyebrow-label";
  label.textContent = `${record.displayKind} · ${record.recruitingStatus || UNKNOWN}`;
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
    const academic = record.academicProfile || {};
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
      field("Citations", academic.citationCount),
      field("Works", academic.worksCount),
      field("h-index", academic.hIndex),
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
    const publications = record.academicProfile?.recentPublications || [];
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
  els.drawer.classList.add("is-open");
  els.drawer.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function linkFreeList(items) {
  const tags = document.createElement("div");
  tags.className = "tag-list";
  tags.replaceChildren(...(items.length ? items : [NOT_FOUND]).map(makeTag));
  return tags;
}

function closeDrawer() {
  els.drawer.classList.remove("is-open");
  els.drawer.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  state.activeRecord = null;
}

function applyStateFromControls() {
  state.query = els.query.value;
  state.type = els.type.value;
  state.recruiting = els.recruiting.value;
  state.institution = els.institution.value;
  state.department = els.department.value;
  state.area = els.area.value;
  state.sort = els.sort.value;
}

async function loadData() {
  const response = await fetch(DATA_URL, { credentials: "omit" });
  if (!response.ok) throw new Error(`Could not load ${DATA_URL}: ${response.status}`);
  const data = await response.json();
  const realResponse = await fetch(REAL_PORTAL_DATA_URL, { credentials: "omit" }).catch(() => null);
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
  applyStateFromControls();
  state.visibleLimit = PAGE_SIZE;
  renderFacets();
  render();
});

[els.query, els.type, els.recruiting, els.institution, els.department, els.area, els.sort].forEach((control) => {
  control.addEventListener(control === els.query ? "input" : "change", () => {
    applyStateFromControls();
    state.visibleLimit = PAGE_SIZE;
    if (control === els.area) renderFacets();
    render();
  });
});

els.clear.addEventListener("click", () => {
  state.query = "";
  state.type = "all";
  state.institution = "all";
  state.department = "all";
  state.area = "all";
  state.recruiting = "all";
  state.sort = "relevance";
  state.visibleLimit = PAGE_SIZE;
  els.query.value = "";
  els.type.value = "all";
  els.recruiting.value = "all";
  els.institution.value = "all";
  els.department.value = "all";
  els.area.value = "all";
  els.sort.value = "relevance";
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

loadData().catch((error) => {
  els.heading.textContent = "Data unavailable";
  els.updatedAt.textContent = error.message;
  els.results.replaceChildren();
  els.empty.hidden = false;
  els.empty.textContent = "The data file could not be loaded. Run a local server and check data/research-atlas.json.";
});
