"""Fixed single-action control adjudication. No source matching or enforcement."""
from copy import deepcopy
import json
from pathlib import Path

import jsonschema

from src.evidence_digest import evidence_digest
from src.m6_attestation_evidence import validate_control, verify_m6

ROOT = Path(__file__).resolve().parents[1]
RULE = 'control-attestation/1'
FACT_FIELDS = {'governance','reconciliation_result','consistent_with_blocking','target_contract_verified',
               'prohibited_effect_established','relevant_correlation_ambiguous','undermining_uncertainty',
               'supporting_effect_refs','supporting_correlation_refs','source_refs'}
LIMITATIONS = [
    'This finding concerns exactly one evaluated reconciliation/action and its declared observation boundary; no population-wide inference.',
    'REPRESENTATION_SERVED means the configured target reports serving representation bytes; it does not establish downstream consumption, interpretation or use.',
    'A target-effect exception is not root-cause attribution and makes no claim about why the effect occurred.',
    'A positive finding is conditional on the specific observation interval, capture evidence and clock bounds, not unlimited future prevention.',
    'Content identity and deterministic replay are not cryptographic provenance authentication.',
]


def validate_attestation(assertion):
    schema = json.loads((ROOT / 'schemas/control_attestation.schema.json').read_text())
    jsonschema.validate(assertion, schema, format_checker=jsonschema.FormatChecker())
    if assertion['assertion_id'] != evidence_digest({k:v for k,v in assertion.items() if k != 'assertion_id'}):
        raise ValueError('Attestation content identity mismatch')


