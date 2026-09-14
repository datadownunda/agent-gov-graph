"""Read-only v4 link-to-finding accounting; never used as adjudication input."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/strong_link_assurance/results/v4'


def reconcile():
    inputs = json.loads((SOURCE / 'decision-inputs.json').read_text())
    truth = json.loads((SOURCE / 'scorer-only-truth.json').read_text())
    metrics = json.loads((SOURCE / 'metrics.json').read_text())
    controls = [k for k, t in truth.items() if (t['family'], t['variant']) == ('controls', 'deny_effect')]
    ledger = []
    for key, case in metrics['cases'].items():
        if not case['counts']['false_links']:
            continue
        t = truth[key]
        false = [p for p in case['pair_results'] if not p['correct']]
        witnesses = [w for w in case['witnesses'] if w['kind'] == 'FALSE_EXCEPTION']
        for witness in witnesses:
            path_ids = {a for p in witness['correlation_paths'] for a in p['assertion_ids']}
            assert any(p['assertion_id'] in path_ids for p in false)
        full_equal = [c for c in controls if inputs[key] == inputs[c]]
        rows_equal = [c for c in controls if inputs[key]['rows'] == inputs[c]['rows']]
        if full_equal:
            prevention = 'Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.'
        elif t['family'] == 'namespace':
            prevention = 'Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.'
        elif t['variant'] == 'period':
            prevention = 'Timestamp differs, but no declared identifier lifetime makes it invalid. Scope gating cannot selectively reject the false outcome link; new lifetime/non-reuse evidence needed.'
        else:
            prevention = 'Resource difference already prevents a substantive exception; false identity acceptance remains.'
        ledger.append(dict(evaluation_id=key, scenario=t['family']+'/'+t['variant'], presentation=t['presentation'],
            false_links=false, false_merge_components=case['false_merge_components'],
            false_exception_witnesses=witnesses, truth_covered_pairs=t['covered'],
            scope_overreach=case['counts']['scope_overreach'], identical_worker_controls=full_equal,
            identical_source_row_controls=rows_equal, prevention=prevention))
    totals = {name: sum(c['counts'][name] for c in metrics['cases'].values())
              for name in ('false_links', 'false_merges', 'false_exception', 'scope_overreach')}
    assert totals == dict(false_links=21, false_merges=21, false_exception=18, scope_overreach=3)
    assert sum(len(r['false_exception_witnesses']) for r in ledger if r['identical_worker_controls']) == 9
    assert sum(len(r['false_exception_witnesses']) for r in ledger if r['identical_source_row_controls']) == 15
    return dict(source='experiments/strong_link_assurance/results/v4', historical_result='FAILED',
        source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SOURCE.glob('*')) if p.is_file()},
        totals=totals, ledger=ledger)


def render(data):
    lines = ['# Frozen v4 accounting reconciliation', '',
        'Read-only accounting, saved before the M7 v2 patch. Historical result: FAILED.', '',
        '26 base cases have three equivalent presentations (78 evaluations), not independent replications.', '',
        '21 false accepted links produce 21 false merged components and 18 false substantive exceptions. Three replacement evaluations account for all three truth-based scope-overreach acceptances.', '',
        'The claimed 15 indistinguishable cases are identical at the source-row boundary. Only nine are identical at the complete worker-input boundary. Six namespace cases differ in namespace_observations, consumed only by the diagnostic sidecar in v4.', '',
        'Preventability: six of 18 have a distinguishing namespace fact already supplied to the worker, but not passed into the primary M6/M7 verification path. Zero of those six have that namespace fact in the existing primary receipt. Nine of 18 are complete-input-identical to legitimate controls and cannot be selectively rejected by any deterministic code change. The other three differ in time but have no declared identifier lifetime; proximity or an invented timeout is not an admissible fix.', '',
        'The three copied/different false links do not cause false exceptions: the existing target-effect resource check prevents them. Scope truth is satisfied in 15 of the 18 false-exception evaluations; their false link is execution-to-outcome, not governance-to-execution. Namespace/non-reuse/provenance assumptions must not be relabelled as missing governance scope.', '',
        'A blanket missing-declaration abstention may suppress all exceptions including legitimate controls. That is conservative loss of evaluability, not selective repair or authenticated provenance.', '',
        '| Evaluation | Scenario | False edge | Exceptions | G→E truth coverage | Full-input identical control | Source-row identical control |',
        '|---|---|---|---:|---|---|---|']
    for r in data['ledger']:
        lines.append('| '+ ' | '.join([r['evaluation_id'],r['scenario'], '; '.join(' → '.join(p['pair']) for p in r['false_links']),str(len(r['false_exception_witnesses'])),str(r['truth_covered_pairs']),','.join(r['identical_worker_controls']) or 'No',','.join(r['identical_source_row_controls']) or 'No'])+' |')
    for r in data['ledger']:
        lines += ['', '## Evaluation '+r['evaluation_id'], '', r['prevention'], '',
                  'Exact false links, merged components, truth coverage, and contributing exception paths:', '',
                  '```json', json.dumps(r, indent=2, sort_keys=True), '```']
    return '\n'.join(lines)+'\n'


if __name__ == '__main__':
    target = Path(__file__).parent / 'accounting'
    data = reconcile()
    for name, content in [('v4-reconciliation.json',json.dumps(data,indent=2,sort_keys=True)+'\n'), ('v4-reconciliation.md',render(data))]:
        with (target/name).open('x') as f:
            f.write(content)
