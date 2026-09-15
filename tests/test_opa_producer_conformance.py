"""Synthetic evaluator fixtures; these are not empirical OPA producer evidence."""
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('opa_conformance', ROOT / 'experiments/opa_producer_conformance/run_experiment.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    monkeypatch.setattr(m, 'preserved', lambda _: True)
    monkeypatch.setattr(m, 'baseline', lambda: {})
    for name in ('frozen', 'runtime'):
        (tmp_path / name).mkdir()
    (tmp_path / 'frozen/PROTOCOL.md').write_bytes((m.HERE / 'PROTOCOL.md').read_bytes())
    base = json.loads((ROOT / 'input.json').read_text())
    m.dump(tmp_path / 'frozen/input.json', base)
    (tmp_path / 'frozen/run_experiment.py').write_bytes(Path(m.__file__).read_bytes())
    m.dump(tmp_path / 'frozen/source-review.json', {'status': 'SUPPORTED', 'scope': 'stock-opa-exec-1.19.0', 'references': ['fixture-only']})
    identity = 'sha256:' + 'a' * 64
    m.dump(tmp_path / 'runtime/inspect.stdout', [{'Id': identity}])
    (tmp_path / 'runtime/version.stdout').write_text('Version: 1.19.0\n')
    for name in ('version', 'inspect'):
        m.dump(tmp_path / f'runtime/{name}.json', {'returncode': 0})
    m.dump(tmp_path / 'execution-lock.json', {'image_id': identity, 'baseline_commit': m.BASE,
        'baseline_files': {}, 'frozen_files': m.inventory(tmp_path), 'bundle_mount': '/frozen/policies'})
    for i, item in enumerate(m.inputs(base), 1):
        folder = tmp_path / f'invocations/{i:03}'; folder.mkdir(parents=True)
        m.dump(folder / 'input.json', item)
        m.dump(folder / 'invocation.json', {'argv': m.argv(identity, '/frozen/policies'), 'returncode': 0,
            'error': None, 'started_at': '2026-01-01T00:00:00+00:00', 'finished_at': '2026-01-01T00:00:01+00:00'})
        result = {'allowed': i <= 6, 'decision': 'ALLOW' if i <= 6 else 'DENY'}
        identifier = f'aaaaaaaa-aaaa-4aaa-8aaa-{i:012}'
        m.dump(folder / 'stdout.bin', {'result': [{'decision_id': identifier, 'result': result}]})
        (folder / 'stderr.bin').write_text(json.dumps({'type': 'openpolicyagent.org/decision_logs',
            'decision_id': identifier, 'input': item, 'result': result}) + '\n')
    m.dump(tmp_path / 'capture.json', {'complete': True, 'count': 8, 'errors': []})
    return tmp_path


def edit(campaign, case, stream, change):
    path = campaign / f'invocations/{case:03}/{stream}.bin'
    obj = m.read(path); change(obj)
    path.write_text(json.dumps(obj) + '\n')


def test_supported_and_read_only_replay(campaign):
    result = m.evaluate(campaign)
    assert result['verdict'] == 'PRODUCER_CONTRACT_SUPPORTED'
    m.dump(campaign / 'result.json', result)
    m.dump(campaign / 'manifest.json', m.inventory(campaign))
    before = m.inventory(campaign)
    assert m.verify(campaign) == result
    assert m.inventory(campaign) == before


@pytest.mark.parametrize('mode', ['mismatch', 'sentinel', 'duplicate'])
def test_contradictions(campaign, mode):
    identifier = {'mismatch': 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
                  'sentinel': m.SENTINELS[0], 'duplicate': 'aaaaaaaa-aaaa-4aaa-8aaa-000000000001'}[mode]
    edit(campaign, 3, 'stdout', lambda o: o['result'][0].update(decision_id=identifier))
    if mode != 'mismatch':
        edit(campaign, 3, 'stderr', lambda o: o.update(decision_id=identifier))
    assert m.evaluate(campaign)['verdict'] == 'PRODUCER_CONTRACT_CONTRADICTED'


@pytest.mark.parametrize('mode', ['absent', 'extra', 'malformed', 'wrong_input', 'wrong_policy', 'missing_id', 'bad_uuid'])
def test_ambiguous_or_semantically_insufficient(campaign, mode):
    path = campaign / 'invocations/001/stderr.bin'
    if mode == 'absent': path.write_bytes(b'')
    elif mode == 'extra': path.write_bytes(path.read_bytes() * 2)
    elif mode == 'malformed': path.write_bytes(b'{')
    elif mode == 'wrong_input': edit(campaign, 1, 'stderr', lambda o: o.update(input={}))
    elif mode == 'wrong_policy': edit(campaign, 1, 'stderr', lambda o: o.update(result={}))
    else:
        val = None if mode == 'missing_id' else 'not-a-uuid'
        edit(campaign, 1, 'stderr', lambda o: o.update(decision_id=val))
        edit(campaign, 1, 'stdout', lambda o: o['result'][0].update(decision_id=val))
    assert m.evaluate(campaign)['verdict'] == 'NOT_EVALUABLE'


@pytest.mark.parametrize('mode', ['bytes', 'unlisted', 'result', 'baseline'])
def test_verifier_rejects_tampering(campaign, mode, monkeypatch):
    m.dump(campaign / 'result.json', m.evaluate(campaign))
    m.dump(campaign / 'manifest.json', m.inventory(campaign))
    if mode == 'bytes': (campaign / 'invocations/001/stdout.bin').write_bytes(b'{}')
    elif mode == 'unlisted': (campaign / 'extra').write_bytes(b'extra')
    elif mode == 'baseline': monkeypatch.setattr(m, 'baseline', lambda: {'missing': 'abc'})
    else:
        m.dump(campaign / 'result.json', {'verdict': 'FAKE'})
        m.dump(campaign / 'manifest.json', m.inventory(campaign))
    with pytest.raises(ValueError): m.verify(campaign)


def test_existing_directory_refused(tmp_path):
    with pytest.raises(FileExistsError): m.capture(tmp_path, tmp_path / 'source.json')


def test_partial_failure_is_retained(tmp_path):
    out = tmp_path / 'failed'
    result = m.capture(out, tmp_path / 'missing-source.json')
    assert result['verdict'] == 'NOT_EVALUABLE'
    assert (out / 'manifest.json').exists()
    assert m.read(out / 'capture.json')['complete'] is False


def test_duplicate_json_keys_rejected(campaign):
    (campaign / 'invocations/001/stdout.bin').write_bytes(b'{"result":[],"result":[]}')
    assert m.evaluate(campaign)['verdict'] == 'NOT_EVALUABLE'


@pytest.mark.parametrize('value', [None, 123, [], {}, 'invalid'])
def test_invalid_id_never_becomes_duplicate_contradiction(campaign, value):
    for i in (1, 2):
        edit(campaign, i, 'stderr', lambda o: o.update(decision_id=value))
        edit(campaign, i, 'stdout', lambda o: o['result'][0].update(decision_id=value))
    assert m.evaluate(campaign)['verdict'] == 'NOT_EVALUABLE'


def test_unavailable_source_takes_precedence_over_contradiction(campaign):
    source = campaign / 'frozen/source-review.json'
    m.dump(source, {'status': 'UNAVAILABLE', 'references': []})
    lock = m.read(campaign / 'execution-lock.json')
    lock['frozen_files']['frozen/source-review.json'] = m.digest(source.read_bytes())
    m.dump(campaign / 'execution-lock.json', lock)
    edit(campaign, 1, 'stdout', lambda o: o['result'][0].update(decision_id='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'))
    assert m.evaluate(campaign)['verdict'] == 'NOT_EVALUABLE'


def test_nonobject_result_fails_closed(campaign):
    edit(campaign, 1, 'stdout', lambda o: o.update(result=[False]))
    assert m.evaluate(campaign)['verdict'] == 'NOT_EVALUABLE'


@pytest.mark.parametrize('semantic', ['input', 'result'])
def test_semantic_mismatch_precedes_identifier_contradiction(campaign, semantic):
    edit(campaign, 1, 'stderr', lambda o: o.update({semantic: {}}))
    edit(campaign, 1, 'stdout', lambda o: o['result'][0].update(decision_id='bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'))
    assert m.evaluate(campaign)['verdict'] == 'NOT_EVALUABLE'
