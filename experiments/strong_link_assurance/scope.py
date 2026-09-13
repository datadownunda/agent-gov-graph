"""Diagnostic only. No production gates, matching keys or verification receipts."""
from src.correlation_assertion import native_assertions


def assess(records, correlations):
    accepted = set()
    for bundle in correlations:
        for assertion in bundle['assertions']:
            if assertion['result']['state'] == 'LINKED':
                accepted.add(frozenset([assertion['focus']['evidence_ref'],
                                       assertion['result']['linked_evidence'][0]['evidence_ref']]))
    result = []
    for g in (r for r in records if r['role'] == 'governance'):
        for e in (r for r in records if r['role'] == 'execution'):
            linked = frozenset([g['evidence_ref'], e['evidence_ref']]) in accepted
            parent = g['raw'].get('context', {}).get('parent_request_id')
            member = bool(parent and parent == e['raw'].get('parent_request_id'))
            tuple_agrees = all(g.get(k) == e.get(k) for k in ('actor', 'action', 'resource_id', 'resource_type'))
            if not linked and not member:
                status = 'LINKAGE_UNRESOLVED'
            elif not tuple_agrees:
                status = 'LINKAGE_DEFENSIBLE_SCOPE_CONTRADICTED'
            else:
                # Existing evidence does not attest execution-specific cardinality
                # or descendant permission. A copied native value cannot supply it.
                status = 'LINKAGE_CORRECT_SCOPE_NOT_ESTABLISHED'
            result.append({'governance_ref': g['evidence_ref'], 'execution_ref': e['evidence_ref'],
                           'relationship_type': 'TRANSACTION_MEMBERSHIP' if member else 'CONDITIONAL_SAME_ACTION',
                           'state': status, 'coverage_accepted': False,
                           'basis_codes': ['NO_EXECUTION_SPECIFIC_SCOPE_BINDING'] if linked or member else ['NO_DEFENSIBLE_ASSOCIATION'],
                           'limitations': ['Synthetic source declarations do not authenticate identifier issuance or non-reuse.']})
    return result


def namespace_probe(records, observations):
    populations = {'execution': [], 'outcome': []}
    for record in records:
        role = record['role']
        if role not in populations:
            continue
        index = record['location']['line'] - 1
        populations[role].append(dict(record, identifier_namespace=observations[role][index]))
    # No filtering or corrected production linkage: test the existing invariant
    # facility against complete populations and preserve its raw results.
    return native_assertions(populations['execution'], populations['outcome'],
                             identifier_field='request_id', namespace='caller-declared-common',
                             issuer='caller-declared-NGINX', relationship_type='SAME_ATTEMPT',
                             required_equal_fields=['identifier_namespace']) if any(populations.values()) else []


def parent_probe(records):
    from src.action_reconciliation import reconcile
    populations = {'governance': [], 'execution': []}
    augmented = []
    for record in records:
        raw = record['raw']
        parent = raw.get('context', {}).get('parent_request_id') if record['role'] == 'governance' else raw.get('parent_request_id')
        item = dict(record, parent_context=parent)
        augmented.append(item)
        if record['role'] in populations:
            populations[record['role']].append(item)
    if not any(r.get('parent_context') for r in augmented):
        return None
    assertions = native_assertions(populations['governance'], populations['execution'],
        identifier_field='parent_context', namespace='declared-parent-context', issuer='runtime',
        relationship_type='TRANSACTION_MEMBERSHIP')
    bundle = {'roles': {'left': 'governance', 'right': 'execution'}, 'assertions': assertions}
    # Supply E-O assertions as well so full populations remain explicit.
    from experiments.target_outcome.run_experiment import correlate
    bundles = [bundle, correlate(augmented)[1]]
    views = [reconcile(augmented, bundles, governance_ref=g['evidence_ref']) for g in populations['governance']]
    return {'correlations': bundles, 'reconciliation': views,
            'downstream_evaluation': 'UNSUPPORTED_BY_EXISTING_M7_ARCHIVE_ADAPTER',
            'finding': None}
