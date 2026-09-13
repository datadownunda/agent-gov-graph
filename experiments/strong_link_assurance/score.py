"""Scoring-only event history joins. Never imported by the decision worker."""
from collections import Counter, defaultdict


def ratio(a, b):
    return a / b if b else None


def score(output, truth):
    if output.get('status') == 'INTERNAL_ERROR':
        return {'counts': {'internal_errors': 1}, 'rates': {}, 'scope_question': 'NOT EVALUABLE'}
    addresses = {r['evidence_ref']: f"{r['role']}:{r['location']['line'] - 1}" for r in output['records']}
    records = {addresses[r['evidence_ref']]: r for r in output['records']}
    true_edges = {tuple(pair) for pair in truth['true_edges']}
    covered = {tuple(pair) for pair in truth['covered']}
    edges, citations = set(), {}
    order = {'governance': 0, 'execution': 1, 'outcome': 2}
    for bundle in output['correlations']:
        for assertion in bundle['assertions']:
            if assertion['result']['state'] != 'LINKED':
                continue
            refs = [assertion['focus']['evidence_ref'], assertion['result']['linked_evidence'][0]['evidence_ref']]
            pair = tuple(sorted((addresses[r] for r in refs), key=lambda a: order[a.split(':')[0]]))
            edges.add(pair)
            citations[pair] = assertion['assertion_id']
    correct = edges & true_edges
    observed_true = {pair for pair in true_edges if all(a in records for a in pair)}
    parent = {a: a for a in records}

    def root(a):
        while parent[a] != a:
            a = parent[a]
        return a

    for a, b in edges:
        parent[root(a)] = root(b)
    components = defaultdict(list)
    for a in records:
        components[root(a)].append(a)
    linked_components = [c for c in components.values() if len(c) > 1]
    merges = [c for c in linked_components if len({truth['attempts'][a] for a in c}) > 1]
    groups = defaultdict(list)
    for a in records:
        groups[truth['attempts'][a]].append(a)
    observable_groups = [v for v in groups.values() if len(v) > 1]
    splits = [v for v in observable_groups if len({root(a) for a in v}) > 1]
    counts = {'accepted_pairs': len(edges), 'correct_pairs': len(correct),
              'false_links': len(edges - true_edges), 'true_pairs': len(true_edges),
              'observable_true_pairs': len(observed_true), 'linked_components': len(linked_components),
              'false_merges': len(merges), 'observable_attempt_groups': len(observable_groups),
              'false_splits': len(splits), 'applicable': 0, 'assurance_abstentions': 0,
              'not_applicable': 0, 'internal_errors': 0, 'unsupported_evaluations': 0,
              'false_effective': 0, 'false_exception': 0, 'substantive_findings': 0,
              'scope_acceptances': 0, 'correct_scope_acceptances': 0, 'scope_overreach': 0,
              'true_observable_scope': len(covered), 'correctly_linked_scope_uses': 0,
              'correct_link_scope_not_established': 0, 'correctly_linked_executions': 0,
              'scope_unassessed_executions': 0, 'sidecar_scope_acceptances': 0,
              'scope_ambiguous_or_unsupported': 0, 'scope_nonabstentions': 0}
    scope_details = {(addresses[d['governance_ref']], addresses[d['execution_ref']]): d
                     for d in output['scope_diagnostics']}
    used = set()
    witnesses = []
    primary = []
    # Three original governance focuses; the bounded view replaces the unbounded
    # blocked view. Execution-withheld remains saved as a separate coverage probe.
    for name in ('allow', 'critical-deny', 'blocked-bounded'):
        view = output['reconciliation'][name]
        wrapped = output['attestations'][view['assertion_id']]
        a = wrapped['attestation']
        gov = addresses[view['governance_ref']]
        state, finding = a['evaluation_status'], a['finding']
        primary.append({'governance': gov, 'evaluation_status': state, 'finding': finding,
                        'reconciliation_result': view['result'], 'basis_codes': a['basis_codes']})
        if state == 'INTERNAL_ERROR' or wrapped['receipt']['status'] == 'INTERNAL_ERROR':
            counts['internal_errors'] += 1
            continue
        if state == 'NOT_APPLICABLE' or records[gov]['governance_decision'] == 'ALLOW':
            counts['not_applicable'] += 1
            continue
        counts['applicable'] += 1
        if finding not in ('CONTROL_EFFECTIVE', 'CONTROL_EFFECTIVENESS_EXCEPTION'):
            counts['assurance_abstentions'] += 1
            continue
        counts['substantive_findings'] += 1
        outcomes = [addresses[r['evidence_ref']] for r in view['claims']['outcome']]
        if finding == 'CONTROL_EFFECTIVENESS_EXCEPTION':
            correct_effect = any(truth['attempts'][x] == truth['attempts'][gov] for x in outcomes)
            if not correct_effect:
                counts['false_exception'] += 1
                witnesses.append({'kind': 'FALSE_EXCEPTION', 'governance': gov,
                                  'outcomes': outcomes, 'attestation_id': a['assertion_id'],
                                  'correlation_paths': view['correlation_paths']})
            for execution in view['claims']['execution']:
                pair = (gov, addresses[execution['evidence_ref']])
                used.add(pair)
                established = scope_details[pair]['state'] == 'LINKAGE_DEFENSIBLE_SCOPE_ESTABLISHED'
                if pair in correct and not established:
                    witnesses.append({'kind': 'CORRECT_LINK_SCOPE_NOT_ESTABLISHED', 'pair': list(pair),
                                      'attestation_id': a['assertion_id'],
                                      'supporting_assertion_id': citations.get(pair),
                                      'truth_coverage': 'COVERED' if pair in covered else 'NOT_COVERED',
                                      'diagnostic_state': scope_details[pair]['state']})
        else:
            from src.authority_resolver import instant
            interval = a['scope']['observation_interval']
            effects = [r for address, r in records.items() if r['role'] == 'outcome'
                       and truth['attempts'][address] == truth['attempts'][gov]
                       and instant(interval['start']) <= instant(r['observed_at']) <= instant(interval['end'])]
            adequate = wrapped['receipt']['coverage_assessment']['result'] == 'ADEQUATE'
            if effects or not adequate:
                counts['false_effective'] += 1
                witnesses.append({'kind': 'FALSE_EFFECTIVE', 'attestation_id': a['assertion_id']})
    # Production reliance and diagnostic acceptance are separate, not conflated.
    counts['scope_acceptances'] = len(used)
    counts['correct_scope_acceptances'] = len(used & covered)
    counts['scope_overreach'] = len(used - covered)
    counts['correctly_linked_scope_uses'] = len(used & correct)
    counts['correct_link_scope_not_established'] = sum(
        pair in correct and scope_details[pair]['state'] != 'LINKAGE_DEFENSIBLE_SCOPE_ESTABLISHED' for pair in used)
    correct_ge = {pair for pair in correct if pair[0].startswith('governance:')}
    counts['correctly_linked_executions'] = len(correct_ge)
    counts['scope_unassessed_executions'] = len(correct_ge - used)
    for pair, d in scope_details.items():
        counts['sidecar_scope_acceptances'] += int(d['coverage_accepted'])
        unknown = d['state'] in ('LINKAGE_CORRECT_SCOPE_NOT_ESTABLISHED', 'LINKAGE_UNRESOLVED', 'NOT_EVALUABLE')
        counts['scope_ambiguous_or_unsupported'] += int(unknown)
        counts['scope_nonabstentions'] += int(unknown and pair in used)
    if output['parent_probe']:
        counts['unsupported_evaluations'] += 1
    pair_results = [
        {'pair': list(pair), 'correct': pair in true_edges, 'assertion_id': citations[pair]}
        for pair in sorted(edges)
    ]
    per_edge = {}
    for role in ('governance', 'execution'):
        selected = {p for p in edges if p[0].startswith(role + ':')}
        required = {p for p in true_edges if p[0].startswith(role + ':') or role == 'execution' and p[0].startswith('absent:execution')}
        per_edge[role + ('-execution' if role == 'governance' else '-outcome')] = {
            'accepted': len(selected), 'correct': len(selected & true_edges), 'true': len(required),
            'precision': ratio(len(selected & true_edges), len(selected)),
            'recall': ratio(len(selected & true_edges), len(required))}
    focus_result = next(p for p in primary if p['governance'] == truth['focus'])
    return {'counts': counts, 'rates': rates(counts), 'pair_results': pair_results,
            'components': list(components.values()), 'false_merge_components': merges,
            'false_split_groups': splits, 'per_edge': per_edge, 'primary': primary,
            'scope_assessments': [{'pair': list(pair), 'assessment': d, 'truth_covered': pair in covered,
                                   'production_relied_on_scope': pair in used} for pair, d in scope_details.items()],
            'witnesses': witnesses, 'focus_finding': focus_result['finding'],
            'scope_question': 'YES' if counts['correct_link_scope_not_established'] else 'NO IN THE EVALUATED CASES'}


