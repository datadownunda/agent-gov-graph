"""Separate M7 v2 conformance replay. Frozen scenarios/scorer remain unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from experiments.strong_link_assurance.run_experiment import inventory, write
from experiments.strong_link_assurance.score import score

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / 'experiments/strong_link_assurance/results/v4'
BASELINE = 'b8093786311fb2bd3a7c6ef45faefe5d64c69852'


def historical_checkout(destination):
    """Reconstruct all 4,516 original files, including exact pre-patch source bytes.

    Works in shallow CI checkouts without network access or weakened inventories.
    """
    inventory_path=ROOT/'experiments/m7_scope_gate/validation/pre-patch-inventory.json'
    if hashlib.sha256(inventory_path.read_bytes()).hexdigest() != "f5e3393babcb80664b5bb4f1701aae028bd51aa8047a7ae1ef849b7cd5b16521":
        raise ValueError('Historical whole-checkout inventory changed')
    original=json.loads(inventory_path.read_text())
    fixture=json.loads((ROOT/'tests/fixtures/m7_scope_gate/b809378-sources.json').read_text())
    if original['head'] != BASELINE or fixture['commit'] != BASELINE:
        raise ValueError('Historical commit changed')
    if not set(fixture['original_sources']) <= set(original['files']):
        raise ValueError('Unexpected historical source fixture')
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=False)
    for name,expected in original['files'].items():
        data=(fixture['original_sources'][name].encode() if name in fixture['original_sources']
              else (ROOT/name).read_bytes())
        if hashlib.sha256(data).hexdigest()!=expected:
            raise ValueError('Historical file changed: '+name)
        path=destination/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    return destination


def worker(evidence, archive):
    # Frozen worker accepts evidence only. Its unchanged M6 output is preserved.
    from experiments.strong_link_assurance.worker import evaluate
    from src.control_attestation import attest
    output = evaluate(evidence, archive)
    # Preserve the original observations exactly, bound by the archive manifest.
    # No issuer or new scope is supplied by this transport adapter.
    write(archive / 'namespace_observations.json', evidence['namespace_observations'])
    manifest = json.loads((archive / 'manifest.json').read_text())
    manifest['files'] = inventory(archive)
    write(archive / 'manifest.json', manifest)
    control = json.loads((ROOT / 'experiments/control_attestation/control.json').read_text())
    for name, view in output['reconciliation'].items():
        a, receipt = attest(archive, view['assertion_id'], control,
                            coverage_support='coverage_observations.json' if name == 'blocked-bounded' else None)
        output['attestations'][view['assertion_id']] = {'attestation': a, 'receipt': receipt}
    return output


def run_worker(evidence, archive):
    completed = subprocess.run([sys.executable, '-B', '-m', 'experiments.m7_scope_gate.run_conformance', 'worker', str(archive)],
                               input=json.dumps(evidence, sort_keys=True), text=True, capture_output=True, cwd=ROOT, check=True)
    return json.loads(completed.stdout), completed.stderr


def comparison(outputs, metrics, old, truths):
    rows = []
    for key, result in metrics.items():
        before = old['cases'][key]
        changes = []
        for b, a in zip(before['primary'], result['primary']):
            if b['finding'] != a['finding']:
                changes.append({'before': b, 'after': a})
        codes = [p['basis_codes'] for p in result['primary'] if p['evaluation_status'] == 'INSUFFICIENT_EVIDENCE']
        rows.append(dict(evaluation_id=key, scenario=truths[key]['family']+'/'+truths[key]['variant'],
            presentation=truths[key]['presentation'], false_exceptions_before=before['counts']['false_exception'],
            false_exceptions_after=result['counts']['false_exception'], changes=changes,
            scope_abstentions=sum('GOVERNANCE_SCOPE_NOT_ESTABLISHED' in c for c in codes),
            namespace_abstentions=sum(any(x.startswith('NATIVE_IDENTIFIER_NAMESPACE_') for x in c) for c in codes),
            legitimate_exception_lost=(before['counts']['false_exception'] == 0 and any(c['before']['finding'] == 'CONTROL_EFFECTIVENESS_EXCEPTION' and c['after']['finding'] == 'CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED' for c in changes))))
    return {'campaign_kind': 'POST_PATCH_REGRESSION_CONFORMANCE', 'historical_result': 'FAILED',
        'false_exceptions_before':sum(r['false_exceptions_before'] for r in rows),
        'false_exceptions_after':sum(r['false_exceptions_after'] for r in rows),
        'previously_false_now_abstaining':[r['evaluation_id'] for r in rows if r['false_exceptions_before'] and not r['false_exceptions_after'] and r['changes']],
        'legitimate_exception_evaluations_lost':[r['evaluation_id'] for r in rows if r['legitimate_exception_lost']],
        'scope_abstentions':sum(r['scope_abstentions'] for r in rows),
        'namespace_abstentions':sum(r['namespace_abstentions'] for r in rows),
        'unchanged_false_links':sum(m['counts']['false_links'] for m in metrics.values()),
        'unchanged_false_merges':sum(m['counts']['false_merges'] for m in metrics.values()),
        'internal_errors':sum(m['counts']['internal_errors'] for m in metrics.values()),
        'cases':rows}


def report(c):
    return '\n'.join(['# M7 v2 regression/conformance campaign', '',
        'This is not the preregistered experiment. Historical strong-link result remains FAILED.', '',
        f"False substantive exceptions: {c['false_exceptions_before']} → {c['false_exceptions_after']}.",
        f"Previously false evaluations now abstaining: {c['previously_false_now_abstaining']}.",
        f"Legitimate exception evaluations lost to abstention: {c['legitimate_exception_evaluations_lost']}.",
        f"Scope-related abstentions: {c['scope_abstentions']}; namespace-related abstentions: {c['namespace_abstentions']}. Counts may overlap.",
        f"False links remain {c['unchanged_false_links']}; false merges remain {c['unchanged_false_merges']}; internal errors: {c['internal_errors']}.", '',
        'All 26 base cases and three presentations use byte-identical saved decision inputs and scorer truth. M6 correlations and reconciliation remain unchanged.',
        'Missing producer issuer/namespace declarations are not invented. Namespace observations are transported unchanged into the manifest-covered archive. Qualification is a declaration check, not independent authentication or evidence of producer enforcement.',
        'Losses to abstention are new failures to demonstrate legitimate exceptions, not findings that the controls were effective. The positive CONTROL_EFFECTIVE gate is unchanged.',
        'Nine input-identical false-exception evaluations remain informationally irreducible. Conservative namespace abstention suppresses their legitimate counterparts too. No improved discrimination, provenance authentication, or repair of the historical FAILED milestone is claimed.', '',
        'See comparison.json for every before/after finding and structured abstention basis.', ''])


def run(directory):
    directory.mkdir(parents=True, exist_ok=False)
    dependencies = [*sorted((ROOT/'src').glob('*.py')),
                    *sorted((ROOT/'schemas').glob('*.json')),
                    *sorted((ROOT/'experiments/strong_link_assurance').glob('*.py')),
                    *sorted((ROOT/'experiments/m7_scope_gate').glob('*.py')),
                    ROOT/'experiments/control_attestation/run_experiment.py',
                    ROOT/'experiments/target_outcome/run_experiment.py']
    lock = {'base_commit':BASELINE, 'campaign_kind':'POST_PATCH_REGRESSION_CONFORMANCE',
            'files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dependencies}}
    write(directory/'execution-lock.json',lock)
    inputs = json.loads((FROZEN / 'decision-inputs.json').read_text())
    truths = json.loads((FROZEN / 'scorer-only-truth.json').read_text())
    old_outputs = json.loads((FROZEN / 'decisions.json').read_text())
    outputs, metrics = {}, {}
    for key, evidence in inputs.items():
        output, stderr = run_worker(evidence, directory / 'archives' / key)
        if stderr:
            (directory / f'worker-{key}.log').write_text(stderr)
        for field in ('records', 'correlations', 'reconciliation', 'verification', 'scope_diagnostics', 'namespace_probe', 'parent_probe'):
            assert output[field] == old_outputs[key][field], (key, field)
        outputs[key] = output
        print(key + ' completed', file=sys.stderr, flush=True)
    for key in outputs:
        metrics[key] = score(outputs[key], truths[key])
    for name in ('decision-inputs.json', 'scorer-only-truth.json'):
        (directory/name).write_bytes((FROZEN/name).read_bytes())
    write(directory/'decisions.json', outputs)
    write(directory/'metrics.json', {'cases':metrics})
    c = comparison(outputs, metrics, json.loads((FROZEN/'metrics.json').read_text()), truths)
    write(directory/'comparison.json',c)
    (directory/'REPORT.md').write_text(report(c))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == h for p,h in lock['files'].items())
    write(directory/'manifest.json', {'files':inventory(directory), 'campaign_kind':c['campaign_kind']})
    return {k:v for k,v in c.items() if k != 'cases'}


def audit(directory):
    assert json.loads((directory/'manifest.json').read_text())['files'] == inventory(directory)
    lock=json.loads((directory/'execution-lock.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in lock['files'].items())
    inputs=json.loads((directory/'decision-inputs.json').read_text())
    outputs=json.loads((directory/'decisions.json').read_text())
    truths=json.loads((directory/'scorer-only-truth.json').read_text())
    for name in ('decision-inputs.json','scorer-only-truth.json'):
        assert (directory/name).read_bytes() == (FROZEN/name).read_bytes()
    with tempfile.TemporaryDirectory() as temporary:
        for key,evidence in inputs.items():
            replay, stderr=run_worker(evidence,Path(temporary)/key)
            assert replay == outputs[key], (key,stderr)
    metrics={k:score(v,truths[k]) for k,v in outputs.items()}
    assert {'cases':metrics} == json.loads((directory/'metrics.json').read_text())
    c=comparison(outputs,metrics,json.loads((FROZEN/'metrics.json').read_text()),truths)
    assert c == json.loads((directory/'comparison.json').read_text())
    assert report(c) == (directory/'REPORT.md').read_text()
    return {'status':'VERIFIED','evaluations':len(inputs)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['worker','run','audit','historical-checkout'])
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    if args.command == 'worker':
        result=worker(json.load(sys.stdin),args.directory)
    elif args.command == 'historical-checkout':
        result={'root':str(historical_checkout(args.directory))}
    else:
        result=globals()[args.command](args.directory)
    print(json.dumps(result,sort_keys=True))