def adjudicate(control, receipt):
    """Pure rule on a locally verified, allowlisted receipt.

    External callers use attest(), which recomputes verification from the archive.
    A receipt hash is not a signature or a substitute for that verification.
    """
    out = {'schema_version':'1.0','rule_version':RULE,
           'control_reference':{'content_digest':evidence_digest(control)},
           'reconciliation_reference':receipt.get('reconciliation_ref'),
           'verification_reference':receipt.get('receipt_id'),
           'scope':{'cardinality':'SINGLE_ACTION'}, 'source_evidence_refs':[], 'correlation_assertion_refs':[],
           'coverage_assessment':deepcopy(receipt.get('coverage_assessment')),
           'evaluation_status':'NOT_EVALUABLE','finding':None,'basis_codes':[], 'limitations':list(LIMITATIONS)}

    def finish(status, finding, codes):
        out.update(evaluation_status=status, finding=finding, basis_codes=sorted(set(codes)))
        out['assertion_id'] = evidence_digest(out)
        validate_attestation(out)
        return out

    def abstain(codes):
        return finish('INSUFFICIENT_EVIDENCE','CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED',codes)

    try:
        validate_control(control)
        if (receipt['receipt_id'] != evidence_digest({k:v for k,v in receipt.items() if k != 'receipt_id'})
                or receipt['control_digest'] != evidence_digest(control)
                or receipt['rule_version'] != 'm6-attestation-verification/1'):
            raise ValueError('Receipt/control mismatch')
        out['control_reference'].update(control_id=control['control_id'],control_version=control['control_version'])
        if receipt['status'] == 'EVIDENCE_DEFECT':
            return finish('NOT_EVALUABLE',None,receipt['basis_codes'] or ['EVIDENCE_INTEGRITY_DEFECT'])
        if receipt['status'] == 'INSUFFICIENT_EVIDENCE':
            return abstain(receipt['basis_codes'])
        if receipt['status'] != 'VERIFIED':
            raise ValueError('Invalid verification state')
        facts = receipt['facts']
        if set(facts) != FACT_FIELDS:
            raise ValueError('Non-allowlisted adjudication input')
        g = facts['governance']
        if set(g) != {'evidence_ref','decision','actor','action','resource_id','resource_type','observed_at'}:
            raise ValueError('Non-allowlisted governance facts')
        for key in ('consistent_with_blocking','target_contract_verified','prohibited_effect_established',
                    'relevant_correlation_ambiguous','undermining_uncertainty'):
            if type(facts[key]) is not bool:
                raise ValueError('Invalid fact type')
        assessment = receipt['coverage_assessment']
        if assessment['control_digest'] != evidence_digest(control):
            raise ValueError('Coverage/control mismatch')
        out['scope'].update({k:deepcopy(g[k]) for k in ('actor','action','resource_id','resource_type')})
        out['scope'].update(governance_evidence_ref=g['evidence_ref'],
                            target_id=control['prohibited_target_effect']['target_id'],
                            observation_interval=deepcopy(assessment['interval']))
        out['source_evidence_refs'] = deepcopy(facts['source_refs'])
        out['correlation_assertion_refs'] = deepcopy(facts['supporting_correlation_refs'])
        if g['decision'] == 'ALLOW' or any(g[k] != control['scope'][k] for k in ('action','resource_type')):
            return finish('NOT_APPLICABLE',None,['CONTROL_GOVERNANCE_CONDITION_OR_SCOPE_NOT_APPLICABLE'])
        if g['decision'] != 'DENY':
            return abstain(['GOVERNANCE_DENY_NOT_ESTABLISHED'])
        if facts['reconciliation_result'] == 'NOT_EVALUABLE':
            return finish('NOT_EVALUABLE',None,['M6_NOT_EVALUABLE'])
        if not facts['target_contract_verified']:
            return abstain(['TARGET_OBSERVATION_SEMANTICS_NOT_ESTABLISHED'])
        if facts['relevant_correlation_ambiguous']:
            return abstain(['REQUIRED_CORRELATION_UNRESOLVED'])
        # Positive observation and negative coverage deliberately have different gates.
        if facts['prohibited_effect_established']:
            if not facts['supporting_effect_refs'] or not facts['supporting_correlation_refs']:
                return abstain(['TARGET_EFFECT_LINKAGE_NOT_ESTABLISHED'])
            return finish('EVALUATED','CONTROL_EFFECTIVENESS_EXCEPTION',
                          ['DENY_ESTABLISHED','CORRELATED_PROHIBITED_TARGET_EFFECT'])
        if (assessment['result'] == 'ADEQUATE' and facts['consistent_with_blocking']
                and not facts['undermining_uncertainty']):
            return finish('EVALUATED','CONTROL_EFFECTIVE',
                          ['DENY_ESTABLISHED','BOUNDED_TARGET_COVERAGE_ADEQUATE','NO_PROHIBITED_EFFECT_IN_EVALUATED_OBSERVATIONS'])
        return abstain(assessment['basis_codes'] + ['EFFECTIVENESS_GATES_NOT_SATISFIED'])
    except (ValueError, TypeError, KeyError, ArithmeticError, jsonschema.ValidationError):
        return finish('NOT_EVALUABLE',None,['INVALID_CONTROL_OR_VERIFICATION_RECEIPT'])


def attest(archive, assertion_id, control, *, coverage_support=None):
    receipt = verify_m6(archive, assertion_id, control, coverage_support=coverage_support)
    return adjudicate(control, receipt), receipt


def reconstruct_attestation(saved, archive, control, *, coverage_support=None):
    """Replay both verification and adjudication; never trust a saved receipt alone."""
    try:
        validate_attestation(saved)
        expected, receipt = attest(archive, saved['reconciliation_reference'], control, coverage_support=coverage_support)
        if receipt['status'] != 'VERIFIED':
            return {'status':receipt['status'],'basis_codes':receipt['basis_codes']}
        if expected != saved:
            return {'status':'EVIDENCE_DEFECT','basis_codes':['ATTESTATION_REPLAY_DISAGREEMENT']}
        return {'status':'VERIFIED','evaluation_status':expected['evaluation_status'],'finding':expected['finding']}
    except (ValueError, TypeError, KeyError, jsonschema.ValidationError):
        return {'status':'EVIDENCE_DEFECT','basis_codes':['INVALID_ATTESTATION']}
