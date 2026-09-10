"""Frozen M9a-i evaluator. Native IDs/truth remain outside the decision worker."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

from src.action_evidence import ingest_governance, ingest_execution
from src.target_outcome_evidence import ingest_nginx
from src.foreign_opa_evidence import timestamp_ns

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LIVE = ROOT / 'experiments/target_outcome/results/v1'
PROTOCOL_SHA256 = '3c166973460fe8111d4aa7fec411f32989eb1dde8458cf60dcdaa69e36807224'
ROLES = ('governance', 'execution', 'outcome')
EDGES = (('governance', 'execution'), ('execution', 'outcome'))
SCENARIOS = (
    ('preserved_population', {}), ('isolated', {}),
    ('repetition', {'repetitions': 2, 'separation': 100_000_000}),
    ('clock_skew_execution', {'repetitions': 3, 'separation': 5_000_000_000, 'skew_role': 'execution', 'skew': 5_000_000_000}),
    ('clock_skew_outcome', {'repetitions': 3, 'separation': 5_000_000_000, 'skew_role': 'outcome', 'skew': 5_000_000_000}),
    ('clock_skew_outcome_negative', {'repetitions': 3, 'separation': 5_000_000_000, 'skew_role': 'outcome', 'skew': -5_000_000_000}),
    ('impostor_execution', {'replace': 'execution'}),
    ('impostor_outcome', {'replace': 'outcome'}),
    ('missing_execution', {'remove': 'execution'}),
    ('missing_outcome', {'remove': 'outcome'}),
    ('ambiguous_execution', {'add': 'execution'}),
    ('ambiguous_outcome', {'add': 'outcome'}),
)
DEPENDENCIES = ('experiments/identifier_withholding/worker.py',
                'experiments/identifier_withholding/run_experiment.py',
                'src/evidence_correlation.py', 'src/foreign_opa_evidence.py',
                'src/action_evidence.py', 'src/target_outcome_evidence.py',
                'src/evidence_digest.py', 'src/authority_resolver.py')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def verify_frozen():
    freeze = json.loads((HERE / 'freeze.json').read_text())
    if digest(HERE / 'PROTOCOL.md') != PROTOCOL_SHA256 or freeze['protocol_sha256'] != PROTOCOL_SHA256:
        raise ValueError('Frozen protocol changed')
    for member, expected in freeze['baseline_files'].items():
        if digest(ROOT / member) != expected:
            raise ValueError('Preserved baseline changed: ' + member)
    return freeze


def stamp(ns):
    seconds, fraction = divmod(ns, 1_000_000_000)
    return datetime.fromtimestamp(seconds, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S') + f'.{fraction:09d}Z'


def project(record, ref, mapping):
    """Construct a fresh allowlist; never copy envelopes or original identifiers."""
    actor = deepcopy(record['actor'])
    targets = [entry['target'] for entry in mapping['entries'] if entry['source'] == actor]
    if len(targets) > 1:
        raise ValueError('Ambiguous operator identity mapping')
    if targets:
        actor = targets[0]
    if set(actor) != {'namespace', 'id'} or any(type(v) is not str for v in actor.values()):
        raise ValueError('Invalid namespaced actor')
    if record.get('defects'):
        raise ValueError('Cannot silently drop source defects')
    return dict(evidence_ref=ref, actor=json.dumps(actor, sort_keys=True, separators=(',', ':')),
                **{k: record[k] for k in ('action', 'resource_id', 'resource_type', 'observed_at')})


def build():
    """Evaluator-owned construction and native-link scoring oracle, never decisions."""
    target = json.loads((LIVE / 'target.json').read_text())
    mapping = json.loads((LIVE / 'identity_mapping.json').read_text())
    source = {'governance': ingest_governance(LIVE / 'governance.jsonl', root=LIVE),
              'execution': ingest_execution(LIVE / 'execution.jsonl', root=LIVE),
              'outcome': ingest_nginx(LIVE / 'native/access.jsonl', root=LIVE, target=target)}
    triples = []
    for g in source['governance']:
        executions = [e for e in source['execution'] if e['action_attempt_id'] == g['action_attempt_id']]
        if len(executions) > 1:
            raise ValueError('Scoring oracle is not unique')
        if executions:
            e = executions[0]
            outcomes = [o for o in source['outcome'] if o['request_id'] == e['request_id']]
            if len(outcomes) != 1:
                raise ValueError('Scoring oracle is not unique')
            triples.append((g, e, outcomes[0]))
    if len(triples) != 2 or [len(source[r]) for r in ROLES] != [3, 2, 2]:
        raise ValueError('Frozen source population changed')
    rng = random.Random(90101)
    used = set()

    def ref():
        while True:
            value = f'{rng.getrandbits(128):032x}'
            if value not in used:
                used.add(value)
                return value

    inputs, truths = [], []
    base = timestamp_ns('2026-09-06T00:00:00Z')
    for name, settings in SCENARIOS:
        case = {role: [] for role in ROLES}
        truth = {'scenario': name, 'evidence_kind': 'PRESERVED_LIVE_PROJECTION' if name == 'preserved_population'
                 else 'SYNTHETIC_PERTURBATION', 'pairs': {a+'-'+b: [] for a,b in EDGES}, 'triples': [],
                 'provenance': {}}

        def add(record, role):
            address = ref()
            case[role].append(project(record, address, mapping))
            truth['provenance'][address] = {'source_ref': record['evidence_ref'], 'role': role}
            return address

        def remember(addresses):
            truth['triples'].append(list(addresses))
            for i, (a,b) in enumerate(EDGES):
                truth['pairs'][a+'-'+b].append(list(addresses[i:i+2]))

        if name == 'preserved_population':
            refs = {r['evidence_ref']: add(r, role) for role in ROLES for r in source[role]}
            for triple in triples:
                remember([refs[r['evidence_ref']] for r in triple])
        else:
            for triple in triples:
                for repetition in range(settings.get('repetitions', 1)):
                    addresses = []
                    for role, original in zip(ROLES, triple):
                        address = add(original, role)
                        addresses.append(address)
                        record = case[role][-1]
                        delta = timestamp_ns(original['observed_at']) - timestamp_ns(triple[0]['observed_at'])
                        skew = settings.get('skew', 0) if role == settings.get('skew_role') else 0
                        record['observed_at'] = stamp(base + repetition * settings.get('separation', 0) + delta + skew)
                        if role in (settings.get('remove'), settings.get('replace')):
                            case[role].pop()
                        if role in (settings.get('add'), settings.get('replace')):
                            impostor = deepcopy(record)
                            impostor['evidence_ref'] = ref()
                            case[role].append(impostor)
                            truth['provenance'][impostor['evidence_ref']] = {
                                'source_ref': original['evidence_ref'], 'role': role, 'transformation': 'impostor'}
                    remember(addresses)
        for role in ROLES:
            rng.shuffle(case[role])
        inputs.append(case)
        truths.append(truth)
    return inputs, truths


def run_worker(inputs):
    # Only stdin observation data crosses the boundary. The worker has no truth,
    # scenario argument, output-directory argument, archive path or gate override.
    completed = subprocess.run([sys.executable, '-B', '-m', 'experiments.identifier_withholding.worker'],
                               cwd=ROOT, input=json.dumps(inputs), text=True, capture_output=True, check=True)
    return json.loads(completed.stdout)


def ratio(n, d):
    return n / d if d else None


def metrics(counts):
    c = dict(counts)
    c.update(precision=ratio(c['correct'], c['accepted']), recall=ratio(c['correct'], c['planned']),
             observable_recall=ratio(c['correct'], c['observable']),
             false_link_rate=ratio(c['false'], c['accepted']),
             abstention_rate=ratio(c['abstained_observations'], c['observations']))
    return c


def score(inputs, decisions, truths):
    if not len(inputs) == len(decisions) == len(truths) == len(SCENARIOS):
        raise ValueError('Case count differs from protocol')
    rows = []
    for case, decision, truth in zip(inputs, decisions, truths):
        edges = {}
        for a,b in EDGES:
            key = a+'-'+b
            accepted = {(r['evidence_ref'], r['candidate_refs'][0]) for r in decision['edges'][key]
                        if r['source'] == 'opa' and r['state'] == 'MATCHED'}
            true = {tuple(p) for p in truth['pairs'][key]}
            present = {r['evidence_ref'] for role in (a,b) for r in case[role]}
            states = decision['edges'][key]
            edges[key] = metrics({'accepted': len(accepted), 'correct': len(accepted & true),
                                  'false': len(accepted - true), 'planned': len(true),
                                  'observable': sum(x in present and y in present for x,y in true),
                                  'observations': len(states),
                                  'abstained_observations': sum(r['state'] != 'MATCHED' for r in states)})
        paths = {tuple(p) for p in decision['candidate_paths']}
        true_paths = {tuple(p) for p in truth['triples']}
        downstream = decision['downstream']
        rows.append({'scenario': truth['scenario'], 'evidence_kind': truth['evidence_kind'], 'edges': edges,
                     'candidate_paths': len(paths), 'false_candidate_paths': len(paths - true_paths),
                     'governance_focuses': len(downstream),
                     'assurance_abstentions': sum(d['status'] == 'ABSTAIN' for d in downstream),
                     'assurance_abstention_rate': ratio(sum(d['status'] == 'ABSTAIN' for d in downstream), len(downstream)),
                     'm6_invocations': sum(d['m6_invoked'] for d in downstream),
                     'm7_invocations': sum(d['m7_invoked'] for d in downstream),
                     'attestations_emitted': sum(d['finding'] is not None for d in downstream)})
    count_fields = ('accepted','correct','false','planned','observable','observations','abstained_observations')
    pooled = metrics({key: sum(e[key] for row in rows for e in row['edges'].values()) for key in count_fields})
    isolated = next(r for r in rows if r['scenario'] == 'isolated')
    screen = (pooled['false'] == 0 and not any(r['false_candidate_paths'] for r in rows)
              and all(e['recall'] == 1 for e in isolated['edges'].values()))
    return {'protocol_sha256': PROTOCOL_SHA256, 'scenarios': rows, 'pooled_stress_diagnostic': pooled,
            'candidate_quality_screen_passed': screen, 'claim_demonstrated': False,
            'claim_status': 'NOT_DEMONSTRATED', 'stop': True,
            'assurance_eligibility': 'NO_SUBSTANTIATED_CLOCK_AND_POPULATION_GUARANTEES',
            'downstream_attestations': [],
            'interpretation': 'Candidate accuracy does not establish identity. No new M6/M7 adjudication was authorized by the fixed evidence gate. Pooled rates are not production estimates.'}


def inventory(directory):
    return {p.relative_to(directory).as_posix(): digest(p) for p in sorted(directory.rglob('*'))
            if p.is_file() and p != directory / 'manifest.json'}


def run(directory):
    verify_frozen()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'PROTOCOL.md').write_bytes((HERE / 'PROTOCOL.md').read_bytes())
    lock = {'protocol_sha256': PROTOCOL_SHA256, 'freeze_sha256': digest(HERE / 'freeze.json'),
            'implementation': {p: digest(ROOT / p) for p in DEPENDENCIES},
            'python': sys.version, 'worker_transport': 'stdin unlabelled observation arrays'}
    write(directory / 'execution-lock.json', lock)
    inputs, truths = build()
    write(directory / 'decision-inputs.json', inputs)
    decisions = run_worker(inputs)
    write(directory / 'decisions.json', decisions)
    # Deliberately persisted only after decision worker exit; never passed back.
    write(directory / 'scorer-only-truth.json', truths)
    result = score(inputs, decisions, truths)
    write(directory / 'results.json', result)
    write(directory / 'manifest.json', {'files': inventory(directory)})
    return result


def audit(directory):
    verify_frozen()
    directory = Path(directory)
    if json.loads((directory / 'manifest.json').read_text())['files'] != inventory(directory):
        raise ValueError('Result inventory changed')
    lock = json.loads((directory / 'execution-lock.json').read_text())
    if (lock['protocol_sha256'] != PROTOCOL_SHA256
            or digest(directory / 'PROTOCOL.md') != PROTOCOL_SHA256
            or lock['freeze_sha256'] != digest(HERE / 'freeze.json')
            or lock['implementation'] != {p: digest(ROOT / p) for p in DEPENDENCIES}):
        raise ValueError('Frozen execution dependency changed')
    inputs, truths = build()
    if inputs != json.loads((directory / 'decision-inputs.json').read_text()):
        raise ValueError('Input regeneration disagrees')
    decisions = run_worker(inputs)
    if decisions != json.loads((directory / 'decisions.json').read_text()):
        raise ValueError('Decision replay disagrees')
    if truths != json.loads((directory / 'scorer-only-truth.json').read_text()):
        raise ValueError('Scoring truth regeneration disagrees')
    expected = score(inputs, decisions, truths)
    if expected != json.loads((directory / 'results.json').read_text()):
        raise ValueError('Score replay disagrees')
    return {'status': 'VERIFIED', 'protocol_sha256': PROTOCOL_SHA256,
            'claim_demonstrated': expected['claim_demonstrated'], 'scenarios': len(inputs)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('run','audit'))
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory) if args.command == 'run' else audit(args.directory), indent=2))


if __name__ == '__main__':
    main()
