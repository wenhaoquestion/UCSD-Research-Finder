#!/usr/bin/env python3
"""Refresh public UCSD teaching evidence without modifying the canonical atlas.

Only explicit instructor assignments are collected. Catalogs supply titles only.
Scheduled means advertised/planned, never proof that teaching actually happened.
The department pages and their publicly linked exports are the source of truth.
Run with --refresh to refetch; --rematch rebinds saved evidence after a roster update.
Uses the standard library and certificate-validating system curl fallback.
PDF sources additionally use pdftotext and optional pdfplumber (--pdf-python).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from zoneinfo import ZoneInfo
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TERMS = ["Fall 2026", "Winter 2027", "Spring 2027"]
DEFAULT_CACHE = Path(tempfile.gettempdir()) / "research-atlas-teaching-cache"
COURSE_RE = re.compile(r"^([A-Z]{2,5})[ -]*(\d+[A-Z]*)(?:\b|[ .:])", re.I)
NO_INSTRUCTOR = re.compile(r"^(?:staff|tbd|tba|not offered|various|cancelled|canceled|none|n/?a|\u2714|\u2713|x)(?:\W|$)", re.I)


def spec(key, department, url, parser, **extra):
    return {"id": key, "department": department, "url": url, "parser": parser, **extra}


SOURCES = [
    spec("math-2026", "Mathematics", "https://www.math.ucsd.edu/students/planned-course-offerings?year=2026-2027", "matrix", courseCol=0, titleCol=1, termCols=[3, 4, 5]),
    spec("ece-2026", "Electrical and Computer Engineering", "https://www.ece.ucsd.edu/ece-tentative-course-list", "joined"),
    spec("physics-2026", "Physics", "https://www.physics.ucsd.edu/students/courseofferings", "matrix", courseCol=0, titleCol=1, termCols=[4, 5, 6], prefix="PHYS"),
    spec("econ-2026", "Economics", "https://economics.ucsd.edu/undergraduate-program/resources/courses/", "joined"),
    spec("history-fall-2026", "History", "https://history.ucsd.edu/courses/courses-fall.html", "simple", term="Fall 2026"),
    spec("philosophy-fall-2026", "Philosophy", "https://philosophy.ucsd.edu/courses/current-quarter.html", "simple", term="Fall 2026"),
    spec("philosophy-2026", "Philosophy", "https://philosophy.ucsd.edu/courses/year-at-a-glance-26-27.html", "philosophy"),
    spec("psychology-grad-2026", "Psychology", "https://psychology.ucsd.edu/graduate-program/current-students/graduate-courses/course-offerings.html", "simple"),
    spec("psychology-undergrad-2026", "Psychology", "https://psychology.ucsd.edu/undergraduate-program/courses/2026-2027-courses.html", "no_instructors"),
    spec("mae-2026", "Mechanical & Aerospace Engineering", "https://mae.ucsd.edu/courses", "no_instructors"),
    spec("cse-2026", "Computer Science and Engineering", "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYc7qv9lyLh-F8EzlVcE2td3jObRp2B88ZIru9XQw0_G70kfDCjVRo64EWWDdEEkzyc_s1sX2JMfqb/pub?gid=684727614&single=true&output=csv", "csv", titleCol=1, termCols=[2, 3, 4], landingUrl="https://cse.ucsd.edu/undergraduate/tentative-course-offerings"),
    spec("cogs-2026", "Cognitive Science", "https://docs.google.com/spreadsheets/d/e/2PACX-1vR-pFK5zou3FdqmceGomf_NC47wKhhVhQxe5uwp18Kw32AyJGG3-Bfk-cJPac5YjW26rcCN-wVYWLj0/pub?gid=866922720&single=true&output=csv", "csv", termCols=[1, 2, 3], landingUrl="https://cogsci.ucsd.edu/undergraduates/courses/index.html", titleSourceId="cogs-catalog"),
    spec("anthropology-2026", "Anthropology", "https://docs.google.com/document/d/1UgfUjs_Xbj3eizuMloz0RueXwW84kEVu5peV6yyCZQk/export?format=html", "anthropology", landingUrl="https://anthropology.ucsd.edu/undergraduate-studies/courses/index.html"),
    spec("linguistics", "Linguistics", "https://linguistics.ucsd.edu/undergrad/courses/index.html", "linguistics"),
    spec("public-health", "Public Health", "https://ph.ucsd.edu/undergrad/courses/index.html", "public_health", titleSourceId="ph-catalog"),
    spec("chemistry-undergrad-2026", "Chemistry & Biochemistry", "https://chem-web.ucsd.edu/ext/getCourseCatalogList/?level=undergrad&year=2026-2027", "chemistry", landingUrl="https://chem-web.ucsd.edu/ext/ugcourses.html?year=2026-2027"),
    spec("chemistry-grad-2026", "Chemistry & Biochemistry", "https://chem-web.ucsd.edu/ext/getCourseCatalogList/?level=grad&year=2026-2027", "chemistry", landingUrl="https://chem-web.ucsd.edu/ext/grcourses.html?year=2026-2027"),
    spec("biology-2026", "Biological Sciences", "https://public.biology.ucsd.edu/api/prod/website-data/v1/courses?termCode=FA26&termCode=WI27&termCode=SP27", "biology", landingUrl="https://biology.ucsd.edu/education/undergrad/course/course-offerings.html"),
    spec("cogs-catalog", "Cognitive Science", "https://catalog.ucsd.edu/courses/COGS.html", "titles_only"),
    spec("ph-catalog", "Public Health", "https://catalog.ucsd.edu/courses/PH.html", "titles_only"),
    spec("communication-2026", "Communication", "https://communication.ucsd.edu/undergrad/courses/index.html", "communication"),
    spec("visual-arts-2026", "Visual Arts", "https://docs.google.com/spreadsheets/d/1pY1l3IxffuFeA1nXXx-mjnD2flb3ZFBr/export?format=csv", "visual_arts", landingUrl="https://visarts.ucsd.edu/undergrad/annual-schedule.html"),
    spec("political-science-2026", "Political Science", "https://polisci.ucsd.edu/undergrad/political-science-courses/_Undergraduate-Tentative-Schedule-2026---2027-2.pdf", "pdf_text"),
    spec("sociology-2026", "Sociology", "https://www.sociology.ucsd.edu/undergraduate/26-27-UG-Course-List-22.pdf", "pdf_tables"),
    spec("cse-grad-2026", "Computer Science and Engineering", "https://docs.google.com/spreadsheets/d/e/2PACX-1vTDTNtlPYvGvEm2NAlRACOPxduVhbecIA5yZFl9Bduo6lwZ9tWQH_DKPGg2MqVm-kBFY42Syb52hO33/pub?gid=76770152&single=true&output=csv", "csv", titleCol=1, termCols=[2, 3, 4], landingUrl="https://cse.ucsd.edu/graduate/tentative-2026-2027-cse-graduate-course-offerings"),
    spec("structural-engineering-2026", "Structural Engineering", "https://se.ucsd.edu/academics/undergraduate-program/course-offerings", "matrix", courseCol=0, titleCol=1, termCols=[2, 3, 4]),
    spec("astronomy-2026", "Astronomy and Astrophysics", "https://astro.ucsd.edu/undergraduate/courses/index.html", "matrix", courseCol=0, titleCol=1, termCols=[2, 3, 4], prefix="ASTR"),
    spec("data-science-grad-2026", "Halicioğlu Data Science Institute", "https://datascience.ucsd.edu/graduate/graduate-courses/course-offerings/", "no_instructors"),
]
for _quarter, _year, _term_code in [("fall", 2026, "FA26"), ("winter", 2027, "WI27"), ("spring", 2027, "SP27")]:
    for _level, _query in [("ug", "UD,LD"), ("phd", "GR")]:
        SOURCES.append(spec(f"literature-{_quarter}-{_level}", "Literature",
            f"https://lit-courses.ucsd.edu/cms-reports/cms-course_desc.php?acmc={_query}&qtr={_term_code}", "literature",
            term=f"{_quarter.title()} {_year}", landingUrl=f"https://literature.ucsd.edu/courses/courseofferings/2026-2027-{_quarter}-{_level}.html"))

# The registrar's Schedule of Classes lists the instructor of record for every
# section campus-wide. Each Schedule department maps to the one atlas department
# whose faculty own its courses; programs and colleges taught across departments
# are not mapped, because same-department matching would have nothing to bind to.
SOC_BASE = "https://act.ucsd.edu/scheduleOfClasses/"
SOC_LANDING = SOC_BASE + "scheduleOfClassesStudent.htm"
SOC_DEPARTMENTS = {
    "ANTH": "Anthropology", "ASTR": "Astronomy and Astrophysics", "BENG": "Bioengineering",
    "BIOL": "Biological Sciences", "CMM": "Cellular & Molecular Medicine", "CHEM": "Chemistry & Biochemistry",
    "COGS": "Cognitive Science", "COMM": "Communication", "CSE": "Computer Science and Engineering",
    "DSC": "Halicioğlu Data Science Institute", "DERM": "Dermatology", "ECON": "Economics",
    "EDS": "Education Studies", "ECE": "Electrical and Computer Engineering", "EMED": "Emergency Medicine",
    "ETHN": "Ethnic Studies", "GPS": "Global Policy and Strategy", "HIST": "History", "LING": "Linguistics",
    "LIT": "Literature", "MATH": "Mathematics", "MAE": "Mechanical & Aerospace Engineering", "MED": "Medicine",
    "MUS": "Music", "NENG": "NanoEngineering", "NEU": "Neurosciences",
    "OBG": "Obstetrics, Gynecology & Reproductive Sciences", "RMED": "Obstetrics, Gynecology & Reproductive Sciences",
    "PATH": "Pathology", "PEDS": "Pediatrics", "PHAR": "Pharmacology", "CLPH": "Pharmacy and Pharmaceutical Sciences",
    "PHIL": "Philosophy", "PHYS": "Physics", "POLI": "Political Science", "PSY": "Psychiatry", "PSYC": "Psychology",
    "SPH": "Public Health", "RMAS": "Radiation Medicine", "RAD": "Radiology", "RSM": "Rady School of Management",
    "SIO": "Scripps Institution of Oceanography", "SOC": "Sociology", "SE": "Structural Engineering",
    "THEA": "Theatre & Dance", "USP": "Urban Studies & Planning", "UROL": "Urology", "VIS": "Visual Arts",
}
SOC_QUARTERS = {"FA": "Fall", "WI": "Winter", "SP": "Spring"}
# Independent study, internships, exams, and review sessions list supervisors or
# proctors rather than a taught class.
SOC_TEACHING_TYPES = {"LE", "SE", "LA", "DI", "ST", "TU", "CL", "PR", "FW", "CO", "PB"}
SOC_EXCLUDED_TITLE = re.compile(r"\b(?:independent study|directed (?:group )?study|special stud(?:y|ies)|thesis|dissertation|teaching apprentice|graduate research|doctoral research|honors research)\b", re.I)
SOC_PAGE_RE = re.compile(r"Page\s*\(\s*\d+(?:&nbsp;|\s)+of(?:&nbsp;|\s)+(\d+)\s*\)")


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def course_code(value: str, prefix: str = "") -> str | None:
    value = clean(value)
    if prefix:
        value = f"{prefix} {value}"
    match = COURSE_RE.match(value)
    if not match:
        return None
    number = re.sub(r"^0+(?=\d)", "", match[2].upper())
    return f"{match[1].upper()} {number}"


class ScheduleHTML(HTMLParser):
    """Keep cell boundaries, line breaks, row spans, and nearest term heading."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self.blocks = []
        self.headings = []
        self._row = []
        self._cell = None
        self._spans = {}
        self._column = 0
        self._block = None
        self._skip = 0
        self._table_depth = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag in {"script", "style"}:
            self._skip += 1
        if self._skip:
            return
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._spans = {}
        if tag == "tr":
            self._row, self._column = [], 0
        if tag in {"td", "th"}:
            while self._column in self._spans:
                value, remaining = self._spans[self._column]
                self._row.append(value)
                if remaining == 1:
                    del self._spans[self._column]
                else:
                    self._spans[self._column] = (value, remaining - 1)
                self._column += 1
            self._cell = {"parts": [], "rowspan": int(attr.get("rowspan", 1)), "colspan": int(attr.get("colspan", 1))}
        if tag in {"br", "p", "div", "li"} and self._cell:
            self._cell["parts"].append("\n")
        if tag in {"h1", "h2", "h3", "h4", "p"}:
            self._block = {"tag": tag, "class": attr.get("class", ""), "parts": []}

    def handle_data(self, data):
        if self._skip:
            return
        if self._cell is not None:
            self._cell["parts"].append(data)
        if self._block is not None:
            self._block["parts"].append(data)

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._skip = max(0, self._skip - 1)
            return
        if self._skip:
            return
        if tag in {"td", "th"} and self._cell is not None:
            value = "\n".join(clean(line) for line in "".join(self._cell["parts"]).splitlines() if clean(line))
            for _ in range(self._cell["colspan"]):
                self._row.append(value)
                if self._cell["rowspan"] > 1:
                    self._spans[self._column] = (value, self._cell["rowspan"] - 1)
                self._column += 1
            self._cell = None
        if tag == "tr" and self._row:
            self.rows.append({"cells": self._row, "headings": self.headings[-8:]})
            self._row = []
        if tag == "table":
            self._table_depth = max(0, self._table_depth - 1)
        if self._block and tag == self._block["tag"]:
            value = clean("".join(self._block["parts"]))
            self.blocks.append({"tag": tag, "text": value, "class": self._block["class"]})
            if tag.startswith("h") and value:
                self.headings.append(value)
            self._block = None


