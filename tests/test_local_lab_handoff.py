"""Admission/provenance guards use isolated captures, never live collection state."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import lab_summary_handoff as handoff


def digest(data):
    return hashlib.sha256(data).hexdigest()


class ReviewedHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.hp = self.root / handoff.HANDOFF_RELATIVE_PATH
        self.dp = self.root / handoff.DECISIONS_RELATIVE_PATH
        self.bp = self.root / 'data/research-atlas.json'
        self.qp = self.root / '.cache/coverage-20261016/queue.json'
        self.responses = self.qp.parent / 'responses'
        self.responses.mkdir(parents=True)
        self.frozen_ids = frozenset({'alpha', 'beta'})
        self.url = 'https://official.ucsd.edu/labs/'
        self.observed = '2026-10-01T01:00:00+00:00'
        self.body = b'<main><h1>Alpha Lab</h1><p>Beta Group at UC San Diego. PI: G. Scientist</p></main>\r\n'
        self.cache = self.responses / (digest(self.url.encode()) + '.html')
        self.cache.write_bytes(self.body)
        self.baseline = {'labs': [{'id': 'baseline', 'labWebsiteUrl': 'https://baseline.ucsd.edu/'}],
                         'professors': [{'id': 'known-professor'}]}
        self.queue = {'updatedAt': '2026-10-16T02:00:00+00:00',
                      'counts': {'done': 1, 'pending': 99, 'running': 1}, 'items': {
                          self.url: {'url': self.url, 'state': 'done', 'fetch': {
                              'status': 'ok', 'httpStatus': 200, 'sourceUrl': self.url,
                              'finalUrl': self.url, 'observedAt': self.observed, 'sha256': digest(self.body)}},
                          'pending': {'url': 'https://pending.ucsd.edu/', 'state': 'pending'},
                          'running': {'url': 'https://running.ucsd.edu/', 'state': 'running'}}}
        self.labs = []
        self.decisions = {'schemaVersion': 1, 'labs': {}}
        for lid, name, website in [('alpha', 'Alpha Lab', 'https://alpha.ucsd.edu/'),
                                    ('beta', 'Beta Group', 'https://beta.ucsd.edu/')]:
            proof = self.proof(name)
            institution = self.proof('UC San Diego')
            lab = {'id': lid, 'labName': name, 'institution': 'University of California San Diego',
                   'department': 'Unknown', 'labWebsiteUrl': website, 'recordSubtype': 'lab',
                   'principalInvestigator': 'Not found', 'principalInvestigatorProfileUrl': 'Not found',
                   'researchAreas': [], 'description': 'Reviewed research entity.', 'contactEmail': 'Not found',
                   'recruitingStatus': 'Unknown', 'recruitingEvidence': {'text': '', 'url': ''},
                   'sourceUrls': [self.url], 'lastVerified': '2026-10-15', 'professorIds': [],
                   'fieldEvidence': {'labName': [proof], 'institution': [institution],
                                     'labWebsiteUrl': [copy.deepcopy(proof)]}}
            decision = {'action': 'accept', 'stableLabId': lid, 'name': name, 'recordSubtype': 'lab',
                        'reason': 'Explicit fixture review.', 'identityEvidence': [copy.deepcopy(proof)],
                        'institutionEvidence': [copy.deepcopy(institution)]}
            self.labs.append(lab)
            self.decisions['labs'][website] = decision
        self.labs[1].update(principalInvestigator='G. Scientist',
                            principalInvestigatorIdentityScope='initials_as_published; unresolved full identity',
                            contentDateNote='Last updated 2019; not current personnel evidence.')
        pi = self.proof('PI: G. Scientist')
        self.labs[1]['fieldEvidence']['principalInvestigator'] = [pi]
        self.decisions['labs']['https://beta.ucsd.edu/'].update(
            principalInvestigator='G. Scientist', piEvidence=[copy.deepcopy(pi)],
            principalInvestigatorIdentityScope=self.labs[1]['principalInvestigatorIdentityScope'])
        self.data = {'schemaVersion': 1, 'generatedAt': '2026-10-16T01:30:00+00:00',
                     'collectionState': 'reviewed_incremental', 'isFinalExport': False,
                     'servedAtlasModified': False, 'queueCheckpointAt': '2026-10-16T01:25:00+00:00',
                     'queueStates': {'done': 1, 'pending': 100}, 'labs': self.labs, 'recordCount': 2,
                     'labAliases': [{'labId': 'baseline', 'url': 'https://alias.ucsd.edu/'}],
                     'reviewedAliasCount': 24,
                     'labUpdates': [{'labId': 'baseline', 'fields': {'labName': 'DO NOT APPLY'}}],
                     'sourceManifest': [{'sourceUrl': self.url, 'requestedUrl': self.url,
                                         'observedAt': self.observed, 'bodySha256': digest(self.body),
                                         'cachePath': str(self.cache)}]}
        self.save()
        self.pins = self.current_pins()

    def proof(self, text):
        return {'sourceUrl': self.url, 'observedAt': self.observed,
                'method': 'reviewed_fixture', 'evidence': text, 'status': 'verified'}

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def save(self):
        for lab in self.data['labs']:
            lab['verification'] = {'status': 'source_checked',
                                   'fieldsVerified': sorted(lab['fieldEvidence']),
                                   'lastEvidenceAt': self.observed}
        self.write(self.dp, self.decisions)
        self.write(self.bp, self.baseline)
        self.data['decisionArtifactSha256'] = digest(self.dp.read_bytes())
        self.data['servedAtlasSha256'] = digest(self.bp.read_bytes())
        self.write(self.hp, self.data)
        self.write(self.qp, self.queue)

    def current_pins(self):
        return {'HANDOFF_SHA256': digest(self.hp.read_bytes()),
                'DECISIONS_SHA256': digest(self.dp.read_bytes()),
                'BASELINE_SHA256': digest(self.bp.read_bytes()),
                'BASELINE_LAB_COUNT': 1, 'FROZEN_LAB_IDS': self.frozen_ids}

    def load(self, *, repin=False, baseline=None):
        pins = self.current_pins() if repin else self.pins
        with patch.multiple(handoff, **pins):
            return handoff.load_reviewed_handoff(self.baseline if baseline is None else baseline,
                                                collection=self.root)

    def add_shared_pair(self):
        """Real reviewed IDs/names/action shape, backed by isolated cache bytes."""
        self.shared_url = handoff.SHARED_URL
        text = ('Welcome to the labs at UC San Diego. '
                + '. '.join(handoff.SHARED_IDENTITY_QUOTES.values())
                + '. The two labs collaborate closely on research.')
        body = ('<main><p>' + text + '</p></main>').encode()
        path = self.responses / (digest(self.shared_url.encode()) + '.html')
        path.write_bytes(body)
        self.queue['items'][self.shared_url] = {
            'url': self.shared_url, 'state': 'done', 'fetch': {
                'status': 'ok', 'httpStatus': 200, 'sourceUrl': self.shared_url,
                'finalUrl': self.shared_url, 'observedAt': self.observed, 'sha256': digest(body)}}
        self.data['sourceManifest'].append({
            'sourceUrl': self.shared_url, 'requestedUrl': self.shared_url,
            'observedAt': self.observed, 'bodySha256': digest(body), 'cachePath': str(path)})
        def proof(quote):
            return dict(self.proof(quote), sourceUrl=self.shared_url)
        sharing_proofs = [proof(text)]
        sharing = {'kind': 'distinct_named_labs', 'groupId': handoff.SHARED_GROUP_ID,
                   'memberLabIds': sorted(handoff.SHARED_LAB_NAMES), 'evidence': sharing_proofs}
        entities = []
        for lid, name in handoff.SHARED_LAB_NAMES.items():
            identity = [proof(handoff.SHARED_IDENTITY_QUOTES[lid])]
            lab = copy.deepcopy(self.labs[0])
            lab.update(id=lid, labName=name, labWebsiteUrl=self.shared_url,
                       sourceUrls=[self.shared_url], websiteSharing=copy.deepcopy(sharing),
                       fieldEvidence={'labName': identity, 'institution': [proof('UC San Diego')],
                                      'labWebsiteUrl': copy.deepcopy(identity),
                                      'websiteSharing': copy.deepcopy(sharing_proofs)})
            self.data['labs'].append(lab)
            entities.append({'stableLabId': lid, 'name': name, 'reason': 'Separate named lab.',
                             'identityEvidence': copy.deepcopy(identity),
                             'institutionEvidence': [proof('UC San Diego')]})
        self.decisions['labs'][self.shared_url] = {
            'action': 'accept_shared_entities', 'reason': 'Two separately reviewed labs.',
            'sharingGroupId': handoff.SHARED_GROUP_ID,
            'sharingEvidence': copy.deepcopy(sharing_proofs), 'sharedEntities': entities}
        self.frozen_ids |= frozenset(handoff.SHARED_LAB_NAMES)
        self.data['recordCount'] = len(self.frozen_ids)
        self.save()
        self.pins = self.current_pins()

    def test_shared_pair_binds_two_entities_to_the_only_reviewed_resource(self):
        self.add_shared_pair()
        prior = copy.deepcopy(self.data['labs'][:2])
        labs, receipt = self.load()
        self.assertEqual(labs[:2], prior)
        self.assertEqual({l['id'] for l in labs[2:]}, set(handoff.SHARED_LAB_NAMES))
        self.assertEqual({l['labWebsiteUrl'] for l in labs[2:]}, {handoff.SHARED_URL})
        bindings = receipt['decisionBindings'][2:]
        self.assertEqual({b['labId'] for b in bindings}, set(handoff.SHARED_LAB_NAMES))
        self.assertTrue(all(b['action'] == 'accept_shared_entities'
                            and b['sharingGroupId'] == handoff.SHARED_GROUP_ID for b in bindings))
        self.assertEqual(receipt['validation']['rawByteCapturesVerified'], 2)

    def test_shared_pair_rejects_another_url_even_with_the_reviewed_ids(self):
        self.add_shared_pair()
        self.decisions['labs']['https://other.ucsd.edu/'] = self.decisions['labs'].pop(self.shared_url)
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Unreviewed shared URL/group'):
            self.load(repin=True)

    def test_shared_pair_rejects_unreviewed_group_ids_and_entity_ids(self):
        self.add_shared_pair()
        original = copy.deepcopy(self.decisions)
        for field in ['sharingGroupId', 'stableLabId']:
            with self.subTest(field=field):
                self.decisions = copy.deepcopy(original)
                decision = self.decisions['labs'][self.shared_url]
                if field == 'sharingGroupId':
                    decision[field] = 'other-sharing-group'
                else:
                    decision['sharedEntities'][0][field] = 'other-entity'
                self.save()
                with self.assertRaises(handoff.HandoffImportError):
                    self.load(repin=True)

    def test_shared_pair_requires_each_fixed_name_and_own_identity_quote(self):
        self.add_shared_pair()
        original = copy.deepcopy(self.decisions)
        for change in ['name', 'missing', 'swapped', 'source']:
            with self.subTest(change=change):
                self.decisions = copy.deepcopy(original)
                entities = self.decisions['labs'][self.shared_url]['sharedEntities']
                if change == 'name':
                    entities[0]['name'] = 'Combined Robotics Lab'
                elif change == 'missing':
                    entities[0]['identityEvidence'] = []
                elif change == 'swapped':
                    entities[0]['identityEvidence'] = copy.deepcopy(entities[1]['identityEvidence'])
                else:
                    entities[0]['identityEvidence'][0]['sourceUrl'] = self.url
                self.save()
                with self.assertRaisesRegex(handoff.HandoffImportError, 'name/identity proof'):
                    self.load(repin=True)

    def test_shared_pair_rejects_an_extra_third_entity(self):
        self.add_shared_pair()
        entities = self.decisions['labs'][self.shared_url]['sharedEntities']
        entities.append(dict(entities[0], stableLabId='third-entity'))
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'exactly two'):
            self.load(repin=True)

    def test_shared_pair_requires_explicit_parent_accept_action(self):
        self.add_shared_pair()
        for action in ['accept', 'unresolved', 'alias', None]:
            with self.subTest(action=action):
                self.decisions['labs'][self.shared_url]['action'] = action
                self.save()
                with self.assertRaisesRegex(handoff.HandoffImportError, 'explicit accept_shared_entities'):
                    self.load(repin=True)

    def test_shared_pair_cannot_be_admitted_as_two_ordinary_accepts(self):
        self.add_shared_pair()
        parent = self.decisions['labs'].pop(self.shared_url)
        for n, entity in enumerate(parent['sharedEntities']):
            self.decisions['labs'][self.shared_url + ('#second' if n else '')] = dict(entity, action='accept')
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'explicit accept_shared_entities'):
            self.load(repin=True)

    def test_plain_duplicate_urls_still_fail_without_a_reviewed_pair(self):
        decision = self.decisions['labs'].pop('https://beta.ucsd.edu/')
        self.labs[1]['labWebsiteUrl'] = 'http://www.alpha.ucsd.edu/index.html'
        self.decisions['labs'][self.labs[1]['labWebsiteUrl']] = decision
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'URL collision'):
            self.load(repin=True)

    def test_shared_pair_never_exempts_a_baseline_url_collision(self):
        self.add_shared_pair()
        self.baseline['labs'][0]['labWebsiteUrl'] = self.shared_url
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'URL collision'):
            self.load(repin=True)

    def test_shared_pair_requires_complete_identical_record_sharing(self):
        self.add_shared_pair()
        original = copy.deepcopy(self.data)
        for change in ['missing', 'membership', 'field_proof', 'identity']:
            with self.subTest(change=change):
                self.data = copy.deepcopy(original)
                lab = self.data['labs'][2]
                if change == 'missing':
                    lab.pop('websiteSharing')
                elif change == 'membership':
                    lab['websiteSharing']['memberLabIds'].append('third')
                elif change == 'field_proof':
                    lab['fieldEvidence']['websiteSharing'] = [self.proof('Alpha Lab')]
                else:
                    lab['fieldEvidence']['labName'] = [self.proof('Alpha Lab')]
                self.save()
                with self.assertRaisesRegex(handoff.HandoffImportError, 'inconsistent reviewed shared record'):
                    self.load(repin=True)

    def test_shared_pair_requires_explicit_two_lab_collaboration_evidence(self):
        self.add_shared_pair()
        self.decisions['labs'][self.shared_url]['sharingEvidence'][0]['evidence'] = 'The two labs collaborate closely'
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'both distinct collaborating labs'):
            self.load(repin=True)

    def test_shared_proof_still_must_be_literal_even_when_all_objects_agree(self):
        self.add_shared_pair()
        proofs = self.decisions['labs'][self.shared_url]['sharingEvidence']
        proofs[0]['evidence'] += ' An uncaptured claim.'
        for lab in self.data['labs'][2:]:
            lab['websiteSharing']['evidence'] = copy.deepcopy(proofs)
            lab['fieldEvidence']['websiteSharing'] = copy.deepcopy(proofs)
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Field quote not present'):
            self.load(repin=True)

    def test_shared_pair_keeps_pi_profile_and_professor_links_unresolved(self):
        self.add_shared_pair()
        original = copy.deepcopy(self.data)
        for field, value in [('principalInvestigator', 'Thomas Bewley'),
                             ('principalInvestigatorProfileUrl', 'https://example.ucsd.edu/person'),
                             ('professorIds', ['known-professor'])]:
            with self.subTest(field=field):
                self.data = copy.deepcopy(original)
                self.data['labs'][2][field] = value
                self.save()
                with self.assertRaisesRegex(handoff.HandoffImportError, 'PI/professor links'):
                    self.load(repin=True)

    def test_valid_batch_ignores_all_aliases_updates_and_keeps_actual_times(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        baseline = copy.deepcopy(self.baseline)
        labs, receipt = self.load()
        self.assertEqual([l['id'] for l in labs], ['alpha', 'beta'])
        self.assertEqual(self.baseline, baseline)
        self.assertEqual(receipt['ignoredLabAliases'], 1)
        self.assertEqual(receipt['declaredReviewedAliasCount'], 24)
        self.assertEqual(receipt['ignoredLabUpdates'], 1)
        self.assertEqual(receipt['globalQueueCounts']['pending'], 99)
        self.assertEqual(receipt['handoffQueueCounts']['pending'], 100)
        self.assertFalse(receipt['globalCollectionDeclaredComplete'])
        self.assertFalse(receipt['isFinalExport'])
        self.assertEqual(receipt['sourceManifest'][0]['observedAt'], self.observed)
        self.assertEqual(labs[0]['principalInvestigator'], 'Not found')
        self.assertEqual(labs[1]['principalInvestigator'], 'G. Scientist')
        self.assertIn('2019', labs[1]['contentDateNote'])
        self.assertEqual(receipt['sourceFile'], str(self.hp.resolve()))
        self.assertEqual(receipt['generatedAt'], self.data['generatedAt'])
        json.dumps(receipt)
        labs[0]['labName'] = 'Caller mutation'
        self.assertEqual(self.load()[0][0]['labName'], 'Alpha Lab')
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_absent_exact_handoff_is_optional_without_reading_other_files(self):
        self.hp.unlink()
        self.dp.unlink()
        self.qp.unlink()
        self.assertEqual(self.load(), ([], None))

    def test_approved_snapshot_retains_only_reviewed_ids_after_mutable_regeneration(self):
        directory=self.root/'approved';directory.mkdir()
        hp=directory/(handoff.HANDOFF_RELATIVE_PATH.stem+'-'+self.pins['HANDOFF_SHA256']+'.json')
        dp=directory/(handoff.DECISIONS_RELATIVE_PATH.stem+'-'+self.pins['DECISIONS_SHA256']+'.json')
        hp.write_bytes(self.hp.read_bytes());dp.write_bytes(self.dp.read_bytes())
        self.data['labs'].append({'id':'not-reviewed'});self.data['recordCount']=3
        self.write(self.hp,self.data)
        self.write(self.dp,{'labs':{'new':{'action':'accept','stableLabId':'not-reviewed'}}})
        with patch.multiple(handoff,**self.pins):
            labs,receipt=handoff.load_reviewed_handoff(self.baseline,collection=self.root,approved_snapshot_dir=directory)
        self.assertEqual([x['id'] for x in labs],['alpha','beta'])
        self.assertTrue(receipt['usesFrozenApprovedSnapshot'])
        self.assertFalse(receipt['mutableRevisionAutomaticallyAdmitted'])
        self.assertEqual(receipt['sourceSha256'],self.pins['HANDOFF_SHA256'])
        self.assertEqual(receipt['observedMutableHandoffSha256'],digest(self.hp.read_bytes()))
        self.assertNotEqual(receipt['sourceSha256'],receipt['observedMutableHandoffSha256'])

    def test_corrupt_approved_snapshot_fails_closed_even_if_mutable_file_is_valid(self):
        directory=self.root/'approved';directory.mkdir()
        hp=directory/(handoff.HANDOFF_RELATIVE_PATH.stem+'-'+self.pins['HANDOFF_SHA256']+'.json')
        hp.write_bytes(self.hp.read_bytes()+b'changed')
        with patch.multiple(handoff,**self.pins):
            with self.assertRaisesRegex(handoff.HandoffImportError,'SHA256'):
                handoff.load_reviewed_handoff(self.baseline,collection=self.root,approved_snapshot_dir=directory)

    def test_broken_symlink_is_not_an_absent_handoff(self):
        self.hp.unlink()
        self.hp.symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Cannot read'):
            self.load()

    def test_changed_handoff_bytes_fail_the_audited_pin(self):
        self.hp.write_bytes(self.hp.read_bytes() + b'\n')
        with self.assertRaisesRegex(handoff.HandoffImportError, 'handoff SHA256'):
            self.load()

    def test_changed_decision_bytes_fail_the_audited_pin(self):
        self.dp.write_bytes(self.dp.read_bytes() + b'\n')
        with self.assertRaisesRegex(handoff.HandoffImportError, 'decisions SHA256'):
            self.load()

    def test_decision_digest_must_be_bound_by_the_handoff(self):
        self.data['decisionArtifactSha256'] = '0' * 64
        self.write(self.hp, self.data)
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Decision artifact binding'):
            self.load(repin=True)

    def test_state_flags_schema_and_count_do_not_widen_completion_gate(self):
        original = copy.deepcopy(self.data)
        for field, value in [('collectionState', 'completed'), ('collectionState', 'reviewable'),
                             ('isFinalExport', True), ('isFinalExport', 0),
                             ('servedAtlasModified', True), ('schemaVersion', True), ('recordCount', 3)]:
            with self.subTest(field=field, value=value):
                self.data = copy.deepcopy(original)
                self.data[field] = value
                self.save()
                with self.assertRaises(handoff.HandoffImportError):
                    self.load(repin=True)

    def test_frozen_ids_reject_missing_extra_duplicate_and_renamed_records(self):
        original = copy.deepcopy(self.data)
        variants = [original['labs'][:1], original['labs'] + [dict(original['labs'][0], id='extra')],
                    [original['labs'][0], copy.deepcopy(original['labs'][0])],
                    [dict(original['labs'][0], id='renamed'), original['labs'][1]]]
        for labs in variants:
            with self.subTest(ids=[l['id'] for l in labs]):
                self.data = copy.deepcopy(original)
                self.data['labs'] = labs
                self.save()
                with self.assertRaisesRegex(handoff.HandoffImportError, 'frozen lab IDs'):
                    self.load(repin=True)

    def test_only_accept_with_exact_frozen_stable_id_is_admission(self):
        original = copy.deepcopy(self.decisions)
        for field, value in [('action', 'alias'), ('action', 'unresolved'), ('stableLabId', 'another-id')]:
            with self.subTest(field=field, value=value):
                self.decisions = copy.deepcopy(original)
                self.decisions['labs']['https://alpha.ucsd.edu/'][field] = value
                self.save()
                with self.assertRaisesRegex(handoff.HandoffImportError, 'accept decisions'):
                    self.load(repin=True)

    def test_duplicate_accept_binding_cannot_be_ambiguous(self):
        self.decisions['labs']['https://extra.ucsd.edu/'] = copy.deepcopy(
            self.decisions['labs']['https://alpha.ucsd.edu/'])
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Duplicate/missing accepted'):
            self.load(repin=True)

    def test_accept_reason_and_explicit_overrides_are_required(self):
        for field, value in [('reason', ''), ('name', 'Different lab')]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.decisions)
                self.decisions['labs']['https://alpha.ucsd.edu/'][field] = value
                self.save()
                with self.assertRaises(handoff.HandoffImportError):
                    self.load(repin=True)
                self.decisions = original

    def test_pi_cannot_be_inferred_or_initials_scope_expanded(self):
        self.labs[0]['principalInvestigator'] = 'Invented PI'
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'PI inferred'):
            self.load(repin=True)
        self.labs[0]['principalInvestigator'] = 'Not found'
        self.labs[1]['principalInvestigatorIdentityScope'] = 'full_person_confirmed'
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'PI identity scope'):
            self.load(repin=True)

    def test_unresolved_department_caveat_is_preserved(self):
        reason = 'No department stated.'
        self.decisions['labs']['https://alpha.ucsd.edu/']['departmentUnresolvedReason'] = reason
        self.labs[0].update(unverifiedFields=['department'],
                            departmentAssessment={'status': 'unresolved', 'reason': reason})
        self.save()
        self.assertEqual(self.load(repin=True)[0][0]['department'], 'Unknown')
        self.labs[0]['department'] = 'Inferred department'
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Unresolved department'):
            self.load(repin=True)

    def test_lab_schema_and_existing_professor_references_are_checked(self):
        self.labs[0]['contactEmail'] = 'not-an-email'
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'schema/references'):
            self.load(repin=True)
        self.labs[0]['contactEmail'] = 'Not found'
        self.labs[0]['professorIds'] = ['unreviewed-professor']
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'schema/references'):
            self.load(repin=True)

    def test_baseline_bytes_and_caller_baseline_must_both_match(self):
        self.bp.write_bytes(self.bp.read_bytes() + b'\n')
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Baseline atlas SHA256'):
            self.load()
        self.save()
        wrong = copy.deepcopy(self.baseline)
        wrong['labs'][0]['id'] = 'changed-in-memory'
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Caller baseline'):
            self.load(baseline=wrong)

    def test_id_and_canonical_url_collisions_never_merge_existing_records(self):
        self.baseline['labs'][0]['id'] = 'alpha'
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'ID collides'):
            self.load(repin=True)
        self.baseline['labs'][0].update(id='baseline', labWebsiteUrl='http://www.alpha.ucsd.edu/index.html')
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'URL collision'):
            self.load(repin=True)

    def test_capture_hash_is_for_saved_raw_bytes(self):
        self.cache.write_bytes(self.body.replace(b'\r\n', b'\n'))
        with self.assertRaisesRegex(handoff.HandoffImportError, 'raw-byte hash'):
            self.load()

    def test_cache_path_and_symlink_cannot_escape_responses(self):
        outside = self.root / self.cache.name
        outside.write_bytes(self.body)
        self.data['sourceManifest'][0]['cachePath'] = str(outside)
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'escapes responses'):
            self.load(repin=True)
        self.data['sourceManifest'][0]['cachePath'] = str(self.cache)
        self.cache.unlink()
        self.cache.symlink_to(outside)
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'escapes responses'):
            self.load(repin=True)

    def test_cache_filename_binds_requested_url(self):
        other = self.responses / 'wrong.html'
        other.write_bytes(self.body)
        self.data['sourceManifest'][0]['cachePath'] = str(other)
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'filename'):
            self.load(repin=True)

    def test_original_queue_capture_date_hash_and_success_are_required(self):
        original = copy.deepcopy(self.queue)
        for field, value in [('observedAt', '2026-10-02T01:00:00+00:00'),
                             ('sha256', '0' * 64), ('status', 'robots_denied')]:
            with self.subTest(field=field):
                self.queue = copy.deepcopy(original)
                self.queue['items'][self.url]['fetch'][field] = value
                self.write(self.qp, self.queue)
                with self.assertRaisesRegex(handoff.HandoffImportError, 'actual queue capture'):
                    self.load()

    def test_naive_or_later_source_dates_are_not_generation_dates(self):
        for value in ['2026-10-01', '2026-10-17T01:00:00+00:00']:
            with self.subTest(value=value):
                self.data['sourceManifest'][0]['observedAt'] = value
                self.save()
                with self.assertRaises(handoff.HandoffImportError):
                    self.load(repin=True)

    def test_exact_field_quotes_and_manifest_source_time_are_required(self):
        self.labs[0]['fieldEvidence']['labWebsiteUrl'][0]['evidence'] = 'Absent research claim'
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Field quote not present'):
            self.load(repin=True)
        self.labs[0]['fieldEvidence']['labWebsiteUrl'][0] = self.proof('Alpha Lab')
        self.labs[0]['fieldEvidence']['labWebsiteUrl'][0]['observedAt'] = self.data['generatedAt']
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'no source manifest URL/time'):
            self.load(repin=True)

    def test_duplicate_source_manifest_entries_are_rejected(self):
        self.data['sourceManifest'].append(copy.deepcopy(self.data['sourceManifest'][0]))
        self.save()
        with self.assertRaisesRegex(handoff.HandoffImportError, 'Duplicate source URL/time'):
            self.load(repin=True)

    def test_legacy_identity_quote_is_allowed_without_research_approval(self):
        body = b'<body><main><h1>Header</h1></main><div id="navmenu">Alpha Lab Beta Group at UC San Diego. PI: G. Scientist</div></body>'
        self.cache.write_bytes(body)
        self.data['sourceManifest'][0]['bodySha256'] = digest(body)
        self.queue['items'][self.url]['fetch']['sha256'] = digest(body)
        self.assertNotIn('Alpha Lab', handoff.ContentDOM(body.decode()).main().text())
        self.assertIn('Alpha Lab', handoff.LegacyDOM(body.decode()).main().text())
        self.save()
        labs, receipt = self.load(repin=True)
        self.assertTrue(labs)
        self.assertTrue(all('status' not in lab for lab in labs))
        self.assertIn('no aliases', receipt['scope'])


if __name__ == '__main__':
    unittest.main()
