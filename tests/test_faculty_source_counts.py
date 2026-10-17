import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from review_ucsd_coverage import source_listing_counts


class FacultySourceCountsTests(unittest.TestCase):
    def test_distinct_people_are_counted_under_each_exact_request_resource(self):
        rows = [
            {'name': 'Dana Chen', 'sourceUrl': 'https://example.ucsd.edu', 'department': 'Physics'},
            {'name': 'Dana  Chen', 'sourceUrl': 'https://EXAMPLE.ucsd.edu/#contact', 'department': 'Chemistry'},
            {'name': 'Rui Park', 'sourceUrl': 'https://example.ucsd.edu/'},
            {'name': 'Dana Chen', 'sourceUrl': 'http://example.ucsd.edu/'},
            {'name': 'Dana Chen', 'sourceUrl': 'https://example.ucsd.edu/index.html'},
            {'name': 'Dana Chen', 'sourceUrl': 'https://example.ucsd.edu/?page=1'},
            {'name': 'Dana Chen', 'sourceUrl': 'https://example.ucsd.edu/?page=2'},
        ]
        before = copy.deepcopy(rows)
        self.assertEqual(source_listing_counts(rows), {
            'https://example.ucsd.edu/': 2,
            'http://example.ucsd.edu/': 1,
            'https://example.ucsd.edu/index.html': 1,
            'https://example.ucsd.edu/?page=1': 1,
            'https://example.ucsd.edu/?page=2': 1,
        })
        self.assertEqual(rows, before)

    def test_empty_or_invalid_source_observations_are_retained_without_cross_run_state(self):
        self.assertEqual(source_listing_counts([]), {})
        rows = [{'name': 'Dana Chen', 'sourceUrl': ''},
                {'name': 'Dana Chen', 'sourceUrl': 'not-a-url'}]
        self.assertEqual(source_listing_counts(rows), {'': 1})
        rows.append({'name': 'Rui Park', 'sourceUrl': ''})
        self.assertEqual(source_listing_counts(rows), {'': 2})
        self.assertEqual(source_listing_counts([]), {})


if __name__ == '__main__':
    unittest.main()
