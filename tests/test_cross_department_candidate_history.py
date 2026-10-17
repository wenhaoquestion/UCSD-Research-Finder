import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect_ucsd_coverage import profiles_appointment, faculty_table_rows
from faculty_profile_bindings import profile_metadata, captured_source
from faculty_candidate_history import candidate_history
from lab_resource_reviews import record_sha256
from review_ucsd_coverage import faculty_review
from rebuild_verified_atlas import build
from audit_ucsd_preservation import audit
from test_atlas_quality import professor, atlas


class CrossDepartmentCandidateHistoryTests(unittest.TestCase):
    def fixture(self,cache,table=False):
        (cache/'responses').mkdir()
        uri='https://radiology.ucsd.edu/about/faculty.html' if table else 'https://profiles.ucsd.edu/jane.example'
        body=('<main><h1>Faculty</h1><table><tr><td><a href="https://providers.ucsd.edu/details/123/radiology">Example, Jane, MD</a></td><td>Assistant Clinical Professor</td></tr></table></main>' if table else
              '<html><head><title>Jane Example | UCSD Profiles</title><link rel="canonical" href="https://profiles.ucsd.edu/jane.example"><link rel="alternate" type="application/rdf+xml" href="https://researcherprofiles.org/profile/123/123.rdf"></head><body><main><div class="pageTitle"><h2>Jane Example</h2></div><table><tr><th>Title(s)</th><td>Professor, Medicine</td></tr><tr><th>School</th><td>Vc-health Sciences-schools</td></tr></table></main></body></html>')
        path=cache/'responses'/(hashlib.sha256(uri.encode()).hexdigest()+'.html');path.write_text(body)
        meta={'sourceUrl':uri,'finalUrl':uri,'status':'ok','observedAt':'2020-01-01','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        row=faculty_table_rows('Radiology',meta,body)[0] if table else profiles_appointment(meta,body)[1]
        q={'items':{uri:{'url':uri,'state':'done','fetch':meta}},'facultyListings':[row]}
        original=professor('original','J. Example','Bioengineering');base=atlas();base.update(qualityMigrationVersion=1,professors=[original])
        faculty=faculty_review(copy.deepcopy(q),base,cache,profile_identity_review={'entries':[]})
        hold=next(h for h in faculty['uncertainListings'] if h['reason']=='cross_department_legacy_initials_requires_identity_review')
        prior=copy.deepcopy(hold['provisionalRecordSnapshot'])
        proof=captured_source(q['items'][uri],cache)[0] if table else profile_metadata(q['items'][uri],cache)[0]
        entry={'record':prior,'recordSha256':record_sha256(prior),'captures':[proof],'candidateProfessorIds':['original'],
               'qualificationType':'named_faculty_table_row' if table else 'profiles_explicit_appointment',
               'disposition':'pending_cross_department_initial_alias_review','reason':'Preserve this qualified candidate while its cross-department initial-only original requires review.'}
        history={'sourceCandidateAtlasSha256':'a'*64,'entries':[entry]}
        return base,q,faculty,history,path

    def test_profiles_and_named_table_whole_candidates_are_archived_without_publishing_or_merging(self):
        for table in [False,True]:
            with self.subTest(table=table),tempfile.TemporaryDirectory() as tmp:
                cache=Path(tmp);base,q,faculty,history,_=self.fixture(cache,table)
                patches,archives=candidate_history(history,base['professors'],faculty,q,cache)
                self.assertEqual(patches,{})
                self.assertEqual(archives[0]['record'],history['entries'][0]['record'])
                coverage={'heldFacultyCandidates':archives}
                first,_,_,quarantine=build(copy.deepcopy(base),{},{},{},{},{},{},{},coverage)
                self.assertEqual([p['id'] for p in first['professors']],['original'])
                self.assertEqual(first['professors'][0]['name'],'J. Example')
                self.assertFalse(first['professors'][0].get('aliasIds'))
                previous=copy.deepcopy(base);previous['professors'].append(history['entries'][0]['record'])
                self.assertEqual(audit(previous,first,[quarantine])['status'],'passed')
                repeated,*_=build(copy.deepcopy(first),{},{},{},{},{},{},{},coverage)
                self.assertEqual(first,repeated)

    def test_changed_capture_snapshot_candidate_or_republished_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);base,q,faculty,history,path=self.fixture(cache)
            for mode in ['record_hash','capture_date','wrong_original','same_department','republication','missing_hold','wrong_identifier']:
                h=copy.deepcopy(history);state=copy.deepcopy(q);f=copy.deepcopy(faculty);people=copy.deepcopy(base['professors'])
                if mode=='record_hash':h['entries'][0]['recordSha256']='changed'
                elif mode=='capture_date':h['entries'][0]['captures'][0]['observedAt']='2019-01-01'
                elif mode=='wrong_original':h['entries'][0]['candidateProfessorIds']=['unrelated']
                elif mode=='same_department':people[0]['department']='Medicine'
                elif mode=='republication':f['professors'].append(h['entries'][0]['record'])
                elif mode=='missing_hold':f['uncertainListings']=[]
                else:h['entries'][0]['captures'][0]['rdfAlternateUri']='https://researcherprofiles.org/profile/456/456.rdf'
                with self.subTest(mode=mode),self.assertRaises(ValueError):candidate_history(h,people,f,state,cache)
            path.write_bytes(path.read_bytes()+b' changed')
            with self.assertRaises(ValueError):candidate_history(history,base['professors'],faculty,q,cache)

    def test_a_staff_table_cannot_replace_the_qualified_source_and_unverified_archive_cannot_assemble(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp);base,q,faculty,history,path=self.fixture(cache,True)
            path.write_text(path.read_text().replace('Assistant Clinical Professor','Staff Coordinator'))
            uri=history['entries'][0]['captures'][0]['requestedUrl'];q['items'][uri]['fetch']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            history['entries'][0]['captures'][0]['bodySha256']=q['items'][uri]['fetch']['sha256']
            with self.assertRaises(ValueError):candidate_history(history,base['professors'],faculty,q,cache)
            with self.assertRaises(ValueError):build(copy.deepcopy(base),{},{},{},{},{},{},{},{'heldFacultyCandidates':history['entries']})


if __name__=='__main__':unittest.main()
