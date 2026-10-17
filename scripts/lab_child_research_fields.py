"""Literal research themes and techniques on a named lab's published child.

The RCN WordPress template has two scoped research sections and a separate
technique grid. This reader accepts their own headings,not personal bios,
publication titles,footer text or inferred scientific keywords.
"""
from urllib.parse import urlsplit

from faculty_profile_bindings import captured_source
from refresh_labs import DOM,every_node

KIND='named_lab_published_rcn_research_headings'


def classes(node):
    return set(node.attrs.get('class','').split())


def child_research_fields(parent,child,cache,name):
    root,markup=captured_source(parent,cache)
    capture,child_markup=captured_source(child,cache)
    parsed=urlsplit(root['sourceUrl'])
    if (not name or parsed.scheme!='https' or parsed.query or parsed.fragment
            or not parsed.path.endswith('/') or parsed.path=='/'
            or root['requestedUrl']!=root['sourceUrl'] or capture['requestedUrl']!=capture['sourceUrl']
            or capture['sourceUrl']!=root['sourceUrl']+'research/'
            or any(i['fetch'].get('httpStatus')!=200 or i['fetch'].get('redirects') for i in [parent,child])):
        raise ValueError('Lab research headings require the exact direct named directory home and research child')
    dom=DOM(markup);nodes=list(every_node(dom.root))
    titles=[n.text() for n in nodes if n.tag=='title']
    brands=[n for n in nodes if n.tag=='a' and n.attrs.get('class')=='navbar-brand-sitename'
            and n.attrs.get('rel')=='home' and n.attrs.get('href')==root['sourceUrl']
            and n.attrs.get('title')==name]
    links=[n for n in every_node(dom.main()) if n.tag=='a' and n.attrs.get('href')==capture['sourceUrl']
           and n.attrs.get('class')=='rcn-text-link' and n.text()=='Our research ↗']
    if len(titles)!=1 or not titles[0].startswith(name+' – ') or len(brands)!=1 or len(links)!=1:
        raise ValueError('Research child requires its named home title,unique own brand and literal main research link')
    child_dom=DOM(child_markup);all_nodes=list(every_node(child_dom.root))
    if [n.text() for n in all_nodes if n.tag=='title']!=['Research – '+name]:
        raise ValueError('The research child document must explicitly name the same lab')
    articles=[n for n in every_node(child_dom.main()) if n.tag=='article'
              and {'page','type-page','hentry'}<=classes(n)]
    if len(articles)!=1:
        raise ValueError('Research headings require one own page article')
    nodes=list(articles[0].walk());themes=[]
    for key in ['movement','cognition']:
        sections=[n for n in nodes if n.tag=='section' and 'rcn-research-section' in classes(n)
                  and n.attrs.get('aria-labelledby')==key]
        if len(sections)!=1:
            raise ValueError('Research themes require unique structurally labelled own sections')
        headings=[n for n in sections[0].walk() if n.tag in {'h1','h2','h3'}]
        if len(headings)!=1 or headings[0].tag!='h2' or headings[0].attrs.get('id')!=key:
            raise ValueError('A research theme must be the sole heading of its own labelled section')
        themes.append(headings[0])
    techniques=[n for n in nodes if n.tag=='section' and classes(n)=={'rcn-techniques'}
                and n.attrs.get('aria-labelledby')=='techniques']
    if len(techniques)!=1:
        raise ValueError('Research techniques require their own unique section')
    section=techniques[0]
    headings=[n for n in section.walk() if n.tag=='h2']
    grids=[n for n in section.walk() if n.tag=='div' and classes(n)=={'rcn-technique-grid'}]
    if (len(headings)!=1 or headings[0].attrs.get('id')!='techniques'
            or headings[0].text()!='Techniques we use' or len(grids)!=1):
        raise ValueError('Technique headings must follow the explicit own Techniques we use label')
    cards=[n for n in grids[0].children if hasattr(n,'tag')]
    if len(cards)!=4 or any(n.tag!='div' or classes(n)!={'rcn-technique'} for n in cards):
        raise ValueError('The reviewed research template requires its four direct technique cards')
    selected=list(themes)
    for card in cards:
        hs=[n for n in card.walk() if n.tag in {'h1','h2','h3'}]
        if len(hs)!=1 or hs[0].tag!='h3':
            raise ValueError('Every technique requires one complete own card heading')
        selected.append(hs[0])
    values=[n.text() for n in selected]
    if len(set(values))!=6 or any(not value or len(value)>160 for value in values):
        raise ValueError('Research headings must remain six complete distinct literal statements')
    method='reviewed_own_labelled_lab_research_theme_or_technique'
    identity=[{**root,'status':'verified','method':method,'evidenceType':'document_title','evidence':titles[0]},
        {**root,'status':'verified','method':method,'evidenceType':'html_attribute','elementTag':'a',
         'attributeName':'title','attributeValue':name,'selectorAttributes':{'class':'navbar-brand-sitename','rel':'home','href':root['sourceUrl']},
         'evidence':'a[title] = '+name}]
    link={**root,'status':'verified','method':method,'evidenceType':'named_link','linkText':'Our research ↗',
          'linkUrl':capture['sourceUrl'],'evidence':'Our research ↗ -> '+capture['sourceUrl']}
    title={**capture,'status':'verified','method':method,'evidenceType':'document_title','evidence':'Research – '+name}
    proofs=[{**capture,'status':'verified','method':method,'evidenceType':'document_heading',
             'headingTag':n.tag,'evidence':n.text(),'sourceFieldScope':'research_theme' if n in themes else 'research_technique'} for n in selected]
    return {'kind':KIND,'parentSourceUrl':root['sourceUrl'],'requestedUrl':capture['requestedUrl'],
        'documentLabName':name,'identityEvidence':identity,'publishedLinkEvidence':link,
        'childDocumentTitleEvidence':title,'fields':{'researchAreas':values},'fieldEvidence':{'researchAreas':proofs},
        'evidence':identity+[link,title]+proofs,
        'scope':'The two own research-section headings and four direct cards under Techniques we use only. Complete literal values;no personal biography,publications,footer mining,PI association,recruiting or child homepage alias.'}


def verified_child_research_fields(row,queue,cache,parent,name):
    items={i['url']:i for i in queue['items'].values()}
    scope=row.get('sourceScope',{});child=scope.get('requestedUrl')
    if parent not in items or child not in items:
        raise ValueError('The named lab parent and literal research child must both be captured')
    actual=child_research_fields(items[parent],items[child],cache,name)
    if (row.get('sourceScope')!=actual or row.get('fields')!=actual['fields']
            or row.get('fieldEvidence')!=actual['fieldEvidence'] or row.get('evidence')!=actual['evidence']
            or row.get('identityEvidence')!=actual['identityEvidence']):
        raise ValueError('Lab research headings must equal their complete recomputed own source scope and values')
