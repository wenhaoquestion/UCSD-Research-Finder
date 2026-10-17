import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from candidate_primary_roots import root_observation, source_key, reviewed_primary_roots
from candidate_profile_associations import reviewed_new_candidate_sources
from collect_ucsd_coverage import profiles_appointment
from lab_resource_reviews import record_sha256
from refresh_faculty_directories import build_evidence


class CandidatePrimaryRootTests(unittest.TestCase):
    def capture(self, cache, queue, uri, markup, day='16'):
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.parent.mkdir(exist_ok=True); path.write_text(markup)
        item = {'url': uri, 'state': 'done', 'contexts': [], 'fetch': {
            'sourceUrl': uri, 'finalUrl': uri, 'status': 'ok', 'httpStatus': 200,
            'observedAt': f'2026-10-{day}T00:00:00+00:00',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
        queue['items'][uri] = item
        return item, path

    def fixture(self, cache):
        queue = {'items': {}}
        primary = 'https://matsci.ucsd.edu/faculty/jane-example'
        roster = 'https://matsci.ucsd.edu/index.php/faculty'
        quote = 'Jane Example Associate Professor Mechanical and Aerospace Engineering'
        parent, parent_path = self.capture(cache, queue, roster,
            f'<html><body><main><div><a href="{primary}">Jane Example</a>'
            '<p>Associate Professor</p><p>Mechanical and Aerospace Engineering</p></div></main></body></html>')
        own, own_path = self.capture(cache, queue, primary,
            '<html><body><main><h1>Jane Example</h1><p>Associate Professor</p></main></body></html>')
        row = {'name': 'Jane Example', 'department': 'Mechanical & Aerospace Engineering',
            'listedRole': 'Associate Professor', 'appointmentStatus': 'listed_faculty',
            'directorySection': 'Materials Science affiliated faculty', 'sourceUrl': roster,
            'observedAt': parent['fetch']['observedAt'], 'profileUrl': primary, 'namedLinkUrl': primary,
            'evidence': {'sourceUrl': roster, 'observedAt': parent['fetch']['observedAt'],
                         'evidence': quote, 'method': 'official_materials_faculty_name_title_department_card', 'status': 'verified'},
            'email': '', 'personalWebsiteUrl': '', 'googleScholarUrl': '', 'researchAreas': []}
        previous = build_evidence([row], [])[0][0]
        uri = 'https://profiles.ucsd.edu/jane.example'
        markup = f'''<html><head><link rel="canonical" href="{uri}">
        <link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/123/123.rdf"></head>
        <body><main><div class="pageTitle"><h2>Jane Example</h2></div><table>
        <tr><th>Title(s)</th><td>Associate Professor, Mechanical and Aerospace Engineering</td></tr>
        <tr><th>School</th><td>Vc-academic Affairs</td></tr></table></main></body></html>'''
        incoming, _ = self.capture(cache, queue, uri, markup, '17')
        _, later = profiles_appointment(incoming['fetch'], markup)
        observation = root_observation(previous, row, queue['items'], cache)
        entry = {'action': 'retain_previously_qualified_primary', 'professorId': previous['id'],
            'originalProfessorRecord': previous, 'originalProfessorRecordSha256': record_sha256(previous),
            'sourceCandidateAtlasSha256': 'a' * 64, 'sourceObservationKey': source_key(row),
            'sourceObservation': observation, 'reason': 'Preserve the earlier accepted primary and hold an unbound alternative.'}
        return queue, previous, [later, row], {'entries': [entry]}, parent_path, own_path

    def test_later_source_order_cannot_replace_prior_id_primary_or_bind_same_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); queue, previous, rows, review, *_ = self.fixture(cache)
            before = copy.deepcopy((queue, previous, rows, review))
            unanchored = reviewed_new_candidate_sources(rows, [], queue, cache)
            self.assertEqual(unanchored[0][0]['id'], rows[0]['discoveryId'])
            result = reviewed_new_candidate_sources(rows, [], queue, cache, review)
            self.assertEqual(len(result[0]), 1)
            self.assertEqual(result[0][0], previous)
            self.assertEqual(result[2][0]['incomingProfileUri'], rows[0]['profileUrl'])
            self.assertEqual(result[2][0]['candidateProposedProfessorIds'], [previous['id']])
            self.assertTrue(result[3]['previouslyQualifiedPrimaryRoots'][0]['captureVerified'])
            self.assertEqual((queue, previous, rows, review), before)
            self.assertEqual(result, reviewed_new_candidate_sources(rows, [], queue, cache, review))

    def test_reordering_unrelated_sources_keeps_the_same_accepted_root_and_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); queue, previous, rows, review, *_ = self.fixture(cache)
            first = reviewed_new_candidate_sources(rows, [], queue, cache, review)
            second = reviewed_new_candidate_sources(list(reversed(rows)), [], queue, cache, review)
            self.assertEqual(first, second)
            self.assertEqual(first[0][0]['officialProfileUrl'], previous['officialProfileUrl'])

    def test_missing_qualified_root_or_capture_does_not_resurrect_a_previous_candidate(self):
        for mode in ['qualified-row', 'roster-capture', 'own-capture', 'role']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); queue, previous, rows, review, *_ = self.fixture(cache)
                if mode == 'qualified-row': rows.pop()
                if mode == 'roster-capture': del queue['items'][rows[1]['sourceUrl']]
                if mode == 'own-capture': del queue['items'][previous['officialProfileUrl']]
                if mode == 'role': rows[1]['listedRole'] = 'Research Associate'
                with self.assertRaises(ValueError): reviewed_primary_roots(review, rows, [], queue, cache)

    def test_tampered_record_source_date_or_primary_review_is_rejected(self):
        for mode in ['record-hash', 'snapshot-hash', 'wrong-id', 'date', 'department', 'initials', 'duplicate']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); queue, previous, rows, review, *_ = self.fixture(cache)
                entry = review['entries'][0]
                if mode == 'record-hash': entry['originalProfessorRecordSha256'] = 'changed'
                if mode == 'snapshot-hash': entry['sourceCandidateAtlasSha256'] = 'changed'
                if mode == 'wrong-id': entry['professorId'] = 'another-id'
                if mode == 'date': entry['sourceObservationKey'][1] = '2020-01-01'
                if mode == 'department': previous['department'] = 'Physics'; entry['originalProfessorRecordSha256'] = record_sha256(previous)
                if mode == 'initials':
                    previous['name'] = 'J. Example'; entry['originalProfessorRecordSha256'] = record_sha256(previous)
                if mode == 'duplicate': review['entries'].append(copy.deepcopy(entry))
                with self.assertRaises(ValueError): reviewed_primary_roots(review, rows, [], queue, cache)

    def test_literal_named_roster_link_and_own_subject_are_required_after_rehash(self):
        for mode in ['link', 'subject', 'quote', 'bytes']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); queue, previous, rows, review, parent_path, own_path = self.fixture(cache)
                path = own_path if mode == 'subject' else parent_path
                text = path.read_text()
                if mode == 'link': text = text.replace(previous['officialProfileUrl'], 'https://matsci.ucsd.edu/faculty/other-person')
                if mode == 'subject': text = text.replace('Jane Example', 'Another Person')
                if mode == 'quote': text = text.replace('Associate Professor', 'Research Associate')
                if mode == 'bytes': text += 'changed'
                path.write_text(text)
                if mode != 'bytes':
                    uri = previous['officialProfileUrl'] if mode == 'subject' else rows[1]['sourceUrl']
                    queue['items'][uri]['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaises(ValueError): reviewed_primary_roots(review, rows, [], queue, cache)

    def test_existing_legacy_identity_and_duplicate_primary_ownership_require_separate_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); queue, previous, rows, review, *_ = self.fixture(cache)
            for existing in [previous, {**previous, 'id': 'another-existing-id'}]:
                with self.assertRaises(ValueError): reviewed_primary_roots(review, rows, [existing], queue, cache)
            duplicate = copy.deepcopy(review['entries'][0])
            duplicate['professorId'] = 'another-root'
            duplicate['originalProfessorRecord']['id'] = 'another-root'
            duplicate['originalProfessorRecordSha256'] = record_sha256(duplicate['originalProfessorRecord'])
            with self.assertRaises(ValueError): reviewed_primary_roots({'entries': review['entries'] + [duplicate]}, rows, [], queue, cache)


if __name__ == '__main__':
    unittest.main()