def html_data(body):
    parser = ScheduleHTML()
    parser.feed(body)
    return parser


def instructor_names(value, *, comma_separated=False):
    # Section IDs and Primary/Secondary labels are not part of a person's name.
    value = re.sub(r"\([^)]*\)|\([^)]*$", "", value)
    value = re.sub(r"\b\d{3}:\s*", "", value)
    value = re.sub(r"\b(?:Professor|Prof\.|Dr\.)\s+", "", value)
    parts = re.split(r"\n|;|\s+&\s+|\s+/\s+|\s+and\s+", value)
    if comma_separated:
        parts = [part for segment in parts for part in segment.split(",")]
    output = []
    for part in parts:
        name = clean(part).strip("* ,:.")
        if name and not NO_INSTRUCTOR.match(name) and re.fullmatch(r"[\w\s.,'’\-]+", name) and name not in output:
            output.append(name)
    return output


def term_status(term, as_of):
    """Past schedule evidence remains advertised, not proof of completed teaching."""
    match = re.match(r"(Fall|Winter|Spring|Summer(?: [123])?) (\d{4})$", term or "")
    if not match:
        return "undated"
    month = {"Fall": 12, "Winter": 3, "Spring": 6, "Summer": 9, "Summer 1": 8, "Summer 2": 9, "Summer 3": 9}[match[1]]
    boundary = dt.date(int(match[2]), month, 28)
    return "historical" if boundary < as_of else "scheduled"


