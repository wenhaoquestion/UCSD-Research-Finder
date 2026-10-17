"""Index lab identities independently from their possibly shared web resources.

Only an explicit, complete reviewed group can exempt a URL collision. Ambiguous
resource links resolve to no entity unless an ID or exact lab name identifies it.
"""
import re
import unicodedata
from collections import defaultdict

from atlas_urls import url_key, comparison_key


def label_key(value):
    return re.sub(r"[^a-z0-9]+", " ", unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower()).strip()


def named_lab_key(value):
    key = re.sub(r'\blaborator(?:y|ies)\b', 'lab', label_key(value))
    key = re.sub(r'\bthe\b', '', key)
    key = re.sub(r'\s+', ' ', key).strip()
    return '' if key in {'', 'lab', 'lab website', 'research group', 'website'} else key


def same_named_lab(first, second):
    name = named_lab_key(first.get('labName', ''))
    if not name or name != named_lab_key(second.get('labName', '')):
        return False
    pi = [label_key(r.get('principalInvestigator', '')) for r in [first, second]]
    return not (all(value and value not in {'not found', 'unknown'} for value in pi) and pi[0] != pi[1])


def reviewed_resource_mismatch(record, url):
    key = url_key(url)
    return bool(key) and any(row.get('captureVerified') and row.get('action') == 'record_resource_mismatch_and_current_lab'
                            and row.get('mismatchedLabId') == record['id'] and row.get('currentLabId') != record['id']
                            and row.get('evidence') and url_key(row.get('resourceUri', '')) == key
                            for row in record.get('resourceAssociationReviews', []))


def reviewed_shared_group(records):
    if len(records) < 2:
        return False
    sharing = records[0].get('websiteSharing', {})
    if not isinstance(sharing, dict):
        return False
    ids = [r['id'] for r in records]
    names = [label_key(r['labName']) for r in records]
    proofs = sharing.get('evidence', [])
    members = sharing.get('memberLabIds')
    if (not isinstance(members, list) or not all(isinstance(rid, str) for rid in members)
            or not isinstance(proofs, list) or not proofs
            or not all(isinstance(p, dict) and all(isinstance(p.get(k), str) and p[k].strip()
                       for k in ['sourceUrl', 'observedAt', 'evidence']) for p in proofs)):
        return False
    return (sharing.get('kind') == 'distinct_named_labs' and bool(sharing.get('groupId'))
            and len(ids) == len(set(ids)) and all(names) and len(names) == len(set(names))
            and sorted(members) == sorted(ids)
            and len({url_key(r['labWebsiteUrl']) for r in records}) == 1
            and all(r.get('websiteSharing') == sharing for r in records)
            and all(any(re.search(r'(?<![a-z0-9])' + re.escape(name) + r'(?![a-z0-9])', label_key(p['evidence'])) for p in proofs) for name in names)
            and all(r.get('fieldEvidence', {}).get('websiteSharing') == proofs for r in records))


def reviewed_shared_resource(records, uri):
    if not reviewed_shared_group(records):
        return False
    key = url_key(uri)
    return any(row.get('captureVerified') and row.get('evidence') and row.get('reason')
               and row.get('action') == 'register_shared_lab_resource' and row.get('resourceKind') == 'shared_landing_page'
               and url_key(row.get('resourceUri', '')) == key
               and url_key(row.get('primaryUri', '')) == url_key(records[0]['labWebsiteUrl'])
               and row.get('groupId') == records[0]['websiteSharing']['groupId']
               and sorted(row.get('memberLabIds', [])) == sorted(record['id'] for record in records)
               and all(row in record.get('sharedResourceReviews', [])
                       and any(url_key(url) == key for url in record.get('alternateWebsiteUrls', []))
                       and all(proof in record.get('fieldEvidence', {}).get('alternateWebsiteUrls', []) for proof in row['evidence'])
                       for record in records)
               for row in records[0].get('sharedResourceReviews', []))


