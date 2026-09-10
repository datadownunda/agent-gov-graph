"""Separate historical custody and current-checkout compatibility verification.

The original M9 runner, tests, protocol and result files remain byte-identical.
No frozen verifier is replaced or relaxed here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / 'experiments/identifier_withholding'
FIXTURE = ROOT / 'tests/fixtures/identifier_withholding_history'
BASELINE = 'b585c548a3b68e6611c1f7545f63e7bcfd05d845'
PROTOCOL = '3c166973460fe8111d4aa7fec411f32989eb1dde8458cf60dcdaa69e36807224'
FREEZE = '2d218f21a5e3c209821cc02f523d2350070ebd8d214686452ba2824bac87e95a'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def frozen_artifacts():
    provenance = json.loads((FIXTURE / 'provenance.json').read_text())
    require(provenance['baseline_commit'] == BASELINE, 'Historical commit changed')
    for name, expected in provenance['frozen_m9_files'].items():
        require(digest(ROOT / name) == expected, 'Frozen M9 file changed: ' + name)
    require(digest(EXPERIMENT / 'freeze.json') == FREEZE, 'Frozen inventory changed')
    freeze = json.loads((EXPERIMENT / 'freeze.json').read_text())
    require(freeze['baseline_head'] == BASELINE, 'Frozen source baseline changed')
    require(freeze['protocol_sha256'] == PROTOCOL
            and digest(EXPERIMENT / 'PROTOCOL.md') == PROTOCOL, 'Protocol changed')
    return provenance, freeze


def reconstruct_history(destination):
    """Materialize only the inventoried files; no Git/network/developer-file fallback."""
    provenance, freeze = frozen_artifacts()
    archive = FIXTURE / 'b585c54.tar.gz'
    require(digest(archive) == provenance['archive_sha256'], 'Historical archive changed')
    save = provenance['historical_untracked']
    require(digest(FIXTURE / save['source']) == save['sha256']
            == freeze['baseline_files'][save['destination']], 'Historical save file changed')
    expected = set(freeze['baseline_files']) - {save['destination']}
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as bundle:
        members = [member for member in bundle.getmembers() if not member.isdir()]
        require(len(members) == len(expected)
                and {member.name for member in members} == expected,
                'Historical archive membership changed')
        for member in members:
            name = Path(member.name)
            require(member.isfile() and not name.is_absolute() and '..' not in name.parts,
                    'Unsafe historical archive member')
            data = bundle.extractfile(member).read()
            require(hashlib.sha256(data).hexdigest() == freeze['baseline_files'][member.name],
                    'Historical baseline changed: ' + member.name)
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    shutil.copyfile(FIXTURE / save['source'], destination / save['destination'])
    for name in provenance['frozen_m9_files']:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    return destination


def historical_custody(root):
    """Run the unchanged full-inventory verifier and audit in a fresh process."""
    completed = subprocess.run(
        [sys.executable, '-B', '-m', 'experiments.identifier_withholding.run_experiment',
         'audit', 'experiments/identifier_withholding/results/v1'],
        cwd=root, capture_output=True, text=True, check=True)
    return {'verification_kind': 'HISTORICAL_CUSTODY', 'source_baseline': BASELINE,
            'audit': json.loads(completed.stdout)}


def current_compatibility():
    """Check actual current sources; do not call or monkeypatch verify_frozen()."""
    from experiments.identifier_withholding import run_experiment as exp

    require(exp.ROOT == ROOT, 'Compatibility must use the current checkout')
    _, freeze = frozen_artifacts()
    original = EXPERIMENT / 'results/v1'
    lock = json.loads((original / 'execution-lock.json').read_text())
    require(lock['freeze_sha256'] == FREEZE and lock['protocol_sha256'] == PROTOCOL
            and digest(original / 'PROTOCOL.md') == PROTOCOL, 'Execution lock changed')
    require(exp.inventory(original) == json.loads((original / 'manifest.json').read_text())['files'],
            'Original result inventory changed')
    require(lock['implementation'] == {name: digest(ROOT / name) for name in exp.DEPENDENCIES},
            'Current execution dependency differs from frozen implementation')
    # These are preservation checks, not a substitution for whole-checkout custody.
    for name, expected in freeze['baseline_files'].items():
        if '/results/' in name or name.startswith('artifacts/'):
            require(digest(ROOT / name) == expected, 'Preserved artifact changed: ' + name)
    inputs, truth = exp.build()
    decisions = exp.run_worker(inputs)
    result = exp.score(inputs, decisions, truth)
    comparisons = {}
    for name, data in [('decision-inputs.json', inputs), ('scorer-only-truth.json', truth),
                       ('decisions.json', decisions), ('results.json', result)]:
        # Exactly the frozen writer's byte encoding, without writing original results.
        payload = (json.dumps(data, indent=2, sort_keys=True) + '\n').encode()
        require(payload == (original / name).read_bytes(), 'Compatibility differs: ' + name)
        comparisons[name] = hashlib.sha256(payload).hexdigest()
    return {'verification_kind': 'CURRENT_CHECKOUT_COMPATIBILITY_ONLY',
            'historical_source_baseline': BASELINE, 'protocol_sha256': PROTOCOL,
            'byte_identical_files': comparisons, 'claim_status': result['claim_status'],
            'claim_demonstrated': result['claim_demonstrated']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=('historical', 'compatibility'))
    args = parser.parse_args()
    if args.kind == 'historical':
        with tempfile.TemporaryDirectory(prefix='m9-history-') as temporary:
            receipt = historical_custody(reconstruct_history(Path(temporary) / 'baseline'))
    else:
        receipt = current_compatibility()
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