def emit(records, source, meta, as_of, code, title, term, name, evidence, **extra):
    if not code or not name or NO_INSTRUCTOR.match(name):
        return
    records.append({
        "courseCode": code, "title": clean(title) or None, "titleStatus": "captured" if clean(title) else "not_published_in_captured_sources", "term": term,
        "status": term_status(term, as_of), "sourceUrl": source.get("landingUrl", source["url"]),
        "dataUrl": source["url"], "sourceId": source["id"],
        "observedAt": meta["observedAt"], "evidence": clean(evidence)[:900],
        "instructorName": name, "department": source["department"],
        "assignmentBasis": "advertised_department_schedule", "isTentative": True,
        **extra,
    })


def parse_source(source, body, meta, as_of, titles):
    records = []
    parser = source["parser"]
    if parser in {"titles_only", "no_instructors"}:
        return records
    if parser == "pdf_text":
        term = None
        for line in body.splitlines():
            heading = re.fullmatch(r"\s*(FALL|WINTER|SPRING) (20\d{2})\s*", line)
            if heading:
                term = f"{heading[1].title()} {heading[2]}"
                continue
            cells = re.split(r"\s{2,}", line.strip())
            if term and len(cells) == 3 and re.fullmatch(r"\d+[A-Z]*", cells[0]):
                for name in instructor_names(cells[2]):
                    emit(records, source, meta, as_of, "POLI " + cells[0], cells[1], term, name, f"{term} | " + " | ".join(cells), sourceDateNote="PDF states Last updated February 11, 2025 while explicitly labeling terms 2026–2027; schedule needs confirmation.")
        return records
    if parser == "pdf_tables":
        for table in json.loads(body):
            for row in table:
                cells = [cell or "" for cell in row]
                if len(cells) != 6 or not re.fullmatch(r"\d+[A-Z]*\**", cells[0]):
                    continue
                for cell, term in zip(cells[3:], TERMS):
                    for name in instructor_names(cell):
                        emit(records, source, meta, as_of, "SOCI " + cells[0].rstrip("*"), cells[1], term, name, f"SOCI {cells[0]} | {cells[1]} | {term}: {cell}")
        return records
    if parser == "literature":
        for entry in re.split(r'<div\s+class="course_desc">', body)[1:]:
            course = re.search(r'<p\s+class="course">(.*?)</p>', entry, re.S)
            instructor = re.search(r'<span\s+class="instructor">(.*?)</p>', entry, re.S)
            if not course or not instructor:
                continue
            course_text = html_data("<p>" + course[1] + "</p>").blocks[0]["text"]
            instructor_text = html_data("<p>" + instructor[1] + "</p>").blocks[0]["text"]
            match = COURSE_RE.match(course_text)
            if not match:
                continue
            for name in instructor_names(instructor_text):
                emit(records, source, meta, as_of, course_code(course_text), course_text[match.end():].lstrip(" .:-"), source["term"], name, f"{source['term']} | {course_text} | {name}")
        return records
    if parser == "visual_arts":
        for row in csv.reader(io.StringIO(body)):
            if len(row) < 7:
                continue
            for col, term in zip([1, 3, 5], TERMS):
                match = COURSE_RE.match(row[col])
                if not match:
                    continue
                for name in instructor_names(row[col + 1]):
                    emit(records, source, meta, as_of, course_code(row[col]), row[col][match.end():].lstrip("* .:-"), term, name, f"{row[col]} | {term}: {row[col + 1]}")
        return records
    if parser == "chemistry":
        for row in json.loads(body):
            for quarter, term in zip(["fall", "winter", "spring"], TERMS):
                for name in instructor_names(row.get(quarter, "")):
                    emit(records, source, meta, as_of, course_code(row["course"]), row["course_title"], term, name, f"{row['course']} | {row['course_title']} | {term}: {row.get(quarter, '')}")
        return records
    if parser == "biology":
        for row in json.loads(body)["courses"]["classes"]:
            course = row["course"]
            if not course.get("isApprovedCourse", False):
                continue
            quarter = row["termCode"]
            term = {"FA": "Fall", "WI": "Winter", "SP": "Spring"}.get(quarter[:2])
            if term is None:
                continue
            term += f" 20{quarter[2:]}"
            code = course_code(course["subjectCode"] + " " + course["courseCode"])
            for teacher in row.get("instructors", []):
                name = clean(teacher.get("fname", "") + " " + teacher.get("lname", ""))
                emit(records, source, meta, as_of, code, course["title"], term, name, f"{code} | {course['title']} | {term} | {name}")
        return records
    if parser == "csv":
        csv_rows = list(csv.reader(io.StringIO(body)))
        if not csv_rows or [clean(csv_rows[0][col]) for col in source["termCols"]] != TERMS:
            raise ValueError("Published CSV term headers changed; refusing to assign old term labels")
        for row in csv_rows[1:]:
            if len(row) <= max(source["termCols"]):
                continue
            code = course_code(row[0])
            title = row[source["titleCol"]] if "titleCol" in source else titles.get(code, "")
            for col, term in zip(source["termCols"], TERMS):
                for name in instructor_names(row[col]):
                    extra = {"titleSourceUrl": "https://catalog.ucsd.edu/courses/COGS.html"} if "titleSourceId" in source else {}
                    emit(records, source, meta, as_of, code, title, term, name, f"{row[0]} | {title} | {term}: {row[col]}", **extra)
        return records
    document = html_data(body)
    if parser in {"matrix", "joined", "philosophy"} and not re.search(r"(?:2026\s*[-–/]\s*(?:2027|27)|AY\s*26/27)", " ".join(document.headings)):
        raise ValueError("Expected 2026–2027 schedule heading missing; review source before assigning terms")
    if parser == "simple" and source.get("term"):
        quarter, year = source["term"].split()
        if not any(re.fullmatch(rf"{quarter}(?: Quarter)? {year}", h, re.I) for h in document.headings):
            raise ValueError("Current-quarter heading changed; refusing to assign the configured old term")
    if parser == "linguistics":
        term, code, title = None, None, ""
        for block in document.blocks:
            text = block["text"]
            if re.fullmatch(r"(?:Fall|Winter|Spring|Summer(?: Session)? [123]?)\s*20\d{2}", text):
                term, code = text.replace("Summer Session", "Summer"), None
            elif block["tag"].startswith("h"):
                code, title = course_code(text), ""
            elif code and block["tag"] == "p":
                if text.startswith("Instructor:"):
                    if term and int(term[-4:]) >= 2025:
                        for name in instructor_names(text.split(":", 1)[1]):
                            emit(records, source, meta, as_of, code, title, term, name, f"{term} | {code} | {title} | {text}")
                    code = None
                elif not title:
                    title = text
        return records
    ph_terms = []
    for row in document.rows:
        cells = row["cells"]
        if parser == "matrix":
            if len(cells) <= max(source["termCols"]):
                continue
            code = course_code(cells[source["courseCol"]], source.get("prefix", ""))
            if not code:
                continue
            for col, term in zip(source["termCols"], TERMS):
                for name in instructor_names(cells[col], comma_separated=source.get("prefix") == "PHYS"):
                    emit(records, source, meta, as_of, code, cells[source["titleCol"]], term, name, f"{code} | {cells[source['titleCol']]} | {term}: {cells[col]}")
        elif parser == "joined":
            if len(cells) < 4:
                continue
            match = COURSE_RE.match(clean(cells[0]))
            if not match:
                continue
            code = course_code(cells[0])
            title = clean(cells[0])[match.end():].lstrip(" .:")
            for col, term in zip([1, 2, 3], TERMS):
                for name in instructor_names(cells[col]):
                    emit(records, source, meta, as_of, code, title, term, name, f"{cells[0]} | {term}: {cells[col]}")
        elif parser == "simple":
            if len(cells) != 3 or not course_code(cells[0]):
                continue
            term = source.get("term")
            if not term:
                term = next((h for h in reversed(row["headings"]) if re.fullmatch(r"(?:Fall|Winter|Spring) 20\d{2}", h)), None)
            for name in instructor_names(cells[2]):
                emit(records, source, meta, as_of, course_code(cells[0]), cells[1], term, name, f"{term} | " + " | ".join(cells))
        elif parser == "anthropology":
            if len(cells) != 3:
                continue
            for cell, term in zip(cells, TERMS):
                lines = [clean(v) for v in cell.splitlines() if clean(v)]
                if len(lines) < 2 or not course_code(lines[0]):
                    continue
                match = COURSE_RE.match(lines[0])
                # Export preserves the explicit instructor paragraph following the title.
                name = lines[-1]
                if not re.fullmatch(r"[\w’' .-]+,\s*[\w’' .-]+", name):
                    continue
                emit(records, source, meta, as_of, course_code(lines[0]), lines[0][match.end():].lstrip(" .:"), term, name, cell)
        elif parser == "philosophy":
            if len(cells) != 4:
                continue
            for cell, term in zip(cells[1:], TERMS):
                lines = [clean(v) for v in cell.splitlines() if clean(v)]
                if len(lines) < 2:
                    continue
                match = re.match(r"(\d+[A-Z]?)\.\s*(.+)", lines[0])
                if not match:
                    continue
                name_line = re.split(r"\s+(?:M[WT]?[WF]?|TTh|MWF|MW|Tu|Th|W|TBD)\b|\s+\d{1,2}[:\-]", lines[1])[0]
                for name in instructor_names(name_line):
                    emit(records, source, meta, as_of, "PHIL " + match[1], match[2], term, name, cell)
        elif parser == "public_health":
            if any(re.fullmatch(r"Fall 20\d{2}", clean(c)) for c in cells):
                ph_terms = [clean(c) for c in cells[1:]]
            code = course_code(cells[0])
            if not code or not ph_terms:
                continue
            for cell, term in zip(cells[1:4], ph_terms[:3]):
                # Paragraph boundaries are preserved; repeated names are deduplicated.
                for name in instructor_names(cell):
                    emit(records, source, meta, as_of, code, titles.get(code, ""), term, name, f"{code} | {term}: {cell}", titleSourceUrl="https://catalog.ucsd.edu/courses/PH.html")
        elif parser == "communication":
            if len(cells) != 4 or not re.fullmatch(r"\d+[A-Z]*", cells[1]):
                continue
            term = next((h.title() for h in reversed(row["headings"]) if re.fullmatch(r"(?:FALL|WINTER|SPRING) 20\d{2}", h)), None)
            if not term:
                continue
            for name in instructor_names(cells[3]):
                emit(records, source, meta, as_of, "COMM " + cells[1], cells[2], term, name, f"{term} | COMM " + " | ".join(cells[1:]))
    return records


