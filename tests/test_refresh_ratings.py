import importlib.util
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('refresh_ratings', ROOT / 'scripts/refresh_ratings.py')
ratings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ratings)


def page(school_id=1079, school_name='University of California San Diego', count=12, score=4.2, percent=72):
    store = {'school': {'__typename': 'School', 'legacyId': school_id, 'name': school_name},
             'teacher': {'__typename': 'Teacher', 'legacyId': 123, 'firstName': 'Example', 'lastName': 'Professor',
                         'school': {'__ref': 'school'}, 'avgRating': score, 'numRatings': count,
                         'avgDifficulty': 3.4, 'wouldTakeAgainPercent': percent}}
    return '<script>window.__RELAY_STORE__ = ' + json.dumps(store) + '; window.other = true;</script>'


class PublicRatingTests(unittest.TestCase):
    def test_wrong_school_is_never_attached(self):
        self.assertEqual([], ratings.rmp_teachers(page(school_id=1, school_name='University of San Diego')))
        self.assertEqual([], ratings.rmp_teachers(page(school_id=1)))

    def test_no_reviews_is_missing_score_not_zero_rating(self):
        result = ratings.rmp_teachers(page(count=0, score=0, percent=-1))[0]
        self.assertIsNone(result['score'])
        self.assertIsNone(result['wouldTakeAgainPercent'])
        self.assertEqual('no_reviews', result['status'])
        self.assertEqual(0, result['reviewCount'])

    def test_invalid_aggregate_is_rejected(self):
        self.assertEqual([], ratings.rmp_teachers(page(score=7)))
        with self.assertRaises(ValueError):
            ratings.rmp_teachers('<html>Access denied</html>')

    def test_unambiguous_public_aggregate_retains_sample_and_source(self):
        result = ratings.rmp_teachers(page())[0]
        self.assertEqual(12, result['reviewCount'])
        self.assertEqual(4.2, result['score'])
        self.assertEqual('https://www.ratemyprofessors.com/professor/123', result['sourceUrl'])
        self.assertEqual('Example Professor', result['matchedName'])

    def test_initials_are_ignored_but_different_first_names_are_not_merged(self):
        self.assertEqual(ratings.name_key('Andrew B. Kahng'), ratings.name_key('Andrew Kahng'))
        self.assertNotEqual(ratings.name_key('Andrew Kahng'), ratings.name_key('Anthony Kahng'))
        self.assertNotEqual(ratings.name_key('A. C. Chen'), ratings.name_key('S. Chen'))

    def test_same_name_people_need_department_disambiguation(self):
        people = [{'name': 'Mary E. Boyle', 'department': 'Cognitive Science'},
                  {'name': 'Mary O. Boyle', 'department': 'Radiology'}]
        matches = ratings.matched_records({'matchedName': 'Mary Boyle', 'matchedDepartment': 'Cognitive Science'}, {'mary boyle': people})
        self.assertEqual([people[0]], matches)

    def test_shared_abbreviated_alias_does_not_assign_one_rating_to_two_people(self):
        people = [{'name': 'Shaochen Chen', 'department': 'Bioengineering'},
                  {'name': 'Shengqiang Chen', 'department': 'Bioengineering'}]
        matches = ratings.matched_records({'matchedName': 'S. Chen', 'matchedDepartment': 'Bioengineering'}, {'s chen': people})
        self.assertEqual([], matches)

    def test_cache_keeps_the_original_observation_date(self):
        with tempfile.TemporaryDirectory() as directory:
            url = 'https://www.ratemyprofessors.com/search/professors/1079?q=Example'
            key = hashlib.sha256(url.encode()).hexdigest()
            observed = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
            Path(directory, key + '.html').write_text(page())
            Path(directory, key + '.json').write_text(json.dumps({'url': url, 'status': 'ok', 'observedAt': observed}))
            fetcher = ratings.PublicFetcher(directory, max_cache_age_days=30)
            with patch.object(ratings.urllib.request, 'urlopen') as open_url:
                _, actual = fetcher.get(url)
                self.assertEqual(observed, actual)
                open_url.assert_not_called()
                self.assertTrue(fetcher.events[0]['cached'])
                self.assertEqual(64, len(fetcher.events[0]['contentSha256']))

    def test_rate_limit_stops_further_requests_to_that_host(self):
        with tempfile.TemporaryDirectory() as directory:
            fetcher = ratings.PublicFetcher(directory)
            url = 'https://www.ratemyprofessors.com/search/professors/1079?q=Example'
            with patch.object(ratings.urllib.request, 'urlopen', side_effect=urllib.error.HTTPError(url, 429, 'Rate limited', {}, None)) as open_url:
                with self.assertRaises(urllib.error.HTTPError):
                    fetcher.get(url)
                with self.assertRaises(RuntimeError):
                    fetcher.get(url + '2')
                self.assertEqual(1, open_url.call_count)
                self.assertEqual('skipped', fetcher.events[-1]['status'])


if __name__ == '__main__':
    unittest.main()
