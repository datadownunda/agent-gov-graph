"""M9a-i boundary, frozen-rule, scorer and preservation regressions."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.identifier_withholding import run_experiment as exp
from experiments.identifier_withholding import worker

FORBIDDEN = ('action_attempt_id', 'request_id', '$request_id', 'run_id', 'ground_truth',
             'scenario', 'label', 'raw', 'location', 'content_digest', 'governance_decision',
             'target_outcome', 'client_success', 'bypass', 'authority_binding')


@pytest.fixture
def population():
    return exp.build()[0][1]


def test_frozen_protocol_and_population():
    assert exp.verify_frozen()['protocol_sha256'] == exp.PROTOCOL_SHA256
    inputs, truth = exp.build()
    assert len(inputs) == len(truth) == 12
    assert len({t['scenario'] for t in truth}) == 12
    assert [len(inputs[0][r]) for r in worker.ROLES] == [3, 2, 2]
    assert exp.build() == (inputs, truth)
    for case in inputs:
        worker.validate_case(case)
    payload = json.dumps(inputs)
    for field in FORBIDDEN:
        assert field not in payload
    # Values of native identifiers and control labels also must not leak.
    for member in ('governance.jsonl', 'execution.jsonl', 'native/access.jsonl'):
        for line in (exp.LIVE / member).read_text().splitlines():
            raw = json.loads(line)
            context = raw.get('context', {})
            for value in (raw.get('request_id'), raw.get('action_attempt_id'),
                          context.get('action_attempt_id'), context.get('run_id')):
                if value:
                    assert value not in payload


@pytest.mark.parametrize('field', FORBIDDEN)
def test_extra_keys_rejected_at_both_worker_boundaries(population, field):
    bad = deepcopy(population)
    bad[field] = 'POISON'
    with pytest.raises(ValueError):
        worker.decide(bad)
    bad = deepcopy(population)
    bad['governance'][0][field] = 'POISON'
    with pytest.raises(ValueError):
        worker.decide(bad)


@pytest.mark.parametrize('field', sorted(worker.FIELDS))
def test_nested_smuggling_rejected(population, field):
    population['governance'][0][field] = {'ground_truth': 'POISON'}
    with pytest.raises(ValueError):
        worker.decide(population)


def test_projection_ignores_poison_in_source_envelope():
    source = exp.ingest_governance(exp.LIVE / 'governance.jsonl', root=exp.LIVE)[0]
    mapping = {'entries': []}
    before = exp.project(source, 'opaque', mapping)
    for field in FORBIDDEN:
        source[field] = {'request_id': 'POISON', 'label': 'POISON'}
    assert exp.project(source, 'opaque', mapping) == before
    source['defects'] = ['INVALID_SOURCE']
    with pytest.raises(ValueError):
        exp.project(source, 'opaque', mapping)


def test_unknown_namespaces_are_not_inferred_equivalent():
    source = exp.ingest_governance(exp.LIVE / 'governance.jsonl', root=exp.LIVE)[0]
    a = exp.project(source, 'a', {'entries': []})
    source['actor']['namespace'] = 'unrelated'
    b = exp.project(source, 'b', {'entries': []})
    assert a['actor'] != b['actor']


def test_reordering_and_opaque_reference_renaming_do_not_change_decisions(population):
    before = worker.decide(population)
    renamed = deepcopy(population)
    mapping = {r['evidence_ref']: f'opaque-{i}' for i, r in enumerate(
               r for role in worker.ROLES for r in population[role])}
    for records in renamed.values():
        records.reverse()
        for r in records:
            r['evidence_ref'] = mapping[r['evidence_ref']]
    after = worker.decide(renamed)

    def canonical(value):
        if isinstance(value, str):
            return mapping.get(value, value)
        if isinstance(value, dict):
            return {k: canonical(v) for k,v in value.items()}
        if isinstance(value, list):
            return sorted((canonical(v) for v in value), key=lambda v: json.dumps(v, sort_keys=True))
        return value
    assert canonical(before) == canonical(after)


def test_duplicate_addresses_rejected(population):
    population['execution'][0]['evidence_ref'] = population['governance'][0]['evidence_ref']
    with pytest.raises(ValueError):
        worker.decide(population)


@pytest.mark.parametrize('delta,expected', [(1_000_000_000, 'MATCHED'),
                                           (-1_000_000_000, 'MATCHED'),
                                           (1_000_000_001, 'UNMATCHED'),
                                           (-1_000_000_001, 'UNMATCHED')])
def test_inclusive_fixed_window(population, delta, expected):
    g = population['governance'][0]
    e = dict(g, evidence_ref='separate-source', observed_at=exp.stamp(exp.timestamp_ns(g['observed_at']) + delta))
    out = worker.decide({'governance': [g], 'execution': [e], 'outcome': []})
    assert out['edges']['governance-execution'][0]['state'] == expected


def test_no_downstream_reconciler_or_adjudicator_calls(population, monkeypatch):
    import src.action_reconciliation
    import src.control_attestation
    import src.m6_attestation_evidence

    def forbidden(*args, **kwargs):
        pytest.fail('Blocked evidence reached downstream decision inputs')
    monkeypatch.setattr(src.action_reconciliation, 'reconcile', forbidden)
    monkeypatch.setattr(src.control_attestation, 'adjudicate', forbidden)
    monkeypatch.setattr(src.control_attestation, 'attest', forbidden)
    monkeypatch.setattr(src.m6_attestation_evidence, 'verify_m6', forbidden)
    result = worker.decide(population)
    assert len(result['candidate_paths']) == 2
    assert all(d['status'] == 'ABSTAIN' and d['finding'] is None
               and not d['m6_invoked'] and not d['m7_invoked'] for d in result['downstream'])
    # Check the separate worker entry point has no downstream/evaluator imports.
    import ast
    tree = ast.parse(Path(worker.__file__).read_text())
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert imports == {'src.evidence_correlation'}


def test_process_truth_isolation_and_replay(tmp_path, monkeypatch):
    original = exp.subprocess.run
    output = tmp_path / 'run'
    calls = []

    def inspect(command, **kwargs):
        assert command[-1] == 'experiments.identifier_withholding.worker'
        assert str(output) not in command
        payload = json.loads(kwargs['input'])
        assert isinstance(payload, list)
        for case in payload:
            worker.validate_case(case)
        if not calls:
            assert not (output / 'scorer-only-truth.json').exists()
            assert (output / 'execution-lock.json').exists()
        calls.append(command)
        return original(command, **kwargs)
    monkeypatch.setattr(exp.subprocess, 'run', inspect)
    result = exp.run(output)
    assert exp.audit(output)['status'] == 'VERIFIED'
    assert len(calls) == 2
    assert result['claim_demonstrated'] is False
    assert result['candidate_quality_screen_passed'] is False
    assert result['downstream_attestations'] == []
    with pytest.raises(FileExistsError):
        exp.run(output)
    (output / 'decisions.json').write_text('[]')
    with pytest.raises(ValueError, match='inventory'):
        exp.audit(output)


def test_metrics_missing_and_impostor_denominators():
    inputs, truth = exp.build()
    result = exp.score(inputs, [worker.decide(c) for c in inputs], truth)
    rows = {r['scenario']: r for r in result['scenarios']}
    for e in rows['isolated']['edges'].values():
        assert e['precision'] == e['recall'] == 1
    for e in rows['missing_execution']['edges'].values():
        assert e['precision'] is None and e['false_link_rate'] is None
        assert e['recall'] == 0 and e['observable_recall'] is None
        assert e['planned'] == 2 and e['observable'] == 0 and e['abstention_rate'] == 1
    for e in rows['impostor_execution']['edges'].values():
        assert e['false'] == e['accepted'] == 2
        assert e['precision'] == 0 and e['false_link_rate'] == 1
        assert e['observable_recall'] is None
    assert rows['repetition']['candidate_paths'] == 0
    assert all(r['assurance_abstention_rate'] == 1 for r in rows.values())


@pytest.mark.parametrize('member', ['PROTOCOL.md', 'src/evidence_correlation.py'])
def test_protocol_and_baseline_tamper_fail_before_execution(monkeypatch, member):
    original = exp.digest
    monkeypatch.setattr(exp, 'digest', lambda p: 'tampered' if str(p).endswith(member) else original(p))
    with pytest.raises(ValueError):
        exp.verify_frozen()