def name_tokens(name):
    name = re.sub(r"\([^)]*\)", "", name)
    if "," in name:
        last, first = name.split(",", 1)
        name = first + " " + last
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z]+", name.lower())


def matching_professors(name, department, professors):
    tokens = name_tokens(name)
    if not tokens:
        return [], "unresolved", []
    # Faculty sometimes move between UCSD departments or hold joint listings.
    # Additional departments are accepted only with an observed official card;
    # a bare legacy affiliation string cannot expand the matching scope.
    candidates = [p for p in professors if p["department"] == department or any(
        listing.get("department") == department and listing.get("sourceUrl") and listing.get("observedAt")
        for listing in p.get("directoryListings", [])
    )]
    exact = [p for p in candidates if name_tokens(p["name"]) == tokens]
    if exact:
        return exact, "exact_name_same_department", []
    # A surname-only schedule is accepted only when it identifies one normalized
    # full name in the department. No substring, edit-distance or global matching.
    suffix = [p for p in candidates if name_tokens(p["name"])[-len(tokens):] == tokens]
    if len({tuple(name_tokens(p["name"])) for p in suffix}) == 1:
        return suffix, "unique_surname_same_department", []
    # First and last names may omit middle initials, but must be unambiguous.
    qualified = []
    if len(tokens) >= 2:
        for p in candidates:
            full = name_tokens(p["name"])
            if len(full) < 2 or full[-1] != tokens[-1]:
                continue
            # Two different explicit middle initials name two different people.
            supplied_initials = [t for t in tokens[1:-1] if len(t) == 1]
            roster_initials = [t for t in full[1:-1] if len(t) == 1]
            if supplied_initials and roster_initials and supplied_initials[0] != roster_initials[0]:
                continue
            if (len(tokens[0]) == 1 and full[0].startswith(tokens[0])) or full[0] == tokens[0]:
                # Every supplied non-initial token must occur in order.
                supplied = [t for t in tokens[1:-1] if len(t) > 1]
                if all(t in full[1:-1] for t in supplied):
                    qualified.append(p)
    if len({tuple(name_tokens(p["name"])) for p in qualified}) == 1:
        return qualified, "unique_first_last_same_department", []
    ambiguity = qualified or suffix
    return [], "ambiguous" if ambiguity else "unresolved", [p["id"] for p in ambiguity]