class LabIndex:
    def __init__(self, records=()):
        self.by_id = {}
        self.by_url = defaultdict(list)
        self._url_keys_by_id = defaultdict(set)
        for record in records:
            self.add(record)

    def add(self, record):
        for rid in [record['id']] + record.get('aliasIds', []):
            owner = self.by_id.get(rid)
            if owner is not None and owner['id'] != record['id']:
                raise ValueError('Ambiguous lab identity: ' + rid)
            self.by_id[rid] = record
        for key in self._url_keys_by_id.pop(record['id'], set()):
            self.by_url[key] = [r for r in self.by_url[key] if r['id'] != record['id']]
            if not self.by_url[key]:
                del self.by_url[key]
        for url in [record.get('labWebsiteUrl', '')] + record.get('alternateWebsiteUrls', []):
            self.add_url(url, record)

    def add_url(self, url, record):
        key = url_key(url)
        # Preserve an older listed URI on the scientific record without giving
        # it current resource ownership after an explicit capture review.
        if reviewed_resource_mismatch(record, url):
            return
        if key and not any(r['id'] == record['id'] for r in self.by_url[key]):
            self.by_url[key].append(record)
            self._url_keys_by_id[record['id']].add(key)

    def candidates(self, url):
        return tuple(self.by_url.get(url_key(url), []))

    def possible_variants(self, url):
        """Discovery hints only: these records do not own the supplied URI."""
        key = comparison_key(url)
        if not key:
            return ()
        return tuple({r['id']: r for records in self.by_url.values() for r in records
                      if any(comparison_key(u) == key for u in [r.get('labWebsiteUrl', '')] + r.get('alternateWebsiteUrls', []))}.values())

    def resolve(self, url, *, lab_id=None, name=None):
        records = self.candidates(url)
        if lab_id:
            target = self.by_id.get(lab_id)
            return target if target is not None and any(r['id'] == target['id'] for r in records) else None
        if len(records) == 1:
            return records[0]
        matches = [r for r in records if name and label_key(name) == label_key(r['labName'])]
        return matches[0] if len(matches) == 1 else None

    def url_groups(self):
        shared, duplicates = [], []
        for key, records in self.by_url.items():
            if len(records) > 1:
                accepted = (key == url_key(records[0]['labWebsiteUrl']) and reviewed_shared_group(records)) or reviewed_shared_resource(records, key)
                (shared if accepted else duplicates).append(records)
        return shared, duplicates

    def validate_sharing(self):
        groups = {}
        for record in {r['id']: r for r in self.by_id.values()}.values():
            if 'websiteSharing' in record and not reviewed_shared_group(self.candidates(record['labWebsiteUrl'])):
                raise ValueError('Incomplete or inconsistent reviewed shared website group: ' + record['id'])
            sharing = record.get('websiteSharing')
            if sharing:
                old = groups.setdefault(sharing['groupId'], sharing)
                if old != sharing:
                    raise ValueError('Inconsistent reviewed shared website group ID: ' + sharing['groupId'])
        for record in {r['id']: r for r in self.by_id.values()}.values():
            for row in record.get('resourceAssociationReviews', []):
                previous = self.by_id.get(row.get('mismatchedLabId'))
                current = self.by_id.get(row.get('currentLabId'))
                if (not row.get('captureVerified') or not row.get('evidence') or not row.get('reason')
                        or row.get('action') != 'record_resource_mismatch_and_current_lab'
                        or previous is None or current is None or previous is current
                        or record['id'] not in {previous['id'], current['id']}
                        or row not in previous.get('resourceAssociationReviews', [])
                        or row not in current.get('resourceAssociationReviews', [])
                        or url_key(previous['labWebsiteUrl']) != url_key(row.get('resourceUri', ''))
                        or url_key(current['labWebsiteUrl']) != url_key(row.get('currentLabUri', ''))
                        or self.candidates(row['resourceUri']) != (current,)):
                    raise ValueError('Incomplete or inconsistent reviewed resource association: ' + record['id'])
            for row in record.get('sharedResourceReviews', []):
                if record['id'] not in row.get('memberLabIds', []) or not reviewed_shared_resource(self.candidates(row.get('resourceUri', '')), row.get('resourceUri', '')):
                    raise ValueError('Incomplete or inconsistent reviewed shared resource: ' + record['id'])
