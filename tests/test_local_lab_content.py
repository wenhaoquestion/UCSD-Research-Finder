"""Visible-content regressions derived from four actual cached lab sites."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lab_summary_content import ContentDOM,decode_cached_html

class SummaryContentTests(unittest.TestCase):
    def test_header_role_main_does_not_hide_research_siblings(self):
        dom=ContentDOM('<body><div role="main" data-ux="Header" data-aid="HEADER_WIDGET">Ferguson Lab at UC San Diego</div><section><p>Our lab studies epigenetic mechanisms that control neurodevelopment.</p></section><section><p>'+('Additional research details. '*15)+'</p></section></body>')
        self.assertIn('Our lab studies epigenetic mechanisms',dom.main().text())

    def test_layout_sidebar_class_does_not_remove_primary_article(self):
        dom=ContentDOM('<body><nav>Unrelated menu</nav><div id="primary" class="content-area sidebar-right no-sidebar container-normal"><main id="main" role="main"><article>The Raffatellu Lab studies gut pathogens and mucosal immunity.</article></main></div></body>')
        self.assertIn('gut pathogens',dom.main().text())
        self.assertNotIn('Unrelated menu',dom.main().text())

    def test_google_title_landmark_preserves_substantive_sibling_sections(self):
        text='The main theme of the BOAT group is air-sea physical processes. '
        dom=ContentDOM('<body><nav>Menu</nav><div role="main">Bring Ocean and Atmosphere Together (BOAT)</div><section>'+text*8+'</section></body>')
        self.assertIn(text,dom.main().text())

    def test_scripts_navigation_and_bibliography_still_excluded(self):
        dom=ContentDOM('<body><main>Named Lab research describes protein regulation in cells.</main><script>Invented research</script><nav>Other Lab quantum research</nav><aside>Sidebar research</aside><div class="propertyGroupBibliographic">Publication titles</div><footer>Contact footer</footer></body>')
        text=dom.main().text()
        for term in ['Invented','Other Lab','Sidebar','Publication titles','Contact footer']:self.assertNotIn(term,text)

    def test_profiles_main_boundary_retains_scoped_overview(self):
        dom=ContentDOM('<body><div id="ctl00_divProfilesContentMain">Named Scientist: Our laboratory studies RNA regulation and cell division.</div><div class="propertyGroupBibliographic">Publication titles '+('many papers '*100)+'</div></body>')
        node=dom.main();self.assertEqual(node.attrs['id'],'ctl00_divProfilesContentMain')

    def test_cascade_cms_navigation_index_is_not_page_prose(self):
        dom=ContentDOM('<body><system-index-block name="cms-tree"><system-folder>events true 1770678098766 site://draft</system-folder></system-index-block><div class="navmenu navmenu-fixed-left">Other page menu</div><main>Actual memorial body remembers the professor and their scientific work.</main></body>')
        text=dom.main().text()
        self.assertIn('Actual memorial body',text)
        self.assertNotIn('1770678098766',text)
        self.assertNotIn('site://draft',text)
        self.assertNotIn('Other page menu',text)

    def test_historical_nul_interleaved_cache_restores_surviving_ascii_only(self):
        html='<html><head><title>Miroslav Krstic - Nonlinear and Adaptive Control</title></head><body>Personal academic page at UC San Diego.</body></html>'
        data=b'\xef\xbf\xbd\xef\xbf\xbd'+html.encode('utf-16le')
        original=data[:];text,method,warning=decode_cached_html(data)
        self.assertEqual(text,html)
        self.assertEqual(method,'nul_interleaved_ascii_recovery')
        self.assertIn('not reconstructed',warning)
        self.assertEqual(data,original)
        self.assertIn('Personal academic page',ContentDOM(text).main().text())

if __name__=='__main__':unittest.main()
