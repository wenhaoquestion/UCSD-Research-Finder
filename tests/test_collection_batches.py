import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collection_lock import task_lease
from run_ucsd_coverage_batches import run_batches


class CollectionBatchTests(unittest.TestCase):
    def fixture(self, directory):
        cache = Path(directory)
        (cache / 'queue.json').write_text(json.dumps({'items': {str(i): {'state': 'pending'} for i in range(3)}}))
        script = cache / 'fixture_collector.py'
        script.write_text('''import argparse,json,pathlib
p=argparse.ArgumentParser();p.add_argument('--cache');p.add_argument('--workers');p.add_argument('--max-pages',type=int);a=p.parse_args();c=pathlib.Path(a.cache)
q=json.loads((c/'queue.json').read_text());n=0
for item in q['items'].values():
 if item['state']=='pending' and n<a.max_pages:item['state']='done';n+=1
(c/'queue.json').write_text(json.dumps(q))
''')
        return cache, script

    def test_finite_children_resume_one_queue_until_drained(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, script = self.fixture(tmp)
            self.assertEqual(run_batches(cache, batch_pages=2, collector=script), 0)
            receipt = json.loads((cache / 'batch-runner.json').read_text())
            self.assertEqual(receipt['completedBatches'], 2)
            self.assertEqual(receipt['status'], 'eligible_queue_drained')
            self.assertTrue(all(i['state'] == 'done' for i in json.loads((cache / 'queue.json').read_text())['items'].values()))

    def test_stop_is_preserved_and_never_reported_as_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, script = self.fixture(tmp)
            (cache / 'STOP').touch()
            self.assertEqual(run_batches(cache, collector=script), 0)
            receipt = json.loads((cache / 'batch-runner.json').read_text())
            self.assertEqual(receipt['status'], 'stopped_by_sentinel')
            self.assertEqual(receipt['completedBatches'], 0)
            self.assertTrue((cache / 'STOP').exists())

    def test_failed_child_is_not_retried_or_reported_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache, script = self.fixture(tmp)
            script.write_text('import sys;sys.exit(7)')
            self.assertEqual(run_batches(cache, collector=script), 7)
            receipt = json.loads((cache / 'batch-runner.json').read_text())
            self.assertEqual(receipt['status'], 'collector_failed')
            self.assertEqual(receipt['completedBatches'], 0)

    def test_separate_process_cannot_take_live_queue_writer_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'collector.lock'
            program = 'from pathlib import Path;from collection_lock import task_lease\nwith task_lease(Path(' + repr(str(path)) + ')):pass'
            scripts = str(Path(__file__).resolve().parents[1] / 'scripts')
            with task_lease(path):
                result = subprocess.run([sys.executable, '-c', program], cwd=scripts, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'Another active process', result.stderr)
            self.assertEqual(subprocess.run([sys.executable, '-c', program], cwd=scripts, capture_output=True).returncode, 0)
