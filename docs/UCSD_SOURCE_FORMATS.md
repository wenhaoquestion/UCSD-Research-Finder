# UCSD Source Formats

UCSD department research pages are not one uniform schema. The crawler treats these as the main source shapes:

- `faculty_directory`: professor profile listings, often with research summaries and personal/lab links.
  - Example: CSE `https://cse.ucsd.edu/people/faculty-profiles`
  - Example: Economics `https://economics.ucsd.edu/faculty-and-research/faculty-profiles/faculty.html`

- `lab_directory`: one department page lists labs directly.
  - Example: Neurosciences `https://neurosciences.ucsd.edu/research/labs/index.html`
  - Example: Cognitive Science `https://cogsci.ucsd.edu/research/research-labs.html`
  - Example: OB-GYN `https://obgyn.ucsd.edu/research/labs/index.html`
  - Example: Radiation Medicine `https://radonc.ucsd.edu/research/labs/index.html`

- `faculty_lab_directory`: a lab directory exists, but the path uses faculty-lab wording.
  - Example: Pediatrics `https://pediatrics.ucsd.edu/research/faculty-labs/index.html`
  - Example: Public Health `https://hwsph.ucsd.edu/research/faculty-research-labs/index.html`

- `research_groups`: labs or centers are listed as research groups rather than labs.
  - Example: Bioengineering `https://bioengineering.ucsd.edu/research-focus`
  - Example: Communication `https://communication.ucsd.edu/research/groups/index.html`
  - Example: Philosophy `https://philosophy.ucsd.edu/research-groups/research-groups-overview.html`

- `research_topics`: topic landing pages point to topic pages, which then point to faculty and lab links.
  - Example: Biological Sciences `https://biology.ucsd.edu/research/research-topics/index.html`
  - Biology is Angular/API-driven; the static HTML does not contain the topic/faculty grid. Use `https://public.biology.ucsd.edu/api/prod/website-data/v1/research-topics`.
  - Example: Scripps `https://scripps.ucsd.edu/research/topics`

- `research_areas`: department-level area pages with less direct lab information.
  - Example: Physics `https://physics.ucsd.edu/research`
  - Example: Mathematics `https://www.math.ucsd.edu/research/`

Discovery should keep broad candidate path patterns, but high-value API or unusual formats should be explicit adapters so the index can preserve topic-to-lab relationships.
