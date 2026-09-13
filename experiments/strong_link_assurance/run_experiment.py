"""Frozen runner, isolated worker, scoring-only truth, and read-only replay audit."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from experiments.strong_link_assurance.generate import build, CASES
from experiments.strong_link_assurance.score import score, summarize

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + '\n')


def verify_frozen():
    freeze = json.loads((HERE / 'freeze.json').read_text())
    if digest(HERE / 'PROTOCOL.md') != freeze['protocol_digest']:
        raise ValueError('Frozen protocol changed')
    for name, expected in freeze['tracked_file_hashes'].items():
        if digest(ROOT / name) != expected:
            raise ValueError('Preserved baseline changed: ' + name)
    return freeze


def implementation():
    paths = [p for p in HERE.iterdir() if p.is_file()]
    paths += sorted((ROOT / 'tests').glob('test_strong_link_assurance*.py'))
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}


def run_worker(evidence, archive):
    completed = subprocess.run([sys.executable, '-B', '-m', 'experiments.strong_link_assurance.worker', str(archive)],
                               input=json.dumps(evidence, sort_keys=True), text=True, capture_output=True,
                               cwd=ROOT, check=False)
    if completed.returncode:
        return {'status': 'INTERNAL_ERROR', 'finding': None,
                'basis_codes': ['WORKER_PROCESS_FAILED']}, completed.stderr
    return json.loads(completed.stdout), completed.stderr


def inventory(directory):
    return {p.relative_to(directory).as_posix(): digest(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and p != directory / 'manifest.json'}


def report(summary):
    rows = ['# Strong-Link Assurance Falsification', '',
            '**' + summary['verdict'] + '**', '',
            summary['critical_question'], '', '**' + summary['critical_answer'] + '**', '',
            'Fan-out/governed-action scope is the primary target. Baseline failures were not gated or corrected.', '',
            '| Class | Accepted / wrong | Precision | Recall | False merges | Scope overreach | False M7 findings |',
            '|---|---:|---:|---:|---:|---:|---:|']
    def percent(value):
        return 'undefined' if value is None else f'{value:.2%}'
    for name, values in summary['by_class'].items():
        c, r = values['counts'], values['rates']
        rows.append(f"| {name} | {c['accepted_pairs']} / {c['false_links']} | {percent(r['precision'])} | {percent(r['recall'])} | {c['false_merges']} | {c['scope_overreach']} | {c['false_effective'] + c['false_exception']} |")
    rows += ['', 'All counts pool three equivalent presentations; they are not independent statistical trials.', '',
             summary['scope_count_distinction'], '', summary['limit'], '',
             'The sidecar never accepted coverage: missing execution-specific scope binding remains explicit. Its abstention does not alter baseline attestations. Correctly linked M7 scope reliance with missing supporting scope evidence is separately reported from event-history scope overreach.', '',
             'All unchanged-pipeline outputs are preserved, including all five M6 views and corresponding genuine M7 results per evaluation. Three governance focuses are scored; the bounded view replaces the unbounded blocked view. Parent-context probes remain explicitly unsupported for M7 and do not contribute invented findings.', '',
             'Machine-readable metrics.json contains denominators, per-edge scores, components, scope assessments, witnesses, all rates, and the final preregistered verdict. Operational failures appear separately in validation/debug records.', '']
    return '\n'.join(rows)


def run(directory):
    freeze = verify_frozen()
    directory.mkdir(parents=True, exist_ok=False)
    lock = {'schema_version': '1.0', 'baseline_commit': freeze['baseline_commit'],
            'protocol_digest': freeze['protocol_digest'], 'freeze_digest': digest(HERE / 'freeze.json'),
            'implementation': implementation(), 'started_at': datetime.now(timezone.utc).isoformat()}
    write(directory / 'execution-lock.json', lock)
    (directory / 'PROTOCOL.md').write_bytes((HERE / 'PROTOCOL.md').read_bytes())
    inputs, truths, outputs, metrics = {}, {}, {}, {}
    for family, variants in CASES.items():
        for variant in variants:
            for presentation in ('canonical', 'reversed', 'renamed'):
                key = f'{family}/{variant}/{presentation}'
                evidence, truth = build(family, variant, presentation)
                index = str(len(inputs)).zfill(3)
                inputs[index], truths[index] = evidence, truth
                output, stderr = run_worker(evidence, directory / 'archives' / index)
                outputs[index] = output
                if stderr:
                    (directory / f'operational-debug-{index}.log').write_text(stderr)
                print(f'{index} completed', file=sys.stderr, flush=True)
    # Truth is serialized only after every decision worker has exited.
    write(directory / 'decision-inputs.json', inputs)
    write(directory / 'decisions.json', outputs)
    write(directory / 'scorer-only-truth.json', truths)
    for key, output in outputs.items():
        metrics[key] = score(output, truths[key])
    matching_pair = []
    for presentation in ('canonical', 'reversed', 'renamed'):
        def select(family, variant):
            return next(k for k, t in truths.items() if (t['family'], t['variant'], t['presentation']) == (family, variant, presentation))
        a, b = select('controls', 'deny_effect'), select('copied', 'removed')
        matching_pair.append(inputs[a] == inputs[b] and outputs[a] == outputs[b])
    summary = summarize(metrics, truths, all(matching_pair))
    write(directory / 'metrics.json', {'summary': summary, 'cases': metrics})
    (directory / 'REPORT.md').write_text(report(summary))
    verify_frozen()
    write(directory / 'manifest.json', {'files': inventory(directory), 'content_identity_not_authentication': True})
    return summary


def audit(directory):
    verify_frozen()
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['files'] != inventory(directory):
        raise ValueError('Saved experiment inventory changed')
    lock = json.loads((directory / 'execution-lock.json').read_text())
    if lock['implementation'] != implementation() or lock['freeze_digest'] != digest(HERE / 'freeze.json'):
        raise ValueError('Execution dependencies changed')
    inputs = json.loads((directory / 'decision-inputs.json').read_text())
    outputs = json.loads((directory / 'decisions.json').read_text())
    truths = json.loads((directory / 'scorer-only-truth.json').read_text())
    saved = json.loads((directory / 'metrics.json').read_text())
    import jsonschema
    schema = json.loads((HERE / 'contracts.schema.json').read_text())
    for index, truth in truths.items():
        evidence, expected_truth = build(truth['family'], truth['variant'], truth['presentation'])
        if evidence != inputs[index] or expected_truth != truth:
            raise ValueError('Input/truth regeneration differs')
        with tempfile.TemporaryDirectory() as temporary:
            actual, _ = run_worker(evidence, Path(temporary) / 'archive')
        if actual != outputs[index] or score(actual, truth) != saved['cases'][index]:
            raise ValueError('Replay disagrees')
        if 'scope_diagnostics' in actual:
            jsonschema.Draft202012Validator(schema).validate(actual['scope_diagnostics'])
    repeated = summarize(saved['cases'], truths, all(
        inputs[a] == inputs[b] and outputs[a] == outputs[b]
        for a, ta in truths.items() for b, tb in truths.items()
        if ta['family'] == 'controls' and ta['variant'] == 'deny_effect'
        and tb['family'] == 'copied' and tb['variant'] == 'removed'
        and ta['presentation'] == tb['presentation']))
    if repeated != saved['summary'] or (directory / 'REPORT.md').read_text() != report(repeated):
        raise ValueError('Summary replay disagrees')
    return {'status': 'VERIFIED', 'evaluations': len(inputs), 'verdict': repeated['verdict']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'audit'])
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory) if args.command == 'run' else audit(args.directory), indent=2))


if __name__ == '__main__':
    main()