def bind(records, professors):
    by_id = defaultdict(list)
    unmatched = []
    seen = set()
    for item in records:
        key = tuple(item.get(k) for k in ["courseCode", "title", "term", "instructorName", "sourceId"])
        if key in seen:
            continue
        seen.add(key)
        matches, method, candidates = matching_professors(item["instructorName"], item["department"], professors)
        if not matches:
            unmatched.append({**item, "matchStatus": method, "candidateProfessorIds": candidates})
        for professor in matches:
            surname_only = method == "unique_surname_same_department"
            matched_method = method if professor["department"] == item["department"] else method + "_documented_affiliation"
            by_id[professor["id"]].append({**item, "matchMethod": matched_method,
                "matchConfidence": "low" if surname_only else "high",
                "verificationStatus": "needs_review" if surname_only else "source_matched"})
    for items in by_id.values():
        items.sort(key=lambda x: (x["term"] or "", x["courseCode"], x["sourceId"]))
    return dict(sorted(by_id.items())), unmatched


def fetch(source, cache_dir, refresh):
    cache_file = cache_dir / (source["id"] + ".json")
    if cache_file.exists() and not refresh:
        cached = json.loads(cache_file.read_text())
        if cached["meta"].get("url") == source["url"]:
            return source, cached["body"], {**cached["meta"], "fromCache": True}
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    meta = {"id": source["id"], "url": source["url"], "department": source["department"], "observedAt": now, "fromCache": False}
    try:
        try:
            request = urllib.request.Request(source["url"], headers={"User-Agent": "ResearchAtlas/2.0 (public academic schedules)"})
            with urllib.request.urlopen(request, timeout=35) as response:
                raw = response.read(4_000_001)
                final_url = response.url
                content_type = response.headers.get("Content-Type", "")
        except Exception as first_error:
            # Keep TLS verification enabled. curl uses the macOS system CA store.
            result = subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", "--max-time", "35", "--max-filesize", "4000000", source["url"]], capture_output=True, check=True)
            raw = result.stdout
            final_url, content_type = source["url"], ""
            meta["transportNote"] = "System curl fallback after " + type(first_error).__name__
        if len(raw) > 4_000_000:
            raise ValueError("Response exceeds the 4 MB limit")
        meta.update(status="fetched", sha256=hashlib.sha256(raw).hexdigest(), finalUrl=final_url, contentType=content_type)
        if source["parser"] == "pdf_text":
            with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf:
                pdf.write(raw)
                pdf.flush()
                body = subprocess.run(["pdftotext", "-layout", pdf.name, "-"], capture_output=True, check=True).stdout.decode("utf-8")
            meta["extractionMethod"] = "pdftotext -layout"
        elif source["parser"] == "pdf_tables":
            code = "import io,json,sys,pdfplumber; pdf=pdfplumber.open(io.BytesIO(sys.stdin.buffer.read())); print(json.dumps([t for p in pdf.pages for t in p.extract_tables()]))"
            body = subprocess.run([source.get("pdfPython", sys.executable), "-c", code], input=raw, capture_output=True, check=True).stdout.decode("utf-8")
            meta["extractionMethod"] = "pdfplumber table cell extraction; visually audited initial source"
        else:
            body = raw.decode("utf-8-sig", "replace")
        if source["parser"] == "biology":
            # Do not retain public personnel identifiers or unrelated contact data.
            payload = json.loads(body)
            for row in payload["courses"]["classes"]:
                row["instructors"] = [{k: p.get(k) for k in ("fname", "lname", "isPrimaryInstructor")} for p in row.get("instructors", [])]
            body = json.dumps(payload)
            meta["cachedContentSanitized"] = True
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"meta": meta, "body": body}, ensure_ascii=False))
        return source, body, meta
    except Exception as error:
        meta.update(status="fetch_failed", error=str(error)[:500])
        return source, "", meta


