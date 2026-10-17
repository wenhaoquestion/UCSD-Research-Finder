import copy
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from provider_profile_fields import provider_position_qualification
from review_ucsd_coverage import faculty_review
from test_atlas_quality import professor


class ProviderPositionTests(unittest.TestCase):
    def fixture(self, cache, positions=None):
        uri = 'https://providers.ucsd.edu/details/123/neurology'
        title = 'Jane A. Example, MD | Neurology | UC San Diego Health'
        document = {'name': 'Jane A. Example, MD', 'id': '123', 'uid': 456,
                    'c_metaTitle': title, 'c_pagesURL': uri, 'slug': 'details/123/neurology',
                    'siteDomain': 'providers.ucsd.edu', 'c_affiliation': 'UC_SAN_DIEGO_HEALTH',
                    'meta': {'entityType': {'id': 'healthcareProfessional'}},
                    'c_positions': positions or ['Neurologist', 'Assistant Professor of Neurosciences'],
                    'conditionsTreated': ['Memory disorders'], 'c_aggregateReviews': {'averageRating': '4.9'},
                    '_env': {'UNRELATED_PUBLIC_RUNTIME_VALUE': 'not-a-field-source'}}
        item = {'url': uri, 'state': 'done', 'contexts': [],
                'fetch': {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok', 'observedAt': '2026-10-16T01:00:00Z'}}
        (cache / 'responses').mkdir(exist_ok=True)
        return item, document

    def save(self, cache, item, document, change=lambda markup: markup):
        uri = item['url']; title = document['c_metaTitle']
        payload = quote(json.dumps({'document': document}), safe='')
        markup = ('<html><head><title>' + title + '</title><meta property="og:title" content="' + title + '">'
                  '<link rel="canonical" href="' + document['c_pagesURL'] + '">'
                  '<script id="yext-entity-data" data-entity-id="456"></script><script type="module">'
                  'render.render({Page: component.default, pageProps: JSON.parse(decodeURIComponent("' + payload + '")),});'
                  '</script></head><body><div id="reactele"></div></body></html>')
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.write_text(change(markup)); item['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def test_only_named_render_positions_qualify_with_exact_capture_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, document = self.fixture(cache); path = self.save(cache, item, document)
            before = copy.deepcopy((item, document)); result = provider_position_qualification(item, cache, 'Jane A. Example')
            self.assertEqual(result['roleAsListed'], 'Neurologist | Assistant Professor of Neurosciences')
            self.assertEqual(result['unitAsListed'], '')
            self.assertEqual(result['titleFieldsAsListed'], {'Provider positions': document['c_positions']})
            self.assertEqual(result['evidence']['bodySha256'], hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(result['evidence']['observedAt'], item['fetch']['observedAt'])
            self.assertEqual(result['evidence']['positionSourcePath'], 'pageProps.document.c_positions')
            self.assertNotIn('Memory disorders', json.dumps(result))
            self.assertNotIn('4.9', json.dumps(result)); self.assertNotIn('UNRELATED_PUBLIC_RUNTIME_VALUE', json.dumps(result))
            self.assertEqual((item, document), before)

    def test_clinical_specialties_biography_and_keywords_cannot_substitute_for_positions(self):
        for positions in [[], ['Neurologist'], 'Professor', [None]]:
            with self.subTest(positions=positions), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, document = self.fixture(cache); document['c_positions'] = positions
                document['keywords'] = ['Professor']; document['c_aboutSectionTextV2'] = {'markdown': 'Former Professor at Another University'}
                self.save(cache, item, document)
                self.assertIsNone(provider_position_qualification(item, cache, 'Jane A. Example'))

    def test_display_whitespace_can_vary_without_changing_names_or_resource_uris(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp); item,document=self.fixture(cache)
            document['name']='Jane  A. Example, MD'
            document['c_metaTitle']=document['c_metaTitle'].replace('Jane A.','Jane  A.')
            self.save(cache,item,document)
            result=provider_position_qualification(item,cache,'Jane A. Example')
            self.assertEqual(result['nameAsDisplayed'],'Jane  A. Example, MD')
            self.assertEqual(result['evidence']['requestedUrl'],item['url'])

    def test_subject_provider_id_canonical_and_institution_must_agree(self):
        changes = [('name', 'Jane B. Example, MD'), ('id', '999'), ('uid', 999),
                   ('c_pagesURL', 'https://providers.ucsd.edu/details/999/neurology'),
                   ('slug', 'details/999/neurology'), ('c_affiliation', 'OTHER'),
                   ('siteDomain', 'other.ucsd.edu'), ('meta', {'entityType': {'id': 'directory'}})]
        for field, value in changes:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, document = self.fixture(cache); document[field] = value
                self.save(cache, item, document)
                self.assertIsNone(provider_position_qualification(item, cache, 'Jane A. Example'))

    def test_unrelated_duplicate_or_corrupt_script_payloads_fail_closed(self):
        changes = [lambda m: m.replace('render.render', 'unrelated'),
                   lambda m: m.replace('</head>', m[m.index('<script type="module">'):m.index('</script></head>') + 9] + '</head>'),
                   lambda m: m.replace('%7B%22document', '%ZZ%22document'),
                   None,
                   lambda m: m.replace('</title>', '</title><title>Another Person</title>')]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, document = self.fixture(cache)
                if change is None:
                    # Duplicate JSON object keys are rejected before selecting any field.
                    payload = quote('{"document":' + json.dumps(document) + ',"document":' + json.dumps(document) + '}', safe='')
                    self.save(cache, item, document, lambda m: re.sub(r'decodeURIComponent\("[^"]*"\)', 'decodeURIComponent("' + payload + '")', m))
                else:
                    self.save(cache, item, document, change)
                self.assertIsNone(provider_position_qualification(item, cache, 'Jane A. Example'))

    def test_changed_bytes_or_failed_receipt_cannot_qualify(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, document = self.fixture(cache); path = self.save(cache, item, document)
            path.write_text(path.read_text() + 'changed')
            self.assertIsNone(provider_position_qualification(item, cache, 'Jane A. Example'))
            self.save(cache, item, document); item['fetch']['status'] = 'http_error'
            self.assertIsNone(provider_position_qualification(item, cache, 'Jane A. Example'))

    def test_real_review_keeps_original_id_name_primary_and_roster_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, document = self.fixture(cache); self.save(cache, item, document)
            person = professor('retained-id', 'Jane A. Example', 'Neurosciences'); person['officialProfileUrl'] = item['url']
            row = {'name': person['name'], 'department': person['department'], 'listedRole': 'Neurology',
                   'appointmentStatus': 'listed_faculty', 'directorySection': 'Faculty',
                   'sourceUrl': 'https://neurosciences.ucsd.edu/people/faculty.html', 'observedAt': '2026-10-15',
                   'profileUrl': item['url'], 'namedLinkUrl': item['url'], 'email': '', 'personalWebsiteUrl': '',
                   'googleScholarUrl': '', 'researchAreas': [], 'evidence': {'sourceUrl': 'https://neurosciences.ucsd.edu/people/faculty.html',
                   'observedAt': '2026-10-15', 'method': 'official_faculty_directory_card', 'evidence': 'Jane A. Example | Neurology'}}
            queue = {'items': {item['url']: item}, 'facultyListings': [row]}; before = copy.deepcopy((person, queue))
            result = faculty_review(copy.deepcopy(queue), {'professors': [person], 'labs': []}, cache, profile_identity_review={'entries': []})
            self.assertFalse(result['professors']); self.assertFalse(result['uncertainListings'])
            patch = result['byProfessorId']['retained-id']; listing = patch['directoryListings'][0]
            self.assertEqual(listing['listedRole'], 'Neurology')
            self.assertEqual(listing['academicQualification']['roleAsListed'], 'Neurologist | Assistant Professor of Neurosciences')
            self.assertNotIn('name', patch); self.assertNotIn('officialProfileUrl', patch)
            self.assertEqual((person, queue), before)
