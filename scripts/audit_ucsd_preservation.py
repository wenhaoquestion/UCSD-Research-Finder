#!/usr/bin/env python3
"""Compare a baseline with an assembled atlas and its explicit review archives.

Evidence must remain attached to the same identity (or its declared canonical
alias), with its original field, source, observation date, method and quotation.
An unrelated record containing the same quotation cannot satisfy this audit.
This is an offline integrity check, not a source/identity verification tool.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def proof_key(field, proof):
    return (field, *(json.dumps(proof.get(k), ensure_ascii=False, sort_keys=True)
                     for k in ['sourceUrl', 'observedAt', 'method', 'evidence']))


def evidence_keys(value, context=''):
    found = set()
    if isinstance(value, list):
        for row in value:
            found.update(evidence_keys(row, context))
    elif isinstance(value, dict):
        context = value.get('field', context)
        for key, child in value.items():
            if key == 'fieldEvidence' and isinstance(child, (dict, list)):
                if isinstance(child, dict) and 'sourceUrl' not in child:
                    fields = child.items()
                else:
                    fields = [(context, child)]
                for field, proofs in fields:
                    for proof in proofs if isinstance(proofs, list) else [proofs]:
                        if isinstance(proof, dict):
                            found.add(proof_key(field, proof))
            else:
                found.update(evidence_keys(child, context or key))
    return found


def source_urls(value):
    found = set()
    if isinstance(value, list):
        for row in value:
            found.update(source_urls(row))
    elif isinstance(value, dict):
        found.update(u for u in value.get('sourceUrls', []) if isinstance(u, str))
        for child in value.values():
            if isinstance(child, (list, dict)):
                found.update(source_urls(child))
    return found


def archived_records(archives):
    """Only an explicit, reasoned whole-record archive can preserve a removed ID."""
    for rows in archives:
        for row in rows:
            record = row.get('record')
            if row.get('reason') and isinstance(record, dict) and record.get('id'):
                yield record, row


def relationships(record):
    result = set()
    for pid in record.get('professorIds', []):
        result.add(('professorIds', pid))
    for affiliation in record.get('labAffiliations', []):
        if affiliation.get('labId'):
            result.add(('labAffiliations', affiliation['labId']))
    for observation in record.get('previousFieldObservations', []):
        if observation.get('field') in {'professorIds', 'labAffiliations'}:
            result.update(relationships({observation['field']: observation.get('value', [])}))
    return result


def audit(baseline, current, archives=()):
    owners, by_owner = defaultdict(set), {}
    duplicates, ambiguous, missing, lost_evidence, lost_sources, lost_links = [], [], [], [], [], []
    for kind in ['professors', 'labs']:
        for record in current.get(kind, []):
            rid = record['id']
            if rid in by_owner:
                duplicates.append(rid)
            by_owner[rid] = record
            for identity in [rid] + record.get('aliasIds', []):
                owners[identity].add(rid)
    for identity, targets in owners.items():
        if len(targets) > 1:
            ambiguous.append({'id': identity, 'owners': sorted(targets)})
    preserved = defaultdict(list)
    for record, row in archived_records(archives):
        for identity in [record['id']] + record.get('aliasIds', []):
            preserved[identity].append(record)
        # Isolation archives retain the removed professor relationships too.
        for observation in row.get('affectedProfessorObservations', []):
            if observation.get('professorId'):
                preserved[observation['professorId']].append(observation)
    counts = Counter()
    for kind in ['professors', 'labs']:
        for old in baseline.get(kind, []):
            rid = old['id']
            targets = owners.get(rid, set())
            associated = [by_owner[target] for target in targets] + preserved[rid]
            full_archive = [r for r in preserved[rid] if r.get('id') == rid and old.keys() <= r.keys()]
            if not targets and not full_archive:
                missing.append({'kind': kind, 'id': rid})
            counts['baselineRecords'] += 1
            counts['currentIds' if rid in by_owner else 'aliasIds' if targets else 'archivedIds' if full_archive else 'missingIds'] += 1
            available_evidence = set().union(*(evidence_keys(r) for r in associated))
            expected_evidence = evidence_keys(old)
            counts['baselineEvidenceTuples'] += len(expected_evidence)
            for field, *key in sorted(expected_evidence - available_evidence):
                lost_evidence.append({'kind': kind, 'id': rid, 'field': field,
                                      **{k: json.loads(v) for k, v in zip(['sourceUrl', 'observedAt', 'method', 'evidence'], key)}})
            available_sources = set().union(*(source_urls(r) for r in associated))
            lost = source_urls(old) - available_sources
            if lost:
                lost_sources.append({'kind': kind, 'id': rid, 'sourceUrls': sorted(lost)})
            available_links = set().union(*(relationships(r) for r in associated))
            def canonical_link(link):
                field, identity = link
                targets = owners.get(identity, set())
                return field, next(iter(targets)) if len(targets) == 1 else identity
            links = {canonical_link(link) for link in available_links}
            for link in relationships(old):
                if canonical_link(link) not in links:
                    lost_links.append({'kind': kind, 'id': rid, 'field': link[0], 'targetId': link[1]})
    issues = {'duplicateCurrentIds': sorted(set(duplicates)), 'ambiguousAliasIds': ambiguous,
              'missingRecords': missing, 'lostEvidence': lost_evidence,
              'lostSourceUrls': lost_sources, 'lostRelationships': lost_links}
    return {'schemaVersion': 1, 'generatedAt': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            'status': 'passed' if not any(issues.values()) else 'failed',
            'scope': 'identity-scoped baseline preservation; no claim of collection completeness or current source accuracy',
            'counts': dict(counts), 'issueCounts': {k: len(v) for k, v in issues.items()}, **issues}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--baseline', type=Path, default=ROOT / '.cache/coverage-20261016/baseline/research-atlas.json')
    cli.add_argument('--atlas', type=Path, default=ROOT / 'data/research-atlas.json')
    cli.add_argument('--archive', type=Path, action='append')
    cli.add_argument('--out', type=Path, default=ROOT / 'data/quality/coverage-20261016-preservation.json')
    args = cli.parse_args()
    paths = args.archive if args.archive is not None else [ROOT / 'data/quality/quarantined-records.json']
    result = audit(json.loads(args.baseline.read_text()), json.loads(args.atlas.read_text()),
                   [json.loads(path.read_text()) for path in paths])
    result['inputs'] = {'baseline': str(args.baseline.resolve()), 'atlas': str(args.atlas.resolve()),
                        'archives': [str(path.resolve()) for path in paths]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'counts': result['counts'], 'issues': result['issueCounts'], 'report': str(args.out)}))
    raise SystemExit(0 if result['status'] == 'passed' else 1)


if __name__ == '__main__':
    main()