def soc_term_label(code):
    return f"{SOC_QUARTERS[code[:2]]} 20{code[2:]}"


def soc_strip(fragment):
    return clean(re.sub(r"<[^>]+>", " ", re.sub(r"&nbsp;", " ", fragment)))


def parse_soc_pages(pages):
    """Return one row per course, term-independent: code, title, and each
    instructor with the meeting types they are listed on."""
    courses = {}
    course = None
    for page in pages:
        for match in re.finditer(r"<tr\b([^>]*)>(.*?)</tr>", page, re.S):
            attrs, body = match.group(1), match.group(2)
            if 'class="crsheader"' in body:
                course_id = re.search(r"courseId=([A-Z]+)\s*(\d+[A-Z]*)", body)
                title = re.search(r'<span class="boldtxt">(.*?)</span>', body, re.S)
                if course_id and title:
                    code = course_code(f"{course_id[1]} {course_id[2]}")
                    course = courses.setdefault(code, {"courseCode": code, "title": soc_strip(title[1]), "instructors": {}})
                continue
            if course is None or not re.search(r'class="(?:sectxt|nonenrtxt)"', attrs) or "Cancelled" in body:
                continue
            cells = re.findall(r"<td\b[^>]*>(.*?)</td>", body, re.S)
            kind = next((i for i, cell in enumerate(cells) if 'id="insTyp"' in cell), None)
            if kind is None or kind + 6 >= len(cells):
                continue
            meeting = soc_strip(cells[kind])
            if meeting not in SOC_TEACHING_TYPES or SOC_EXCLUDED_TITLE.search(course["title"]):
                continue
            section = soc_strip(cells[kind + 1])
            for line in re.split(r"<br\s*/?>", cells[kind + 6]):
                for name in instructor_names(soc_strip(line)):
                    course["instructors"].setdefault(name, []).append(f"{meeting} {section}".strip())
    return [row for row in courses.values() if row["instructors"]]


def soc_sections(sections):
    unique_sections = sorted(set(sections))
    return ", ".join(unique_sections[:6]) + (f" +{len(unique_sections) - 6} more sections" if len(unique_sections) > 6 else "")


