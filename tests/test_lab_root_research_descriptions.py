import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_root_research_descriptions import root_research_description
from lab_own_metadata import verified_own_metadata, apply_own_metadata
from lab_resource_reviews import record_sha256
from refresh_labs import make_lab


class RootResearchDescriptionTests(unittest.TestCase):
    def capture(self, cache, queue, uri, markup):
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.parent.mkdir(exist_ok=True); path.write_text(markup)
        item = {'url': uri, 'fetch': {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok', 'httpStatus': 200,
            'observedAt': '2026-10-16T02:42:54+00:00', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'redirects': []}}
        queue['items'][uri] = item
        return item, path

    def fixture(self, cache):
        queue = {'items': {}}; root = 'https://examplelab.ucsd.edu/'; child = root + 'about/'
        home, home_path = self.capture(cache, queue, root,
            '<html><head><title>Example Lab</title></head><body><nav><a class="navigation-link" href="/about/">About</a></nav>'
            '<main><h1>Example Lab</h1></main></body></html>')
        description = 'The lab studies protein structure. We develop structural models. These data support screening.'
        about, child_path = self.capture(cache, queue, child,
            '<html><head><title>About · Example Lab</title></head><body><main><article><header><h1 class="title">About</h1></header>'
            '<h1 id="research-summary">Research Summary <a href="#research-summary">Link to heading</a></h1>'
            '<p>Dr. Example researches unrelated personal biography. ' + description + '</p>'
            '<h1 id="potential-collaborative-programs">Potential Collaborative Programs</h1>'
            '<ul><li>Unsupported potential-program keyword</li></ul></article></main></body></html>')
        lab = make_lab('Example Lab', root, 'Unknown', home['fetch'], 'Example Lab')
        lab.update(id='unchanged-lab', description='Not found', principalInvestigator='Not found',
                   professorIds=[], researchAreas=[], lastVerified='2020-01-01')
        lab.get('fieldEvidence', {}).pop('description', None)
        scope = root_research_description(home, about, cache, lab['labName'])
        row = {'labId': lab['id'], 'originalLabRecord': copy.deepcopy(lab),
            'originalLabRecordSha256': record_sha256(lab), 'reason': 'Read only the scoped collective lab research statements.',
            'fields': {'description': scope['description']}, 'fieldEvidence': {'description': [scope['descriptionEvidence']]},
            'identityEvidence': scope['identityEvidence'], 'evidence': scope['evidence'], 'sourceScope': scope}
        return lab, queue, row, home_path, child_path, description

    def rewrite(self, queue, uri, path, old, new):
        path.write_text(path.read_text().replace(old, new))
        queue['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def verify(self, lab, queue, row, cache, aliases=()):
        return verified_own_metadata({'entries': [row]}, list(aliases), queue, cache, [lab])

    def test_only_explicit_collective_tail_is_used_without_pi_keywords_or_homepage_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); lab, queue, row, _, _, description = self.fixture(cache)
            old = copy.deepcopy(lab); before = copy.deepcopy((queue, row))
            verified = self.verify(lab, queue, row, cache)
            data = {'labs': [lab]}; apply_own_metadata(data, verified)
            self.assertEqual(lab['description'], description)
            self.assertNotIn('personal biography', lab['description'])
            self.assertNotIn('potential-program keyword', lab['description'])
            for field in ['id', 'labName', 'labWebsiteUrl', 'principalInvestigator', 'professorIds', 'department', 'institution', 'researchAreas', 'lastVerified']:
                self.assertEqual(lab.get(field), old.get(field), field)
            self.assertNotIn(row['sourceScope']['requestedUrl'], lab.get('alternateWebsiteUrls', []))
            self.assertEqual((queue, row), before)
            once = copy.deepcopy(data); apply_own_metadata(data, verified); self.assertEqual(data, once)

    def test_an_already_verified_root_alias_can_supply_description_without_replacing_original_primary(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); lab, queue, row, *_ = self.fixture(cache)
            root = lab['labWebsiteUrl']; lab['labWebsiteUrl'] = 'https://pharmacy.ucsd.edu/faculty/example'
            row['originalLabRecord'] = copy.deepcopy(lab); row['originalLabRecordSha256'] = record_sha256(lab)
            aliases = [{'labId': lab['id'], 'url': root, 'captureVerified': True}]
            verified = self.verify(lab, queue, row, cache, aliases); apply_own_metadata({'labs': [lab]}, verified)
            self.assertEqual(lab['labWebsiteUrl'], 'https://pharmacy.ucsd.edu/faculty/example')
            self.assertNotIn(root + 'about/', lab.get('alternateWebsiteUrls', []))
            with self.assertRaises(ValueError): self.verify(lab, queue, row, cache)

    def test_missing_or_changed_literal_navigation_and_own_lab_brand_fail_closed(self):
        for mode in ['unpublished', 'different-path', 'outside-nav', 'wrong-root-name', 'wrong-child-name']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); lab, queue, row, home_path, child_path, _ = self.fixture(cache)
                root = lab['labWebsiteUrl']
                if mode == 'unpublished': self.rewrite(queue, root, home_path, 'href="/about/"', 'href="/other/"')
                if mode == 'different-path': row['sourceScope']['requestedUrl'] = root + 'people/'
                if mode == 'outside-nav': self.rewrite(queue, root, home_path, '<nav>', '<div>'); self.rewrite(queue, root, home_path, '</nav>', '</div>')
                if mode == 'wrong-root-name': self.rewrite(queue, root, home_path, '<h1>Example Lab</h1>', '<h1>Another Lab</h1>')
                if mode == 'wrong-child-name': self.rewrite(queue, root + 'about/', child_path, 'About · Example Lab', 'About · Another Lab')
                with self.assertRaises(ValueError): self.verify(lab, queue, row, cache)

    def test_personal_only_research_or_program_and_biography_boundaries_cannot_be_group_fields(self):
        changes = [('The lab studies protein structure.', 'I study protein structure.'),
            ('We develop structural models.', 'Dr. Another studies a different topic.'),
            ('id="potential-collaborative-programs"', 'id="unrelated-section"'),
            ('<p>Dr. Example researches', '<div>Dr. Example researches'),
            ('</article>', '<h1 id="research-summary">Research Summary Link to heading</h1></article>')]
        for old, new in changes:
            with self.subTest(change=new), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); lab, queue, _, _, child_path, _ = self.fixture(cache)
                child = lab['labWebsiteUrl'] + 'about/'; self.rewrite(queue, child, child_path, old, new)
                with self.assertRaises(ValueError): root_research_description(queue['items'][lab['labWebsiteUrl']], queue['items'][child], cache, lab['labName'])

    def test_changed_bytes_dates_redirects_or_review_claims_are_rejected(self):
        for mode in ['bytes', 'date', 'redirect', 'quote', 'institution', 'keywords']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); lab, queue, row, _, child_path, _ = self.fixture(cache)
                child = lab['labWebsiteUrl'] + 'about/'
                if mode == 'bytes': child_path.write_text(child_path.read_text() + 'changed')
                if mode == 'date': queue['items'][child]['fetch']['observedAt'] = '2026-10-17T00:00:00+00:00'
                if mode == 'redirect': queue['items'][child]['fetch']['finalUrl'] = 'https://other.ucsd.edu/about/'
                if mode == 'quote': row['fields']['description'] = 'Invented group summary.'
                if mode == 'institution': row['fields']['institution'] = 'University of California San Diego'
                if mode == 'keywords': row['fields']['researchAreas'] = ['Unsupported potential-program keyword']
                with self.assertRaises(ValueError): self.verify(lab, queue, row, cache)

    def test_other_shared_owners_and_unsupported_generic_child_scope_cannot_be_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); lab, queue, row, *_ = self.fixture(cache)
            lab['websiteSharing'] = {'groupId': 'shared', 'memberLabIds': ['unchanged-lab', 'another-lab']}
            with self.assertRaises(ValueError): self.verify(lab, queue, row, cache)
            lab.pop('websiteSharing'); row['sourceScope']['kind'] = 'named_own_parent_published_child'
            with self.assertRaises(ValueError): self.verify(lab, queue, row, cache)


if __name__ == '__main__':
    unittest.main()
