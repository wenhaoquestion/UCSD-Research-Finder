import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from faculty_department_normalizations import (
    RULES, unit_observation, appointment_observation,
    verified_department_normalizations, apply_department_normalizations,
)
from collect_ucsd_coverage import profiles_appointment
from lab_resource_reviews import record_sha256
from test_atlas_quality import professor


class DepartmentNormalizationTests(unittest.TestCase):
    def capture(self, cache, queue, uri, markup):
        path = cache / 'responses' / (hashlib.sha256(uri.encode()).hexdigest() + '.html')
        path.parent.mkdir(exist_ok=True); path.write_text(markup)
        item = {'url': uri, 'fetch': {'status': 'ok', 'httpStatus': 200, 'sourceUrl': uri,
            'finalUrl': uri, 'observedAt': '2026-10-16T03:00:00+00:00',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'redirects': []}}
        queue['items'][uri] = item
        return item, path

    def fixture(self, cache, raw='Orthopedic Surgery'):
        unit_id, home, title, published, kind = RULES[raw]
        registry = {'id': unit_id, 'name': 'Orthopaedic Surgery' if raw == 'Orthopedic Surgery' else published,
                    'homepage': home, 'school': 'School of Medicine'}
        queue = {'items': {}}
        unit, unit_path = self.capture(cache, queue, home, f'<html><head><title>{title}</title></head><body><main>Welcome</main></body></html>')
        uri = 'https://profiles.ucsd.edu/jane.example'
        markup = f'''<html><head><title>Jane Example | UCSD Profiles</title>
            <link rel="canonical" href="{uri}">
            <link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/123/123.rdf"></head>
            <body><main><div class="pageTitle"><h2>Jane Example</h2></div>
            <div class="basicInfo"><table>
            <tr><th>Title(s)</th><td>Clinical Professor (Voluntary), {raw}</td></tr>
            <tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table></div>
            <div class="basicInfo scroll"><table><tr><td>Other Person, Pediatrics</td><td>Project Investigator</td></tr></table></div>
            <p>Biography: a center and another department.</p></main></body></html>'''
        own, own_path = self.capture(cache, queue, uri, markup)
        person = professor('unchanged-id', 'Jane Example', 'Unknown')
        person['officialProfileUrl'] = uri
        person['lastVerified'] = '2020-01-01'
        assessment, listing = profiles_appointment(own['fetch'], markup)
        person['directoryListings'] = [listing]
        person['departmentAffiliations'] = ['Unknown']
        rule = {'sourceUnitAsPublished': raw, 'originalDepartmentRecord': registry,
            'originalDepartmentRecordSha256': record_sha256(registry), 'reason': 'Reviewed exact unit spelling.',
            'unitObservation': unit_observation(raw, registry, unit, cache)}
        entry = {'professorId': person['id'], 'sourceUnitAsPublished': raw,
            'originalProfessorRecord': copy.deepcopy(person), 'originalProfessorRecordSha256': record_sha256(person),
            'reason': 'Retain raw dated listing and normalize its registered unit category.',
            'appointmentObservation': appointment_observation(person, own, cache)}
        return person, registry, queue, {'rules': [rule], 'entries': [entry]}, own_path, unit_path

    def verify(self, review, queue, cache, person, registry):
        return verified_department_normalizations(review, queue, cache, [person], [registry])

    def test_dated_unit_category_changes_preserve_identity_role_and_full_history_idempotently(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); person, registry, queue, review, *_ = self.fixture(cache)
            before = copy.deepcopy((person, registry, queue, review))
            verified = self.verify(review, queue, cache, person, registry)
            data = {'professors': [copy.deepcopy(person)], 'labs': []}
            apply_department_normalizations(data, verified)
            updated = data['professors'][0]
            self.assertEqual(updated['department'], 'Orthopaedic Surgery')
            for k in ['id', 'name', 'institution', 'officialProfileUrl', 'lastVerified', 'directoryListings',
                      'departmentAffiliations', 'researchAreas', 'email', 'teaching', 'ratings']:
                self.assertEqual(updated.get(k), person.get(k), k)
            self.assertEqual(updated['departmentNormalizationReviews'][0]['originalProfessorRecord'], person)
            self.assertEqual(len(updated['fieldEvidence']['department']), 4)
            once = copy.deepcopy(data); apply_department_normalizations(data, verified)
            self.assertEqual(data, once)
            self.assertEqual((person, registry, queue, review), before)

    def test_every_reviewed_rule_requires_its_exact_registered_resource_and_document_title(self):
        for raw in RULES:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); person, registry, queue, review, *_ = self.fixture(cache, raw)
                self.assertEqual(len(self.verify(review, queue, cache, person, registry)), 1)
                changed = copy.deepcopy(registry); changed['homepage'] += 'faculty/'
                with self.assertRaises(ValueError): self.verify(review, queue, cache, person, changed)

    def test_changed_bytes_dates_titles_and_redirects_fail_closed(self):
        for mode in ['own-bytes', 'unit-bytes', 'date', 'title', 'redirect', 'status', 'rdf', 'canonical']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); person, registry, queue, review, own_path, unit_path = self.fixture(cache)
                own = queue['items'][person['officialProfileUrl']]; unit = queue['items'][registry['homepage']]
                if mode == 'own-bytes': own_path.write_text(own_path.read_text() + 'changed')
                if mode == 'unit-bytes': unit_path.write_text(unit_path.read_text() + 'changed')
                if mode == 'date': own['fetch']['observedAt'] = '2026-10-17T00:00:00+00:00'
                if mode == 'status': unit['fetch']['httpStatus'] = 404
                if mode == 'redirect': unit['fetch']['finalUrl'] += 'other/'
                if mode in {'title', 'rdf', 'canonical'}:
                    path = unit_path if mode == 'title' else own_path
                    old, new = {'title': ('Department of Orthopedic Surgery', 'Pediatrics'),
                        'rdf': ('/123/123.rdf', '/456/456.rdf'),
                        'canonical': ('rel="canonical" href="https://profiles.ucsd.edu/jane.example"',
                                      'rel="canonical" href="https://profiles.ucsd.edu/other.person"')}[mode]
                    path.write_text(path.read_text().replace(old, new))
                    (unit if mode == 'title' else own)['fetch']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaises(ValueError): self.verify(review, queue, cache, person, registry)

    def test_admin_center_subdivision_and_truncated_unit_names_cannot_infer_a_parent(self):
        for raw in ['Emergency Medical Services', 'Structural System Facility', 'Provost - Muir',
                    'Center for Energy Research', 'Marine Biology', 'Theatre', 'Orthopedic Surgery Research Center']:
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); person, registry, queue, review, *_ = self.fixture(cache)
                review['rules'][0]['sourceUnitAsPublished'] = raw
                review['entries'][0]['sourceUnitAsPublished'] = raw
                with self.assertRaises(ValueError): self.verify(review, queue, cache, person, registry)

    def test_distinct_same_name_profiles_initials_or_owned_primary_cannot_create_a_binding(self):
        for mode in ['different-primary', 'initial-name', 'duplicate-owner', 'changed-id', 'known-department']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); person, registry, queue, review, *_ = self.fixture(cache)
                people = [copy.deepcopy(person)]
                if mode == 'different-primary': people[0]['officialProfileUrl'] = 'https://profiles.ucsd.edu/jane.example.2'
                if mode == 'initial-name':
                    people[0]['name'] = 'J. Example'
                    original = review['entries'][0]['originalProfessorRecord']
                    original['name'] = 'J. Example'
                    review['entries'][0]['originalProfessorRecordSha256'] = record_sha256(original)
                if mode == 'duplicate-owner':
                    extra = copy.deepcopy(person); extra['id'] = 'second-id'; people.append(extra)
                if mode == 'changed-id': review['entries'][0]['professorId'] = 'other-id'
                if mode == 'known-department': people[0]['department'] = 'Pediatrics'
                with self.assertRaises(ValueError): verified_department_normalizations(review, queue, cache, people, [registry])

    def test_unaccepted_or_changed_own_listing_and_tampered_snapshots_are_rejected(self):
        for mode in ['missing-listing', 'role', 'date', 'hash', 'unit', 'duplicate-row']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); person, registry, queue, review, *_ = self.fixture(cache)
                entry = review['entries'][0]; original = entry['originalProfessorRecord']
                if mode == 'missing-listing': original['directoryListings'] = []
                if mode == 'role': original['directoryListings'][0]['listedRole'] = 'Professor, Pediatrics'
                if mode == 'date': original['directoryListings'][0]['observedAt'] = '2025-01-01'
                if mode == 'unit': entry['sourceUnitAsPublished'] = 'Division of Biological Science'
                if mode == 'duplicate-row': review['entries'].append(copy.deepcopy(entry))
                if mode != 'hash': entry['originalProfessorRecordSha256'] = record_sha256(original)
                else: entry['originalProfessorRecordSha256'] = 'changed'
                with self.assertRaises(ValueError): self.verify(review, queue, cache, person, registry)

    def test_ambiguous_own_template_and_unlabelled_biography_do_not_supply_appointment_rows(self):
        for change in ['duplicate', 'outside', 'label']:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                cache = Path(tmp); person, registry, queue, review, own_path, *_ = self.fixture(cache)
                markup = own_path.read_text()
                if change == 'duplicate': markup = markup.replace('</table></div>', '</table></div><div class="basicInfo"><table><tr><th>School</th><td>Other School</td></tr></table></div>', 1)
                if change == 'outside': markup = markup.replace('class="basicInfo"', 'class="biography"')
                if change == 'label': markup = markup.replace('<th>Title(s)</th>', '<td>Title(s)</td>')
                own_path.write_text(markup); item = queue['items'][person['officialProfileUrl']]
                item['fetch']['sha256'] = hashlib.sha256(own_path.read_bytes()).hexdigest()
                with self.assertRaises(ValueError): appointment_observation(person, item, cache)

    def test_batch_is_atomic_and_old_admission_proof_replay_does_not_grow_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp); person, registry, queue, review, *_ = self.fixture(cache)
            rows = self.verify(review, queue, cache, person, registry)
            data = {'professors': [copy.deepcopy(person)]}; before = copy.deepcopy(data)
            bad = copy.deepcopy(rows[0]); bad['professorId'] = 'missing'
            with self.assertRaises(ValueError): apply_department_normalizations(data, rows + [bad])
            self.assertEqual(data, before)
            apply_department_normalizations(data, rows); once = copy.deepcopy(data)
            p = data['professors'][0]
            old = copy.deepcopy(person.get('fieldEvidence', {}).get('department', []))
            p['fieldEvidence']['department'] += old if isinstance(old, list) else [old]
            apply_department_normalizations(data, rows)
            self.assertEqual(data, once)


if __name__ == '__main__':
    unittest.main()
