"""Existing capture reuse must not create new observations or change bytes."""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import local_lab_cache_candidates as candidates


class CachedSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'data/local-lab-summaries')
        self.addCleanup(self.temp.cleanup)
        self.cache=Path(self.temp.name);(self.cache/'responses').mkdir()
        self.url='https://example.ucsd.edu/research'
        self.body=b'<html><head><title>Example Lab</title><meta property="article:modified_time" content="2025-01-01" /></head><body><main>Example Lab studies memory.</main></body></html>'
        self.digest=hashlib.sha256(self.body).hexdigest()
        self.path=self.cache/'responses'/(hashlib.sha256(self.url.encode()).hexdigest()+'.html')
        self.path.write_bytes(self.body)
        self.meta={'status':'ok','sourceUrl':self.url,'finalUrl':self.url,'httpStatus':200,
            'observedAt':'2026-10-01T01:00:00+00:00','sha256':self.digest}
        self.queue={'items':{'one':{'url':self.url,'fetch':self.meta}}}
        self.candidate={'requestedUrl':self.url,'sourceUrl':self.url,'observedAt':self.meta['observedAt'],
            'bodySha256':self.digest,'cachePath':str(self.path)}

    def test_reuse_keeps_capture_date_content_date_and_bytes_separate(self):
        with patch.object(candidates,'CACHE',self.cache):
            source=candidates.source_from_capture(self.candidate,self.queue)
        self.assertEqual(source['observedAt'],'2026-10-01T01:00:00+00:00')
        self.assertEqual(source['sourceContentDates'][0]['value'],'2025-01-01')
        self.assertEqual(source['captureOrigin'],'collection_cache_reuse')
        self.assertEqual(source['bodySha256'],self.digest)
        self.assertEqual(self.path.read_bytes(),self.body)
        self.assertNotIn('identityReview',source)  # Extraction never authorizes admission.

    def test_changed_capture_metadata_cannot_borrow_an_old_date(self):
        self.meta['observedAt']='2026-10-02T01:00:00+00:00'
        with patch.object(candidates,'CACHE',self.cache):
            with self.assertRaisesRegex(ValueError,'original queue capture'):
                candidates.source_from_capture(self.candidate,self.queue)

    def test_actual_requested_url_is_separate_from_original_queue_url(self):
        self.meta['sourceUrl']='http://example.ucsd.edu/research'
        with patch.object(candidates,'CACHE',self.cache):
            source=candidates.source_from_capture(self.candidate,self.queue)
        self.assertEqual(source['queueUrl'],self.url)
        self.assertEqual(source['requestedUrl'],'http://example.ucsd.edu/research')
        self.assertEqual(source['checkedUrl'],self.meta['sourceUrl'])
        self.assertEqual(source['redirectChain'],[])

    def test_matching_preserved_attempt_can_support_its_original_observation(self):
        old=copy.deepcopy(self.meta);self.meta['observedAt']='2026-10-02T01:00:00+00:00'
        self.queue['items']['one']['attemptHistory']=[old]
        with patch.object(candidates,'CACHE',self.cache):
            source=candidates.source_from_capture(self.candidate,self.queue)
        self.assertEqual(source['observedAt'],old['observedAt'])

    def test_changed_body_or_path_is_rejected_before_extraction(self):
        with patch.object(candidates,'CACHE',self.cache):
            wrong=dict(self.candidate,cachePath=str(self.cache/'another.html'))
            with self.assertRaisesRegex(ValueError,'cache path'):
                candidates.source_from_capture(wrong,self.queue)
            self.path.write_bytes(self.body+b'changed')
            with self.assertRaisesRegex(ValueError,'body changed'):
                candidates.source_from_capture(self.candidate,self.queue)


if __name__=='__main__':unittest.main()
