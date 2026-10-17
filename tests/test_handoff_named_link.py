"""Named-link evidence must prove the literal anchor, not co-occurring prose."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_summary_handoff import _named_link_present, _field_proof_present, _redirect_proof_present
from lab_summary_content import ContentDOM


class NamedLinkTests(unittest.TestCase):
    def test_contact_attribute_requires_exact_named_mailto_anchor(self):
        proof = {'evidenceType': 'html_attribute', 'elementTag': 'a', 'attributeName': 'href',
                 'attributeValue': 'mailto:pi@ucsd.edu', 'evidence': 'a[href] = mailto:pi@ucsd.edu',
                 'selectorAttributes': {'href': 'mailto:pi@ucsd.edu'}, 'linkTextAsPublished': 'Email PI'}
        dom = ContentDOM('<main><a href="mailto:pi@ucsd.edu">Email PI</a></main>')
        self.assertTrue(_field_proof_present(proof, dom, []))
        for changed in [{'linkTextAsPublished': 'Other PI'}, {'selectorAttributes': {}},
                        {'attributeValue': 'mailto:other@ucsd.edu'}, {'attributeValue': 'https://ucsd.edu'}]:
            self.assertFalse(_field_proof_present({**proof, **changed}, dom, []))
        self.assertFalse(_field_proof_present(proof, ContentDOM('<p>a[href] = mailto:pi@ucsd.edu</p>'),
                                             [proof['evidence']]))

    def test_relative_link_needs_explicit_literal_and_exact_resolution(self):
        target = 'https://anthropology.ucsd.edu/research/climate-change-group.html'
        proof = {'sourceUrl': 'https://anthropology.ucsd.edu/research/index.html',
                 'linkText': 'Climate Change Interest Group', 'linkUrl': target,
                 'evidence': 'Climate Change Interest Group -> ' + target}
        dom = ContentDOM('<main><a href="climate-change-group.html">Climate Change Interest Group</a></main>')
        self.assertFalse(_named_link_present(proof, dom))
        self.assertTrue(_named_link_present({**proof, 'literalHref': 'climate-change-group.html'}, dom))
        self.assertFalse(_named_link_present({**proof, 'literalHref': 'another.html'}, dom))
        self.assertFalse(_named_link_present({**proof, 'literalHref': 'climate-change-group.html',
                                             'linkUrl': target + '/'}, dom))

    def test_redirect_receipt_requires_actual_exact_metadata(self):
        hop = {'from': 'http://palab.ucsd.edu/', 'to': 'https://www.palab.ucsd.edu/', 'httpStatus': 301}
        proof = {'requestedUrl': hop['from'], 'observedAt': '2026-10-16T22:01:02+00:00',
                 'bodySha256': 'abc', 'redirects': [hop],
                 'evidence': 'HTTP 301: http://palab.ucsd.edu/ -> https://www.palab.ucsd.edu/'}
        meta = {'sourceUrl': hop['from'], 'finalUrl': hop['to'], 'redirects': [hop],
                'observedAt': proof['observedAt'], 'sha256': 'abc'}
        self.assertTrue(_redirect_proof_present(proof, [meta]))
        for field, value in [('sourceUrl', hop['to']), ('sha256', 'changed'),
                             ('observedAt', '2026-10-17T00:00:00+00:00'), ('redirects', [])]:
            with self.subTest(field=field):
                self.assertFalse(_redirect_proof_present(proof, [{**meta, field: value}]))
        self.assertFalse(_redirect_proof_present({**proof, 'evidence': 'invented'}, [meta]))
        self.assertFalse(_redirect_proof_present(proof, []))

    def test_exact_anchor_required(self):
        proof = {'linkText': 'Digital Health Technologies Lab',
                 'linkUrl': 'https://digihealth.ucsd.edu/home',
                 'evidence': 'Digital Health Technologies Lab -> https://digihealth.ucsd.edu/home'}
        def dom(href, label='Digital Health Technologies Lab'):
            return ContentDOM('<main><h1>Official faculty profile</h1><a href="' + href + '">' + label + '</a></main>')
        self.assertTrue(_named_link_present(proof, dom(proof['linkUrl'])))
        for href in ['http://digihealth.ucsd.edu/home', proof['linkUrl'] + '/', 'https://other.ucsd.edu/']:
            with self.subTest(href=href):
                self.assertFalse(_named_link_present(proof, dom(href)))
        self.assertFalse(_named_link_present(proof, dom(proof['linkUrl'], 'Other Lab')))
        self.assertFalse(_named_link_present(proof, ContentDOM('<main><p>' + proof['evidence'] + '</p></main>')))
        self.assertFalse(_named_link_present({**proof, 'evidence': 'invented'}, dom(proof['linkUrl'])))

    def test_document_title_requires_actual_exact_title(self):
        proof = {'evidenceType': 'document_title', 'evidence': 'MOSAIC Laboratory'}
        dom = ContentDOM('<html><head><title>MOSAIC Laboratory</title></head><body><main>Research team</main></body></html>')
        self.assertTrue(_field_proof_present(proof, dom, [dom.main().text()]))
        self.assertFalse(_field_proof_present({**proof, 'evidence': 'MOSAIC'}, dom, ['MOSAIC']))
        self.assertFalse(_field_proof_present(proof, ContentDOM('<main>MOSAIC Laboratory</main>'), ['MOSAIC Laboratory']))

    def test_heading_and_frame_attribute_are_literal_structural_proofs(self):
        heading = {'evidenceType': 'document_heading', 'headingTag': 'h2', 'evidence': 'Example Lab'}
        dom = ContentDOM('<h2>Example Lab</h2><frameset><frame src="lab-main.html"></frameset>')
        self.assertTrue(_field_proof_present(heading, dom, []))
        self.assertFalse(_field_proof_present({**heading, 'headingTag': 'h1'}, dom, ['Example Lab']))
        frame = {'evidenceType': 'html_attribute', 'elementTag': 'frame', 'attributeName': 'src',
                 'attributeValue': 'lab-main.html', 'evidence': 'frame[src] = lab-main.html'}
        self.assertTrue(_field_proof_present(frame, dom, []))
        self.assertFalse(_field_proof_present({**frame, 'attributeValue': 'other.html'}, dom, []))
        self.assertFalse(_field_proof_present(frame, ContentDOM('<p>frame[src] = lab-main.html</p>'), ['frame[src] = lab-main.html']))


if __name__ == '__main__':
    unittest.main()