class SocClient:
    """Sequential, cookie-preserving client: result pages 2..N belong to the
    session's most recent query."""
    def __init__(self, delay):
        import http.cookiejar
        self.delay = delay
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self._last = 0.0

    def get(self, url):
        import time
        wait = self._last + self.delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": "ResearchAtlas/2.0 (public academic schedules)"})
        try:
            with self.opener.open(request, timeout=45) as response:
                return response.read(4_000_001).decode("utf-8", "replace")
        finally:
            self._last = time.monotonic()


def soc_available_terms(client, limit):
    page = client.get(SOC_LANDING)
    codes = re.findall(r'<option value="((?:FA|WI|SP)\d{2})"', page)
    terms = []
    for code in codes:
        if json.loads(client.get(f"{SOC_BASE}subject-list.json?selectedTerm={code}")):
            terms.append(code)
        if len(terms) == limit:
            break
    return terms


def soc_query_url(term, department):
    return f"{SOC_BASE}scheduleOfClassesStudentResult.htm?selectedTerm={term}&tabNum=tabs-dept&selectedDepartments={department}&_selectedDepartments=1"


def fetch_soc(client, term, department, cache_dir, refresh):
    cache_file = cache_dir / "soc" / f"{term}-{department}.json"
    url = soc_query_url(term, department)
    if cache_file.exists() and not refresh:
        cached = json.loads(cache_file.read_text())
        return cached["pages"], {**cached["meta"], "fromCache": True}
    meta = {"id": f"soc-{term}-{department}", "url": url, "landingUrl": SOC_LANDING, "department": SOC_DEPARTMENTS[department],
            "scheduleDepartment": department, "term": soc_term_label(term),
            "observedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "fromCache": False}
    try:
        pages = [client.get(url)]
        total = SOC_PAGE_RE.search(pages[0])
        for number in range(2, int(total[1]) + 1 if total else 1):
            pages.append(client.get(f"{SOC_BASE}scheduleOfClassesStudentResult.htm?page={number}"))
        # Email lookup tokens identify personnel records and are not needed.
        pages = [re.sub(r"pid=[^'\")]+", "pid=", page) for page in pages]
        meta.update(status="fetched", pageCount=len(pages), sha256=hashlib.sha256("".join(pages).encode()).hexdigest())
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"meta": meta, "pages": pages}, ensure_ascii=False))
        return pages, meta
    except Exception as error:
        meta.update(status="fetch_failed", error=str(error)[:500])
        return [], meta


def collect_soc(terms, cache_dir, refresh, delay, as_of):
    client = SocClient(delay)
    if terms == ["auto"]:
        terms = soc_available_terms(client, 3)
    records, sources = [], []
    for term in terms:
        for department in SOC_DEPARTMENTS:
            pages, meta = fetch_soc(client, term, department, cache_dir, refresh)
            parsed = []
            source = {"id": meta["id"], "department": meta["department"], "url": meta["url"], "landingUrl": SOC_LANDING}
            for row in parse_soc_pages(pages):
                for name, sections in row["instructors"].items():
                    emit(parsed, source, meta, as_of, row["courseCode"], row["title"], meta["term"], name,
                         f"{meta['term']} | {row['courseCode']} {row['title']} | {soc_sections(sections)} | {name}",
                         assignmentBasis="official_schedule_of_classes", isTentative=False,
                         meetingTypes=sorted({s.split()[0] for s in sections}))
            records.extend(parsed)
            if meta["status"] == "fetched" or meta.get("fromCache"):
                meta["status"] = "parsed" if parsed else "no_instructor_assignments"
            meta["assignmentCount"] = len(parsed)
            sources.append(meta)
            print(f"{meta['id']}: {meta['status']} ({len(parsed)} assignments, {meta.get('pageCount', 0)} pages)", flush=True)
    return records, sources


