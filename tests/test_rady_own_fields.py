import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_resource_reviews import record_sha256
from professor_own_field_reviews import verified_professor_fields, apply_professor_fields
from rady_own_fields import rady_own_fields
from test_atlas_quality import professor


class RadyOwnFieldsTests(unittest.TestCase):
    def fixture(self, cache):
        uri = 'https://rady.ucsd.edu/faculty-research/faculty/avery-lane.html'
        raw = '''<html><head><title>Avery Lane, Assistant Professor</title></head><body>
        <nav><p>Machine Vision</p><a href="mailto:office@ucsd.edu">office@ucsd.edu</a></nav>
        <main><section aria-label="Profile Container"><div class="clearfix">
        <header aria-label="Profile Name" class="profile-section profile-section-header"><h1>Avery Lane</h1>
        <p class="subhead">Assistant Professor</p></header>
        <article aria-label="Profile Details" class="profile-section-contact"><div><ul>
        <li class="email"><a href="mailto:alane@ucsd.edu">alane@ucsd.edu</a></li></ul></div></article>
        <article id="profileTab" aria-label="Profile Tabs"><ul>
        <li role="tab" id="tab_item-0" aria-controls="tab_item-0">Profile</li>
        <li role="tab" id="tab_item-1" aria-controls="tab_item-1">Publications</li>
        <li role="tab" id="tab_item-2" aria-controls="tab_item-2">Research Areas</li></ul>
        <div class="resp-tabs-container" role="tabpanel">
        <h2 class="resp-accordion" aria-controls="tab_item-0">Profile</h2>
        <div class="resp-tab-content" aria-labelledby="tab_item-0"><p>Avery Lane researches a separate topic.</p></div>
        <h2 class="resp-accordion" aria-controls="tab_item-1">Publications</h2>
        <div class="resp-tab-content" aria-labelledby="tab_item-1"><p><strong>Methodological Areas:</strong></p>
        <ul><li>Publication title is not a research area</li></ul></div>
        <h2 class="resp-accordion" aria-controls="tab_item-2">Research Areas</h2>
        <div class="resp-tab-content" aria-labelledby="tab_item-2"><p><strong>Methodological Areas:</strong></p>
        <ul><li>Causal Inference</li><li>Optimization Modeling</li></ul><p></p>
        <p><strong>Application Domains:</strong></p><ul><li>Healthcare Operations Management</li></ul></div>
        </div></article></div></section></main></body></html>'''
        file = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        file.parent.mkdir(); file.write_text(raw)
        item = {'url': uri, 'state': 'done', 'fetch': {'sourceUrl': uri, 'finalUrl': uri,
                'status': 'ok', 'httpStatus': 200, 'redirects': [], 'observedAt': '2026-10-17T08:55:12+00:00',
                'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}}
        person = professor('original-id', 'Avery Lane', 'Rady School of Management')
        person.update(officialProfileUrl=uri, researchAreas=[], email='alane@ucsd.edu')
        return item, file, person

    def revise(self, item, file, old, new):
        file.write_text(file.read_text().replace(old, new))
        item['fetch']['sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()

    def review(self, item, cache, person):
        actual = rady_own_fields(item, cache, person['name'])
        return {'professorId': person['id'], 'sourceProfessorId': person['id'],
                'originalSourceProfessorRecord': copy.deepcopy(person), 'originalSourceRecordSha256': record_sha256(person),
                'sourceTemplate': 'rady_profile_tabs_own_fields', 'sourceObservation': actual,
                'fields': actual['fields'], 'fieldEvidence': actual['fieldEvidence'],
                'reason': 'Literal own research lists and public own contact on the unchanged original primary.'}

    def test_own_lists_keep_labels_and_capture_proofs_without_publication_or_navigation_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, file, person = self.fixture(cache); before = copy.deepcopy(item)
            actual = rady_own_fields(item, cache, person['name'])
            self.assertEqual(actual['fields'], {'researchAreas': ['Causal Inference', 'Optimization Modeling',
                             'Healthcare Operations Management'], 'email': 'alane@ucsd.edu'})
            self.assertEqual([g['labelAsListed'] for g in actual['groupsAsListed']], ['Methodological Areas:', 'Application Domains:'])
            for proofs in actual['fieldEvidence'].values():
                for proof in proofs:
                    self.assertEqual(proof['bodySha256'], hashlib.sha256(file.read_bytes()).hexdigest())
                    self.assertEqual(proof['observedAt'], item['fetch']['observedAt'])
                    self.assertEqual(proof['requestedUrl'], person['officialProfileUrl'])
            self.assertEqual(item, before)

    def test_wrong_or_ambiguous_subject_and_foreign_or_unobserved_transport_require_review(self):
        modes = ['wrong_subject', 'extra_subject', 'wrong_title', 'foreign', 'generic', 'redirect', 'http', 'bytes']
        for mode in modes:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, file, person = self.fixture(cache)
                if mode == 'wrong_subject': self.revise(item, file, '<h1>Avery Lane</h1>', '<h1>Another Person</h1>')
                if mode == 'extra_subject': self.revise(item, file, '<h1>Avery Lane</h1>', '<h1>Avery Lane</h1><h1>Another Person</h1>')
                if mode == 'wrong_title': self.revise(item, file, '<title>Avery Lane,', '<title>Another Person,')
                if mode == 'foreign': item['fetch']['finalUrl'] = 'https://other.ucsd.edu/faculty-research/faculty/avery-lane.html'
                if mode == 'generic': item['fetch']['finalUrl'] = 'https://rady.ucsd.edu/faculty-research/faculty/'
                if mode == 'redirect': item['fetch']['redirects'] = [{'from': 'https://unobserved.ucsd.edu/', 'to': item['url'], 'httpStatus': 301}]
                if mode == 'http': item['fetch']['httpStatus'] = 404
                if mode == 'bytes': file.write_text(file.read_text() + 'changed')
                with self.assertRaises(ValueError): rady_own_fields(item, cache, person['name'])

    def test_wrong_or_duplicate_research_tab_and_nonliteral_lists_are_not_field_evidence(self):
        changes = [('id="tab_item-2" aria-controls="tab_item-2"', 'id="tab_item-2" aria-controls="tab_item-1"'),
                   ('aria-labelledby="tab_item-2"', 'aria-labelledby="tab_item-1"'),
                   ('<li>Causal Inference</li>', '<li><span>Causal Inference</span></li>'),
                   ('<li>Optimization Modeling</li>', '<li>Coming soon</li>'),
                   ('<li role="tab" id="tab_item-2" aria-controls="tab_item-2">Research Areas</li>',
                    '<li role="tab" id="tab_item-2" aria-controls="tab_item-2">Research Areas</li><li role="tab" id="tab_item-3" aria-controls="tab_item-3">Research Areas</li>')]
        for old, new in changes:
            with self.subTest(new=new), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, file, person = self.fixture(cache); self.revise(item, file, old, new)
                with self.assertRaises(ValueError): rady_own_fields(item, cache, person['name'])

    def test_conflicting_contact_and_forged_review_values_or_original_ownership_fail_closed(self):
        for mode in ['contact', 'value', 'proof', 'original', 'owner', 'additional']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, file, person = self.fixture(cache)
                if mode == 'contact':
                    self.revise(item, file, '<li class="email">', '<li class="email"><a href="mailto:other@ucsd.edu">other@ucsd.edu</a>')
                    with self.assertRaises(ValueError): rady_own_fields(item, cache, person['name'])
                    continue
                row = self.review(item, cache, person); people = [person]
                if mode == 'value': row['fields'] = {**row['fields'], 'researchAreas': ['Invented']}
                if mode == 'proof': row['fieldEvidence']['researchAreas'][0]['evidence'] = 'Invented'
                if mode == 'original':
                    row['originalSourceProfessorRecord']['name'] = 'Another Person'
                    row['originalSourceRecordSha256'] = record_sha256(row['originalSourceProfessorRecord'])
                if mode == 'owner': people.append({**copy.deepcopy(person), 'id': 'other-id'})
                if mode == 'additional': row['additionalSourceIdentity'] = {'requestedUrl': item['url']}
                with self.assertRaises(ValueError): verified_professor_fields({'entries': [row]}, {'items': {'x': item}}, cache, people)

    def test_shared_verifier_and_application_preserve_identity_primary_summary_teaching_and_ratings(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, _, person = self.fixture(cache); before = copy.deepcopy(person)
            row = self.review(item, cache, person)
            reviewed = verified_professor_fields({'entries': [row]}, {'items': {'x': item}}, cache, [person])
            data = {'professors': [person]}; apply_professor_fields(data, reviewed)
            for field in ['id', 'name', 'department', 'institution', 'officialProfileUrl', 'researchSummary', 'teaching', 'ratings']:
                self.assertEqual(person.get(field), before.get(field), field)
            self.assertEqual(person['researchAreas'], row['fields']['researchAreas'])
            self.assertTrue(person['professorFieldReviews'][0]['captureVerified'])
            first = copy.deepcopy(person); apply_professor_fields(data, reviewed)
            self.assertEqual(person, first)


if __name__ == '__main__':
    unittest.main()
