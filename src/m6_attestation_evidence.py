"""M7 read-only verification adapter for the preserved complaint M6 archive format.

The adapter reuses M6 replay. It neither discovers links nor changes M6 results.
The returned receipt is a local content-identified computation, not a signature.
"""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import jsonschema

from experiments.target_outcome.run_experiment import audit, derive
from src.authority_resolver import instant
from src.evidence_digest import evidence_digest

RULE = 'm6-attestation-verification/1'
ROOT = Path(__file__).resolve().parents[1]


def validate_control(control):
    schema = json.loads((ROOT / 'schemas/control_definition.schema.json').read_text())
    jsonschema.validate(control, schema)
    seconds = Decimal(control['coverage_requirement']['post_decision_seconds'])
    if not seconds.is_finite() or seconds <= 0:
        raise ValueError('Invalid bounded observation horizon')


def _file_digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def _member(root, name):
    path = (root / name).resolve()
    path.relative_to(root.resolve())
    return path


def _coverage(control, assertion, support, contract_digest):
    """Specific to DENY preventing representation serving at this static target."""
    coverage = assertion['evidence_coverage']
    assessment = {'control_digest':evidence_digest(control), 'result':'UNKNOWN',
                  'basis_codes':[], 'interval':None, 'support_ref':evidence_digest(support) if support else None,
                  'coverage_ref':evidence_digest(coverage) if coverage else None}
    codes = assessment['basis_codes']
    if not coverage:
        codes.append('TARGET_COVERAGE_UNKNOWN')
        return assessment
    assessment['interval'] = {'start':coverage['interval_start'], 'end':coverage['interval_end']}
    g = assertion['claims']['governance'][0]
    inadequate = False
    try:
        start, end, decision = instant(coverage['interval_start']), instant(coverage['interval_end']), instant(g['observed_at'])
        horizon = Decimal(control['coverage_requirement']['post_decision_seconds'])
        if start > decision or end < decision + horizon:
            codes.append('CONTROL_OBSERVATION_HORIZON_INADEQUATE')
            inadequate = True
        if coverage['roles'].get('outcome') != 'CAPTURED':
            codes.append('TARGET_CAPTURE_UNAVAILABLE')
            inadequate = True
        if coverage['scope'] != {key:g[key] for key in ('actor','action','resource_id','resource_type')}:
            codes.append('CONTROL_SCOPE_MISMATCH')
            inadequate = True
        if not support:
            codes.extend(['CAPTURE_FINALIZATION_NOT_SUBSTANTIATED', 'CLOCK_ASSUMPTIONS_NOT_SUBSTANTIATED'])
        else:
            expected = {'action':g['action'], 'resource_id':g['resource_id'], 'resource_type':g['resource_type']}
            if (support['control_digest'] != evidence_digest(control)
                    or support['reconciliation_ref'] != assertion['assertion_id']
                    or support['target_contract_digest'] != contract_digest
                    or support['target_id'] != control['prohibited_target_effect']['target_id']
                    or support['scope'] != expected or support['identity_scope'] != 'ALL_TARGET_IDENTITIES'):
                codes.append('CONTROL_COVERAGE_BINDING_MISMATCH')
                inadequate = True
            offset = Decimal(support['clocks']['maximum_offset_seconds'])
            if not offset.is_finite() or offset < 0 or not support['clocks']['basis']:
                raise ValueError('Unsubstantiated clock bound')
            capture = support['capture']
            # Bounds apply to capture, including possible clock offset. No timestamp
            # adjustment is supplied to a correlator or to M6.
            if (capture['available'] is not True or capture['finalized'] is not True
                    or instant(capture['from']) > start - offset
                    or instant(capture['through']) < end + offset
                    or instant(capture['finalized_at']) < instant(capture['through'])):
                codes.append('TARGET_CAPTURE_INTERVAL_OR_FINALIZATION_INADEQUATE')
                inadequate = True
            if support['unresolved_gaps'] is not False or support['candidate_ambiguity'] is not False:
                codes.append('UNRESOLVED_OBSERVATION_GAPS_OR_CANDIDATES')
                inadequate = True
            if not codes:
                codes.append('BOUNDED_TARGET_COVERAGE_ADEQUATE')
                assessment['result'] = 'ADEQUATE'
    except (KeyError, TypeError, ValueError, ArithmeticError):
        codes.append('CONTROL_COVERAGE_SUPPORT_INSUFFICIENT')
    if inadequate:
        assessment['result'] = 'INADEQUATE'
    assessment['basis_codes'] = sorted(set(codes))
    return assessment


