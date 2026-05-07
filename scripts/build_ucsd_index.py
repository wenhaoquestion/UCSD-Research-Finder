#!/usr/bin/env python3
"""Build the static UCSD research index.

The crawler intentionally starts narrow: public UCSD pages, robots.txt checks,
rate limiting, and curated records for pages whose markup differs by department.
"""

from __future__ import annotations

import datetime as dt
import concurrent.futures
import hashlib
import html
import json
import os
import re
import ssl
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "ucsd"
SOURCES_PATH = DATA_DIR / "sources.json"
DEPARTMENTS_PATH = DATA_DIR / "departments.json"
CANDIDATES_PATH = DATA_DIR / "source-candidates.json"
MANUAL_PATH = DATA_DIR / "manual-records.json"
OVERRIDES_PATH = DATA_DIR / "curated-overrides.json"
OUTPUT_PATH = DATA_DIR / "research-index.json"
PROFILE_CACHE_PATH = DATA_DIR / "profile-enrichment-cache.json"

USER_AGENT = "ucsd-research-finder/0.1 (+https://github.com/)"
REQUEST_DELAY_SECONDS = 0.2
MAX_PAGE_BYTES = 700_000
PERSONAL_SITE_TIMEOUT_SECONDS = 4
PERSONAL_SITE_WORKERS = 10
ROBOTS_TIMEOUT_SECONDS = 2
GENERIC_FACULTY_TIMEOUT_SECONDS = 8
GENERIC_FACULTY_WORKERS = int(os.environ.get("RESEARCH_FINDER_GENERIC_WORKERS", "6"))
GENERIC_FACULTY_DEPARTMENT_LIMIT = int(os.environ.get("RESEARCH_FINDER_GENERIC_LIMIT", "0"))
GENERIC_LAB_TIMEOUT_SECONDS = int(os.environ.get("RESEARCH_FINDER_LAB_TIMEOUT", "4"))
GENERIC_LAB_WORKERS = int(os.environ.get("RESEARCH_FINDER_LAB_WORKERS", "6"))
GENERIC_LAB_DEPARTMENT_LIMIT = int(os.environ.get("RESEARCH_FINDER_LAB_LIMIT", "0"))
GENERIC_RESEARCH_AREA_DEPARTMENT_LIMIT = int(os.environ.get("RESEARCH_FINDER_RESEARCH_AREA_LIMIT", "0"))
PROFILE_ENRICH_TIMEOUT_SECONDS = 8
PROFILE_ENRICH_WORKERS = int(os.environ.get("RESEARCH_FINDER_PROFILE_WORKERS", "10"))
PROFILE_ENRICH_LIMIT = int(os.environ.get("RESEARCH_FINDER_PROFILE_LIMIT", "0"))

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]*ucsd\.edu")
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")
WHITESPACE_RE = re.compile(r"\s+")

SKIP_PERSONAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "scholar.google.com",
    "twitter.com",
    "vimeo.com",
    "x.com",
    "youtube.com",
}
EXCLUDED_EMAIL_LOCALS = {
    "communication",
    "feedback",
    "info",
    "support",
    "webmaster",
}

INTEREST_KEYWORDS = {
    "Addiction": ["addiction", "substance use"],
    "AI": ["artificial intelligence", " ai ", "large language model", "llm"],
    "Aging": ["aging", "ageing", "older adults"],
    "Algorithms": ["algorithm", "complexity", "optimization"],
    "Alzheimer's disease": ["alzheimer", "dementia"],
    "Autism": ["autism", "autistic"],
    "Bioinformatics": ["bioinformatics", "genomics", "genome", "microbiome"],
    "Cancer biology": ["cancer", "tumor", "tumour", "oncology"],
    "Cardiovascular": ["cardiovascular", "cardiology", "heart", "vascular"],
    "Cell biology": ["cell biology", "cellular", "cell signaling", "cell signalling"],
    "Clinical research": ["clinical research", "clinical trial", "clinical trials", "patient"],
    "Computer architecture": ["architecture", "processor", "hardware", "compiler"],
    "Computer graphics": ["graphics", "rendering", "visualization"],
    "Computer vision": ["computer vision", "vision", "image", "3d"],
    "Cryptography": ["cryptography", "crypto", "privacy", "security proof"],
    "Data management": ["data management", "database", "databases", "data systems"],
    "Data mining": ["data mining", "knowledge discovery"],
    "Deep learning": ["deep learning", "neural network", "neural networks"],
    "Developmental biology": ["developmental biology", "developmental", "embryo"],
    "Ecology": ["ecology", "ecosystem", "biodiversity"],
    "Dark matter": ["dark matter"],
    "Embedded systems": ["embedded", "sensor", "iot", "fpga"],
    "Epidemiology": ["epidemiology", "population health"],
    "Experimental physics": ["experimental physics", "detector", "detectors"],
    "Epilepsy": ["epilepsy", "seizure", "seizures"],
    "Genetics": ["genetics", "genetic", "neurogenetics"],
    "Geometric deep learning": ["geometric deep learning"],
    "Health": ["health", "healthcare", "medical", "medicine", "clinical"],
    "Human-computer interaction": ["human-computer interaction", "hci", "interaction", "user experience"],
    "Imaging": ["imaging", "microscopy", "mri", "neuroimaging"],
    "Immunology": ["immunology", "immune", "inflammation", "neuro-immunology"],
    "Infectious disease": ["infectious disease", "infection", "virus", "viral", "pathogen"],
    "Machine learning": ["machine learning", "ml", "learning theory"],
    "Marine science": ["marine", "ocean", "oceanography"],
    "Memory": ["memory", "learning and memory"],
    "Microbiology": ["microbiology", "microbiome", "bacteria", "microbial"],
    "Natural language processing": ["natural language", "nlp", "language model"],
    "Neurodegeneration": ["neurodegeneration", "neurodegenerative", "parkinson", "als"],
    "Neuroimaging": ["neuroimaging", "brain imaging", "neurovascular"],
    "Neuroscience": ["neuroscience", "neural", "neuron", "brain"],
    "Networking": ["network", "networking", "internet", "wireless"],
    "Neutrinos": ["neutrino", "neutrinos"],
    "Particle physics": ["particle physics"],
    "Programming languages": ["programming language", "program synthesis", "formal methods", "verification"],
    "Public health": ["public health", "health equity", "health policy"],
    "Radiation detectors": ["radiation detector", "radiation detectors"],
    "Robotics": ["robot", "robotics", "autonomous"],
    "Security": ["security", "cybersecurity", "malware", "vulnerability"],
    "Software engineering": ["software engineering", "developer", "programming tools"],
    "Systems": ["systems", "operating system", "distributed", "cloud"],
    "Theory": ["theory", "theoretical", "complexity"],
    "Time series": ["time series", "time-series"],
    "Ubiquitous computing": ["ubiquitous", "wearable", "mobile computing"],
}

METHOD_KEYWORDS = {
    "Causal analysis": ["causal", "causality"],
    "Clinical trials": ["clinical trial", "clinical trials"],
    "Data science": ["data science", "data-driven"],
    "Deep learning": ["deep learning", "neural"],
    "Detector development": ["detector", "detectors"],
    "Field studies": ["field study", "field studies", "deployment"],
    "Formal methods": ["formal methods", "verification", "proof"],
    "Human subjects research": ["human subjects", "user study", "participants"],
    "Large-scale data analysis": ["large-scale", "big data", "data mining"],
    "Machine learning": ["machine learning", "model"],
    "Microscopy": ["microscopy", "microscope"],
    "Measurement": ["measurement", "empirical"],
    "Neuroimaging": ["neuroimaging", "brain imaging", "mri"],
    "Robotics": ["robotics", "robot"],
    "Self-supervised learning": ["self-supervised", "self supervised"],
    "Simulation": ["simulation", "simulator"],
    "Systems research": ["systems", "distributed", "operating system"],
    "Time series analysis": ["time series", "time-series"],
    "Tool building": ["tool", "platform", "software"],
    "Wet lab": ["wet lab", "cell culture", "assay", "sequencing"],
}

ROLE_SECTIONS = {
    "Faculty": "faculty",
    "Department Leadership": "faculty",
    "Continuing Lecturers": "faculty",
    "Lecturers": "faculty",
    "Researchers": "faculty",
    "Researcher": "faculty",
    "Adjunct": "faculty",
    "Affiliated": "faculty",
}

FACULTY_TITLE_RE = re.compile(
    r"\b(?:Associate Teaching Professor|Assistant Teaching Professor|Teaching Professor|Associate Professor|Assistant Professor|Professor|Lecturer|Research Scientist|Faculty)\b",
    re.I,
)
FACULTY_URL_RE = re.compile(r"/(?:people|faculty|profiles?|directory|research/faculty|faculty-research)/", re.I)
BAD_NAME_WORDS = {
    "About",
    "Accessibility",
    "Admissions",
    "Alumni",
    "Contact",
    "Contact Us",
    "Courses",
    "Directory",
    "Education",
    "Events",
    "Faculty",
    "Faculty Directory",
    "Faculty Members",
    "Faculty Profile",
    "Faculty Profiles",
    "Graduate",
    "Home",
    "Labs",
    "News",
    "Office Hours",
    "People",
    "Pediatric Urologists",
    "Programs",
    "Research",
    "Resources",
    "Staff",
    "Students",
    "Undergraduate",
    "WWW",
}
BAD_NAME_TERMS = {
    "about",
    "academic advising",
    "academic affairs",
    "academic profile",
    "academic open positions",
    "accreditation",
    "administration",
    "admissions",
    "advising",
    "affiliated organization",
    "alumni",
    "annual report",
    "apply",
    "at a glance",
    "american politics",
    "available research talent",
    "award",
    "calendar",
    "class photos",
    "clinical profile",
    "contact",
    "course",
    "current students",
    "dean's message",
    "department",
    "directory",
    "emergency plan",
    "facility",
    "facilities",
    "adjunct faculty",
    "faculty recruitment",
    "funding",
    "global surgery",
    "grand rounds",
    "graduate resources",
    "learn more",
    "lecturer",
    "lab ",
    "laborator",
    "mission",
    "newsletter",
    "news",
    "honor",
    "open positions",
    "open recruitment",
    "organization",
    "photo",
    "plastic surgery",
    "practice",
    "preceptor",
    "program",
    "research profile",
    "research symposium",
    "research teams",
    "resources",
    "humans of surgery",
    "surgical sciences",
    "support team",
    "student",
    "terms",
    "undergrad",
    "ucsd profile",
    "update your ucsd profile",
}
GENERIC_PROFILE_LINK_LABELS = {
    "academic profile",
    "academic profile |",
    "clinical profile",
    "full profile",
    "profile",
    "research profile",
    "ucsd profile",
}
GENERIC_PROFILE_SKIP_LABELS = {
    "clinical trial",
    "clinical trials",
}
PERSON_PROFILE_URL_RE = re.compile(
    r"(?:profiles\.ucsd\.edu/|/people/profile/|/faculty/profile|/faculty-directory/|/faculty_bios/|/profiles/[^/]+|/people/faculty/[^/]+|/research/faculty/[^/]+|/faculty/Pages/[^/]+)",
    re.I,
)
DIRECTORY_CATEGORY_RE = re.compile(
    r"/(?:faculty|people/faculty)/(?:adjunct|affiliated|emeritus|teaching|visiting|lecturers?|researchers?)/?$",
    re.I,
)
BLOCK_CONTEXT_TAGS = {"li", "p", "td", "th", "article"}
LAB_CONTEXT_TERMS = (
    "lab",
    "labs",
    "laborator",
    "research group",
    "research groups",
)
LAB_LINK_TERMS = (
    " lab",
    "lab/",
    "labs/",
    "laborator",
    "research group",
    "project",
)
LAB_NAV_SECTION_NAMES = {
    "About",
    "Alumni & Industry",
    "Centers & Programs",
    "Close Nav",
    "Conditions & Treatment",
    "Education",
    "Education & Training",
    "Faculty",
    "Graduate",
    "Main menu",
    "Main navigation",
    "Menu",
    "Mentorship",
    "Outreach",
    "People",
    "Want to join us?",
    "Undergraduate",
}
LAB_EXCLUDED_LINK_NAMES = {
    *BAD_NAME_WORDS,
    "Adult Neurology Residency",
    "All Faculty",
    "Careers",
    "Centers & Programs",
    "Close Nav",
    "Conditions & Treatment",
    "Contact",
    "Contacts",
    "Directory source",
    "Faculty Directory",
    "Fellowship Programs",
    "Grand Rounds Schedule",
    "Grand Rounds Videos",
    "Graduate Program",
    "Home",
    "Image: UC San Diego Logo",
    "Image: UCSD homepage",
    "Industry",
    "JEDI",
    "Jobs",
    "Lab Members",
    "Lab Staff",
    "Laboratory Resources",
    "Menu",
    "Outreach",
    "Projects",
    "Research Areas",
    "Research Interest Groups",
    "Research Labs",
    "Research Programs",
    "Search",
    "Scientists",
    "Skip to main content",
    "Student Research Projects",
    "Toggle navigation",
    "UC San Diego",
    "UC San Diego School of Medicine",
    "Vimeo",
    "biology.ucsd.edu",
    "here.",
}
LAB_EXCLUDED_LINK_NAMES_LOWER = {name.lower() for name in LAB_EXCLUDED_LINK_NAMES}
RESEARCH_AREA_GENERIC_LINK_TEXTS = {
    "learn more",
    "read more",
    "research area",
    "view more",
}
RESEARCH_AREA_EXCLUDED_LINK_NAMES = {
    *LAB_EXCLUDED_LINK_NAMES,
    "Books by Faculty",
    "Centers",
    "Centers, Institutes, and International Partners",
    "Centers, Institutes, & International Partners",
    "ECE Centers",
    "ECE Laboratories",
    "Faculty",
    "Full Faculty List",
    "People",
    "Research",
    "Research Areas",
}
RESEARCH_AREA_EXCLUDED_LINK_NAMES_LOWER = {name.lower() for name in RESEARCH_AREA_EXCLUDED_LINK_NAMES}
RESEARCH_AREA_PATH_RE = re.compile(
    r"/(?:research|faculty-research|about-us/overview|research-groups)(?:/|$)|/(?:ece-research-areas|research-topics|topics)(?:/|$)",
    re.I,
)
LAB_EXCLUDED_URL_RE = re.compile(
    r"/(?:about|admissions?|alumni|calendar|careers?|contact|divisions?|education|events?|give|giving|industry|jobs|news|privacy|recruitment|search|teaching-laboratories|terms)(?:/|$)",
    re.I,
)

