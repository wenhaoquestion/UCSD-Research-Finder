import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collection_scope import ScopePolicy, key
from collect_ucsd_coverage import Queue, audit_queue_scope, discover_lab_identity_pages
from refresh_labs import DOM


def context(kind, source=''):
    return {'kind': kind, 'sourceUrl': source, 'department': 'Example', 'candidateId': '', 'professorId': ''}


def item(url, title='', contexts=None, final=None):
    return {'url': url, 'state': 'done' if title else 'pending', 'attempts': 1 if title else 0,
            'contexts': contexts or [context('discovered_lab', 'https://department.ucsd.edu/research/labs/')],
            'fetch': {'status': 'ok', 'observedAt': '2020-01-01', 'finalUrl': final or url} if title else {},
            'page': {'title': title, 'headings': [title], 'mainTextExcerpt': title}}


class CollectionScopeTests(unittest.TestCase):
    def policy(self, rows, candidates=None, atlas=None, decisions=None):
        state = {'items': {key(i['url']): i for i in rows}, 'labCandidates': candidates or {}}
        return ScopePolicy(state, atlas or {'professors': [], 'labs': []}, decisions), state

    def test_berkeley_brand_parent_and_contact_are_excluded_without_new_capture(self):
        root = item('https://creative.lbl.gov/visual-identity/', 'The Berkeley Lab Brand', [context('discovered_lab', 'https://physics.ucsd.edu/about')])
        child = item('https://creative.lbl.gov/contact-us/', contexts=[context('identity_page', root['url'])])
        policy, _ = self.policy([root, child])
        self.assertIn('branding', policy.request_reason(root))
        self.assertFalse(policy.can_expand(root))
        self.assertIsNotNone(policy.request_reason(child))
        self.assertEqual(child['fetch'], {})

    def test_nimh_funding_program_does_not_expand_institution_navigation(self):
        url = 'https://www.nimh.nih.gov/research/research-funded-by-nimh/research-initiatives/advanced-laboratories-for-accelerating-the-reach-and-impact-of-treatments-for-youth-and-adults-with-mental-illness-alacrity'
        root = item(url, 'ALACRITY - National Institute of Mental Health', [context('discovered_lab', 'https://today.ucsd.edu/story/new-grant')])
        children = [item(u, contexts=[context('identity_page', url)]) for u in ['https://www.nimh.nih.gov/', 'https://www.nimh.nih.gov/index%2ephp/about', 'https://www.nimh.nih.gov/index%2ephp/site-info/contact-nimh']]
        policy, _ = self.policy([root] + children)
        self.assertIn('funder', policy.request_reason(root))
        self.assertTrue(all(policy.request_reason(c) for c in children))

    def test_generic_cambridge_redirect_cannot_expand_all_faculty_people(self):
        requested = 'http://www.educ.cam.ac.uk/people/old-profile'
        final = 'http://faculty.educ.cam.ac.uk/'
        root = item(requested, 'Faculty of Education - University of Cambridge', final=final)
        child = item('http://faculty.educ.cam.ac.uk/about-us/our-people', contexts=[context('identity_page', final)])
        atlas = {'professors': [], 'labs': [{'id': 'old', 'labName': 'Example Research Lab', 'labWebsiteUrl': requested}]}
        policy, _ = self.policy([root, child], atlas=atlas)
        self.assertFalse(policy.can_expand(root))
        self.assertIsNotNone(policy.destination_reason(root))
        self.assertIsNotNone(policy.request_reason(child))

    def test_named_ucsd_lab_on_external_host_keeps_bounded_identity_discovery(self):
        root = item('https://real-lab.org/', 'Real Lab')
        people = item('https://real-lab.org/people', contexts=[context('identity_page', root['url'])])
        candidates = {key(root['url']): {'record': {'labName': 'Real Lab'}, 'observations': []}}
        policy, _ = self.policy([root, people], candidates)
        self.assertIsNone(policy.request_reason(root))
        self.assertTrue(policy.can_expand(root))
        self.assertIsNone(policy.request_reason(people))
        self.assertTrue(policy.can_expand(people))

    def test_shared_host_identity_navigation_stays_within_named_site(self):
        root = item('https://sites.google.com/ucsd.edu/real-lab/home', 'Real Lab')
        inside = item('https://sites.google.com/ucsd.edu/real-lab/people', contexts=[context('identity_page', root['url'])])
        outside = item('https://sites.google.com/ucsd.edu/other-site/people', contexts=[context('identity_page', root['url'])])
        candidates = {key(root['url']): {'record': {'labName': 'Real Lab'}, 'observations': []}}
        policy, _ = self.policy([root, inside, outside], candidates)
        self.assertIsNone(policy.request_reason(inside))
        self.assertIsNotNone(policy.request_reason(outside))

    def test_frozen_ucsd_department_and_person_seeds_remain_eligible(self):
        rows = [item('https://profiles.ucsd.edu/staff.person', contexts=[context('profile_discovery')]),
                item('https://department.ucsd.edu/', contexts=[context('department')]),
                item('https://department.ucsd.edu/faculty', contexts=[context('faculty_directory'), context('identity_page', 'https://creative.lbl.gov/visual-identity/')])]
        policy, _ = self.policy(rows)
        self.assertTrue(all(policy.request_reason(i) is None for i in rows))

    def test_unknown_external_lab_requires_named_campus_association(self):
        root = item('https://unrelated-lab.org/', 'Unrelated Lab', [context('discovered_lab', 'https://today.ucsd.edu/story/guest-speaker')])
        candidates = {key(root['url']): {'record': {'labName': 'Unrelated Lab'}, 'observations': []}}
        policy, _ = self.policy([root], candidates)
        self.assertIsNotNone(policy.request_reason(root))
        self.assertFalse(policy.can_expand(root))

    def test_nonprofit_support_group_is_not_an_external_lab_identity_root(self):
        root = item('http://www.11qusa.org/', 'Nonforprofit | 11q Research & Resource Group', [context('discovered_lab', 'https://pediatrics.ucsd.edu/research/faculty-labs/grossfeld-lab/about.html')])
        candidates = {key(root['url']): {'record': {'labName': '11q Research and Resource Group'}, 'observations': []}}
        child = item('http://www.11qusa.org/about-us', contexts=[context('identity_page', root['url'])])
        policy, _ = self.policy([root, child], candidates)
        self.assertFalse(policy.can_expand(root))
        self.assertIsNotNone(policy.request_reason(child))

    def test_named_lab_core_allows_research_direction_in_navigation_only(self):
        root = item('https://du-ucsd.github.io/', 'Du Quantum Sensing Lab')
        people = item('https://du-ucsd.github.io/people.html', contexts=[context('identity_page', root['url'])])
        contact = item('https://du-ucsd.github.io/contact.html', contexts=[context('identity_page', root['url'])])
        candidates = {key(root['url']): {'record': {'labName': 'Du Research Lab'}, 'observations': []}}
        policy, _ = self.policy([root, people, contact], candidates)
        self.assertTrue(policy.can_expand(root))
        self.assertIsNone(policy.request_reason(people))
        self.assertIsNone(policy.request_reason(contact))
        root['page']['title'] = root['page']['headings'][0] = 'Smith Quantum Sensing Lab'
        self.assertFalse(policy.can_expand(root))

    def test_baseline_lab_abbreviations_and_new_names_keep_identity_checks(self):
        for url, old_name, title, body in [
            ('https://zeidanlab.com/', 'Zeidan Lab', 'Home', 'Our research studies mindfulness with the UCSD CMCR and a university institute.'),
            ('https://elephantresearch.net/index.html', 'Shermin de Silva Lab', 'DE SILVA HUMANATURE LAB', 'The HumaNature Lab @ UCSD, Department of Biological Sciences.'),
            ('https://tyelab.org/', 'Kay Tye Lab', 'Tye Laboratory', 'The Tye Lab studies circuits at an institute.')]:
            with self.subTest(url=url):
                root = item(url, title)
                root['page']['mainTextExcerpt'] = body
                atlas = {'professors': [], 'labs': [{'id': 'old', 'labName': old_name, 'labWebsiteUrl': url}]}
                policy, _ = self.policy([root], atlas=atlas)
                self.assertIsNone(policy.destination_reason(root))
                self.assertTrue(policy.can_expand(root))

    def test_shared_parent_dag_returns_one_root_without_combinatorial_expansion(self):
        root = item('https://real-lab.org/', 'Real Lab')
        rows, previous = [root], [root]
        for level in range(25):
            current = [item('https://real-lab.org/' + str(level) + '-' + str(n), contexts=[context('identity_page', p['url']) for p in previous]) for n in range(2)]
            rows.extend(current); previous = current
        policy, _ = self.policy(rows)
        self.assertEqual([r['url'] for r in policy.roots(previous[0])], [root['url']])

    def test_specific_campus_person_in_own_body_can_support_navigation_but_not_institution_root(self):
        source = item('https://profiles.ucsd.edu/jane.example', 'Jane Example', [context('profile_discovery')])
        source['profileEligibility'] = {'nameAsDisplayed': 'Jane Example', 'titleAsListed': 'Associate Professor, Physics', 'schoolAsListed': 'VC-Academic Affairs'}
        root = item('https://jane-example.org/', 'Home', [context('lab_link_candidate', source['url'])])
        root['page']['headings'] = ['Welcome']
        root['page']['mainTextExcerpt'] = 'Jane Example is an Associate Professor at UC San Diego. Our lab studies physics.'
        policy, _ = self.policy([source, root])
        self.assertTrue(policy.can_expand(root))
        root['page']['title'] = root['page']['headings'][0] = 'Faculty of Education'
        self.assertFalse(policy.can_expand(root))

    def test_scope_exclusion_preserves_capture_and_can_admit_new_specific_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            queue = Queue(Path(temporary) / 'queue.json')
            root = item('https://new-lab.org/', 'New Lab', [context('discovered_lab', 'https://today.ucsd.edu/story/guest')])
            queue.state['items'][key(root['url'])] = root
            queue.state['labCandidates'][key(root['url'])] = {'record': {'labName': 'New Lab'}, 'observations': []}
            queue.scope_policy = ScopePolicy(queue.state, {'professors': [], 'labs': []})
            original_fetch = copy.deepcopy(root['fetch'])
            audit_queue_scope(queue)
            self.assertEqual(root['state'], 'scope_excluded')
            self.assertEqual(root['fetch'], original_fetch)
            root['contexts'].append(context('discovered_lab', 'https://department.ucsd.edu/research/labs/'))
            audit_queue_scope(queue)
            self.assertEqual(root['state'], 'done')
            self.assertEqual(root['fetch'], original_fetch)
            self.assertTrue(root['scopeAssessmentHistory'])

    def test_known_nonlab_parent_produces_no_identity_children(self):
        with tempfile.TemporaryDirectory() as temporary:
            queue = Queue(Path(temporary) / 'queue.json')
            root = item('https://creative.lbl.gov/visual-identity/', 'The Berkeley Lab Brand')
            root['depth'] = 3
            queue.state['items'][key(root['url'])] = root
            queue.scope_policy = ScopePolicy(queue.state, {'professors': [], 'labs': []})
            discover_lab_identity_pages(queue, root, root['fetch'], DOM('<nav><a href="/contact-us/">Contact Us</a></nav>'))
            self.assertEqual(len(queue.state['items']), 1)
