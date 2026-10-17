#!/usr/bin/env python3
"""Offline reviewed-lab assembly checks in cache; never export the served atlas.

This deliberately exercises an incomplete reviewed subset in memory. It cannot
replace the completion-gated final export, full faculty review or final checks.
"""
from __future__ import annotations

import copy
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

from apply_ucsd_coverage import verified_destination_reviews, preserve_supported_values, attach_reviewed_lab_associations
from audit_ucsd_preservation import audit
from lab_identity_merges import verified_reviews
from rebuild_verified_atlas import build
from validate_data import validate_lab, validate_professor, validate_references
from lab_entities import LabIndex
from lab_research_resource_reviews import verified_new_lab_scopes
from lab_resource_reviews import verified_resource_reviews, verified_alias_reviews
from person_identity_reviews import verified_person_reviews
from lab_field_reviews import verified_lab_fields
from lab_own_metadata import verified_own_metadata
from lab_ownership_reviews import verified_lab_ownership_reviews
from lab_preferred_resources import verified_preferred_resources
from published_organization_resources import verified_published_organizations, attach_published_organization_aliases
from lab_resource_associations import verified_resource_associations
from shared_lab_resources import verified_shared_resources
from queue_resource_keys import normalize_queue_keys
from faculty_candidate_history import candidate_history, attach_history_patches
from professor_own_field_reviews import verified_professor_fields
from professor_profile_link_reviews import verified_profile_link_reviews
from faculty_department_normalizations import verified_department_normalizations
from existing_lab_own_resources import verified_existing_own_resources, attach_existing_own_resources