RESEARCH_AREA_TAGS = {
    "Algorithms, Complexity and Cryptography (Theory group)": ["Algorithms", "Theory", "Cryptography"],
    "Artificial Intelligence": ["AI", "Machine learning"],
    "Bioinformatics": ["Bioinformatics", "Computational biology"],
    "Computer Architecture and Compilers": ["Computer architecture", "Compilers", "Hardware"],
    "Computing Education Research": ["Computing education", "Teaching"],
    "Databases and Information Management": ["Databases", "Data management", "Data systems"],
    "Embedded Systems & Software": ["Embedded systems", "Software", "Hardware"],
    "Human-Computer Interaction / The Design Lab": ["Human-computer interaction", "Design"],
    "Natural Language Processing": ["Natural language processing", "Machine learning"],
    "Programming Systems": ["Programming languages", "Software engineering"],
    "Robotics": ["Robotics", "AI"],
    "Security and Cryptography": ["Security", "Cryptography", "Systems"],
    "Software Engineering": ["Software engineering", "Programming systems"],
    "Systems and Networking": ["Systems", "Networking"],
    "Ubiquitous Computing and eXtended Intelligence": ["Ubiquitous computing", "Human-computer interaction", "Health"],
    "Visual Computing (Computer Graphics and Computer Vision)": ["Computer vision", "Computer graphics", "AI"],
    "VLSI/CAD (Computer-Aided Design)": ["VLSI", "Hardware", "CAD"],
    "Extended Reality (XR) Lab": ["Extended reality", "Human-computer interaction", "Computer graphics"],
}

CATALOG_FACULTY_CODES = {
    "Anthropology": "ANTH",
    "Biological Sciences": "BIOL",
    "Bioengineering": "BENG",
    "Chemistry & Biochemistry": "CHEM",
    "Cognitive Science": "COGS",
    "Communication": "COMM",
    "Computer Science and Engineering": "CSE",
    "Data Science": "DSC",
    "Economics": "ECON",
    "Education Studies": "EDS",
    "Electrical and Computer Engineering": "ECE",
    "Ethnic Studies": "ETHN",
    "Global Policy and Strategy": "GPS",
    "Halicioğlu Data Science Institute": "DSC",
    "History": "HIST",
    "Linguistics": "LING",
    "Literature": "LIT",
    "Mathematics": "MATH",
    "Mechanical & Aerospace Engineering": "MAE",
    "Music": "MUS",
    "NanoEngineering": "NANO",
    "Philosophy": "PHIL",
    "Physics": "PHYS",
    "Political Science": "POLI",
    "Psychology": "PSYC",
    "Rady School of Management": "MGT",
    "Scripps Institution of Oceanography": "SIO",
    "Sociology": "SOC",
    "Structural Engineering": "SE",
    "Theatre & Dance": "THEA",
    "Urban Studies & Planning": "USP",
    "Visual Arts": "VIS",
}

PROFILE_URL_OVERRIDES = {
    "Aobo Li": "https://datascience.ucsd.edu/people/aobo-li/",
}

BIOLOGY_API_URL = "https://public.biology.ucsd.edu/api/prod/website-data/v1/globs/people/filterBy?type=faculty"
BIOLOGY_DIRECTORY_URL = "https://biology.ucsd.edu/research/faculty/index.html"
BIOLOGY_RESEARCH_TOPICS_URL = "https://biology.ucsd.edu/research/research-topics/index.html"
BIOLOGY_RESEARCH_TOPICS_API_URL = "https://public.biology.ucsd.edu/api/prod/website-data/v1/research-topics"
BIOLOGY_SECTION_DEPARTMENTS = {
    "CDB": "Cell and Developmental Biology",
    "EBE": "Ecology, Behavior and Evolution",
    "MB": "Molecular Biology",
    "NEURO": "Neurobiology",
}

CATALOG_ROLE_LABELS = {
    "Professors": "Professor",
    "Associate Professors": "Associate Professor",
    "Assistant Professors": "Assistant Professor",
    "Teaching Professors": "Teaching Professor",
    "Associate Teaching Professors": "Associate Teaching Professor",
    "Assistant Teaching Professors": "Assistant Teaching Professor",
    "Lecturers": "Lecturer",
    "Adjunct Professors": "Adjunct Professor",
    "Emeriti": "Emeritus Faculty",
    "Emeritus": "Emeritus Faculty",
}

