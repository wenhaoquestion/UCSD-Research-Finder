"""Migrate selectors without equating different transport resources.

Queue items are keyed by the URI actually requested. A legacy candidate selector
keeps the destination request its review used; its separate literal target is
retained in the record and binding history. A selector is never
proof that a second path was visited. Scientific IDs and entry bodies do not
change. Caller-owned queue leases still govern every persisted live mutation.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json

from atlas_urls import url_key

VERSION = 2


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def normalize_queue_keys(state):
    """Atomically reindex a caller-owned in-memory snapshot, keeping all values."""
    if state.get('requestResourceKeyVersion', 0) >= VERSION:
        return state
    selectors = {'items': lambda row: row.get('url', ''),
                 'labCandidates': lambda row: row.get('record', {}).get('labWebsiteUrl', ''),
                 'centers': lambda row: row.get('url', '')}
    original_items = state.get('items', {})
    replacements, moves, counts, unresolved, candidate_bindings = {}, [], {}, [], []
    for collection, literal in selectors.items():
        if collection not in state:
            continue
        target = {}; counts[collection] = len(state[collection])
        for old_key, entry in state[collection].items():
            uri = literal(entry)
            if collection == 'labCandidates' and old_key in original_items:
                original_request = original_items[old_key]
                requested = original_request.get('url', '')
                if url_key(requested):
                    if url_key(uri) != url_key(requested):
                        meta = original_request.get('fetch', {})
                        candidate_bindings.append({'previousSelector': old_key, 'currentSelector': url_key(requested),
                            'discoveredLiteralTarget': uri, 'reviewedRequestUri': requested,
                            'observedAt': meta.get('observedAt'), 'bodySha256': meta.get('sha256'),
                            'literalTargetVisitEstablished': False})
                    uri = requested
            if not uri:
                if collection == 'items':
                    raise ValueError('Queue item lacks its actual requested URI: ' + old_key)
                unresolved.append({'collection': collection, 'legacySelector': old_key,
                                   'reason': 'Literal target URI is absent; retain the opaque selector without inferring a target.'})
            # Malformed literals remain separate original observations. They
            # do not acquire an empty/root URI or become requestable.
            new_key = url_key(uri) or old_key
            if new_key in target:
                raise ValueError('Duplicate exact resource in ' + collection + ': ' + new_key)
            target[new_key] = entry
            if old_key != new_key:
                moves.append({'collection': collection, 'previousKey': old_key, 'currentKey': new_key,
                              'keyBasisUri': uri, 'entrySha256': digest(entry),
                              'scientificId': entry.get('id', entry.get('record', {}).get('id'))})
        replacements[collection] = target
    # Preflight every collection before changing even the first key.
    for collection, entries in replacements.items():
        state[collection] = entries
    previous = state.get('requestResourceKeyMigration')
    if previous:
        state.setdefault('requestResourceKeyMigrationHistory', []).append(copy.deepcopy(previous))
    state['requestResourceKeyMigration'] = {'version': VERSION, 'at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'entryCounts': counts, 'moves': moves, 'candidateRequestBindings': candidate_bindings,
        'unresolvedLegacySelectors': unresolved,
        'wireRequests': 0, 'entryValuesUnchanged': True,
        'sourceObservationsPreserved': True, 'scientificIdsUnchanged': True}
    state['requestResourceKeyVersion'] = VERSION
    return state


def candidate_selector(state, record):
    """Append observations to the same discovery case without duplicating IDs."""
    target = url_key(record['labWebsiteUrl'])
    if target in state.get('labCandidates', {}):
        return target
    matches = [selector for selector, candidate in state.get('labCandidates', {}).items()
               if candidate.get('record', {}).get('id') == record.get('id')
               and url_key(candidate['record'].get('labWebsiteUrl', '')) == target]
    if len(matches) > 1:
        raise ValueError('Multiple legacy discovery cases require an explicit selector review: ' + target)
    return matches[0] if matches else target


def rebind_decisions(decisions, state):
    """Resolve legacy selectors once; later exact decisions stay exact.

Persist the returned versioned configuration only after offline verification.
That marker prevents a new slashless decision from being mistaken for a legacy
selector that originally referred to a slash-terminated candidate.
"""
    if decisions.get('requestResourceDecisionKeyVersion', 0) >= VERSION:
        return copy.deepcopy(decisions)
    normalize_queue_keys(state)
    changes = state['requestResourceKeyMigration']['moves']
    mapping = {}
    # Candidate selectors preserve the actual destination capture a legacy
    # review used. Their distinct literal targets remain unverified observations.
    for collection in ['centers', 'items', 'labCandidates']:
        mapping.update({row['previousKey']: row for row in changes if row['collection'] == collection})
    result = copy.deepcopy(decisions); result['labs'] = {}; history = []
    for selector, decision in decisions.get('labs', {}).items():
        binding = mapping.get(selector)
        target = binding['currentKey'] if binding else selector
        if target in result['labs']:
            raise ValueError('Two reviewed decisions bind the same exact resource: ' + target)
        result['labs'][target] = copy.deepcopy(decision)
        if target != selector:
            history.append({'previousSelector': selector, 'currentSelector': target,
                            'basis': copy.deepcopy(binding), 'originalDecision': copy.deepcopy(decision)})
    result['requestResourceDecisionKeyVersion'] = VERSION
    result['legacyDecisionKeyBindings'] = history
    result['decisionKeyMigrationPolicy'] = 'Selector migration only; no resource equivalence, new acceptance, source observation or scientific ID change.'
    return result
