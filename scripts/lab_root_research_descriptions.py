"""Verify a collective research paragraph on a dedicated lab root's child.

The child is a description source, never a homepage alias. The published root
link, own child brand and article boundaries must all agree. Personal opening
sentences and later potential-program lists remain context, not group fields.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit

from faculty_profile_bindings import captured_source
from refresh_labs import DOM, every_node

KIND = 'named_root_published_collective_research_child'


def root_research_description(root_item, child_item, cache, lab_name):
    home, root_markup = captured_source(root_item, cache)
    child, child_markup = captured_source(child_item, cache)
    root_uri = home['sourceUrl']; parsed = urlsplit(root_uri)
    if (parsed.scheme != 'https' or not (parsed.hostname or '').endswith('.ucsd.edu')
            or parsed.path != '/' or parsed.query or parsed.fragment
            or home['requestedUrl'] != root_uri or child['requestedUrl'] != root_uri + 'about/'
            or child['sourceUrl'] != child['requestedUrl']
            or any(i['fetch'].get('httpStatus') != 200 or i['fetch'].get('redirects')
                   for i in [root_item, child_item])):
        raise ValueError('Collective research child requires its exact reviewed direct campus lab root and About captures')
    dom = DOM(root_markup); main = list(dom.main().walk())
    titles = [n.text() for n in every_node(dom.root) if n.tag == 'title']
    headings = [n.text() for n in main if n.tag == 'h1']
    if titles != [lab_name] or headings != [lab_name] or not re.search(r'\b(?:lab|laboratory|group)\b', lab_name, re.I):
        raise ValueError('Research parent must explicitly name its single unchanged lab in title and H1')
    published = []
    for node in every_node(dom.root):
        if node.tag != 'a' or not node.attrs.get('href'):
            continue
        label, uri = node.text(), urljoin(root_uri, node.attrs['href'])
        ancestor = node.parent
        while ancestor is not None and ancestor.tag != 'nav': ancestor = ancestor.parent
        if (ancestor is not None and label == 'About' and uri == child['requestedUrl']
                and node.attrs.get('href') == '/about/'
                and 'navigation-link' in node.attrs.get('class', '').split()):
            published.append(node)
    if len(published) != 1:
        raise ValueError('Lab root must literally publish its single own About navigation link')
    page = DOM(child_markup); nodes = list(page.main().walk())
    child_titles = [n.text() for n in every_node(page.root) if n.tag == 'title']
    subjects = [n for n in nodes if n.tag == 'h1' and 'title' in n.attrs.get('class', '').split()]
    sections = [n for n in nodes if n.tag == 'h1' and n.attrs.get('id') == 'research-summary']
    if (child_titles != ['About · ' + lab_name] or len(subjects) != 1 or subjects[0].text() != 'About'
            or len(sections) != 1 or sections[0].text() != 'Research Summary Link to heading'
            or sections[0].parent.tag != 'article'):
        raise ValueError('Own About child must publish its lab brand and unique Research Summary article section')
    heading = sections[0]; siblings = [n for n in heading.parent.children if hasattr(n, 'tag')]
    index = siblings.index(heading)
    if (index + 2 >= len(siblings) or siblings[index + 1].tag != 'p'
            or siblings[index + 2].tag != 'h1'
            or siblings[index + 2].attrs.get('id') != 'potential-collaborative-programs'):
        raise ValueError('Research paragraph must end before the separately labelled potential collaborative programs')
    paragraph = siblings[index + 1]
    if any(n is not paragraph and n.tag not in {'a', 'span', 'em', 'strong', 'br', 'b', 'i'} for n in paragraph.walk()):
        raise ValueError('Collective research must be one scoped paragraph, not nested people or publication lists')
    text = paragraph.text()
    if text.count('The lab ') != 1:
        raise ValueError('A named lab child must explicitly establish the collective lab subject')
    offset = text.index('The lab '); prefix = text[:offset]; quote = text[offset:]
    if prefix and not prefix.endswith('. '):
        raise ValueError('A personal opening must end before the complete collective lab statement')
    sentences = re.split(r'(?<=[.!?])\s+', quote)
    if (not 20 < len(quote) <= 2000 or not quote.endswith('.')
            or not re.match(r'^The lab (?:screens|studies|develops|investigates|explores)\b', sentences[0])
            or any(not re.match(r'^(?:The applications |To extend |We |These data )', s) for s in sentences[1:])):
        raise ValueError('Only the explicit lab subject and following collective research sentences may supply the description')
    def proof(capture, kind, value, **extra):
        return {**capture, 'status': 'verified', 'method': 'reviewed_named_root_research_child',
                'evidenceType': kind, 'evidence': value, **extra}
    identity = [proof(home, 'document_title', lab_name), proof(home, 'document_heading', lab_name, headingTag='h1')]
    link = proof(home, 'html_attribute', 'a[href] = /about/', elementTag='a', attributeName='href',
                 attributeValue='/about/', selectorAttributes={'class': published[0].attrs['class']},
                 linkText='About', linkUrl=child['sourceUrl'])
    title = proof(child, 'document_title', child_titles[0])
    section = proof(child, 'document_heading', heading.text(), headingTag='h1')
    description = {**proof(child, 'main_text_quote', quote), 'method': 'reviewed_own_lab_research_description'}
    return {'kind': KIND, 'requestedUrl': child['requestedUrl'], 'parentCapture': home, 'childCapture': child,
            'publishedLinkEvidence': link, 'identityEvidence': identity,
            'evidence': identity + [link, title, section, description], 'descriptionEvidence': description,
            'sourceParagraphAsPublished': text, 'excludedPersonalOpeningAsPublished': prefix.strip(),
            'description': quote, 'sectionId': 'research-summary', 'followingSectionId': 'potential-collaborative-programs',
            'scope': 'Explicit collective research paragraph only. The personal opening and potential-program list are excluded. No homepage alias,keywords,PI,person binding,department,institution or current-HR claim.'}


def verified_root_research_scope(row, queue, cache, parent, expected_name):
    scope = row.get('sourceScope', {})
    items = {i['url']: i for i in queue['items'].values()}
    home, child = items.get(parent), items.get(scope.get('requestedUrl'))
    if home is None or child is None:
        raise ValueError('Named root research description requires both actual source captures')
    actual = root_research_description(home, child, cache, expected_name)
    if (scope != actual or row.get('fields') != {'description': actual['description']}
            or row.get('identityEvidence') != actual['identityEvidence'] or row.get('evidence') != actual['evidence']
            or row.get('fieldEvidence') != {'description': [actual['descriptionEvidence']]}):
        raise ValueError('Every collective lab sentence and child-scope proof must equal the actual named-source observation')
    return actual['childCapture']['sourceUrl']