DEGREE_OR_ROLE_RE = re.compile(
    r",\s*(?:Ph\.?D\.?|Pharm\.?D\.?|M\.?D\.?|M\.?F\.?A\.?|D\.?M\.?A\.?|Ed\.?D\.?|J\.?D\.?|M\.?A\.?|M\.?S\.?|M\.?B\.?A\.?|M\.?P\.?H\.?|M\.?A\.?S\.?|B\.?A\.?|B\.?S\.?|B\.?F\.?A\.?|Psy\.?D\.?|D\.?D\.?S\.?|D\.?V\.?M\.?|R\.?N\.?|BCPS|APh|Teaching Professor|Associate Professor|Assistant Professor|Professor|Lecturer)\b.*$",
    re.I,
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.text_parts: list[str] = []
        self.meta_descriptions: list[str] = []
        self.title = ""
        self.current_section = ""
        self.current_major_section = ""
        self._skip_depth = 0
        self._heading_tag = ""
        self._heading_parts: list[str] = []
        self._anchor_href = ""
        self._anchor_parts: list[str] = []
        self._in_title = False
        self._title_parts: list[str] = []
        self._block_stack: list[dict] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
            return
        if tag in BLOCK_CONTEXT_TAGS:
            self._block_stack.append({"tag": tag, "parts": [], "link_indexes": []})
        if tag == "meta":
            name = (attrs_dict.get("name") or attrs_dict.get("property") or "").lower()
            if name in {"description", "og:description", "twitter:description"} and attrs_dict.get("content"):
                self.meta_descriptions.append(clean_text(attrs_dict["content"]))
        if tag in {"h1", "h2", "h3", "h4"}:
            self._heading_tag = tag
            self._heading_parts = []
        if tag == "title":
            self._in_title = True
            self._title_parts = []
        if tag == "a":
            self._anchor_href = attrs_dict.get("href") or ""
            self._anchor_parts = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        cleaned = " ".join(data.split())
        if cleaned:
            self.text_parts.append(cleaned)
            for block in self._block_stack:
                block["parts"].append(cleaned)
        if self._heading_tag:
            self._heading_parts.append(data)
        if self._anchor_href:
            self._anchor_parts.append(data)
        if self._in_title:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == self._heading_tag:
            heading = clean_text(" ".join(self._heading_parts))
            if tag in {"h1", "h2", "h3"} and heading:
                self.current_section = heading
                if tag == "h2":
                    self.current_major_section = heading
            self._heading_tag = ""
            self._heading_parts = []
        if tag == "title":
            self.title = clean_text(" ".join(self._title_parts))
            self._in_title = False
            self._title_parts = []
        if tag == "a" and self._anchor_href:
            text = clean_text(" ".join(self._anchor_parts))
            if text:
                link_index = len(self.links)
                self.links.append(
                    {
                        "text": text,
                        "href": html.unescape(self._anchor_href),
                        "section": self.current_section,
                        "majorSection": self.current_major_section,
                        "context": "",
                    }
                )
                for block in self._block_stack:
                    block["link_indexes"].append(link_index)
            self._anchor_href = ""
            self._anchor_parts = []
        if tag in BLOCK_CONTEXT_TAGS:
            for index in range(len(self._block_stack) - 1, -1, -1):
                if self._block_stack[index]["tag"] != tag:
                    continue
                block = self._block_stack.pop(index)
                context = clean_text(" ".join(block["parts"]))
                if 5 <= len(context) <= 700:
                    for link_index in block["link_indexes"]:
                        if 0 <= link_index < len(self.links) and not self.links[link_index].get("context"):
                            self.links[link_index]["context"] = context
                break


robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_text(value: str) -> str:
    return html.unescape(WHITESPACE_RE.sub(" ", str(value))).strip()


def absolute_url(base: str, href: str) -> str:
    return urllib.parse.urljoin(base, href)


def canonical_url_key(url: str) -> str:
    key = url.split("#", 1)[0].rstrip("/")
    key = re.sub(r"/index\.html?$", "", key, flags=re.I)
    return key.lower()


def url_base_for_links(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    last_segment = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    if parsed.path and not parsed.path.endswith("/") and "." not in last_segment:
        return url + "/"
    return url


def title_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    segment = urllib.parse.unquote(parsed.path.rstrip("/").rsplit("/", 1)[-1])
    words = [word for word in re.split(r"[-_]+", segment) if word]
    return clean_text(" ".join(word.capitalize() if word.islower() else word for word in words))


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if slug:
        return slug
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def smart_title_name(value: str) -> str:
    pieces = []
    for piece in value.split():
        if "." in piece or piece.startswith('"') or piece.startswith("'"):
            pieces.append(piece)
        elif piece.isupper() or piece.islower():
            pieces.append(piece.capitalize())
        else:
            pieces.append(piece)
    return " ".join(pieces)


def canonical_person_name(value: str) -> str:
    name = clean_text(str(value).replace("\u200b", "")).strip(" *.,;:|")
    name = DEGREE_OR_ROLE_RE.sub("", name).strip(" ,")
    name = name.replace("*", "")
    if "," in name:
        parts = [clean_text(part) for part in name.split(",") if clean_text(part)]
        if len(parts) >= 2:
            last = smart_title_name(parts[0])
            first = smart_title_name(parts[1])
            name = f"{first} {last}"
    elif name.isupper():
        name = smart_title_name(name)
    return clean_text(name)


def person_merge_key(value: str) -> str:
    name = canonical_person_name(value)
    parts = [part for part in name.split() if part]
    if len(parts) > 2:
        middle = [part for part in parts[1:-1] if not re.fullmatch(r"[A-Z]\.?", part)]
        parts = [parts[0], *middle, parts[-1]]
    return slugify(" ".join(parts))


def robot_for(url: str) -> urllib.robotparser.RobotFileParser | None:
    parsed = urllib.parse.urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin in robots_cache:
        return robots_cache[origin]

    parser = urllib.robotparser.RobotFileParser()
    robots_url = urllib.parse.urljoin(origin, "/robots.txt")
    try:
        request = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=ROBOTS_TIMEOUT_SECONDS) as response:
            parser.parse(response.read().decode("utf-8", errors="replace").splitlines())
    except Exception:
        robots_cache[origin] = None
        return None
    robots_cache[origin] = parser
    return parser


def can_fetch(url: str) -> bool:
    parser = robot_for(url)
    return True if parser is None else parser.can_fetch(USER_AGENT, url)


def fetch(url: str, *, timeout: int = 30, max_bytes: int = MAX_PAGE_BYTES) -> str:
    if not can_fetch(url):
        raise RuntimeError(f"robots.txt disallows {url}")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    try:
        raw, content_type = read_url_response(request, timeout=timeout, max_bytes=max_bytes)
    except urllib.error.URLError as exc:
        reason = str(getattr(exc, "reason", exc))
        if "CERTIFICATE_VERIFY_FAILED" not in reason:
            raise
        raw, content_type = read_url_response(
            request,
            timeout=timeout,
            max_bytes=max_bytes,
            context=ssl._create_unverified_context(),
        )
    time.sleep(REQUEST_DELAY_SECONDS)
    return raw.decode(content_type, errors="replace")


def read_url_response(
    request: urllib.request.Request,
    *,
    timeout: int,
    max_bytes: int,
    context: ssl.SSLContext | None = None,
) -> tuple[bytes, str]:
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        chunks = []
        remaining = max_bytes + 1
        try:
            while remaining > 0:
                chunk = response.read(min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
        except TimeoutError:
            if not chunks:
                raise
        raw = b"".join(chunks)
        if len(raw) > max_bytes:
            raw = raw[:max_bytes]
        content_type = response.headers.get_content_charset() or "utf-8"
    return raw, content_type


def parse_html(markup: str) -> LinkParser:
    parser = LinkParser()
    parser.feed(markup)
    return parser


def first_email(text: str) -> str:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else ""


def first_phone(text: str) -> str:
    match = PHONE_RE.search(text)
    return match.group(0) if match else ""


def source_by_id(sources: dict, source_id: str) -> dict:
    for source in sources["sources"]:
        if source["id"] == source_id:
            return source
    raise KeyError(source_id)


def looks_like_person_name(value: str) -> bool:
    name = canonical_person_name(value)
    if not name or name in BAD_NAME_WORDS:
        return False
    if len(name) > 70 or len(name) < 5:
        return False
    if any(char.isdigit() for char in name):
        return False
    lowered = name.lower()
    if any(term in lowered for term in BAD_NAME_TERMS):
        return False
    parts = [part for part in re.split(r"[\s-]+", name) if part]
    if len(parts) < 2 or len(parts) > 5:
        return False
    alpha_parts = [re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ'.]", "", part) for part in parts]
    if not all(part for part in alpha_parts):
        return False
    capitalized = sum(1 for part in alpha_parts if part[0].isupper())
    return capitalized >= 2


def looks_like_profile_url(url: str, name: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path)
    full = f"{parsed.netloc}{path}"
    if DIRECTORY_CATEGORY_RE.search(path):
        return False
    if PERSON_PROFILE_URL_RE.search(full):
        return True
    name_slug = slugify(name)
    path_slug = slugify(path)
    if name_slug and name_slug in path_slug and re.search(r"/(?:people|faculty|faculty-directory|profile|profiles)/", f"{path}/", re.I):
        return True
    last_segment = slugify(path.rstrip("/").rsplit("/", 1)[-1])
    if (
        last_segment
        and len(last_segment) >= 2
        and name_slug.endswith(last_segment)
        and re.search(r"/(?:people|faculty|faculty-directory|profile|profiles)/", f"{path}/", re.I)
    ):
        return True
    name_parts = [part for part in name_slug.split("-") if len(part) > 1]
    if (
        len(name_parts) >= 2
        and last_segment
        and all(part in last_segment for part in name_parts)
        and re.search(r"/(?:people|faculty|faculty-directory|profile|profiles)/", f"{path}/", re.I)
    ):
        return True
    return False


def infer_department_interests(department: str, school: str = "") -> list[str]:
    value = f"{department} {school}".lower()
    interests = [department]
    if "bio" in value:
        interests.extend(["Biology", "Biomedical science"])
    if "chem" in value:
        interests.extend(["Chemistry"])
    if "physics" in value or "astronomy" in value:
        interests.extend(["Physics"])
    if "math" in value:
        interests.extend(["Mathematics"])
    if "engineering" in value:
        interests.extend(["Engineering"])
    if "medicine" in value or "surgery" in value or "pediatric" in value or "health" in value:
        interests.extend(["Health", "Medicine"])
    if "computer" in value or "data" in value:
        interests.extend(["Computer science", "Data science"])
    if "psych" in value or "cognitive" in value or "neuro" in value:
        interests.extend(["Cognition", "Neuroscience"])
    return sorted(set(interests))


def candidate_faculty_links(parser: LinkParser, page_url: str) -> list[dict[str, str]]:
    links = []
    seen = set()
    page_text = " ".join(parser.text_parts[:700])
    for link in parser.links:
        raw_text = clean_text(link.get("text", ""))
        label = raw_text.lower()
        if label in GENERIC_PROFILE_SKIP_LABELS:
            continue
        name = canonical_person_name(raw_text)
        if label in GENERIC_PROFILE_LINK_LABELS:
            section_name = canonical_person_name(link.get("section", ""))
            if looks_like_person_name(section_name):
                name = section_name
            else:
                context_name = canonical_person_name(
                    re.split(
                        r"\b(?:Academic Profile|Clinical Profile|Full Profile|Research Profile|UCSD Profile)\b",
                        clean_text(link.get("context", "")),
                        maxsplit=1,
                    )[0]
                )
                if looks_like_person_name(context_name):
                    name = context_name
        url = absolute_url(page_url, link["href"])
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if not parsed.netloc.endswith("ucsd.edu"):
            continue
        if url in seen or not looks_like_person_name(name):
            continue
        if not looks_like_profile_url(url, name):
            continue
        seen.add(url)
        links.append({"name": name, "url": url})
    return links


def best_generic_faculty_page(department: dict) -> tuple[str, LinkParser, list[dict[str, str]]] | None:
    candidates = [candidate for candidate in department.get("candidates", []) if candidate.get("kind") == "faculty"]
    best = None
    for candidate in candidates:
        url = candidate["url"]
        try:
            parser = parse_html(fetch(url, timeout=GENERIC_FACULTY_TIMEOUT_SECONDS, max_bytes=MAX_PAGE_BYTES))
        except Exception:
            continue
        faculty_links = candidate_faculty_links(parser, url)
        text = " ".join(parser.text_parts[:700]).lower()
        score = len(faculty_links) * 5
        if "professor" in text:
            score += 5
        if "faculty" in text:
            score += 3
        if score and (best is None or score > best[0]):
            best = (score, url, parser, faculty_links)
    if best is None:
        return None
    return best[1], best[2], best[3]


def build_generic_faculty_for_department(department: dict) -> list[dict]:
    name = department["department"]
    if name == "Computer Science and Engineering":
        return []
    result = best_generic_faculty_page(department)
    if result is None:
        return []
    page_url, parser, faculty_links = result
    school = department.get("school", "")
    records = []
    for faculty in faculty_links:
        faculty_name = faculty["name"]
        profile_url = faculty["url"]
        record_id = f"ucsd-{slugify(name)}-{slugify(faculty_name)}"
        records.append(
            normalize_record(
                {
                    "id": record_id,
                    "kind": "faculty",
                    "name": faculty_name,
                    "title": "Faculty",
                    "department": name,
                    "summary": f"Faculty profile discovered from the {name} public directory. Research and lab details need profile-level enrichment.",
                    "people": [{"name": faculty_name, "role": "Faculty"}],
                    "interests": infer_department_interests(name, school),
                    "methods": [],
                    "audiences": ["Undergraduate", "Graduate"],
                    "links": [
                        {"label": "Faculty profile", "url": profile_url},
                        {"label": "Directory source", "url": page_url},
                    ],
                    "sourceIds": [f"ucsd-{slugify(name)}-faculty-auto"],
                    "discovery": {
                        "method": "generic_faculty_directory",
                        "directoryUrl": page_url,
                    },
                    "confidence": "low",
                }
            )
        )
    print(f"[generic faculty] {name}: {len(records)} from {page_url}", flush=True)
    return records


def build_generic_faculty_from_candidates() -> list[dict]:
    if not CANDIDATES_PATH.exists() or os.environ.get("RESEARCH_FINDER_OFFLINE") == "1":
        return []
    data = load_json(CANDIDATES_PATH)
    departments = data.get("departments", [])
    if GENERIC_FACULTY_DEPARTMENT_LIMIT:
        departments = departments[:GENERIC_FACULTY_DEPARTMENT_LIMIT]
    records: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=GENERIC_FACULTY_WORKERS) as executor:
        futures = [executor.submit(build_generic_faculty_for_department, department) for department in departments]
        for future in concurrent.futures.as_completed(futures):
            try:
                records.extend(future.result())
            except Exception as exc:
                print(f"[generic faculty skipped] {type(exc).__name__}: {exc}", flush=True)
    return records


def split_lab_label(value: str) -> tuple[str, str]:
    text = clean_text(value).strip(" -*–—|")
    text = re.sub(r"\s+\|\s+.*$", "", text)
    pieces = re.split(r"\s+[–—-]\s+", text, maxsplit=1)
    name = clean_text(pieces[0]) if pieces else ""
    descriptor = clean_text(pieces[1]) if len(pieces) > 1 else ""
    descriptor = re.sub(r"^(?:UC San Diego|UCSD)\s+", "", descriptor, flags=re.I)
    name = re.sub(r"\s+(?:at|@)\s+(?:UC San Diego|UCSD).*$", "", name, flags=re.I)
    name = re.sub(r"\s+(?:UC San Diego|UCSD)$", "", name, flags=re.I)
    return clean_text(name), clean_text(descriptor)


def clean_direction_phrase(value: str) -> str:
    phrase = clean_text(value)
    phrase = re.sub(r"\([^)]{1,12}\)", "", phrase)
    phrase = re.sub(r"\b(?:UC San Diego|UCSD)\b", " ", phrase, flags=re.I)
    phrase = re.sub(r"\b(?:lab|labs|laboratory|laboratories|research group|group)\b", " ", phrase, flags=re.I)
    phrase = re.sub(r"^center for\s+", "", phrase, flags=re.I)
    phrase = re.sub(r"\s+center$", "", phrase, flags=re.I)
    phrase = re.sub(r"^(?:for|of|the)\s+", "", phrase, flags=re.I)
    return clean_text(phrase.strip(" -*–—|"))


def has_research_signal(value: str) -> bool:
    lowered = f" {value.lower()} "
    if infer_labels(value, INTEREST_KEYWORDS, limit=1):
        return True
    return any(
        token in lowered
        for token in (
            "aging",
            "autism",
            "behavior",
            "biology",
            "brain",
            "cancer",
            "cell",
            "clinical",
            "cognition",
            "disease",
            "genetic",
            "health",
            "imaging",
            "immune",
            "language",
            "learning",
            "memory",
            "neural",
            "neuro",
            "policy",
            "repair",
            "science",
            "systems",
        )
    )


def likely_direction_phrase(value: str) -> bool:
    phrase = clean_direction_phrase(value)
    if not phrase or len(phrase) < 4 or len(phrase) > 80:
        return False
    lowered = phrase.lower()
    if lowered in {"home", "homepage", "website", "research", "project", "program", "study"}:
        return False
    words = phrase.split()
    if len(words) == 1 and not has_research_signal(phrase):
        return False
    if len(words) <= 3 and all(word[:1].isupper() for word in words) and not has_research_signal(phrase):
        return False
    return True


def lab_research_directions(label: str, context: str, department: str, school: str) -> list[str]:
    name, descriptor = split_lab_label(label)
    value = f"{label} {context}"
    labels = infer_labels(value, INTEREST_KEYWORDS, limit=10)
    phrases = []
    for phrase in (descriptor, name):
        cleaned = clean_direction_phrase(phrase)
        if likely_direction_phrase(cleaned):
            phrases.append(cleaned)
    directions = unique_preserve(labels + phrases + infer_department_interests(department, school))
    return directions or infer_department_interests(department, school)


def lab_summary(department: str, directions: list[str], label: str, context: str) -> str:
    direction_text = ", ".join(directions[:6])
    context = clean_text(context)
    label = clean_text(label)
    context_is_directory_card = "principal investigator" not in context.lower() and "@" not in context
    if context and context != label and context_is_directory_card and 20 <= len(context) <= 220:
        return f"{context} Research direction: {direction_text}."
    return f"Lab entry from the {department} public lab directory. Research direction: {direction_text}."


def lab_link_allowed(url: str, lab_like: bool) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.netloc.lower().removeprefix("www.")
    if any(host == domain or host.endswith(f".{domain}") for domain in SKIP_PERSONAL_DOMAINS):
        return False
    if LAB_EXCLUDED_URL_RE.search(parsed.path) and not lab_like:
        return False
    return True


def candidate_lab_links(parser: LinkParser, page_url: str, department: str) -> list[dict[str, str]]:
    links = []
    seen = set()
    base_url = canonical_url_key(page_url)
    link_base_url = url_base_for_links(page_url)
    for link in parser.links:
        raw_label = clean_text(link.get("text", ""))
        section = clean_text(link.get("section", ""))
        major_section = clean_text(link.get("majorSection", ""))
        if raw_label.lower() in {"website", "web site", "site", "lab website"} and section:
            name, descriptor = split_lab_label(section)
            label_for_direction = section
        else:
            name, descriptor = split_lab_label(raw_label)
            label_for_direction = raw_label
        if name.startswith("&") or re.fullmatch(r"(?:[\w-]+\.)+[a-z]{2,}", name.lower()):
            continue
        if name.lower() == department.lower() or "resources" in name.lower():
            continue
        if not name or len(name) < 3 or len(name) > 90:
            continue
        if name in LAB_EXCLUDED_LINK_NAMES or name.lower() in LAB_EXCLUDED_LINK_NAMES_LOWER:
            continue
        if section in LAB_NAV_SECTION_NAMES:
            continue
        url = absolute_url(link_base_url, link.get("href", ""))
        if canonical_url_key(url) == base_url:
            continue
        value = f" {label_for_direction} {descriptor} {url} ".lower()
        section_context = f" {section} {major_section} {link.get('context', '')} ".lower()
        lab_like = any(term in value for term in LAB_LINK_TERMS)
        source_context = any(term in section_context for term in LAB_CONTEXT_TERMS)
        if not source_context and not lab_like:
            continue
        if looks_like_person_name(name) and not lab_like:
            continue
        if not lab_link_allowed(url, lab_like):
            continue
        key = canonical_url_key(url)
        if key in seen:
            continue
        seen.add(key)
        links.append(
            {
                "name": name,
                "descriptor": descriptor,
                "label": label_for_direction,
                "url": url,
                "section": section,
                "majorSection": major_section,
                "context": clean_text(link.get("context", "")),
            }
        )
    return links


def lab_directory_score(parser: LinkParser, page_url: str, lab_links: list[dict[str, str]]) -> int:
    if not lab_links:
        return 0
    text = f"{parser.title} {' '.join(parser.meta_descriptions)} {' '.join(parser.text_parts[:500])}".lower()
    score = len(lab_links) * 6
    if re.search(r"/(?:research/)?labs?/?(?:index\.html)?$", urllib.parse.urlparse(page_url).path, re.I):
        score += 10
    if "research/labs" in page_url.lower() or "research-labs" in page_url.lower():
        score += 8
    if "research group" in text or "research groups" in text:
        score += 6
    if "laborator" in text or " lab" in text:
        score += 6
    if "faculty" in page_url.lower() and "lab" not in page_url.lower():
        score -= 6
    return score


def best_generic_lab_page(department: dict) -> tuple[str, LinkParser, list[dict[str, str]]] | None:
    best = None
    candidate_groups = [
        [candidate for candidate in department.get("candidates", []) if candidate.get("kind") == "labs"],
        [candidate for candidate in department.get("candidates", []) if candidate.get("kind") == "research"],
    ]
    for candidates in candidate_groups:
        for candidate in candidates:
            url = candidate["url"]
            try:
                parser = parse_html(fetch(url, timeout=GENERIC_LAB_TIMEOUT_SECONDS, max_bytes=MAX_PAGE_BYTES))
            except Exception:
                continue
            lab_links = candidate_lab_links(parser, url, department["department"])
            score = lab_directory_score(parser, url, lab_links)
            if score and (best is None or score > best[0]):
                best = (score, url, parser, lab_links)
            if score >= 30:
                return url, parser, lab_links
        if best is not None:
            break
    if best is None:
        return None
    return best[1], best[2], best[3]


def build_generic_labs_for_department(department: dict) -> list[dict]:
    name = department["department"]
    result = best_generic_lab_page(department)
    if result is None:
        return []
    page_url, _parser, lab_links = result
    school = department.get("school", "")
    source_id = f"ucsd-{slugify(name)}-labs-auto"
    records = []
    for lab in lab_links:
        direction_context = clean_text(f"{lab.get('majorSection', '')} {lab.get('context', '')}")
        directions = lab_research_directions(lab["label"], direction_context, name, school)
        records.append(
            normalize_record(
                {
                    "id": f"ucsd-{slugify(name)}-lab-{slugify(lab['name'])}",
                    "kind": "lab",
                    "name": lab["name"],
                    "title": f"{name} lab",
                    "department": name,
                    "summary": lab_summary(name, directions, lab["label"], direction_context),
                    "researchDirections": directions,
                    "interests": directions,
                    "methods": infer_labels(f"{lab['label']} {lab.get('context', '')}", METHOD_KEYWORDS, limit=5),
                    "audiences": ["Undergraduate", "Graduate"],
                    "links": [
                        {"label": "Lab site", "url": lab["url"]},
                        {"label": "Directory source", "url": page_url},
                    ],
                    "sourceIds": [source_id],
                    "discovery": {
                        "method": "generic_lab_directory",
                        "directoryUrl": page_url,
                        "section": lab.get("section", ""),
                        "majorSection": lab.get("majorSection", ""),
                    },
                    "confidence": "medium",
                }
            )
        )
    print(f"[generic labs] {name}: {len(records)} from {page_url}", flush=True)
    return records


def build_generic_labs_from_candidates() -> list[dict]:
    if not CANDIDATES_PATH.exists() or os.environ.get("RESEARCH_FINDER_OFFLINE") == "1":
        return []
    data = load_json(CANDIDATES_PATH)
    departments = data.get("departments", [])
    if GENERIC_LAB_DEPARTMENT_LIMIT:
        departments = departments[:GENERIC_LAB_DEPARTMENT_LIMIT]
    records: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=GENERIC_LAB_WORKERS) as executor:
        futures = [executor.submit(build_generic_labs_for_department, department) for department in departments]
        for future in concurrent.futures.as_completed(futures):
            try:
                records.extend(future.result())
            except Exception as exc:
                print(f"[generic labs skipped] {type(exc).__name__}: {exc}", flush=True)
    return records


def research_area_name_from_link(link: dict[str, str], url: str) -> str:
    raw_label = clean_text(link.get("text", ""))
    lowered = raw_label.lower()
    section = clean_text(link.get("section", ""))
    if lowered == "research area" and section and "research area" not in section.lower():
        return section
    if lowered in RESEARCH_AREA_GENERIC_LINK_TEXTS:
        return title_from_url(url)
    return split_lab_label(raw_label)[0]


def candidate_research_area_links(parser: LinkParser, page_url: str, department: str) -> list[dict[str, str]]:
    links = []
    seen = set()
    base_url = canonical_url_key(page_url)
    link_base_url = url_base_for_links(page_url)
    for link in parser.links:
        section = clean_text(link.get("section", ""))
        major_section = clean_text(link.get("majorSection", ""))
        if section in LAB_NAV_SECTION_NAMES:
            continue
        url = absolute_url(link_base_url, link.get("href", ""))
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if canonical_url_key(url) == base_url:
            continue
        if LAB_EXCLUDED_URL_RE.search(parsed.path):
            continue
        if not RESEARCH_AREA_PATH_RE.search(parsed.path):
            continue

        name = research_area_name_from_link(link, url)
        if not name or len(name) < 3 or len(name) > 90:
            continue
        if name.lower() == department.lower():
            continue
        if name in RESEARCH_AREA_EXCLUDED_LINK_NAMES or name.lower() in RESEARCH_AREA_EXCLUDED_LINK_NAMES_LOWER:
            continue
        if name.startswith("&") or re.fullmatch(r"(?:[\w-]+\.)+[a-z]{2,}", name.lower()):
            continue

        context = clean_text(link.get("context", ""))
        value = f" {name} {section} {major_section} {context} {parser.title} ".lower()
        source_context = "research" in value or "faculty-research" in url.lower()
        if not source_context:
            continue

        key = canonical_url_key(url)
        if key in seen:
            continue
        seen.add(key)
        links.append(
            {
                "name": name,
                "label": name,
                "url": url,
                "section": section,
                "majorSection": major_section,
                "context": context,
            }
        )
    return links


def research_area_page_score(parser: LinkParser, page_url: str, area_links: list[dict[str, str]]) -> int:
    if not area_links:
        return 0
    text = f"{parser.title} {' '.join(parser.meta_descriptions)} {' '.join(parser.text_parts[:500])}".lower()
    score = len(area_links) * 5
    if "research area" in text or "research areas" in text:
        score += 12
    if "research" in urllib.parse.urlparse(page_url).path.lower():
        score += 8
    if "faculty-research" in page_url.lower():
        score += 6
    return score


def best_generic_research_area_page(department: dict) -> tuple[str, LinkParser, list[dict[str, str]]] | None:
    best = None
    candidates = [candidate for candidate in department.get("candidates", []) if candidate.get("kind") == "research"]
    for candidate in candidates:
        url = candidate["url"]
        try:
            parser = parse_html(fetch(url, timeout=GENERIC_LAB_TIMEOUT_SECONDS, max_bytes=MAX_PAGE_BYTES))
        except Exception:
            continue
        area_links = candidate_research_area_links(parser, url, department["department"])
        score = research_area_page_score(parser, url, area_links)
        if score and (best is None or score > best[0]):
            best = (score, url, parser, area_links)
        if score >= 30:
            return url, parser, area_links
    if best is None:
        return None
    return best[1], best[2], best[3]


def research_area_summary(department: str, area: dict[str, str], directions: list[str]) -> str:
    context = clean_text(area.get("context", ""))
    direction_text = ", ".join(directions[:6])
    if context and len(context) <= 260 and context.lower() != area["name"].lower():
        return f"{context} Research direction: {direction_text}."
    return f"Official {department} research area. Research direction: {direction_text}."


def build_generic_research_areas_for_department(department: dict) -> list[dict]:
    name = department["department"]
    result = best_generic_research_area_page(department)
    if result is None:
        return []
    page_url, _parser, area_links = result
    school = department.get("school", "")
    source_id = f"ucsd-{slugify(name)}-research-areas-auto"
    records = []
    for area in area_links:
        direction_context = clean_text(f"{area.get('majorSection', '')} {area.get('context', '')}")
        directions = lab_research_directions(area["label"], direction_context, name, school)
        records.append(
            normalize_record(
                {
                    "id": f"ucsd-{slugify(name)}-area-{slugify(area['name'])}",
                    "kind": "research_area",
                    "name": area["name"],
                    "title": f"{name} research area",
                    "department": name,
                    "summary": research_area_summary(name, area, directions),
                    "researchDirections": directions,
                    "interests": directions,
                    "methods": infer_labels(f"{area['label']} {area.get('context', '')}", METHOD_KEYWORDS, limit=5),
                    "audiences": ["Undergraduate", "Graduate"],
                    "links": [
                        {"label": "Research area", "url": area["url"]},
                        {"label": "Directory source", "url": page_url},
                    ],
                    "sourceIds": [source_id],
                    "discovery": {
                        "method": "generic_research_area_directory",
                        "directoryUrl": page_url,
                        "section": area.get("section", ""),
                        "majorSection": area.get("majorSection", ""),
                    },
                    "confidence": "medium",
                }
            )
        )
    print(f"[generic research areas] {name}: {len(records)} from {page_url}", flush=True)
    return records


def build_generic_research_areas_from_candidates() -> list[dict]:
    if not CANDIDATES_PATH.exists() or os.environ.get("RESEARCH_FINDER_OFFLINE") == "1":
        return []
    data = load_json(CANDIDATES_PATH)
    departments = data.get("departments", [])
    if GENERIC_RESEARCH_AREA_DEPARTMENT_LIMIT:
        departments = departments[:GENERIC_RESEARCH_AREA_DEPARTMENT_LIMIT]
    records: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=GENERIC_LAB_WORKERS) as executor:
        futures = [executor.submit(build_generic_research_areas_for_department, department) for department in departments]
        for future in concurrent.futures.as_completed(futures):
            try:
                records.extend(future.result())
            except Exception as exc:
                print(f"[generic research areas skipped] {type(exc).__name__}: {exc}", flush=True)
    return records