ROOT = Path(__file__).resolve().parents[1]


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--faculty-review', type=Path, help='Also validate a non-final faculty review; still writes only preview cache files')
    cli.add_argument('--queue-preview', type=Path, help='Use a separate non-final queue snapshot containing actual cache captures; never writes the live queue')
    cli.add_argument('--capture-cache', type=Path, help='Read immutable source bodies from this evidence cache; baseline and live collection stay in the original cache')
    cli.add_argument('--output-directory', type=Path, help='Separate cache directory for this non-final assembly')
    cli.add_argument('--receipt', type=Path, help='Separate local receipt path for this non-final assembly')
    args = cli.parse_args()
    cache, evidence_dir = ROOT / '.cache/coverage-20261016', ROOT / 'data/ucsd'
    capture_cache = args.capture_cache or cache
    def read(name):
        return json.loads((evidence_dir / name).read_text())
    baseline = json.loads((cache / 'baseline/research-atlas.json').read_text())
    queue_path = args.queue_preview or cache / 'queue.json'
    queue = json.loads(queue_path.read_text())
    normalize_queue_keys(queue)
    handoff = read('coverage-20261016-reviewed-lab-handoff.json')
    reviews = read('coverage-20261016-existing-lab-merges.json')
    coverage = {key: copy.deepcopy(handoff[key]) for key in ['labs', 'labAliases', 'labUpdates']}
    coverage['labs'] = verified_new_lab_scopes(coverage['labs'], queue, capture_cache)
    coverage.update(collectionState='reviewed_incremental_preview', isFinalExport=False, generatedAt=reviews['reviewedAt'],
                    labIdentityMerges=verified_reviews(reviews, queue, capture_cache),
                    destinationIdentityReviews=verified_destination_reviews(queue, capture_cache))
    faculty = None
    if args.faculty_review:
        faculty = json.loads(args.faculty_review.read_text())
        coverage['professors'] = copy.deepcopy(faculty['professors'])
        people = {p['id']: p for p in baseline['professors'] + faculty['professors']}
        coverage['byProfessorId'] = {pid: preserve_supported_values(people[pid], patch) for pid, patch in faculty['byProfessorId'].items() if pid in people}
        history_path = evidence_dir / 'faculty-candidate-observation-history-20261016.json'
        history_patches, held_candidates = candidate_history(
            json.loads(history_path.read_text()) if history_path.exists() else {'entries':[]},
            list(people.values()), faculty, queue, capture_cache)
        attach_history_patches(coverage['byProfessorId'], history_patches)
        coverage['heldFacultyCandidates'] = held_candidates
    association_people = {p['id']: p for p in baseline['professors'] + (faculty['professors'] if faculty else [])}
    attach_reviewed_lab_associations(coverage.setdefault('byProfessorId', {}), coverage['labs'], association_people)
    inputs = [read(name) for name in ['lab-evidence.json', 'teaching-evidence.json', 'ratings-evidence.json', 'source-checks.json',
                                     'faculty-evidence.json', 'lab-identity-review.json', 'lab-expansion-review.json']]
    coverage['labResourceReviews'] = verified_resource_reviews(read('lab-resource-identity-review-20261016.json'), queue, capture_cache,
        inputs[0]['labs'] + coverage['labs'], baseline['labs'])
    coverage['labAliasResourceReviews'] = verified_alias_reviews(read('lab-alias-resource-review-20261016.json'), coverage['labAliases'], queue, capture_cache)
    organization_path = evidence_dir / 'lab-published-organization-resource-review-20261016.json'
    coverage['publishedOrganizationResourceReviews'] = verified_published_organizations(
        json.loads(organization_path.read_text()) if organization_path.exists() else {'entries': []},
        queue, capture_cache, baseline['labs'] + coverage['labs'], list(association_people.values()), coverage['labAliases'])
    attach_published_organization_aliases(coverage, coverage['publishedOrganizationResourceReviews'])
    own_resource_path = evidence_dir / 'lab-existing-own-resource-review-20261016.json'
    coverage['existingOwnLabResourceReviews'] = verified_existing_own_resources(
        json.loads(own_resource_path.read_text()) if own_resource_path.exists() else {'entries': []},
        queue, capture_cache, baseline['labs'] + coverage['labs'])
    attach_existing_own_resources(coverage, coverage['existingOwnLabResourceReviews'])
    own_metadata_path = evidence_dir / 'lab-own-metadata-review-20261016.json'
    coverage['labOwnMetadataReviews'] = verified_own_metadata(
        json.loads(own_metadata_path.read_text()) if own_metadata_path.exists() else {'entries': []},
        coverage['labAliasResourceReviews'], queue, capture_cache, baseline['labs'] + coverage['labs'], coverage['labUpdates'])
    ownership_path = evidence_dir / 'lab-own-institution-review-20261016.json'
    coverage['labOwnershipReviews'] = verified_lab_ownership_reviews(
        json.loads(ownership_path.read_text()) if ownership_path.exists() else {'entries': []},
        queue, capture_cache, baseline['labs'] + coverage['labs'])
    preferred_path = evidence_dir / 'lab-preferred-resource-review-20261016.json'
    coverage['labPreferredResourceReviews'] = verified_preferred_resources(
        json.loads(preferred_path.read_text()) if preferred_path.exists() else {'entries': []},
        coverage['labAliasResourceReviews'], queue, capture_cache, baseline['labs'] + coverage['labs'], coverage['labUpdates'])
    coverage['personIdentityReviews'] = verified_person_reviews(read('person-identity-review-20261016.json'), queue, capture_cache, baseline, faculty_review=faculty)
    department_path = evidence_dir / 'faculty-department-normalization-review-20261016.json'
    coverage['reviewedDepartmentNormalizations'] = verified_department_normalizations(
        json.loads(department_path.read_text()),
        queue, capture_cache, baseline['professors'] + (faculty['professors'] if faculty else []),
        read('departments.json')['departments']) if department_path.exists() else []
    professor_fields_path = evidence_dir / 'professor-own-field-review-20261016.json'
    coverage['reviewedProfessorFieldUpdates'] = verified_professor_fields(
        json.loads(professor_fields_path.read_text()) if professor_fields_path.exists() else {'entries': []},
        queue, capture_cache, baseline['professors'] + (faculty['professors'] if faculty else []), coverage['personIdentityReviews'], faculty_review=faculty)
    coverage['reviewedLabFieldUpdates'] = verified_lab_fields(read('lab-field-review-20261016.json'), queue, capture_cache,
        baseline['labs'] + coverage['labs'], baseline['professors'] + (faculty['professors'] if faculty else []))
    link_review_path = evidence_dir / 'professor-profile-link-review-20261016.json'
    coverage['professorProfileLinkReviews'] = verified_profile_link_reviews(
        json.loads(link_review_path.read_text()) if link_review_path.exists() else {'entries': []},
        queue, capture_cache, baseline['professors'] + (faculty['professors'] if faculty else []))
    coverage['labResourceAssociationReviews'] = verified_resource_associations(
        read('lab-resource-association-review-20261016.json'), queue, capture_cache,
        baseline['labs'] + coverage['labs'], coverage['destinationIdentityReviews'])
    coverage['sharedLabResourceReviews'] = verified_shared_resources(
        read('shared-lab-resource-review-20261016.json'), queue, capture_cache, baseline['labs'] + coverage['labs'])
    def assemble(data):
        return build(copy.deepcopy(data), *copy.deepcopy(inputs), coverage_evidence=copy.deepcopy(coverage))
    assembled, _, _, quarantine = assemble(baseline)
    for kind, validate in [('professors', validate_professor), ('labs', validate_lab)]:
        for record in assembled[kind]:
            validate(record)
    validate_references(assembled)
    shared_urls, duplicate_groups = LabIndex(assembled['labs']).url_groups()
    duplicate_urls = len(duplicate_groups)
    duplicate_ids = len(assembled['professors']) + len(assembled['labs']) - len({r['id'] for kind in ['professors', 'labs'] for r in assembled[kind]})
    old_archive = json.loads((ROOT / 'data/quality/quarantined-records.json').read_text())
    preservation = audit(baseline, assembled, [old_archive + quarantine])
    repeated, _, _, repeated_quarantine = assemble(assembled)
    changed = {}
    for kind in ['professors', 'labs']:
        first, second = {r['id']: r for r in assembled[kind]}, {r['id']: r for r in repeated[kind]}
        changed[kind] = [{'id': rid, 'fields': [field for field in sorted(set(first.get(rid, {})) | set(second.get(rid, {})))
                                              if first.get(rid, {}).get(field) != second.get(rid, {}).get(field)]}
                         for rid in sorted(set(first) | set(second)) if first.get(rid) != second.get(rid)]
    output = args.output_directory or cache / ('faculty-assembly-preview' if faculty else 'reviewed-identity-assembly-preview')
    output.mkdir(parents=True, exist_ok=True)
    for filename, value in [('research-atlas.json', assembled), ('repeated-atlas.json', repeated),
                            ('quarantined-records.json', quarantine), ('preservation.json', preservation), ('changed-records.json', changed)]:
        (output / filename).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    receipt = {'at': dt.datetime.now(dt.timezone.utc).isoformat(), 'isFinalExport': False, 'isFinalValidation': False,
               'servedAtlasModified': False, 'wireRequests': 0, 'collectionQueueComplete': False,
               'reviewedPreview': {'newLabs': len(coverage['labs']), 'aliases': len(coverage['labAliases']),
                                   'reviewedGraduateProgramAffiliateLabs': sum(bool(l.get('programAffiliationReview', {}).get('captureVerified')) for l in coverage['labs']),
                                   'reviewedCampusResearchResourceGroups': sum(bool(l.get('campusResearchResourceReview', {}).get('captureVerified')) for l in coverage['labs']),
                                   'reviewedExistingLabOwnershipCorrections': len(coverage['labOwnershipReviews']),
                                   'duplicateIdsMerged': len(coverage['labIdentityMerges']),
                                   'nonLabsIsolated': sum(r['action'] == 'isolate_non_lab' for r in coverage['destinationIdentityReviews']),
                                   'professors': len(assembled['professors']), 'labs': len(assembled['labs']),
                                   'schemaAndReferences': 'passed', 'repeatedAssemblyIdentical': repeated == assembled,
                                   'canonicalLabUrlDuplicateGroups': duplicate_urls, 'primaryIdCollisions': duplicate_ids,
                                   'reviewedSharedLabWebsiteGroups': len({group[0]['websiteSharing']['groupId'] for group in shared_urls}),
                                   'reviewedSharedLabResources': len(shared_urls),
                                   'reviewedCaptureIdentityBindings': len(coverage['labResourceReviews']),
                                   'reviewedProfessorIdsMerged': len(coverage['personIdentityReviews']),
                                   'reviewedScientificPersonIdsMerged': sum(r['identityBasis']['type'] != 'misparsed_research_link_in_named_faculty_card' for r in coverage['personIdentityReviews']),
                                   'reviewedMisparsedProfessorLabelsResolved': sum(r['identityBasis']['type'] == 'misparsed_research_link_in_named_faculty_card' for r in coverage['personIdentityReviews']),
                                   'heldPreviousFacultyCandidates': len(coverage.get('heldFacultyCandidates', [])),
                                   'reviewedProfessorOwnFieldObservations': len(coverage['reviewedProfessorFieldUpdates']),
                                   'reviewedDepartmentLabelNormalizations': len(coverage['reviewedDepartmentNormalizations']),
                                   'reviewedExistingLabFieldUpdates': len(coverage['reviewedLabFieldUpdates']),
                                   'reviewedOwnLabMetadataUpdates': len(coverage['labOwnMetadataReviews']),
                                   'reviewedPreferredLabResources': len(coverage['labPreferredResourceReviews']),
                                   'reviewedProfessorProfileLinkIssues': len(coverage['professorProfileLinkReviews']),
                                   'reviewedResourceAssociationChanges': len(coverage['labResourceAssociationReviews']),
                                   'reviewedSharedResourceAdditions': len(coverage['sharedLabResourceReviews']),
                                   'unresolvedLabCaptureInputs': len(assembled.get('unresolvedLabCaptureInputs', [])),
                                   'firstQuarantineCount': len(quarantine), 'repeatedQuarantineCount': len(repeated_quarantine),
                                   'preservation': preservation['counts'], 'issues': preservation['issueCounts'],
                                   'changedRecordCounts': {kind: len(rows) for kind, rows in changed.items()}},
               'previewDirectory': str(output.resolve()),
               'sourceQueuePath': str(queue_path.resolve()), 'sourceQueueSha256': hashlib.sha256(queue_path.read_bytes()).hexdigest(),
               'sourceCaptureCachePath': str(capture_cache.resolve()),
               'preservationReportSha256': hashlib.sha256((output / 'preservation.json').read_bytes()).hexdigest(),
               'limitation': 'Reviewed lab subset only. Full queue, faculty review, final export and complete validation remain required.'}
    if faculty:
        receipt.update(facultyReviewPath=str(args.faculty_review.resolve()), facultyReviewSha256=hashlib.sha256(args.faculty_review.read_bytes()).hexdigest(),
                       facultyPreview=faculty['coverage'], limitation='Non-final candidate faculty plus reviewed lab subset. Full source queue, identity review and final export are still required.')
    filename = 'faculty-assembly-preview-20261016.json' if faculty else 'identity-merge-preview-20261016.json'
    receipt_path = args.receipt or ROOT / 'docs/operations' / filename
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt['reviewedPreview']))
    raise SystemExit(0 if preservation['status'] == 'passed' and repeated == assembled and not duplicate_urls and not duplicate_ids else 1)


if __name__ == '__main__':
    main()
