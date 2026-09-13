"""Evidence-only subprocess. Scorer truth and scenario labels are not inputs."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

from experiments.control_attestation.run_experiment import create_positive_fixture, inventory, write
from experiments.target_outcome.run_experiment import derive, audit, TARGET
from src.action_evidence import verify_location
from src.control_attestation import attest
from src.evidence_digest import evidence_digest
from experiments.strong_link_assurance.scope import assess, namespace_probe, parent_probe

ROOT = Path(__file__).resolve().parents[2]


def evaluate(evidence, archive):
    if set(evidence) != {'rows', 'namespace_observations'}:
        raise ValueError('Non-allowlisted worker input')
    if set(evidence['rows']) != {'governance', 'execution', 'outcome'}:
        raise ValueError('Unsupported source roles')
    control = json.loads((ROOT / 'experiments/control_attestation/control.json').read_text())
    create_positive_fixture(archive, control)
    for role, name in [('governance', 'governance.jsonl'), ('execution', 'execution.jsonl'), ('outcome', 'native/access.jsonl')]:
        (archive / name).write_text(''.join(json.dumps(row, sort_keys=True) + '\n' for row in evidence['rows'][role]))
    write(archive / 'identity_mapping.json', {'version': '1', 'entries': [
        {'source': {'namespace': TARGET['identity_namespace'], 'id': 'complaint-client'},
         'target': {'namespace': 'agent', 'id': 'fixture-agent'}}]})
    records, correlations, views = derive(archive)
    write(archive / 'correlations.json', correlations)
    write(archive / 'reconciliation.json', views)
    support = json.loads((archive / 'coverage_observations.json').read_text())
    support['reconciliation_ref'] = views['blocked-bounded']['assertion_id']
    support['capture']['native_file_digest'] = 'sha256:' + hashlib.sha256((archive / 'native/access.jsonl').read_bytes()).hexdigest()
    write(archive / 'coverage_observations.json', support)
    write(archive / 'manifest.json', {'schema_version': '1.0', 'files': inventory(archive),
                                    'provenance': 'DETERMINISTIC_SYNTHETIC_FIXTURE_NO_TARGET_PROCESS'})
    verification = audit(archive)
    attestations = {}
    # Adapter reporting names select its existing views; no name enters attest().
    for name, assertion in views.items():
        a, receipt = attest(archive, assertion['assertion_id'], control,
                            coverage_support='coverage_observations.json' if name == 'blocked-bounded' else None)
        attestations[assertion['assertion_id']] = {'attestation': a, 'receipt': receipt}
    # All primary outputs are complete before the diagnostic is even called.
    return {'records': [{k: v for k, v in r.items() if k != 'ingested_at'} for r in records],
            'correlations': correlations, 'reconciliation': views, 'verification': verification,
            'attestations': attestations, 'scope_diagnostics': assess(records, correlations),
            'namespace_probe': namespace_probe(records, evidence['namespace_observations']),
            'parent_probe': parent_probe(records)}


def main():
    archive = Path(sys.argv[1])
    try:
        result = evaluate(json.load(sys.stdin), archive)
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)
        result = {'status': 'INTERNAL_ERROR', 'finding': None,
                  'basis_codes': ['EXPERIMENT_PROCESSING_FAILED']}
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