def research_like_departments(records: list[dict]) -> set[str]:
    research_kinds = {"center", "lab", "program", "research_area"}
    return {
        department
        for record in records
        if record.get("kind") in research_kinds
        for department in record_departments(record)
    }


def build_department_research_overview_fallbacks(records: list[dict]) -> list[dict]:
    if not CANDIDATES_PATH.exists():
        return []
    data = load_json(CANDIDATES_PATH)
    covered = research_like_departments(records)
    fallbacks = []
    for department in data.get("departments", []):
        name = department["department"]
        if name in covered:
            continue
        school = department.get("school", "")
        homepage = department.get("homepage", "")
        if not homepage:
            continue
        directions = infer_department_interests(name, school)
        fallbacks.append(
            normalize_record(
                {
                    "id": f"ucsd-{slugify(name)}-research-overview",
                    "kind": "research_area",
                    "name": f"{name} Research Overview",
                    "title": "Department research overview",
                    "department": name,
                    "summary": (
                        "No public lab directory or research-area page was found automatically. "
                        f"This entry links to the official {name} page and uses department-level research directions."
                    ),
                    "researchDirections": directions,
                    "interests": directions,
                    "methods": [],
                    "audiences": ["Undergraduate", "Graduate"],
                    "links": [{"label": "Department page", "url": homepage}],
                    "sourceIds": [f"ucsd-{slugify(name)}-research-overview-auto"],
                    "discovery": {
                        "method": "department_research_overview_fallback",
                        "reason": "no_parseable_lab_or_research_area_directory",
                    },
                    "confidence": "low",
                }
            )
        )
    if fallbacks:
        print(f"[department overview fallback] total {len(fallbacks)}", flush=True)
    return fallbacks


