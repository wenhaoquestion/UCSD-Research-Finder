import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_ucsd_coverage import prefer_literal_directory_rows


class LiteralDirectoryPreferenceTests(unittest.TestCase):
    def test_saved_literal_http_link_wins_and_transformed_observation_survives_whole(self):
        source = 'https://dept.ucsd.edu/faculty'
        old = {'sourceUrl': source, 'name': 'Jane Example', 'department': 'Physics', 'listedRole': 'Professor',
               'profileUrl': 'https://www.example.ucsd.edu/jane', 'namedLinkUrl': 'https://www.example.ucsd.edu/jane', 'observedAt': '2020-01-01'}
        literal = {**old, 'profileUrl': 'http://www.example.ucsd.edu/jane', 'namedLinkUrl': 'http://www.example.ucsd.edu/jane'}
        raw = b'<main><a href="http://www.example.ucsd.edu/jane">Jane Example</a></main>'
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            (cache / 'responses').mkdir()
            path = cache / 'responses' / (hashlib.sha256(source.encode()).hexdigest() + '.html')
            path.write_bytes(raw)
            item = {'url': source, 'fetch': {'status': 'ok', 'sourceUrl': source, 'finalUrl': source, 'observedAt': old['observedAt']}}
            queue = {'items': {source: item}}
            original = copy.deepcopy([old, literal])
            selected, history = prefer_literal_directory_rows([old, literal], queue, cache)
            self.assertEqual(selected, [literal])
            self.assertEqual(history[0]['previousSourceListingObservations'], [old])
            self.assertEqual(history[0]['bodySha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(history[0]['observedAt'], old['observedAt'])
            self.assertEqual([old, literal], original)
            self.assertEqual(path.read_bytes(), raw)
            # A newer response cannot be backdated as proof for the old row.
            item['fetch']['observedAt'] = '2026-01-01'
            selected, history = prefer_literal_directory_rows([old, literal], queue, cache)
            self.assertEqual(selected, [old])
            self.assertEqual(history[0]['selectionMethod'], 'original_order_no_matching_dated_href_proof')

    def test_unrelated_titles_and_departments_are_not_collapsed(self):
        rows = [{'sourceUrl': 'https://ucsd.edu/faculty', 'name': 'Jane Example', 'department': dept, 'listedRole': role}
                for dept, role in [('Physics', 'Professor'), ('Physics', 'Professor Emerita'), ('Mathematics', 'Professor')]]
        selected, history = prefer_literal_directory_rows(rows, {'items': {}}, Path('/unused'))
        self.assertEqual(selected, rows)
        self.assertEqual(history, [])
