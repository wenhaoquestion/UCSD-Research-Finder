import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import apply_ucsd_coverage as apply
import preview_ucsd_reviewed_labs as preview
from lab_resource_reviews import record_sha256
from refresh_labs import make_lab


class PreviewCaptureCacheTests(unittest.TestCase):
    def fixture(self,tmp):
        root=Path(tmp);cache=root/'.cache/coverage-20261016';private=root/'private-evidence';evidence=root/'data/ucsd'
        for p in [cache/'baseline',cache/'responses',private/'responses',evidence,root/'data/quality']:p.mkdir(parents=True,exist_ok=True)
        write=lambda p,d:p.write_text(json.dumps(d))
        baseline={'schemaVersion':'3.0.0','generatedAt':'2026-10-01','collectionPolicy':{},'professors':[],'labs':[]}
        write(cache/'baseline/research-atlas.json',baseline);write(root/'data/research-atlas.json',baseline);write(root/'data/quality/quarantined-records.json',[])
        uri='https://frame-lab.ucsd.edu/';alias='https://frame-lab.ucsd.edu/home';body='<main><h1>Frame Lab</h1><p>University of California San Diego research group.</p></main>'
        meta={'sourceUrl':alias,'finalUrl':alias,'status':'ok','observedAt':'2026-10-16T01:00:00+00:00','sha256':hashlib.sha256(body.encode()).hexdigest()}
        name=hashlib.sha256(alias.encode()).hexdigest()+'.html'
        (private/'responses'/name).write_text(body);(cache/'responses'/name).write_text('<main>A different public source</main>')
        q={'schemaVersion':1,'items':{alias:{'url':alias,'fetch':meta,'state':'done'}},'updatedAt':'2026-10-16'};write(cache/'queue.json',q)
        lab=make_lab('Frame Lab',uri,'Unknown',meta,'Frame Lab')
        lab['fieldEvidence']={k:[v] for k,v in lab['fieldEvidence'].items()}
        proof={'requestedUrl':alias,'sourceUrl':alias,'observedAt':meta['observedAt'],'bodySha256':meta['sha256'],'evidenceType':'main_text_quote','evidence':'Frame Lab'}
        row={'labId':lab['id'],'url':alias,'fieldEvidence':[proof],'reason':'Captured named own lab home'}
        write(evidence/'coverage-20261016-reviewed-lab-handoff.json',{'labs':[lab],'labAliases':[row],'labUpdates':[]})
        write(evidence/'coverage-20261016-existing-lab-merges.json',{'entries':[],'reviewedAt':'2026-10-16'})
        write(evidence/'lab-alias-resource-review-20261016.json',{'entries':[{'labId':lab['id'],'url':alias,'originalAliasRecord':row,'originalAliasRecordSha256':record_sha256(row),'reason':'Actual private capture','evidence':[proof]}]})
        for n in ['lab-resource-identity-review-20261016.json','person-identity-review-20261016.json','lab-field-review-20261016.json','lab-resource-association-review-20261016.json','shared-lab-resource-review-20261016.json']:write(evidence/n,{'entries':[]})
        for n in ['lab-evidence.json','teaching-evidence.json','ratings-evidence.json','source-checks.json','faculty-evidence.json','lab-identity-review.json','lab-expansion-review.json']:write(evidence/n,{'labs':[]})
        return root,cache,private,alias

    def run_preview(self,root,private):
        argv=['preview_ucsd_reviewed_labs.py','--capture-cache',str(private),'--output-directory',str(root/'preview'),'--receipt',str(root/'receipt.json')]
        with patch.object(preview,'ROOT',root),patch.object(apply,'ROOT',root),patch.object(sys,'argv',argv):preview.main()

    def test_private_evidence_cache_verifies_alias_without_writing_live_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,cache,private,alias=self.fixture(tmp)
            protected=[cache/'queue.json',root/'data/research-atlas.json',cache/'responses'/(hashlib.sha256(alias.encode()).hexdigest()+'.html')]
            old={p:p.read_bytes() for p in protected}
            with self.assertRaises(SystemExit) as result:self.run_preview(root,private)
            self.assertEqual(result.exception.code,0)
            receipt=json.loads((root/'receipt.json').read_text())
            self.assertEqual(receipt['sourceCaptureCachePath'],str(private.resolve()))
            self.assertTrue(receipt['reviewedPreview']['repeatedAssemblyIdentical'])
            self.assertEqual(receipt['reviewedPreview']['labs'],1)
            self.assertEqual({p:p.read_bytes() for p in protected},old)

    def test_private_body_mismatch_is_rejected_even_if_global_cache_is_correct(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,cache,private,alias=self.fixture(tmp);name=hashlib.sha256(alias.encode()).hexdigest()+'.html'
            (cache/'responses'/name).write_bytes((private/'responses'/name).read_bytes())
            (private/'responses'/name).write_text('<main>Altered private evidence</main>')
            with self.assertRaisesRegex(ValueError,'actual capture'):self.run_preview(root,private)
            self.assertFalse((root/'receipt.json').exists())


if __name__=='__main__':unittest.main()