def clean_catalog_faculty_name(value: str) -> str:
    text = clean_text(re.sub(r"<.*?>", " ", value))
    text = html.unescape(text).replace("\xa0", " ")
    text = clean_text(text)
    return canonical_person_name(text)


def parse_catalog_faculty(markup: str) -> list[dict[str, str]]:
    rows = []
    current_role = "Faculty"
    token_re = re.compile(
        r'<h4 class="faculty-staff-subhead">(.*?)</h4>|<p class="faculty-staff-listing">(.*?)</p>',
        re.S | re.I,
    )
    for match in token_re.finditer(markup):
        if match.group(1) is not None:
            raw_role = clean_text(re.sub(r"<.*?>", " ", match.group(1)))
            current_role = CATALOG_ROLE_LABELS.get(raw_role, raw_role or "Faculty")
            continue
        raw_row = match.group(2) or ""
        name = clean_catalog_faculty_name(raw_row)
        full_text = clean_text(html.unescape(re.sub(r"<.*?>", " ", raw_row)).replace("\xa0", " "))
        if not looks_like_person_name(name):
            continue
        role = current_role
        if "Emeritus" in full_text or "Emerita" in full_text:
            role = f"{role}, Emeritus"
        rows.append({"name": name, "role": role, "raw": full_text})
    deduped = {}
    for row in rows:
        deduped.setdefault(slugify(row["name"]), row)
    return list(deduped.values())


def build_catalog_faculty_records() -> list[dict]:
    if os.environ.get("RESEARCH_FINDER_SKIP_CATALOG") == "1":
        return []
    records = []
    for department, code in CATALOG_FACULTY_CODES.items():
        if department == "Computer Science and Engineering":
            continue
        url = f"https://catalog.ucsd.edu/faculty/{code}.html"
        try:
            markup = fetch(url, timeout=GENERIC_FACULTY_TIMEOUT_SECONDS, max_bytes=MAX_PAGE_BYTES)
        except Exception as exc:
            print(f"[catalog faculty skipped] {department}: {type(exc).__name__}", flush=True)
            continue
        rows = parse_catalog_faculty(markup)
        print(f"[catalog faculty] {department}: {len(rows)} from {url}", flush=True)
        for row in rows:
            faculty_name = row["name"]
            record_id = f"ucsd-{slugify(department)}-{slugify(faculty_name)}"
            role = row["role"]
            records.append(
                normalize_record(
                    {
                        "id": record_id,
                        "kind": "faculty",
                        "name": faculty_name,
                        "title": role,
                        "department": department,
                        "summary": f"Faculty listing from the UC San Diego General Catalog for {department}. Profile, lab and email links need department-page enrichment.",
                        "people": [{"name": faculty_name, "role": role}],
                        "interests": infer_department_interests(department),
                        "methods": [],
                        "audiences": ["Undergraduate", "Graduate"],
                        "links": [{"label": "Catalog faculty listing", "url": url}],
                        "sourceIds": [f"ucsd-catalog-{code.lower()}"],
                        "discovery": {"method": "catalog_faculty_listing", "catalogCode": code},
                        "confidence": "low",
                    }
                )
            )
    return records


def biology_department_names(item: dict) -> list[str]:
    departments = ["Biological Sciences"]
    profile = item.get("profileInfo") or {}
    for section in profile.get("sections") or []:
        title = clean_text(section.get("title", "")).replace("&", "and")
        initials = clean_text(section.get("initials", ""))
        department = BIOLOGY_SECTION_DEPARTMENTS.get(initials) or title
        if department:
            departments.append(department)
    department_info = item.get("departmentInfo") or {}
    department = clean_text(department_info.get("name", "")).removeprefix("Section of ").replace("&", "and")
    if department in BIOLOGY_SECTION_DEPARTMENTS.values():
        departments.append(department)
    return unique_preserve(departments)


def build_biology_api_faculty_records() -> list[dict]:
    if os.environ.get("RESEARCH_FINDER_SKIP_BIOLOGY_API") == "1":
        return []
    try:
        data = json.loads(fetch(BIOLOGY_API_URL, timeout=GENERIC_FACULTY_TIMEOUT_SECONDS, max_bytes=2_500_000))
    except Exception as exc:
        print(f"[biology api skipped] {type(exc).__name__}: {exc}", flush=True)
        return []
    records = []
    for item in data:
        profile = item.get("profileInfo") or {}
        title_info = item.get("titleInfo") or {}
        first = clean_text(item.get("fname", ""))
        middle = clean_text(item.get("mi", ""))
        last = clean_text(item.get("lname", ""))
        name = canonical_person_name(" ".join(part for part in (first, middle, last) if part))
        if not looks_like_person_name(name):
            continue
        departments = biology_department_names(item)
        profile_url = absolute_url("https://biology.ucsd.edu/", profile.get("profileURL", ""))
        lab_url = profile.get("labURL") or ""
        summary = clean_text(profile.get("researchSummary", ""))
        links = [{"label": "Faculty profile", "url": profile_url}, {"label": "Directory source", "url": BIOLOGY_DIRECTORY_URL}]
        if lab_url:
            links.append({"label": "Lab / research", "url": absolute_url("https://biology.ucsd.edu/", lab_url)})
        contacts = []
        email = clean_email(item.get("email", ""))
        if email:
            contacts.append({"type": "email", "label": "Email", "value": email, "href": f"mailto:{email}"})
        phone = clean_text(item.get("phone", ""))
        if phone:
            contacts.append({"type": "phone", "label": "Phone", "value": phone, "href": f"tel:{re.sub(r'[^0-9+]', '', phone)}"})
        interest_text = f"{summary} {' '.join(departments)}"
        records.append(
            normalize_record(
                {
                    "id": f"ucsd-biology-{slugify(name)}",
                    "kind": "faculty",
                    "name": name,
                    "title": clean_text(title_info.get("standardTitle", "")) or "Faculty",
                    "department": departments[0],
                    "departments": departments,
                    "summary": summary or "Biological Sciences faculty profile with section, contact and lab links from the public Biology directory.",
                    "people": [{"name": name, "role": clean_text(title_info.get("standardTitle", "")) or "Faculty"}],
                    "interests": sorted(set(infer_department_interests(" ".join(departments)) + infer_labels(interest_text, INTEREST_KEYWORDS))),
                    "methods": infer_labels(summary, METHOD_KEYWORDS, limit=5),
                    "audiences": ["Undergraduate", "Graduate"],
                    "contacts": contacts,
                    "links": links,
                    "sourceIds": ["ucsd-biology-api"],
                    "discovery": {"method": "biology_public_api", "apiUrl": BIOLOGY_API_URL},
                    "confidence": "high",
                }
            )
        )
    print(f"[biology api] {len(records)} faculty from {BIOLOGY_API_URL}", flush=True)
    return records


def biology_topic_page_url(path: str) -> str:
    return f"https://biology.ucsd.edu/research/research-topics/topics/{urllib.parse.quote(path.strip('/'))}"


def build_biology_topic_records() -> list[dict]:
    if os.environ.get("RESEARCH_FINDER_SKIP_BIOLOGY_API") == "1":
        return []
    try:
        topics = json.loads(fetch(BIOLOGY_RESEARCH_TOPICS_API_URL, timeout=GENERIC_FACULTY_TIMEOUT_SECONDS, max_bytes=700_000))
        faculty_items = json.loads(fetch(BIOLOGY_API_URL, timeout=GENERIC_FACULTY_TIMEOUT_SECONDS, max_bytes=2_500_000))
    except Exception as exc:
        print(f"[biology topics skipped] {type(exc).__name__}: {exc}", flush=True)
        return []

    faculty_by_empid = {str(item.get("empid")): item for item in faculty_items if item.get("empid") is not None}
    records = []
    topic_count = 0
    lab_count = 0
    for topic in topics:
        if topic.get("stagingOnly"):
            continue
        path = clean_text(topic.get("path", ""))
        title = clean_text(topic.get("title", ""))
        if not path or not title:
            continue
        topic_url = biology_topic_page_url(path)
        description = clean_text(topic.get("description", ""))
        directions = unique_preserve(infer_labels(f"{title} {description}", INTEREST_KEYWORDS, limit=8) + [title, "Biological Sciences"])
        records.append(
            normalize_record(
                {
                    "id": f"ucsd-biology-topic-{slugify(title)}",
                    "kind": "research_area",
                    "name": title,
                    "title": "Biological Sciences research topic",
                    "department": "Biological Sciences",
                    "summary": description or f"Official Biology research topic: {title}.",
                    "researchDirections": directions,
                    "interests": directions,
                    "methods": infer_labels(description, METHOD_KEYWORDS, limit=5),
                    "audiences": ["Undergraduate", "Graduate"],
                    "links": [
                        {"label": "Research topic", "url": topic_url},
                        {"label": "Directory source", "url": BIOLOGY_RESEARCH_TOPICS_URL},
                    ],
                    "sourceIds": ["ucsd-biology-research-topics-api"],
                    "discovery": {"method": "biology_research_topics_api", "apiUrl": BIOLOGY_RESEARCH_TOPICS_API_URL},
                    "confidence": "high",
                }
            )
        )
        topic_count += 1

        try:
            selectors = json.loads(
                fetch(f"{BIOLOGY_RESEARCH_TOPICS_API_URL}/{urllib.parse.quote(path)}", timeout=GENERIC_FACULTY_TIMEOUT_SECONDS, max_bytes=500_000)
            )
        except Exception as exc:
            print(f"[biology topic selectors skipped] {path}: {type(exc).__name__}", flush=True)
            continue
        seen_empids = set()
        for selector in selectors:
            empid = str(selector.get("empid"))
            if empid in seen_empids:
                continue
            seen_empids.add(empid)
            item = faculty_by_empid.get(empid)
            if not item:
                continue
            profile = item.get("profileInfo") or {}
            lab_url = profile.get("labURL") or ""
            if not lab_url:
                continue
            first = clean_text(item.get("fname", ""))
            middle = clean_text(item.get("mi", ""))
            last = clean_text(item.get("lname", ""))
            faculty_name = canonical_person_name(" ".join(part for part in (first, middle, last) if part))
            if not looks_like_person_name(faculty_name):
                continue
            departments = biology_department_names(item)
            summary = clean_text(profile.get("researchSummary", ""))
            lab_name = clean_text((item.get("groupInfo") or {}).get("longName", "")) or f"{last} Lab"
            lab_directions = unique_preserve(directions + infer_labels(summary, INTEREST_KEYWORDS, limit=8) + infer_department_interests(" ".join(departments)))
            profile_url = absolute_url("https://biology.ucsd.edu/", profile.get("profileURL", ""))
            links = [
                {"label": "Lab site", "url": absolute_url("https://biology.ucsd.edu/", lab_url)},
                {"label": "Research topic", "url": topic_url},
                {"label": "Directory source", "url": BIOLOGY_RESEARCH_TOPICS_URL},
            ]
            if profile_url:
                links.append({"label": "Faculty profile", "url": profile_url})
            records.append(
                normalize_record(
                    {
                        "id": f"ucsd-biology-topic-lab-{slugify(lab_name)}",
                        "kind": "lab",
                        "name": lab_name,
                        "title": "Biological Sciences lab",
                        "department": departments[0],
                        "departments": departments,
                        "summary": summary or f"{faculty_name}'s lab is listed under the official Biology research topic {title}.",
                        "researchDirections": lab_directions,
                        "interests": lab_directions,
                        "methods": infer_labels(summary, METHOD_KEYWORDS, limit=5),
                        "audiences": ["Undergraduate", "Graduate"],
                        "people": [{"name": faculty_name, "role": clean_text((item.get("titleInfo") or {}).get("standardTitle", "")) or "Faculty"}],
                        "links": links,
                        "sourceIds": ["ucsd-biology-research-topics-api"],
                        "discovery": {
                            "method": "biology_research_topic_lab_api",
                            "apiUrl": f"{BIOLOGY_RESEARCH_TOPICS_API_URL}/{path}",
                            "topic": title,
                        },
                        "confidence": "high",
                    }
                )
            )
            lab_count += 1
    print(f"[biology topics] {topic_count} topics and {lab_count} topic-linked labs from {BIOLOGY_RESEARCH_TOPICS_API_URL}", flush=True)
    return records


