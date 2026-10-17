import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from matsci_own_fields import matsci_own_fields
from professor_own_field_reviews import verified_professor_fields, apply_professor_fields
from lab_resource_reviews import record_sha256
from test_atlas_quality import professor


class MaterialsOwnFieldTests(unittest.TestCase):
    def fixture(self, cache, focus='Materials in extreme environments; nuclear materials; fusion energy; material design and discovery'):
        uri = 'https://matsci.ucsd.edu/faculty/jane-example'
        summary = 'Jane Example studies material degradation and develops computational machine learning tools.'
        markup = f'''<html><head><title>Jane Example | Program in Materials Science and Engineering</title>
        <link rel="canonical" href="{uri}"></head><body><main><h1 class="title">Jane Example</h1>
        <article role="article" class="faculty-listing faculty full clearfix" about="/faculty/jane-example">
        <div class="field field--name-field-research-focus field--type-string-long field--label-above">
          <div class="field__label">Research Focus</div><div class="field__item">{focus}</div></div>
        <div class="clearfix text-formatted field field--name-field-research-summary field--type-text-long field--label-above">
          <div class="field__label">Research Summary</div><div class="field__item">{summary}</div></div>
        <h4>Bio</h4><div class="field--name-body">Another Person studied unsupported biography topics.</div>
        </article><aside><p>Research Focus: unrelated sidebar topics.</p></aside></main></body></html>'''
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.parent.mkdir(); path.write_text(markup)
        item = {'url': uri, 'fetch': {'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok', 'httpStatus': 200,
            'observedAt': '2026-10-16T01:16:08+00:00', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
        person = professor('unchanged-id', 'Jane Example', 'Mechanical & Aerospace Engineering')
        person['officialProfileUrl'] = uri; person['researchAreas'] = []
        person['researchSummary'] = 'Earlier unverified research overview.'
        return item, path, person, summary

    def rewrite(self, item, path, old, new, rehash=True):
        path.write_text(path.read_text().replace(old, new))
        if rehash: item['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def review(self, person, item, cache):
        actual = matsci_own_fields(item, cache, person['name'])
        return {'professorId': person['id'], 'sourceProfessorId': person['id'],
            'originalSourceProfessorRecord': copy.deepcopy(person), 'originalSourceRecordSha256': record_sha256(person),
            'sourceTemplate': 'matsci_drupal_labelled_own_fields', 'reason': 'Read literal labelled own research fields.',
            'sourceObservation': actual, 'fields': actual['fields'], 'fieldEvidence': actual['fieldEvidence']}

    def test_explicit_focus_and_summary_exclude_bio_and_do_not_infer_summary_keywords(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, _, person, summary = self.fixture(cache)
            actual = matsci_own_fields(item, cache, person['name'])
            self.assertEqual(actual['fields'], {'researchAreas': ['Materials in extreme environments', 'nuclear materials', 'fusion energy', 'material design and discovery'], 'researchSummary': summary})
            self.assertNotIn('machine learning', actual['fields']['researchAreas'])
            self.assertNotIn('unsupported biography topics', str(actual['fields']))
            for proofs in actual['fieldEvidence'].values():
                self.assertEqual(proofs[0]['sourceUrl'], item['url'])
                self.assertEqual(proofs[0]['observedAt'], item['fetch']['observedAt'])
                self.assertEqual(proofs[0]['bodySha256'], item['fetch']['sha256'])

    def test_commas_inside_a_published_focus_statement_remain_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); value = 'Molecular and cellular interactions in microbial systems, ion channel mediated electrical signaling in bacteria'
            item, _, person, _ = self.fixture(cache, value)
            self.assertEqual(matsci_own_fields(item, cache, person['name'])['fields']['researchAreas'], [value])

    def test_wrong_ambiguous_subject_canonical_and_drupal_article_fail_closed(self):
        changes = [('<h1 class="title">Jane Example</h1>', '<h1>Another Person</h1>'),
            ('Jane Example | Program', 'Another Person | Program'),
            ('rel="canonical" href="https://matsci.ucsd.edu/faculty/jane-example"', 'rel="canonical" href="https://matsci.ucsd.edu/faculty/other-person"'),
            ('</head>', '<link rel="canonical" href="https://matsci.ucsd.edu/faculty/jane-example"></head>'),
            ('about="/faculty/jane-example"', 'about="/faculty/other-person"'),
            ('class="faculty-listing faculty full clearfix"', 'class="other-people"'),
            ('</main>', '<h1>Another Person</h1></main>')]
        for old, new in changes:
            with self.subTest(change=new), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path, person, _ = self.fixture(cache); self.rewrite(item, path, old, new)
                with self.assertRaises(ValueError): matsci_own_fields(item, cache, person['name'])

    def test_label_duplicates_nested_people_publications_and_bio_cannot_supply_fields(self):
        changes = [('<div class="field__label">Research Focus</div>', '<div class="field__label">Bio</div>'),
            ('<div class="field__item">Materials', '<div class="field__item"><article>Another Person</article>Materials'),
            ('<div class="field__item">Jane Example studies', '<div class="field__item"><ul><li>Paper title</li></ul>Jane Example studies'),
            ('</article>', '<div class="field--name-field-research-focus">Unrelated second field</div></article>')]
        for old, new in changes:
            with self.subTest(change=new), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path, person, _ = self.fixture(cache); self.rewrite(item, path, old, new)
                with self.assertRaises(ValueError): matsci_own_fields(item, cache, person['name'])

    def test_stale_bytes_dates_or_reviewed_values_and_additional_source_bindings_are_rejected(self):
        for mode in ['bytes', 'date', 'value', 'additional', 'department']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); item, path, person, _ = self.fixture(cache); row = self.review(person, item, cache)
                if mode == 'bytes': self.rewrite(item, path, '</main>', 'changed</main>', False)
                if mode == 'date': item['fetch']['observedAt'] = '2026-10-17T00:00:00+00:00'
                if mode == 'value': row['fields']['researchAreas'].append('Invented topic')
                if mode == 'additional': row['additionalSourceIdentity'] = {'requestedUrl': item['url']}
                if mode == 'department': row['fields']['department'] = 'Physics'
                with self.assertRaises(ValueError): verified_professor_fields({'entries': [row]}, {'items': {'x': item}}, cache, [person])

    def test_review_application_preserves_identity_dates_contacts_relationships_and_old_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); item, _, person, summary = self.fixture(cache)
            before = copy.deepcopy(person); row = self.review(person, item, cache)
            verified = verified_professor_fields({'entries': [row]}, {'items': {'x': item}}, cache, [person])
            data = {'professors': [person]}; apply_professor_fields(data, verified)
            self.assertEqual(person['researchSummary'], summary)
            for field in ['id', 'name', 'department', 'officialProfileUrl', 'email', 'lastVerified', 'labAffiliation', 'labAffiliationUrl', 'teaching', 'ratings']:
                self.assertEqual(person.get(field), before.get(field), field)
            self.assertTrue(any(o['field'] == 'researchSummary' and o['value'] == before['researchSummary'] for o in person['previousFieldObservations']))
            once = copy.deepcopy(data); apply_professor_fields(data, verified); self.assertEqual(data, once)


if __name__ == '__main__':
    unittest.main()