def coverage(by_id, unmatched, sources, professor_count):
    linked = [item for rows in by_id.values() for item in rows]
    return {
        "rosterProfessorCount": professor_count,
        "professorsWithTeachingEvidence": len(by_id),
        "professorsWithoutTeachingEvidence": professor_count - len(by_id),
        "linkedAssignmentCount": len(linked), "unmatchedAssignmentCount": len(unmatched),
        "assignmentsNeedingIdentityReview": sum(x.get("verificationStatus") == "needs_review" for x in linked),
        "highConfidenceAssignmentEvidenceCount": sum(x.get("verificationStatus") == "source_matched" for x in linked),
        "professorsWithHighConfidenceEvidence": sum(any(x.get("verificationStatus") == "source_matched" for x in rows) for rows in by_id.values()),
        "uniqueProfessorCourseTermCount": len({(pid, x["courseCode"], x["term"]) for pid, rows in by_id.items() for x in rows}),
        "sourceCount": len(sources), "failedSources": sum(s["status"] in {"fetch_failed", "parse_failed"} for s in sources),
        "byDepartment": dict(Counter(x["department"] for x in linked)),
        "professorsByDepartment": dict(Counter(department for rows in by_id.values() for department in {r["department"] for r in rows})),
        "byStatus": dict(Counter(x["status"] for x in linked)),
        "countingNote": "linkedAssignmentCount counts source evidence rows; multiple sources or topics can describe the same professor/course/term. Low-confidence surname candidates are included separately from high-confidence counts. professorsByDepartment counts each person once in each evidenced teaching department; cross-listed professors may appear in more than one department.",
        "missingEvidenceMeaning": "No assignment evidence captured by these sources; does not mean the professor does not teach.",
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--atlas", type=Path, default=ROOT / "data/research-atlas.json")
    cli.add_argument("--output", type=Path, default=ROOT / "data/ucsd/teaching-evidence.json")
    cli.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    cli.add_argument("--pdf-python", default=sys.executable, help="Python executable with pdfplumber, used only for PDF table sources")
    cli.add_argument("--refresh", action="store_true", help="Fetch sources again; preserve actual observation timestamps when using cache")
    cli.add_argument("--rematch", action="store_true", help="Rebind existing output only, with no network requests")
    cli.add_argument("--as-of", default=dt.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat(), help="Client date used to classify advertised terms")
    cli.add_argument("--soc-terms", default="auto", help="Comma-separated Schedule of Classes term codes (e.g. FA25,WI26,SP26); 'auto' uses the three latest published quarters")
    cli.add_argument("--soc-delay", type=float, default=1.0, help="Seconds between Schedule of Classes requests")
    cli.add_argument("--no-soc", action="store_true", help="Skip the campus Schedule of Classes")
    cli.add_argument("--soc-only", action="store_true", help="Collect only the Schedule of Classes; keep every other source's saved evidence and observation dates")
    args = cli.parse_args()
    as_of = dt.date.fromisoformat(args.as_of)
    professors = json.loads(args.atlas.read_text())["professors"]
    if args.soc_only:
        # Department sources keep their saved rows untouched; only the Schedule
        # of Classes is (re)collected and its previous rows are replaced.
        output = json.loads(args.output.read_text())
        is_soc = lambda row: str(row.get("sourceId", row.get("id", ""))).startswith("soc-")
        records = [row for rows in output["byProfessorId"].values() for row in rows] + output["unmatchedAssignments"]
        records = [{k: v for k, v in row.items() if k not in {"matchMethod", "matchStatus", "candidateProfessorIds", "matchConfidence", "verificationStatus"}} for row in records if not is_soc(row)]
        for row in records:
            row["status"] = term_status(row["term"], as_of)
        soc_records, soc_sources = collect_soc(args.soc_terms.split(","), args.cache_dir, args.refresh, args.soc_delay, as_of)
        records += soc_records
        sources = [meta for meta in output["sources"] if not is_soc(meta)] + soc_sources
        output["scope"] = "UCSD public departmental teaching schedules and the campus Schedule of Classes"
        output["warnings"] = [w for w in output["warnings"] if not w.startswith(("Psychology undergraduate", "Schedule of Classes rows"))] + [
            "Psychology undergraduate and MAE department pages expose course availability without instructor names; the campus Schedule of Classes supplies their instructors of record.",
            "Schedule of Classes rows record the instructor of record listed for past quarters. Independent study, internships, exams and review sessions are excluded. Programs and colleges taught across departments are not mapped.",
        ]
    elif args.rematch:
        output = json.loads(args.output.read_text())
        records = [row for rows in output["byProfessorId"].values() for row in rows] + output["unmatchedAssignments"]
        records = [{k: v for k, v in row.items() if k not in {"matchMethod", "matchStatus", "candidateProfessorIds", "matchConfidence", "verificationStatus"}} for row in records]
        for row in records:
            row["status"] = term_status(row["term"], as_of)
        sources = output["sources"]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            fetched = list(executor.map(lambda s: fetch({**s, "pdfPython": args.pdf_python}, args.cache_dir, args.refresh), SOURCES))
        titles = {}
        for source, body, meta in fetched:
            if source["parser"] == "titles_only" and body:
                for block in html_data(body).blocks:
                    if "course-name" in block["class"]:
                        match = COURSE_RE.match(block["text"])
                        if match:
                            titles[course_code(block["text"])] = re.sub(r"\s*\([\d–, -]+\)\s*$", "", block["text"][match.end():].lstrip(" .:"))
        records, sources = [], []
        for source, body, meta in fetched:
            if body:
                try:
                    parsed = parse_source(source, body, meta, as_of, titles)
                    records.extend(parsed)
                    meta["assignmentCount"] = len(parsed)
                    meta["status"] = "titles_only" if source["parser"] == "titles_only" else "parsed" if parsed else "no_instructor_assignments"
                    if not parsed and source["parser"] != "titles_only":
                        meta["note"] = "Fetched current course availability but no parseable instructor assignments; no professor associations inferred."
                except Exception as error:
                    meta.update(status="parse_failed", error=str(error)[:500], assignmentCount=0)
            if source.get("landingUrl"):
                meta["landingUrl"] = source["landingUrl"]
            sources.append(meta)
            print(f"{source['id']}: {meta['status']} ({meta.get('assignmentCount', 0)} assignments)", flush=True)
        if not args.no_soc:
            soc_records, soc_sources = collect_soc(args.soc_terms.split(","), args.cache_dir, args.refresh, args.soc_delay, as_of)
            records.extend(soc_records)
            sources.extend(soc_sources)
        output = {"schemaVersion": "1.0.0", "scope": "UCSD public departmental teaching schedules and the campus Schedule of Classes", "warnings": [
            "Coverage is partial. Departments and instructors not represented here have not been exhaustively checked.",
            "Department schedules are tentative. Scheduled/historical classify the advertised term, not proof of actual or completed teaching.",
            "Catalog pages are used only to supply course titles after a teaching assignment is separately evidenced.",
            "Surname matching is limited to a unique person in the same department; ambiguous and unrecognized names remain unmatched.",
            "Surname-only links are low-confidence candidates marked needs_review; they are not verified instructor identities.",
            "A professor may match an additional department only when an observed faculty-directory listing explicitly supports that department.",
            "Psychology undergraduate and MAE department pages expose course availability without instructor names; the campus Schedule of Classes supplies their instructors of record.",
            "Schedule of Classes rows record the instructor of record listed for past quarters. Independent study, internships, exams and review sessions are excluded. Programs and colleges taught across departments are not mapped.",
        ]}
    by_id, unmatched = bind(records, professors)
    output.update(generatedAt=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), asOf=args.as_of, sources=sources, byProfessorId=by_id, unmatchedAssignments=unmatched, coverage=coverage(by_id, unmatched, sources, len(professors)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(output["coverage"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