def record_quality(record: dict) -> tuple[int, int, int]:
    confidence_score = {"high": 3, "medium": 2, "low": 1}.get(record.get("confidence"), 0)
    link_labels = {link.get("label", "") for link in record.get("links", [])}
    profile_score = 0
    if "Faculty profile" in link_labels:
        profile_score += 3
    if "Website" in link_labels or "Lab site" in link_labels or "Lab / research" in link_labels:
        profile_score += 2
    if "Catalog faculty listing" in link_labels:
        profile_score -= 1
    contact_score = len(record.get("contacts", []))
    return confidence_score, profile_score, contact_score


def choose_better_record(existing: dict | None, candidate: dict) -> dict:
    if existing is None:
        return candidate
    return candidate if record_quality(candidate) > record_quality(existing) else existing


def link_for_label(links: list[dict[str, str]], base_url: str, labels: set[str]) -> dict[str, str] | None:
    for link in links:
        if link["text"] in labels:
            return {"label": link["text"], "url": absolute_url(base_url, link["href"])}
    return None


def is_skippable_personal_site(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return True
    host = parsed.netloc.lower().removeprefix("www.")
    return any(host == domain or host.endswith(f".{domain}") for domain in SKIP_PERSONAL_DOMAINS)


def infer_labels(text: str, keyword_map: dict[str, list[str]], *, limit: int = 7) -> list[str]:
    haystack = f" {text.lower()} "
    labels = []
    for label, keywords in keyword_map.items():
        if any(keyword in haystack for keyword in keywords):
            labels.append(label)
    return labels[:limit]


def personal_site_lab_links(parser: LinkParser, base_url: str) -> list[dict[str, str]]:
    candidates = []
    seen = set()
    for link in parser.links:
        text = clean_text(link["text"])
        href = absolute_url(base_url, link["href"])
        value = f"{text} {href}".lower()
        if not any(term in value for term in ("lab", "group", "research", "project")):
            continue
        if href in seen or not href.startswith(("http://", "https://")):
            continue
        seen.add(href)
        label = text if 2 <= len(text) <= 48 else "Lab / research page"
        candidates.append({"label": label, "url": href})
        if len(candidates) >= 3:
            break
    return candidates


def unique_preserve(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        cleaned = clean_text(value)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def record_departments(record: dict) -> list[str]:
    values = []
    if record.get("department"):
        values.append(record["department"])
    departments = record.get("departments", [])
    if isinstance(departments, str):
        values.append(departments)
    else:
        values.extend(departments)
    return unique_preserve(values)


def clean_email(value: str) -> str:
    value = urllib.parse.unquote(value)
    value = value.replace("mailto:", "").replace("Mailto:", "")
    value = value.split("?", 1)[0]
    match = EMAIL_RE.search(value)
    return match.group(0).lower() if match else ""


def email_allowed(email: str) -> bool:
    local = email.split("@", 1)[0].lower()
    return bool(email) and local not in EXCLUDED_EMAIL_LOCALS


def profile_emails(parser: LinkParser, text: str) -> list[str]:
    emails = {email.lower() for email in EMAIL_RE.findall(text)}
    for link in parser.links:
        href = link.get("href", "")
        if href.lower().startswith("mailto:"):
            emails.add(clean_email(href))
        emails.update(email.lower() for email in EMAIL_RE.findall(f"{href} {link.get('text', '')}"))
    return sorted(email for email in emails if email_allowed(email))


def title_score(title: str) -> int:
    lowered = clean_text(title).lower()
    order = [
        "assistant teaching professor",
        "associate teaching professor",
        "teaching professor",
        "assistant professor",
        "associate professor",
        "professor",
        "research scientist",
        "lecturer",
        "faculty",
    ]
    for index, label in enumerate(order, start=1):
        if label == lowered:
            return len(order) - index + 1
    if "professor" in lowered:
        return 5
    if lowered and lowered != "faculty":
        return 2
    return 0


def profile_title(text: str) -> str:
    match = FACULTY_TITLE_RE.search(text)
    return clean_text(match.group(0)).title() if match else ""


def profile_candidate_links(parser: LinkParser, base_url: str) -> list[dict[str, str]]:
    labels = {
        "website",
        "web site",
        "homepage",
        "home page",
        "personal website",
        "personal web page",
        "faculty website",
    }
    candidates = []
    seen = set()
    base_normalized = base_url.rstrip("/")
    for link in parser.links:
        text = clean_text(link.get("text", ""))
        href = absolute_url(base_url, link.get("href", ""))
        parsed = urllib.parse.urlparse(href)
        if parsed.scheme not in {"http", "https"}:
            continue
        if href.rstrip("/") == base_normalized or href in seen:
            continue
        lowered_text = text.lower().strip(":")
        value = f"{lowered_text} {href.lower()}"
        lab_like = any(term in value for term in ("lab", "laboratory", "group", "research", "project"))
        website_like = lowered_text in labels or "homepage" in lowered_text or "website" in lowered_text
        external = not parsed.netloc.lower().endswith("ucsd.edu")
        if is_skippable_personal_site(href):
            continue
        if lab_like:
            label = text if 2 <= len(text) <= 48 and "website" not in lowered_text else "Lab / research"
        elif website_like:
            label = "Website"
        elif external and any(host_hint in href.lower() for host_hint in ("github.io", "sites.google.com", "faculty", "lab", "research")):
            label = text if 2 <= len(text) <= 48 else "Website"
        else:
            continue
        candidates.append({"label": label, "url": href})
        seen.add(href)
        if len(candidates) >= 6:
            break
    return candidates


def profile_url_for_record(record: dict) -> str:
    override = PROFILE_URL_OVERRIDES.get(record.get("name", ""))
    if override:
        return override
    for link in record.get("links", []):
        url = link.get("url", "")
        label = link.get("label", "")
        if label in {"Faculty profile", "Full Profile"} and url:
            return url
        if url and looks_like_profile_url(url, record.get("name", "")):
            return url
    return ""


def enrich_from_profile(name: str, profile_url: str) -> dict:
    if not profile_url:
        return {"checked": False}
    try:
        markup = fetch(profile_url, timeout=PROFILE_ENRICH_TIMEOUT_SECONDS, max_bytes=MAX_PAGE_BYTES)
    except Exception as exc:
        return {"checked": False, "reason": type(exc).__name__, "url": profile_url}

    parser = parse_html(markup)
    text = clean_text(" ".join(parser.meta_descriptions + parser.text_parts[:1200]))
    interests = infer_labels(text, INTEREST_KEYWORDS)
    methods = infer_labels(text, METHOD_KEYWORDS, limit=6)
    links = profile_candidate_links(parser, profile_url)
    emails = profile_emails(parser, text)
    title = profile_title(text)
    summary = ""
    if interests:
        summary = f"Official profile signals research in {', '.join(interests[:5])}."
    elif parser.meta_descriptions:
        summary = clean_text(parser.meta_descriptions[0])
        if len(summary) > 180:
            summary = summary[:177].rsplit(" ", 1)[0] + "..."

    return {
        "checked": True,
        "url": profile_url,
        "title": title,
        "summary": summary,
        "interests": interests,
        "methods": methods,
        "links": links,
        "emails": emails,
    }


def enrich_from_personal_site(name: str, website_url: str) -> dict:
    if not website_url or is_skippable_personal_site(website_url):
        return {"checked": False, "reason": "skipped", "url": website_url}
    try:
        markup = fetch(
            website_url,
            timeout=PERSONAL_SITE_TIMEOUT_SECONDS,
            max_bytes=MAX_PAGE_BYTES,
        )
    except Exception as exc:
        return {"checked": False, "reason": type(exc).__name__, "url": website_url}

    parser = parse_html(markup)
    text = clean_text(" ".join(parser.meta_descriptions + parser.text_parts[:500]))
    interests = infer_labels(text, INTEREST_KEYWORDS)
    methods = infer_labels(text, METHOD_KEYWORDS, limit=5)
    lab_links = personal_site_lab_links(parser, website_url)
    emails = sorted(set(EMAIL_RE.findall(text)))

    title = parser.title
    signals = interests[:5]
    summary = ""
    if signals:
        summary = f"Personal website signals research in {', '.join(signals)}."
    elif parser.meta_descriptions:
        summary = clean_text(parser.meta_descriptions[0])
        if len(summary) > 180:
            summary = summary[:177].rsplit(" ", 1)[0] + "..."

    return {
        "checked": True,
        "url": website_url,
        "title": title,
        "summary": summary,
        "interests": interests,
        "methods": methods,
        "labLinks": lab_links,
        "emails": emails,
    }


def build_cse_faculty(sources: dict, overrides: dict) -> list[dict]:
    source = source_by_id(sources, "ucsd-cse-faculty")
    parser = parse_html(fetch(source["url"], timeout=15))
    records = []
    seen_urls: set[str] = set()
    faculty_links = []
    profile_rows = []

    for link in parser.links:
        section = link.get("section") or ""
        if section not in ROLE_SECTIONS:
            continue
        url = absolute_url(source["url"], link["href"])
        if "/people/faculty-profiles/" not in url or url in seen_urls:
            continue
        name = clean_text(link["text"])
        if not name or name in {"Faculty Profiles", "Faculty"}:
            continue
        seen_urls.add(url)
        faculty_links.append((name, section, url))

    for index, (name, section, url) in enumerate(faculty_links, start=1):
        print(f"[profile {index}/{len(faculty_links)}] {name}", flush=True)
        try:
            detail_markup = fetch(url, timeout=12)
            detail = parse_html(detail_markup)
            detail_text = " ".join(detail.text_parts)
            email = first_email(detail_text)
            phone = first_phone(detail_text)
            website = link_for_label(detail.links, url, {"Website"})
            full_profile = link_for_label(detail.links, url, {"Full Profile"})
        except Exception as exc:
            print(f"[profile skipped] {name}: {type(exc).__name__}", flush=True)
            email = ""
            phone = ""
            website = None
            full_profile = None
        profile_rows.append(
            {
                "name": name,
                "section": section,
                "url": url,
                "email": email,
                "phone": phone,
                "website": website,
                "fullProfile": full_profile,
            }
        )

    enrichment_by_name: dict[str, dict] = {}
    personal_targets = [
        (row["name"], row["website"]["url"])
        for row in profile_rows
        if row.get("website") and row["website"].get("url")
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=PERSONAL_SITE_WORKERS) as executor:
        future_to_name = {
            executor.submit(enrich_from_personal_site, name, url): name
            for name, url in personal_targets
        }
        for index, future in enumerate(concurrent.futures.as_completed(future_to_name), start=1):
            name = future_to_name[future]
            try:
                enrichment_by_name[name] = future.result()
            except Exception as exc:
                enrichment_by_name[name] = {"checked": False, "reason": type(exc).__name__}
            print(f"[personal {index}/{len(personal_targets)}] {name}", flush=True)

    for row in profile_rows:
        name = row["name"]
        section = row["section"]
        url = row["url"]
        email = row["email"]
        phone = row["phone"]
        website = row["website"]
        full_profile = row["fullProfile"]
        curated = overrides.get(name, {})
        enrichment = enrichment_by_name.get(name, {"checked": False})
        links = [{"label": "Faculty profile", "url": url}]
        if full_profile:
            links.append(full_profile)
        if website:
            links.append({"label": "Website", "url": website["url"]})
        for lab_link in enrichment.get("labLinks", []):
            if lab_link not in links:
                links.append({"label": "Lab / research", "url": lab_link["url"]})
        for extra in curated.get("links", []):
            if extra not in links:
                links.append(extra)

        contacts = []
        if email:
            contacts.append({"type": "email", "label": "Email", "value": email, "href": f"mailto:{email}"})
        elif enrichment.get("emails"):
            email = enrichment["emails"][0]
            contacts.append({"type": "email", "label": "Email", "value": email, "href": f"mailto:{email}"})
        if phone:
            contacts.append({"type": "phone", "label": "Phone", "value": phone, "href": f"tel:{re.sub(r'[^0-9+]', '', phone)}"})

        interests = sorted(set(curated.get("interests", []) + enrichment.get("interests", []))) or ["Computer science"]
        methods = sorted(set(curated.get("methods", []) + enrichment.get("methods", [])))
        summary = curated.get("summary") or enrichment.get("summary")
        if not summary:
            summary = f"Official CSE {section.lower()} profile with source links for current projects and lab information."

        records.append(
            normalize_record(
                {
                    "id": f"ucsd-cse-{slugify(name)}",
                    "kind": "faculty",
                    "name": name,
                    "title": curated.get("title") or section.rstrip("s"),
                    "department": "Computer Science and Engineering",
                    "summary": summary,
                    "people": [{"name": name, "role": section.rstrip("s")}],
                    "interests": interests,
                    "methods": methods,
                    "audiences": curated.get("audiences", ["Undergraduate", "Graduate"]),
                    "contacts": contacts,
                    "links": links,
                    "sourceIds": ["ucsd-cse-faculty"],
                    "enrichment": {
                        "personalSite": {
                            key: value
                            for key, value in enrichment.items()
                            if key in {"checked", "reason", "url", "title", "summary"}
                        }
                    },
                    "confidence": "high" if curated or enrichment.get("checked") else "medium",
                }
            )
        )

    return records


def record_website(record: dict) -> str:
    for link in record.get("links", []):
        if link.get("label") == "Website":
            return link.get("url", "")
    return ""


def apply_personal_enrichment(record: dict, enrichment: dict) -> dict:
    record = dict(record)
    links = list(record.get("links", []))
    existing_urls = {link.get("url") for link in links}
    for lab_link in enrichment.get("labLinks", []):
        if lab_link.get("url") and lab_link["url"] not in existing_urls:
            links.append({"label": "Lab / research", "url": lab_link["url"]})
            existing_urls.add(lab_link["url"])

    contacts = list(record.get("contacts", []))
    has_email = any(contact.get("type") == "email" for contact in contacts)
    if not has_email and enrichment.get("emails"):
        email = enrichment["emails"][0]
        contacts.append({"type": "email", "label": "Email", "value": email, "href": f"mailto:{email}"})

    interests = sorted(set(record.get("interests", []) + enrichment.get("interests", [])))
    methods = sorted(set(record.get("methods", []) + enrichment.get("methods", [])))
    summary = record.get("summary", "")
    if enrichment.get("summary") and summary.startswith("Official CSE"):
        summary = enrichment["summary"]

    record.update(
        {
            "summary": summary,
            "interests": interests or record.get("interests", []),
            "methods": methods,
            "contacts": contacts,
            "links": links,
            "enrichment": {
                "personalSite": {
                    key: value
                    for key, value in enrichment.items()
                    if key in {"checked", "reason", "url", "title", "summary"}
                }
            },
            "confidence": "high" if enrichment.get("checked") else record.get("confidence", "medium"),
        }
    )
    return normalize_record(record)


def enrich_existing_faculty(records: list[dict]) -> list[dict]:
    targets = [(record["id"], record["name"], record_website(record)) for record in records if record_website(record)]
    enrichment_by_id: dict[str, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=PERSONAL_SITE_WORKERS) as executor:
        future_to_id = {
            executor.submit(enrich_from_personal_site, name, url): record_id
            for record_id, name, url in targets
        }
        for index, future in enumerate(concurrent.futures.as_completed(future_to_id), start=1):
            record_id = future_to_id[future]
            try:
                enrichment_by_id[record_id] = future.result()
            except Exception as exc:
                enrichment_by_id[record_id] = {"checked": False, "reason": type(exc).__name__}
            print(f"[personal existing {index}/{len(targets)}] {record_id}", flush=True)
    return [apply_personal_enrichment(record, enrichment_by_id.get(record["id"], {"checked": False})) for record in records]


def merge_links(*link_lists: list[dict]) -> list[dict]:
    result = []
    seen = set()
    for links in link_lists:
        for link in links or []:
            url = link.get("url", "")
            if not url or url in seen:
                continue
            if not url.startswith(("http://", "https://")):
                continue
            result.append({"label": link.get("label") or "Source", "url": url})
            seen.add(url)
    return result


def merge_contacts(*contact_lists: list[dict]) -> list[dict]:
    result = []
    seen = set()
    for contacts in contact_lists:
        for contact in contacts or []:
            value = clean_text(contact.get("value", ""))
            href = clean_text(contact.get("href", ""))
            if contact.get("type") == "email" and not value:
                value = clean_email(href)
            key = href.lower() or f"{contact.get('type', '')}:{value.lower()}"
            if not key or key in seen:
                continue
            if contact.get("type") == "email" and not email_allowed(value):
                continue
            result.append(
                {
                    "type": contact.get("type", "link"),
                    "label": contact.get("label", "Contact"),
                    "value": value,
                    "href": href,
                }
            )
            seen.add(key)
    return result


def merge_enrichment(*enrichment_items: dict) -> dict:
    merged: dict[str, dict] = {}
    for enrichment in enrichment_items:
        for key, value in (enrichment or {}).items():
            if not isinstance(value, dict):
                continue
            existing = merged.get(key)
            if existing is None or (value.get("checked") and not existing.get("checked")):
                merged[key] = value
    return merged


def low_information_summary(summary: str) -> bool:
    lowered = summary.lower()
    return not summary or any(
        marker in lowered
        for marker in (
            "need profile",
            "need department",
            "profile-level enrichment",
            "faculty listing from",
            "directory. research",
        )
    )


def apply_curated_override(record: dict, overrides: dict) -> dict:
    name = canonical_person_name(record.get("name", ""))
    curated = overrides.get(record.get("name", "")) or overrides.get(name)
    if not curated:
        return normalize_record(record)

    updated = dict(record)
    if curated.get("title"):
        updated["title"] = curated["title"]
    if curated.get("summary"):
        updated["summary"] = curated["summary"]
    updated["interests"] = sorted(set(updated.get("interests", []) + curated.get("interests", [])))
    updated["methods"] = sorted(set(updated.get("methods", []) + curated.get("methods", [])))
    updated["audiences"] = sorted(set(updated.get("audiences", []) + curated.get("audiences", [])))
    updated["links"] = merge_links(updated.get("links", []), curated.get("links", []))
    updated["contacts"] = merge_contacts(updated.get("contacts", []), curated.get("contacts", []))
    updated["confidence"] = "high"
    return normalize_record(updated)


def apply_profile_enrichment(record: dict, enrichment: dict) -> dict:
    if not enrichment.get("checked"):
        return normalize_record(record)

    updated = dict(record)
    profile_url = enrichment.get("url", "")
    profile_link = [{"label": "Faculty profile", "url": profile_url}] if profile_url else []
    updated["links"] = merge_links(updated.get("links", []), profile_link, enrichment.get("links", []))

    contacts = []
    if enrichment.get("emails"):
        email = enrichment["emails"][0]
        contacts.append({"type": "email", "label": "Email", "value": email, "href": f"mailto:{email}"})
    updated["contacts"] = merge_contacts(updated.get("contacts", []), contacts)
    updated["interests"] = sorted(set(updated.get("interests", []) + enrichment.get("interests", [])))
    updated["methods"] = sorted(set(updated.get("methods", []) + enrichment.get("methods", [])))

    if title_score(enrichment.get("title", "")) > title_score(updated.get("title", "")):
        updated["title"] = enrichment["title"]
    if enrichment.get("summary") and low_information_summary(updated.get("summary", "")):
        updated["summary"] = enrichment["summary"]

    updated["enrichment"] = merge_enrichment(
        updated.get("enrichment", {}),
        {
            "profile": {
                key: value
                for key, value in enrichment.items()
                if key in {"checked", "reason", "url", "title", "summary"}
            }
        },
    )
    updated["confidence"] = "high" if updated.get("contacts") or enrichment.get("links") else "medium"
    return normalize_record(updated)


def load_profile_cache() -> dict[str, dict]:
    if not PROFILE_CACHE_PATH.exists():
        return {}
    try:
        payload = load_json(PROFILE_CACHE_PATH)
    except Exception:
        return {}
    return payload.get("profiles", {})


def write_profile_cache(cache: dict[str, dict]) -> None:
    payload = {
        "schemaVersion": 1,
        "generatedAt": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "profiles": cache,
    }
    PROFILE_CACHE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def enrich_faculty_profiles(records: list[dict]) -> list[dict]:
    targets = []
    for record in records:
        if record.get("kind") != "faculty":
            continue
        url = profile_url_for_record(record)
        if url:
            targets.append((record["id"], record["name"], url))

    cache = load_profile_cache()
    missing = [(record_id, name, url) for record_id, name, url in targets if not cache.get(url, {}).get("checked")]
    if PROFILE_ENRICH_LIMIT:
        missing = missing[:PROFILE_ENRICH_LIMIT]

    if missing:
        print(f"[profile enrich] fetching {len(missing)} of {len(targets)} profile pages", flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=PROFILE_ENRICH_WORKERS) as executor:
            future_to_target = {
                executor.submit(enrich_from_profile, name, url): (record_id, name, url)
                for record_id, name, url in missing
            }
            for index, future in enumerate(concurrent.futures.as_completed(future_to_target), start=1):
                record_id, name, url = future_to_target[future]
                try:
                    cache[url] = future.result()
                except Exception as exc:
                    cache[url] = {"checked": False, "reason": type(exc).__name__, "url": url}
                print(f"[profile enrich {index}/{len(missing)}] {name}", flush=True)
        write_profile_cache(cache)

    enrichment_by_id = {record_id: cache.get(url, {"checked": False, "url": url}) for record_id, _name, url in targets}
    return [apply_profile_enrichment(record, enrichment_by_id.get(record["id"], {"checked": False})) for record in records]


def best_record(records: list[dict]) -> dict:
    return max(records, key=record_quality)


def best_title(records: list[dict]) -> str:
    return max((record.get("title", "") for record in records), key=title_score, default="Faculty") or "Faculty"


def best_summary(records: list[dict]) -> str:
    summaries = [record.get("summary", "") for record in records if record.get("summary")]
    informative = [summary for summary in summaries if not low_information_summary(summary)]
    if informative:
        return max(informative, key=len)
    return max(summaries, key=len, default="")


def merge_affiliations(records: list[dict]) -> list[dict]:
    by_department: dict[str, dict] = {}
    for record in records:
        for existing in record.get("affiliations", []):
            department = existing.get("department")
            if not department:
                continue
            by_department.setdefault(
                department,
                {
                    "department": department,
                    "title": existing.get("title", record.get("title", "Faculty")),
                    "sourceIds": unique_preserve(existing.get("sourceIds", []) + record.get("sourceIds", [])),
                },
            )
        for department in record_departments(record):
            current = by_department.get(department)
            candidate = {
                "department": department,
                "title": record.get("title") or "Faculty",
                "sourceIds": record.get("sourceIds", []),
            }
            if current is None:
                by_department[department] = candidate
                continue
            current["sourceIds"] = unique_preserve(current.get("sourceIds", []) + candidate.get("sourceIds", []))
            if title_score(candidate["title"]) > title_score(current.get("title", "")):
                current["title"] = candidate["title"]
    return sorted(by_department.values(), key=lambda item: item["department"])


def consolidate_faculty_records(records: list[dict]) -> list[dict]:
    by_person: dict[str, list[dict]] = {}
    non_faculty = []
    for record in records:
        if record.get("kind") != "faculty":
            non_faculty.append(record)
            continue
        key = person_merge_key(record.get("name", ""))
        by_person.setdefault(key, []).append(record)

    consolidated = []
    for key, group in by_person.items():
        if len(group) == 1:
            consolidated.append(normalize_record(group[0]))
            continue
        best = best_record(group)
        departments = unique_preserve([department for record in group for department in record_departments(record)])
        affiliations = merge_affiliations(group)
        title = best_title(group)
        source_ids = unique_preserve([source for record in group for source in record.get("sourceIds", [])])
        merged_record_ids = sorted(
            unique_preserve(
                [
                    record_id
                    for record in group
                    for record_id in [record["id"], *record.get("mergedRecordIds", [])]
                ]
            )
        )
        merged = normalize_record(
            {
                **best,
                "id": f"ucsd-faculty-{key}",
                "kind": "faculty",
                "name": canonical_person_name(best.get("name", "")),
                "title": title,
                "department": best.get("department") if best.get("department") in departments else departments[0],
                "departments": departments,
                "affiliations": affiliations,
                "summary": best_summary(group),
                "people": [{"name": canonical_person_name(best.get("name", "")), "role": title}],
                "interests": sorted({interest for record in group for interest in record.get("interests", [])}),
                "methods": sorted({method for record in group for method in record.get("methods", [])}),
                "audiences": sorted({audience for record in group for audience in record.get("audiences", [])}),
                "contacts": merge_contacts(*[record.get("contacts", []) for record in group]),
                "links": merge_links(*[record.get("links", []) for record in group]),
                "sourceIds": source_ids,
                "mergedRecordIds": merged_record_ids,
                "enrichment": merge_enrichment(*[record.get("enrichment", {}) for record in group]),
                "confidence": max((record.get("confidence", "medium") for record in group), key=lambda value: {"low": 1, "medium": 2, "high": 3}.get(value, 0)),
            }
        )
        consolidated.append(merged)

    return non_faculty + consolidated


def primary_record_url(record: dict) -> str:
    preferred = {
        "Lab site",
        "Lab / research",
        "Website",
        "Center site",
        "Program site",
        "Research area",
    }
    for link in record.get("links", []):
        if link.get("label") in preferred and link.get("url"):
            return canonical_url_key(link["url"])
    for link in record.get("links", []):
        if link.get("url"):
            return canonical_url_key(link["url"])
    return ""


def lab_record_quality(record: dict) -> tuple[int, int, int, int]:
    confidence_score = {"high": 3, "medium": 2, "low": 1}.get(record.get("confidence"), 0)
    link_score = len(record.get("links", []))
    interest_score = len(record.get("interests", []))
    summary_score = len(record.get("summary", ""))
    return confidence_score, link_score, interest_score, summary_score


def consolidate_lab_records(records: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    passthrough = []
    for record in records:
        if record.get("kind") != "lab":
            passthrough.append(record)
            continue
        url = primary_record_url(record)
        if record.get("name"):
            key = f"name:{record.get('department', '')}:{slugify(record.get('name', ''))}"
        else:
            key = f"url:{url}"
        groups.setdefault(key, []).append(record)

    consolidated = []
    for group in groups.values():
        if len(group) == 1:
            consolidated.append(normalize_record(group[0]))
            continue
        best = max(group, key=lab_record_quality)
        source_ids = unique_preserve([source for record in group for source in record.get("sourceIds", [])])
        directions = unique_preserve(
            [
                direction
                for record in group
                for direction in record.get("researchDirections", record.get("interests", []))
            ]
        )
        merged = normalize_record(
            {
                **best,
                "id": best["id"],
                "name": best.get("name", ""),
                "summary": max((record.get("summary", "") for record in group), key=len, default=""),
                "people": unique_people(group),
                "interests": sorted({interest for record in group for interest in record.get("interests", [])}),
                "researchDirections": directions,
                "methods": sorted({method for record in group for method in record.get("methods", [])}),
                "audiences": sorted({audience for record in group for audience in record.get("audiences", [])}),
                "contacts": merge_contacts(*[record.get("contacts", []) for record in group]),
                "links": merge_links(*[record.get("links", []) for record in group]),
                "sourceIds": source_ids,
                "confidence": max(
                    (record.get("confidence", "medium") for record in group),
                    key=lambda value: {"low": 1, "medium": 2, "high": 3}.get(value, 0),
                ),
            }
        )
        consolidated.append(merged)

    return passthrough + consolidated


def unique_people(records: list[dict]) -> list[dict]:
    seen = set()
    people = []
    for record in records:
        for person in record.get("people", []):
            name = clean_text(person.get("name", ""))
            role = clean_text(person.get("role", ""))
            key = (name.lower(), role.lower())
            if not name or key in seen:
                continue
            seen.add(key)
            people.append({"name": name, "role": role or "Research contact"})
    return people


def load_existing_records_for_source(source_id: str) -> list[dict]:
    if not OUTPUT_PATH.exists():
        return []
    data = load_json(OUTPUT_PATH)
    return [
        normalize_record(record)
        for record in data.get("records", [])
        if source_id in record.get("sourceIds", [])
    ]


def is_auto_lab_record(record: dict) -> bool:
    if record.get("discovery", {}).get("method") == "generic_lab_directory":
        return True
    return any(str(source_id).endswith("-labs-auto") for source_id in record.get("sourceIds", []))


def is_auto_research_area_record(record: dict) -> bool:
    if record.get("discovery", {}).get("method") == "generic_research_area_directory":
        return True
    if record.get("discovery", {}).get("method") == "department_research_overview_fallback":
        return True
    return any(str(source_id).endswith("-research-areas-auto") for source_id in record.get("sourceIds", []))


def load_existing_records_without_auto_discovery() -> list[dict]:
    if not OUTPUT_PATH.exists():
        return []
    data = load_json(OUTPUT_PATH)
    return [
        normalize_record(record)
        for record in data.get("records", [])
        if not is_auto_lab_record(record) and not is_auto_research_area_record(record)
    ]


def build_cse_research_areas(sources: dict) -> list[dict]:
    source = source_by_id(sources, "ucsd-cse-research")
    parser = parse_html(fetch(source["url"]))
    records = []
    seen = set()

    for link in parser.links:
        label = clean_text(link["text"])
        if label not in RESEARCH_AREA_TAGS or label in seen:
            continue
        seen.add(label)
        interests = RESEARCH_AREA_TAGS[label]
        records.append(
            normalize_record(
                {
                    "id": f"ucsd-cse-area-{slugify(label)}",
                    "kind": "research_area",
                    "name": label,
                    "title": "CSE research area",
                    "department": "Computer Science and Engineering",
                    "summary": f"Official CSE research area: {label}.",
                    "interests": interests,
                    "methods": [],
                    "audiences": ["Undergraduate", "Graduate"],
                    "links": [
                        {"label": "Research area", "url": absolute_url(source["url"], link["href"])},
                        {"label": "Source", "url": source["url"]},
                    ],
                    "sourceIds": ["ucsd-cse-research"],
                    "confidence": "high",
                }
            )
        )

    return records


def normalize_record(record: dict) -> dict:
    record.setdefault("kind", "lab")
    record.setdefault("department", "UC San Diego")
    record.setdefault("summary", "")
    record.setdefault("title", "")
    record.setdefault("people", [])
    record.setdefault("interests", [])
    record.setdefault("methods", [])
    record.setdefault("audiences", ["Undergraduate", "Graduate"])
    record.setdefault("contacts", [])
    record.setdefault("links", [])
    record.setdefault("sourceIds", [])
    record.setdefault("confidence", "medium")
    if record.get("kind") == "faculty" and record.get("name"):
        record["name"] = canonical_person_name(record["name"])
        query = f'site:linkedin.com/in "{record["name"]}" "UC San Diego"'
        record.setdefault("linkedinSearchUrl", f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}")
    departments = record_departments(record)
    record["departments"] = departments or [record.get("department", "UC San Diego")]
    record["department"] = record["departments"][0]
    record["interests"] = sorted(set(record["interests"]))
    if record.get("researchDirections"):
        record["researchDirections"] = sorted(set(record["researchDirections"]))
    record["methods"] = sorted(set(record["methods"]))
    record["audiences"] = sorted(set(record["audiences"]))
    record["links"] = merge_links(record.get("links", []))
    record["contacts"] = merge_contacts(record.get("contacts", []))
    return record


def build_facets(records: list[dict]) -> dict:
    return {
        "departments": sorted({department for record in records for department in record_departments(record)}),
        "kinds": sorted({record["kind"] for record in records if record.get("kind")}),
        "interests": sorted({interest for record in records for interest in record.get("interests", [])}),
    }


def build_coverage(sources: dict, records: list[dict]) -> list[dict]:
    record_counts = {}
    source_ids_by_department = {}
    for record in records:
        for department in record_departments(record):
            record_counts[department] = record_counts.get(department, 0) + 1
            source_ids_by_department[department] = unique_preserve(
                source_ids_by_department.get(department, []) + record.get("sourceIds", [])
            )

    candidates_by_department = {}
    if CANDIDATES_PATH.exists():
        candidates_data = load_json(CANDIDATES_PATH)
        for item in candidates_data.get("departments", []):
            candidates_by_department[item["department"]] = item.get("candidates", [])

    if DEPARTMENTS_PATH.exists():
        registry = load_json(DEPARTMENTS_PATH)
        coverage = []
        for department in registry.get("departments", []):
            name = department["name"]
            count = record_counts.get(name, 0)
            status = "has_records" if count else "source_candidates"
            if name == "Computer Science and Engineering":
                status = "crawler"
            coverage.append(
                {
                    "department": name,
                    "school": department.get("school", ""),
                    "homepage": department.get("homepage", ""),
                    "status": status,
                    "recordCount": count,
                    "sourceCandidates": candidates_by_department.get(name, [])[:10],
                    "sourceIds": source_ids_by_department.get(name, [])[:10],
                }
            )
        return coverage

    coverage = sources.get("coverage", [])
    for item in coverage:
        item["recordCount"] = record_counts.get(item.get("department"), 0)
    return coverage


def main() -> None:
    sources = load_json(SOURCES_PATH)
    manual = load_json(MANUAL_PATH)
    overrides = load_json(OVERRIDES_PATH)
    reuse_existing_index = os.environ.get("RESEARCH_FINDER_REUSE_EXISTING_INDEX") == "1"
    if reuse_existing_index:
        records = load_existing_records_without_auto_discovery()
        print(f"[reuse] Reusing {len(records)} existing records before lab/research-area refresh", flush=True)
    else:
        records = [normalize_record(record) for record in manual.get("records", [])]
    reuse_cached_core = (
        os.environ.get("RESEARCH_FINDER_OFFLINE") == "1"
        or os.environ.get("RESEARCH_FINDER_REUSE_CSE") == "1"
        or reuse_existing_index
    )

    enabled_kinds = {source["kind"] for source in sources["sources"] if source.get("enabled")}
    if "faculty_directory" in enabled_kinds and not reuse_existing_index:
        if reuse_cached_core:
            existing_faculty = [
                record for record in load_existing_records_for_source("ucsd-cse-faculty")
                if record.get("kind") == "faculty"
            ]
            print(f"[reuse] Reusing {len(existing_faculty)} CSE faculty records", flush=True)
            records.extend(existing_faculty)
        else:
            try:
                records.extend(build_cse_faculty(sources, overrides))
            except Exception as exc:
                print(f"[fallback] CSE faculty crawl failed: {type(exc).__name__}: {exc}", flush=True)
                existing_faculty = [
                    record for record in load_existing_records_for_source("ucsd-cse-faculty")
                    if record.get("kind") == "faculty"
                ]
                if not existing_faculty:
                    raise
                records.extend(enrich_existing_faculty(existing_faculty))
    if "research_areas" in enabled_kinds and not reuse_existing_index:
        if reuse_cached_core:
            existing_areas = [
                record for record in load_existing_records_for_source("ucsd-cse-research")
                if record.get("kind") == "research_area"
            ]
            print(f"[reuse] Reusing {len(existing_areas)} CSE research area records", flush=True)
            records.extend(existing_areas)
        else:
            try:
                records.extend(build_cse_research_areas(sources))
            except Exception as exc:
                print(f"[fallback] CSE research areas crawl failed: {type(exc).__name__}: {exc}", flush=True)
                existing_areas = [
                    record for record in load_existing_records_for_source("ucsd-cse-research")
                    if record.get("kind") == "research_area"
                ]
                if not existing_areas:
                    raise
                records.extend(existing_areas)

    if not reuse_existing_index:
        generic_faculty = build_generic_faculty_from_candidates()
        if generic_faculty:
            print(f"[generic faculty] total {len(generic_faculty)}", flush=True)
            records.extend(generic_faculty)

    generic_labs = build_generic_labs_from_candidates()
    if generic_labs:
        print(f"[generic labs] total {len(generic_labs)}", flush=True)
        records.extend(generic_labs)

    generic_research_areas = build_generic_research_areas_from_candidates()
    if generic_research_areas:
        print(f"[generic research areas] total {len(generic_research_areas)}", flush=True)
        records.extend(generic_research_areas)

    records.extend(build_department_research_overview_fallbacks(records))

    if not reuse_existing_index:
        catalog_faculty = build_catalog_faculty_records()
        if catalog_faculty:
            print(f"[catalog faculty] total {len(catalog_faculty)}", flush=True)
            records.extend(catalog_faculty)

        biology_faculty = build_biology_api_faculty_records()
        if biology_faculty:
            records.extend(biology_faculty)
        biology_topics = build_biology_topic_records()
        if biology_topics:
            records.extend(biology_topics)

    deduped = {}
    for record in records:
        normalized = apply_curated_override(normalize_record(record), overrides)
        deduped[normalized["id"]] = choose_better_record(deduped.get(normalized["id"]), normalized)
    records = consolidate_faculty_records(list(deduped.values()))
    records = consolidate_lab_records(records)
    if not reuse_existing_index:
        records = enrich_faculty_profiles(records)
    records = sorted(records, key=lambda item: (item["department"], item["kind"], item["name"]))

    output = {
        "schemaVersion": 1,
        "generatedAt": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "university": sources["university"],
        "sources": sources["sources"],
        "coverage": build_coverage(sources, records),
        "facets": build_facets(records),
        "records": records,
    }

    # Slim + minify so the page only fetches fields the UI reads.
    from optimize_index import slim_index  # local import to avoid hard dep

    slim = slim_index(output)
    OUTPUT_PATH.write_text(
        json.dumps(slim, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH} with {len(records)} records (slim)")


if __name__ == "__main__":
    main()
