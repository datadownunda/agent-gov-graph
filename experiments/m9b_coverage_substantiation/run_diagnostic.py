"""Frozen seven-case synthetic public-API diagnostic; never runs native producers.

Run only after implementation freeze. Archive-member support is required by the
public API, so copied manifests are re-inventoried after the sole support change.
Labels and mutation descriptions remain outside attest/adjudication inputs.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from src.control_attestation import attest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/control_attestation/results/v1/deterministic_fixture'
CONTROL = ROOT / 'experiments/control_attestation/control.json'
SUPPORT = 'coverage_observations.json'
BASELINE = '6f765ebe6f5452d8b9ee85bd609771b301bd503f'
RULE = 'control-attestation/2'
UNMEASURED_BASIS = 'No clock offset measurement exists; zero is an unsupported declaration.'
CASES = ('baseline', 'missing_support', 'short_capture', 'identity_scope',
         'snapshot_mismatch', 'unmeasured_clock_basis', 'unresolved_gaps')


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory):
    if directory.is_symlink() or any(p.is_symlink() for p in directory.rglob('*')):
        raise ValueError('Symlinks are forbidden in diagnostic inventories')
    return {p.relative_to(directory).as_posix(): digest(p)
            for p in sorted(directory.rglob('*')) if p.is_file()}


def variant(case, original, decision_time):
    """Return one declared support-field replacement, or request-level omission."""
    support = deepcopy(original)
    changes = {
        'short_capture': (('capture', 'through'), decision_time),
        'identity_scope': (('identity_scope',), 'GOVERNED_ACTOR_ONLY'),
        'snapshot_mismatch': (('capture', 'native_file_digest'), 'sha256:' + '0' * 64),
        'unmeasured_clock_basis': (('clocks', 'basis'), UNMEASURED_BASIS),
        'unresolved_gaps': (('unresolved_gaps',), True),
    }
    if case == 'baseline':
        return support, {'operation': 'none'}
    if case == 'missing_support':
        return None, {'operation': 'omit_support_argument', 'archive_changed': False}
    if case not in changes:
        raise ValueError('Unknown frozen diagnostic case')
    keys, replacement = changes[case]
    parent = support
    for key in keys[:-1]:
        parent = parent[key]
    previous = parent[keys[-1]]
    if previous == replacement:
        raise ValueError('Frozen mutation must change its supplied value')
    parent[keys[-1]] = replacement
    return support, {'operation': 'replace', 'path': '/' + '/'.join(keys),
                     'before': previous, 'after': replacement}


def prepare_case(baseline, directory, case):
    """Copy existing bytes; never manufacture or rederive the original fixture."""
    shutil.copytree(baseline, directory)
    original = json.loads((baseline / SUPPORT).read_text())
    reconciliation = json.loads((baseline / 'reconciliation.json').read_text())
    selected = [a for a in reconciliation.values()
                if a['assertion_id'] == original['reconciliation_ref']]
    if len(selected) != 1:
        raise ValueError('Synthetic positive assertion is not unique')
    decision_time = selected[0]['claims']['governance'][0]['observed_at']
    support, mutation = variant(case, original, decision_time)
    if mutation['operation'] == 'replace':
        write(directory / SUPPORT, support)
        manifest = json.loads((directory / 'manifest.json').read_text())
        manifest['files'][SUPPORT] = digest(directory / SUPPORT)
        write(directory / 'manifest.json', manifest)
    before, after = inventory(baseline), inventory(directory)
    changed = sorted(name for name in before.keys() | after.keys()
                     if before.get(name) != after.get(name))
    expected = sorted([SUPPORT, 'manifest.json']) if mutation['operation'] == 'replace' else []
    if changed != expected:
        raise ValueError('Unexpected archive mutation')
    return {
        'case': case,
        'evidence_kind': 'EXISTING_DETERMINISTIC_SYNTHETIC_FIXTURE',
        'mutation': mutation,
        'changed_archive_members': changed,
        'request': {'archive': f'cases/{case}/archive',
                    'assertion_id': original['reconciliation_ref'],
                    'control': 'control.json', 'coverage_support': SUPPORT if support is not None else None,
                    'rule_version': RULE},
        'archive_hashes': after,
    }


def evaluate(baseline, directory, control):
    rows = []
    for case in CASES:
        case_dir = directory / 'cases' / case
        case_dir.mkdir(parents=True)
        row = prepare_case(baseline, case_dir / 'archive', case)
        write(case_dir / 'request.json', row)
        request = row['request']
        assertion, receipt = attest(case_dir / 'archive', request['assertion_id'], control,
                                    coverage_support=request['coverage_support'],
                                    rule_version=request['rule_version'])
        write(case_dir / 'attestation.json', assertion)
        write(case_dir / 'receipt.json', receipt)
        assessment = receipt.get('coverage_assessment') or {}
        rows.append({'case': case, 'receipt_status': receipt['status'],
                     'evaluation_status': assertion['evaluation_status'],
                     'finding': assertion.get('finding'),
                     'coverage_result': assessment.get('result'),
                     'coverage_basis_codes': assessment.get('basis_codes'),
                     'receipt_basis_codes': receipt['basis_codes']})
    operational_failure = any(row['receipt_status'] == 'INTERNAL_ERROR' or
                              row['evaluation_status'] == 'INTERNAL_ERROR' for row in rows)
    return {'status': 'NOT_EVALUABLE' if operational_failure else 'COMPLETED',
            'evidence_kind': 'EXISTING_DETERMINISTIC_SYNTHETIC_FIXTURE',
            'empirical_coverage_substantiated': False, 'cases': rows}


def execution_lock():
    changed = subprocess.check_output(
        ['git', 'diff', '--name-only', '--diff-filter=DMRTUXB', BASELINE],
        cwd=ROOT, text=True).strip()
    if changed:
        raise ValueError('Protected baseline tracked files changed: ' + changed)
    paths = [Path(__file__).resolve(), ROOT / 'tests/test_m9b_coverage_substantiation.py',
             ROOT / 'experiments/m9b_coverage_substantiation/PROTOCOL.md', CONTROL]
    paths.extend(sorted((ROOT / 'src').rglob('*.py')))
    paths.extend(sorted((ROOT / 'schemas').rglob('*.json')))
    paths.append(ROOT / 'experiments/target_outcome/run_experiment.py')
    return {'baseline_commit': BASELINE,
            'freeze_commit': subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'implementation_hashes': {p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
            'source_archive_hashes': inventory(SOURCE)}


def finish_inventory(directory):
    files = inventory(directory)
    files.pop('manifest.json', None)
    write(directory / 'manifest.json', {'files': files})


def run(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    try:
        return _run(directory)
    except Exception as error:
        write(directory / 'run_status.json', {
            'status': 'NOT_EVALUABLE', 'error_type': type(error).__name__,
            'error': str(error), 'partial_capture': True})
        finish_inventory(directory)
        raise


def _run(directory):
    lock = execution_lock()
    write(directory / 'execution_lock.json', lock)
    before = inventory(SOURCE)
    shutil.copytree(SOURCE, directory / 'baseline_archive')
    shutil.copyfile(CONTROL, directory / 'control.json')
    write(directory / 'source.json', {
        'archive': SOURCE.relative_to(ROOT).as_posix(), 'archive_hashes': before,
        'control': CONTROL.relative_to(ROOT).as_posix(), 'control_hash': digest(CONTROL),
        'limitations': 'Content integrity is not authenticated completeness. All seven cases are synthetic.'})
    summary = evaluate(directory / 'baseline_archive', directory,
                       json.loads((directory / 'control.json').read_text()))
    write(directory / 'summary.json', summary)
    if inventory(SOURCE) != before:
        raise ValueError('Original archive changed during diagnostic')
    write(directory / 'run_status.json', {'status': summary['status']})
    finish_inventory(directory)
    return summary


def audit(directory):
    """Replay from fresh copies, comparing complete output bytes without path edits."""
    directory = Path(directory)
    expected = json.loads((directory / 'manifest.json').read_text())['files']
    actual = inventory(directory)
    actual.pop('manifest.json')
    if actual != expected:
        raise ValueError('Diagnostic inventory changed')
    frozen = json.loads((directory / 'execution_lock.json').read_text())
    current = execution_lock()
    freeze_commit = frozen.pop('freeze_commit')
    current.pop('freeze_commit')
    if frozen != current:
        raise ValueError('Current implementation or source differs from execution freeze')
    if subprocess.run(['git', 'merge-base', '--is-ancestor', freeze_commit, 'HEAD'],
                      cwd=ROOT, capture_output=True).returncode != 0:
        raise ValueError('Execution freeze commit is not an ancestor of current checkout')
    if json.loads((directory / 'run_status.json').read_text())['status'] != 'COMPLETED':
        raise ValueError('Incomplete diagnostic is not replay-verifiable')
    source = json.loads((directory / 'source.json').read_text())
    if (inventory(directory / 'baseline_archive') != source['archive_hashes']
            or digest(directory / 'control.json') != source['control_hash']):
        raise ValueError('Preserved inputs disagree with source inventory')
    with tempfile.TemporaryDirectory(prefix='agg-m9b-replay-') as scratch:
        replay = Path(scratch)
        summary = evaluate(directory / 'baseline_archive', replay,
                           json.loads((directory / 'control.json').read_text()))
        if inventory(replay / 'cases') != inventory(directory / 'cases'):
            raise ValueError('Fresh public-API replay disagrees')
        if summary != json.loads((directory / 'summary.json').read_text()):
            raise ValueError('Replay summary disagrees')
    return {'status': 'VERIFIED', 'case_count': len(CASES),
            'empirical_coverage_substantiated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'audit'])
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps((run if args.command == 'run' else audit)(args.directory), indent=2))


if __name__ == '__main__':
    main()
