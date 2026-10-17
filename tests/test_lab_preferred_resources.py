import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_ucsd_preservation import audit
from lab_entities import LabIndex
from lab_preferred_resources import verified_preferred_resources, apply_preferred_resources
from lab_resource_reviews import record_sha256, verified_alias_reviews
from rebuild_verified_atlas import build
from test_atlas_quality import atlas
import test_lab_own_metadata as metadata_fixture


class PreferredLabResourceTests(unittest.TestCase):
    def fixture(self, path):
        data, queue, source, aliases, alias = metadata_fixture.OwnLabMetadataTests().fixture(path)
        data, *_ = build(data, {}, {}, {}, {})
        people, *_ = build(atlas(), {}, {}, {}, {})
        data['professors'] = people['professors']
        lab, person = data['labs'][0], data['professors'][0]
        old, new = lab['labWebsiteUrl'], alias['url']
        lab['websiteCheck'] = {'sourceUrl': old, 'status': 'unavailable', 'observedAt': '2026-10-01T00:00:00+00:00'}
        proof = {'sourceUrl': person['officialProfileUrl'], 'observedAt': '2026-10-01T00:00:00+00:00',
                 'method': 'official_profile_explicit_lab_link', 'evidence': 'Example Lab → ' + old}
        person.update(labAffiliation=lab['labName'], labAffiliationUrl=old, labAffiliations=[
            {'labId': lab['id'], 'labName': lab['labName'], 'url': old,
             'relationship': 'faculty_lab_link', 'fieldEvidence': proof}])
        person['fieldEvidence'].update(labAffiliation=[proof], labAffiliationUrl=[proof])
        row = {'labId': lab['id'], 'action': 'select_preferred_lab_resource',
               'previousPreferredUrl': old, 'preferredUrl': new, 'originalLabRecord': copy.deepcopy(lab),
               'originalLabRecordSha256': record_sha256(lab), 'reason': 'Select the captured named own resource; preserve the old listing.',
               'evidence': copy.deepcopy(aliases[0]['evidence']), 'identityEvidence': copy.deepcopy(source['identityEvidence'])}
        return data, queue, row, aliases, alias

    def verified(self, path, data, queue, row, aliases):
        return verified_preferred_resources({'entries': [row]}, aliases, queue, path, data['labs'])

    def test_selection_preserves_identity_old_records_and_relationships_and_replays(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp); data, queue, row, aliases, alias = self.fixture(path); before = copy.deepcopy(data)
            rows = self.verified(path, data, queue, row, aliases)
            coverage = {'labAliases': [alias], 'labAliasResourceReviews': aliases, 'labPreferredResourceReviews': rows}
            first, *_ = build(copy.deepcopy(data), {}, {}, {}, {}, coverage_evidence=coverage)
            lab, person = first['labs'][0], first['professors'][0]
            for field in ['id', 'labName', 'department', 'lastVerified', 'principalInvestigator', 'recruitingStatus']:
                self.assertEqual(lab.get(field), before['labs'][0].get(field))
            self.assertEqual(lab['labWebsiteUrl'], row['preferredUrl'])
            self.assertEqual(lab['websiteCheck']['status'], 'reachable')
            self.assertEqual(lab['preferredResourceReviews'][0]['originalLabRecord'], before['labs'][0])
            self.assertTrue(any(o['field'] == 'websiteCheck' and o['value'] == before['labs'][0]['websiteCheck'] for o in lab['previousFieldObservations']))
            self.assertEqual(person['labAffiliationUrl'], row['preferredUrl'])
            self.assertEqual(person['labAffiliations'][0]['labId'], lab['id'])
            self.assertEqual(person['labAffiliations'][0]['fieldEvidence'], before['professors'][0]['labAffiliations'][0]['fieldEvidence'])
            self.assertEqual(person['labAffiliations'][0]['relationship'], 'faculty_lab_link')
            self.assertTrue(any(o['field'] == 'labAffiliations' and o['value'] == before['professors'][0]['labAffiliations'] for o in person['previousFieldObservations']))
            self.assertIsNone(LabIndex(first['labs']).resolve(row['previousPreferredUrl']))
            self.assertEqual(audit(before, first)['status'], 'passed')
            second, *_ = build(copy.deepcopy(first), {}, {}, {}, {}, coverage_evidence=coverage)
            self.assertEqual(first, second)
            self.assertEqual(data, before)

    def test_exact_capture_owned_alias_and_named_document_are_required(self):
        for mode in ['unverified_alias', 'different_scheme', 'shared_owner', 'shared_lab', 'title', 'date', 'body', 'hash', 'old_uri', 'alias_id', 'unvisited_final']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp); data, queue, row, aliases, _ = self.fixture(path)
                if mode == 'unverified_alias': aliases[0]['captureVerified'] = False
                if mode == 'different_scheme': row['preferredUrl'] = row['preferredUrl'].replace('https:', 'http:')
                if mode == 'shared_owner': aliases.append({**copy.deepcopy(aliases[0]), 'labId': 'different-lab'})
                if mode == 'shared_lab': data['labs'][0]['websiteSharing'] = {'kind': 'distinct_named_labs'}
                if mode == 'title': row['identityEvidence'][0]['evidence'] = 'Unrelated Lab'
                if mode == 'date': row['evidence'][0]['observedAt'] = '2000-01-01'
                if mode == 'body': next((path / 'responses').glob('*.html')).write_text('Changed body')
                if mode == 'hash': row['evidence'][0]['bodySha256'] = '0' * 64
                if mode == 'old_uri': row['previousPreferredUrl'] = 'https://other.ucsd.edu/'
                if mode == 'alias_id': data['labs'][0]['aliasIds'] = ['retired']; row['labId'] = 'retired'
                if mode == 'unvisited_final': queue['items'][row['preferredUrl']]['fetch']['finalUrl'] += 'elsewhere/'
                with self.assertRaises(ValueError): self.verified(path, data, queue, row, aliases)

    def test_no_relationship_is_created_from_a_url_or_name_and_scalar_requires_its_existing_link(self):
        for mode in ['missing_id', 'different_id', 'different_scalar_name', 'different_affiliation_url']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp); data, queue, row, aliases, alias = self.fixture(path)
                rows = self.verified(path, data, queue, row, aliases); person = data['professors'][0]
                if mode == 'missing_id': person['labAffiliations'][0].pop('labId')
                if mode == 'different_id': person['labAffiliations'][0]['labId'] = 'other'
                if mode == 'different_scalar_name': person['labAffiliation'] = 'Other Lab'
                if mode == 'different_affiliation_url': person['labAffiliations'][0]['url'] += 'people/'
                before = copy.deepcopy(person)
                data['labs'][0]['alternateWebsiteUrls'] = [alias['url']]
                apply_preferred_resources(data, rows)
                self.assertEqual(person['labAffiliationUrl'], before['labAffiliationUrl'])
                if mode != 'different_scalar_name': self.assertEqual(person, before)

    def test_newer_failures_remain_checks_and_old_checks_cannot_replace_the_positive_capture(self):
        for stamp, status in [('2026-10-01T00:00:00+00:00', 'reachable'), ('2026-10-17T00:00:00+00:00', 'unavailable')]:
            with self.subTest(stamp=stamp), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp); data, queue, row, aliases, alias = self.fixture(path)
                rows = self.verified(path, data, queue, row, aliases)
                coverage = {'labAliases': [alias], 'labAliasResourceReviews': aliases, 'labPreferredResourceReviews': rows}
                checks = {'checks': [{'sourceUrl': row['preferredUrl'], 'observedAt': stamp, 'status': 'unavailable'}]}
                first, *_ = build(data, {}, {}, {}, checks, coverage_evidence=coverage)
                self.assertEqual(first['labs'][0]['websiteCheck']['status'], status)
                self.assertNotIn('websiteCheck', first['labs'][0]['fieldEvidence'])
                second, *_ = build(copy.deepcopy(first), {}, {}, {}, checks, coverage_evidence=coverage)
                self.assertEqual(first, second)

    def test_all_selection_targets_are_checked_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp); data, queue, row, aliases, alias = self.fixture(path)
            rows = self.verified(path, data, queue, row, aliases)
            data['labs'][0]['alternateWebsiteUrls'] = [alias['url']]
            rows.append({**copy.deepcopy(rows[0]), 'labId': 'missing'})
            before = copy.deepcopy(data)
            with self.assertRaises(ValueError): apply_preferred_resources(data, rows)
            self.assertEqual(data, before)

    def test_retired_lab_id_inputs_keep_both_literal_and_previous_canonical_associations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp); data, queue, row, aliases, alias = self.fixture(path)
            lab = data['labs'][0]; lab['aliasIds'] = ['retired-lab-id']
            person = data['professors'][0]
            person['labAffiliations'].append({**copy.deepcopy(person['labAffiliations'][0]), 'labId':'retired-lab-id'})
            literal = copy.deepcopy(person['labAffiliations'])
            canonical = [dict(a, labId=lab['id']) for a in literal]
            rows = self.verified(path, data, queue, row, aliases)
            coverage = {'labAliases':[alias], 'labAliasResourceReviews':aliases, 'labPreferredResourceReviews':rows}
            first, *_ = build(copy.deepcopy(data), {}, {}, {}, {}, coverage_evidence=coverage)
            updated = first['professors'][0]
            observations = [o['value'] for o in updated['previousFieldObservations'] if o['field']=='labAffiliations']
            self.assertIn(literal, observations)
            self.assertIn(canonical, observations)
            self.assertEqual(len(updated['labAffiliations']), 1)
            second, *_ = build(copy.deepcopy(first), {}, {}, {}, {}, coverage_evidence=coverage)
            self.assertEqual(first, second)

    def test_a_generic_label_can_follow_a_separately_proven_owned_name_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,queue,row,aliases,alias=self.fixture(path)
            lab=data['labs'][0];lab['labName']='Jane Example — lab website'
            person=data['professors'][0];person['labAffiliation']=lab['labName'];person['labAffiliations'][0]['labName']=lab['labName']
            row['originalLabRecord']=copy.deepcopy(lab);row['originalLabRecordSha256']=record_sha256(lab)
            row['preferredLabName']='Example Lab'
            update={'labId':lab['id'],'fields':{'labName':'Example Lab'},'fieldEvidence':{'labName':row['identityEvidence']}}
            with self.assertRaisesRegex(ValueError,'explicit reviewed name update'):
                self.verified(path,data,queue,row,aliases)
            bad=copy.deepcopy(update);bad['fieldEvidence']['labName'][0]['evidenceType']='main_text_quote'
            with self.assertRaises(ValueError):
                verified_preferred_resources({'entries':[row]},aliases,queue,path,data['labs'],[bad])
            rows=verified_preferred_resources({'entries':[row]},aliases,queue,path,data['labs'],[update])
            coverage={'labAliases':[alias],'labAliasResourceReviews':aliases,'labUpdates':[update],'labPreferredResourceReviews':rows}
            first,*_=build(copy.deepcopy(data),{},{},{},{},coverage_evidence=coverage)
            self.assertEqual(first['labs'][0]['labName'],'Example Lab')
            self.assertEqual(first['labs'][0]['labWebsiteUrl'],row['preferredUrl'])
            self.assertEqual(first['labs'][0]['preferredResourceReviews'][0]['originalLabRecord']['labName'],lab['labName'])
            self.assertEqual(audit(data,first)['status'],'passed')
            second,*_=build(copy.deepcopy(first),{},{},{},{},coverage_evidence=coverage)
            self.assertEqual(first,second)

    def test_an_actual_redirect_selects_its_visited_final_resource_and_keeps_the_real_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);data,queue,row,aliases,alias=self.fixture(path)
            new=row['preferredUrl'];requested='http://publisher.ucsd.edu/example-lab/'
            original=path/'responses'/(hashlib.sha256(new.encode()).hexdigest()+'.html')
            target=path/'responses'/(hashlib.sha256(requested.encode()).hexdigest()+'.html')
            target.write_text(original.read_text().replace('<title>Example Lab</title>','<title>Personal names at UCSD</title>'))
            item=queue['items'].pop(new);item['url']=requested;meta=item['fetch'];meta['sourceUrl']=requested
            meta['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
            meta['redirects']=[{'from':requested,'to':new,'httpStatus':302}];queue['items'][requested]=item
            def revise(value):
                if isinstance(value,list):
                    for x in value:revise(x)
                elif isinstance(value,dict):
                    if value.get('requestedUrl')==new:
                        value.update(requestedUrl=requested,bodySha256=meta['sha256'])
                        if value.get('evidence')=='Example Lab':value.update(evidenceType='document_heading',headingTag='h1')
                    for x in value.values():revise(x)
            revise(row);revise(alias);revise(aliases)
            aliases[0].update(originalAliasRecord=copy.deepcopy(alias),originalAliasRecordSha256=record_sha256(alias))
            aliases=verified_alias_reviews({'entries':aliases},[alias],queue,path)
            rows=self.verified(path,data,queue,row,aliases)
            coverage={'labAliases':[alias],'labAliasResourceReviews':aliases,'labPreferredResourceReviews':rows}
            older={'checks':[{'sourceUrl':new,'observedAt':'2026-10-01T00:00:00+00:00','status':'unavailable'}]}
            first,*_=build(copy.deepcopy(data),{},{},{},older,coverage_evidence=coverage)
            check=first['labs'][0]['websiteCheck']
            self.assertEqual(check['sourceUrl'],requested)
            self.assertEqual(check['finalUrl'],new)
            self.assertEqual(check['status'],'reachable')
            self.assertEqual(check['title'],'Personal names at UCSD')
            second,*_=build(copy.deepcopy(first),{},{},{},older,coverage_evidence=coverage)
            self.assertEqual(first,second)
            meta['redirects'][0]['from']='http://unrelated.ucsd.edu/'
            with self.assertRaisesRegex(ValueError,'continuous redirect chain'):
                self.verified(path,data,queue,row,aliases)