def rates(c):
    return {'precision': ratio(c['correct_pairs'], c['accepted_pairs']),
            'recall': ratio(c['correct_pairs'], c['true_pairs']),
            'observable_recall': ratio(c['correct_pairs'], c['observable_true_pairs']),
            'false_link_rate': ratio(c['false_links'], c['accepted_pairs']),
            'false_merge_rate': ratio(c['false_merges'], c['linked_components']),
            'false_split_rate': ratio(c['false_splits'], c['observable_attempt_groups']),
            'assurance_abstention_rate': ratio(c['assurance_abstentions'], c['applicable']),
            'governed_scope_precision': ratio(c['correct_scope_acceptances'], c['scope_acceptances']),
            'governed_scope_recall': ratio(c['correct_scope_acceptances'], c['true_observable_scope']),
            'unsupported_scope_abstention_rate': ratio(c['scope_ambiguous_or_unsupported'] - c['scope_nonabstentions'], c['scope_ambiguous_or_unsupported'])}


def summarize(results, truths, indistinguishable):
    total = Counter()
    classes = {}
    for key, result in results.items():
        total.update(result['counts'])
        family = truths[key]['family']
        classes.setdefault(family, Counter()).update(result['counts'])
    invariant = True
    for family in classes:
        variants = {t['variant'] for t in truths.values() if t['family'] == family}
        for variant in variants:
            cohort = [r for key, r in results.items() if truths[key]['family'] == family and truths[key]['variant'] == variant]
            signatures = [(r['counts'], r.get('focus_finding'), sorted((p['evaluation_status'], p['finding'], p['reconciliation_result'], tuple(p['basis_codes'])) for p in r.get('primary', []))) for r in cohort]
            invariant &= all(s == signatures[0] for s in signatures)
    controls = [r for key, r in results.items() if truths[key]['family'] == 'controls']
    control_findings = all(r.get('focus_finding') == truths[key]['expected_control'] for key, r in results.items() if truths[key]['family'] == 'controls')
    nonvacuity = control_findings and all(r['counts']['false_links'] == 0 and r['counts']['false_splits'] == 0 and r['counts']['correct_pairs'] == r['counts']['observable_true_pairs'] for r in controls)
    breaches = {key: total[key] for key in ('false_links', 'false_merges', 'false_effective', 'false_exception', 'scope_overreach', 'scope_nonabstentions', 'correct_link_scope_not_established') if total[key]}
    valid = invariant and indistinguishable and total['internal_errors'] == 0
    verdict = 'INVALID_EXPERIMENT' if not valid else 'FAILED' if breaches else 'CLAIM_NOT_DEMONSTRATED' if not nonvacuity else 'TESTED_SAFETY_BOUNDARY_SUPPORTED'
    return {'verdict': verdict, 'counts': dict(total), 'rates': rates(total),
            'by_class': {k: {'counts': dict(v), 'rates': rates(v)} for k, v in classes.items()},
            'breaches': breaches, 'presentation_invariant': invariant,
            'indistinguishable_pair_outputs_equal': indistinguishable,
            'nonvacuity': nonvacuity,
            'critical_question': 'Did any correctly linked execution inherit governance coverage that was not actually established?',
            'critical_answer': 'NOT EVALUABLE' if total['internal_errors'] else 'YES' if total['correct_link_scope_not_established'] else 'NO IN THE EVALUATED CASES',
            'scope_count_distinction': 'Scope overreach counts false/unspecified event-history coverage. Correct-link scope-not-established counts actual M7 reliance where the independent evidence-only diagnostic cannot establish scope; it does not assert ground-truth noncoverage.',
            'limit': 'Deterministic synthetic evidence; no enterprise error frequency or independently authenticated namespace/non-reuse/scope claim. Fan-out assurance remains undemonstrated where scope is not established.'}
