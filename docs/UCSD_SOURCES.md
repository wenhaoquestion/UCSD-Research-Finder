# UCSD Sources

当前 MVP 使用的公开来源：

- CSE Faculty Profiles: https://cse.ucsd.edu/people/faculty-profiles
- CSE Research Areas: https://cse.ucsd.edu/research
- Biological Sciences Faculty List/API-backed directory: https://biology.ucsd.edu/research/faculty/index.html
- Biological Sciences Research Topics/API-backed topic pages: https://biology.ucsd.edu/research/research-topics/index.html
- Neurosciences Research Labs: https://neurosciences.ucsd.edu/research/labs/index.html
- CSE Undergraduate Research: https://cse.ucsd.edu/undergraduate/undergraduate-research
- CSE Undergraduate Tutors: https://cse.ucsd.edu/undergraduate/undergraduate-tutors
- Cognitive Science Research Labs: https://cogsci.ucsd.edu/research/research-labs.html
- Bioengineering Research Focus & Groups: https://bioengineering.ucsd.edu/research-focus
- Cardiology Research Groups & Labs: https://cardiology.ucsd.edu/research/labs/index.html
- Design Lab Faculty: https://designlab.ucsd.edu/people/faculty.html
- Design Lab About: https://designlab.ucsd.edu/about/index.html
- HDSI Faculty: https://datascience.ucsd.edu/faculty/
- Data Science Teaching and Learning Lab: https://dstl.ucsd.edu/

`sources.json` 中 `enabled: true` 的来源会被脚本自动抓取；其余来源先作为人工确认过的 seed data 引用，后续可以逐步写 adapter。

不同院系的页面格式整理见 `docs/UCSD_SOURCE_FORMATS.md`。