def _project(assertion, control, target, target_verified):
    """Only allowlisted M6 fields. No raw data, run IDs, filenames or prose labels."""
    governors = assertion['claims']['governance']
    if len(governors) != 1:
        raise ValueError('Exactly one governed action is required')
    g = governors[0]
    governance = {key:deepcopy(g[key]) for key in ('evidence_ref','actor','action','resource_id','resource_type','observed_at')}
    governance['decision'] = g['governance_decision']
    connected = {g['evidence_ref'], *[p['evidence_ref'] for p in assertion['correlation_paths']]}
    ambiguous = any(a['focus']['evidence_ref'] in connected and a['result']['state'] in
                    ('AMBIGUOUS','CONTRADICTED','INSUFFICIENT_EVIDENCE')
                    for a in assertion['correlation_assertions'])
    linked_ids = {a['assertion_id'] for a in assertion['correlation_assertions'] if a['result']['state']=='LINKED'}
    paths = {p['evidence_ref']:p['assertion_ids'] for p in assertion['correlation_paths']}
    effect_refs, correlation_refs = [], set()
    for outcome in assertion['claims']['outcome']:
        path = paths.get(outcome['evidence_ref'], [])
        if (outcome.get('target_outcome') == 'REPRESENTATION_SERVED'
                and all(outcome.get(f) == g.get(f) for f in ('action','resource_id','resource_type'))
                and outcome.get('target_contract_digest') == evidence_digest(target)
                and path and set(path) <= linked_ids and not outcome.get('defects')):
            effect_refs.append(outcome['evidence_ref'])
            correlation_refs.update(path)
    benign_absence = {'CONSISTENT_WITH_BLOCKING','CORRELATION_UNMATCHED',
                      'EXECUTION_EVIDENCE_MISSING','OUTCOME_EVIDENCE_MISSING'}
    uncertainty = (assertion['result'] != 'CONSISTENT'
                   or bool(set(assertion['issue_codes']) - benign_absence))
    return {'governance':governance, 'reconciliation_result':assertion['result'],
            'consistent_with_blocking':'CONSISTENT_WITH_BLOCKING' in assertion['issue_codes'],
            'target_contract_verified':target_verified,
            'prohibited_effect_established':bool(effect_refs),
            'relevant_correlation_ambiguous':ambiguous,
            'undermining_uncertainty':uncertainty,
            'supporting_effect_refs':sorted(effect_refs),
            'supporting_correlation_refs':sorted(correlation_refs),
            'source_refs':sorted(r['evidence_ref'] for r in assertion['source_evidence'])}


def verify_m6(archive, assertion_id, control, *, coverage_support=None):
    """Verify a stored assertion by opaque ID against the unchanged M6 adapter.

    coverage_support is an optional archive member containing affirmative,
    control-specific observations; it is never an instruction to mark adequate.
    The archive layout is intentionally limited to the existing complaint M6
    format. Unavailable or unsupported evidence is not guessed into a new path.
    """
    receipt = {'schema_version':'1.0', 'rule_version':RULE, 'status':'EVIDENCE_DEFECT',
               'control_digest':evidence_digest(control), 'reconciliation_ref':assertion_id,
               'archive_digest':None, 'facts':None, 'coverage_assessment':None,
               'basis_codes':[], 'dependency_refs':[],
               'limitations':['Archive and receipt digests identify content; they do not authenticate producers.',
                              'Coverage observations remain evidence subject to their stated provenance and clock assumptions.']}
    try:
        validate_control(control)
        root = Path(archive).resolve()
        manifest = json.loads((root / 'manifest.json').read_text())
        receipt['archive_digest'] = evidence_digest(manifest)
        # Precheck failures without disclosing file/scenario labels to adjudication.
        for member, digest in manifest['files'].items():
            if _file_digest(_member(root, member)) != digest:
                raise ValueError('Archive integrity defect')
        audit(root)  # Existing M6 source ingestion, correlation and reconstruction.
        _, _, replayed = derive(root)
        matches = [a for a in replayed.values() if a['assertion_id'] == assertion_id]
        if len(matches) != 1:
            raise ValueError('Stored assertion is missing or not uniquely replayable')
        assertion = matches[0]
        body = {k:v for k,v in assertion.items() if k != 'assertion_id'}
        if evidence_digest(body) != assertion_id:
            raise ValueError('M6 digest mismatch')
        target = json.loads((root / 'target.json').read_text())
        runtime = json.loads((root / 'target_runtime.json').read_text())
        # The interpretation is pinned to the inspected M6 static target config.
        known_config = ROOT / 'experiments/target_outcome/nginx.conf'
        target_verified = (target.get('target_id') == control['prohibited_target_effect']['target_id']
                           and evidence_digest(target) == control['prohibited_target_effect']['target_contract_digest']
                           and runtime['config_digest'] == _file_digest(root / 'nginx.conf') == _file_digest(known_config)
                           and target.get('basic_auth_required') is True)
        support = None
        if coverage_support is not None:
            if coverage_support not in manifest['files']:
                raise ValueError('Coverage support is not preserved')
            support = json.loads(_member(root, coverage_support).read_text())
            if support['capture']['native_file_digest'] != manifest['files']['native/access.jsonl']:
                raise ValueError('Coverage describes a different target snapshot')
        facts = _project(assertion, control, target, target_verified)
        assessment = _coverage(control, assertion, support, evidence_digest(target))
        receipt.update(status='VERIFIED', facts=facts, coverage_assessment=assessment,
                       dependency_refs=sorted(set(manifest['files'].values())))
    except FileNotFoundError:
        receipt.update(status='INSUFFICIENT_EVIDENCE', basis_codes=['REFERENCED_EVIDENCE_UNAVAILABLE'])
    except (OSError, ValueError, TypeError, KeyError, IndexError, ArithmeticError, jsonschema.ValidationError):
        receipt.update(status='EVIDENCE_DEFECT', basis_codes=['REFERENCED_EVIDENCE_OR_CONTROL_INTEGRITY_DEFECT'])
    receipt['receipt_id'] = evidence_digest(receipt)
    return receipt
