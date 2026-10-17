"""Summary-only visible-content extraction; no fetching or collector mutations.

Fixes observed header-only role=main landmarks and layout sidebar classes without
turning navigation, script state or bibliographies into research evidence.
"""
import re
from refresh_labs import DOM,Node,VOID

EXTRACTION_VERSION='summary-visible-content-v2'

def decode_cached_html(data):
    if data.startswith((b'\xff\xfe',b'\xfe\xff')):
        return data.decode('utf-16',errors='replace'),'utf16_bom',None
    text=data.decode('utf-8',errors='replace')
    if text.count('\x00')>len(text)*.15 and (re.search(r'<\x00(?:h|!|\?)',text[:1000],re.I) or re.search(r'\x00<\x00(?:h|!|\?)',text[:1000],re.I)):
        # The collector's historical cache may already have re-encoded UTF-16
        # bytes through UTF-8 replacement. Restore surviving ASCII markup only;
        # keep any lost-glyph replacement characters instead of inventing them.
        return text.replace('\x00','').lstrip('\ufffd'),'nul_interleaved_ascii_recovery','Historical cache was already re-encoded with replacement markers. Surviving ASCII HTML restored; unrecoverable glyphs are not reconstructed. Original cached bytes/hash/time remain unchanged.'
    return text,'utf8_replacement',None

class ContentNode(Node):
    def excluded(self):
        if self.tag in {'script','style','nav','footer','aside','noscript','button','select','option','system-index-block'}:return True
        if self.attrs.get('role') in {'navigation','complementary','contentinfo','search'}:return True
        tokens=(self.attrs.get('class','')+' '+self.attrs.get('id','')).lower().split()
        if any('propertygroupbibliographic' in token for token in tokens):return True
        if self.tag not in {'html','body'}:
            if any(re.match(r'^(?:navbar|navmenu|breadcrumb|menu|footer|cookie|site-footer)(?:$|[_-])',token) or re.search(r'(?:--footer|masterpagefooter)',token) for token in tokens):return True
            # sidebar-right/left and no-sidebar are layout modifiers. The
            # Raffatellu primary content wrapper includes both; removing it
            # discarded the whole article. Semantic aside/complementary still
            # excludes actual sidebar subtrees.
            if 'sidebar' in tokens and not ({'content-area','primary','main-content'} & set(tokens)):return True
        return False

class ContentDOM(DOM):
    def handle_starttag(self,tag,attrs):
        node=ContentNode(tag,[(k,v or '') for k,v in attrs],self.current)
        self.current.children.append(node)
        if tag not in VOID:self.current=node

    def main(self):
        nodes=list(self.root.walk())
        body=next((n for n in nodes if n.tag=='body'),self.root)
        # Profiles has a deliberate main-content boundary; keep publication
        # and shared chrome exclusions and preserve its exact evidence scope.
        for predicate in [lambda n:n.attrs.get('id')=='ctl00_divProfilesContentMain',
                          lambda n:'main-section' in n.attrs.get('class','').split(),
                          lambda n:n.attrs.get('id') in {'content','main-content','mainContent','content-main'},
                          lambda n:'profile-content' in n.attrs.get('class','').split()]:
            matches=[n for n in nodes if predicate(n) and len(n.text())>30]
            if matches:
                candidate=max(matches,key=lambda n:len(n.text()))
                # A small title landmark cannot hide substantive sibling
                # sections in the same visible document.
                if len(candidate.text())>=len(body.text())*.55 or len(body.text())-len(candidate.text())<200:return candidate
        matches=[n for n in nodes if (n.tag=='main' or n.attrs.get('role')=='main') and n.tag!='header' and n.attrs.get('data-ux','').lower()!='header' and n.attrs.get('data-aid')!='HEADER_WIDGET' and len(n.text())>30]
        if matches:
            candidate=max(matches,key=lambda n:len(n.text()))
            if len(candidate.text())>=len(body.text())*.55 or len(body.text())-len(candidate.text())<200:return candidate
        return body
