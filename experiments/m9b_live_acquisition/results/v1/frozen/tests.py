"""Acquisition tests use no Docker, network, clocks or historical live claims."""
import json
import subprocess
from unittest.mock import Mock

import pytest

from experiments.m9b_live_acquisition import run_acquisition as m


def sample(wall=100*m.NS, latency=100_000_000, discrepancy=0):
    return {'start': {'wall_ns': wall, 'monotonic_ns': 0},
            'end': {'wall_ns': wall+latency+discrepancy, 'monotonic_ns': latency}}


def test_integer_timestamp_is_interval_not_point():
    result = m.assess_sample(sample(), '100\n')
    assert result['accepted']
    assert result['offset_interval_ns'] == [-100_000_000, m.NS]


@pytest.mark.parametrize('raw', ['', 'x', '100.25', '100\n101', '--100'])
def test_bad_clock_output_rejected(raw):
    assert not m.assess_sample(sample(), raw)['accepted']


@pytest.mark.parametrize('s,raw,rc', [(sample(latency=2*m.NS+1),'100',0),
    (sample(discrepancy=50_000_001),'100',0), (sample(),'104',0), (sample(),'100',1),
    (sample(latency=-1),'100',0)])
def test_clock_thresholds_fail_closed(s, raw, rc):
    assert not m.assess_sample(s, raw, rc)['accepted']


def test_failed_command_preserves_bytes_and_metadata(tmp_path, monkeypatch):
    (tmp_path/'commands').mkdir()
    monkeypatch.setattr(m.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a, 7, b'partial', b'failure'))
    with pytest.raises(RuntimeError):
        m.Commands(tmp_path).run(['docker','wait','synthetic'])
    assert (tmp_path/'commands/001.stdout').read_bytes() == b'partial'
    assert json.loads((tmp_path/'commands/001.json').read_text())['returncode'] == 7


def test_timeout_retains_partial_capture(tmp_path, monkeypatch):
    (tmp_path/'commands').mkdir()
    def timeout(*a, **k):
        raise subprocess.TimeoutExpired(a[0], 20, output=b'partial', stderr=b'late')
    monkeypatch.setattr(m.subprocess, 'run', timeout)
    _, ref, meta = m.Commands(tmp_path).run(['docker','wait','synthetic'], timeout=20, required=False)
    assert meta['error_type'] == 'TimeoutExpired'
    assert (tmp_path/(ref+'.stdout')).read_bytes() == b'partial'


def test_existing_directory_refused_without_touching(tmp_path):
    (tmp_path/'untouched').write_text('original')
    with pytest.raises(FileExistsError):
        m.run(tmp_path)
    assert (tmp_path/'untouched').read_text() == 'original'


def test_freeze_failure_archived_and_no_retry(tmp_path, monkeypatch):
    count = []
    def fail(*args):
        count.append(1)
        raise RuntimeError('source absent')
    monkeypatch.setattr(m, 'freeze', fail)
    out = tmp_path/'run'
    result = m.run(out)
    assert count == [1]
    assert result['acquisition'] == 'NOT_EVALUABLE'
    assert result['coverage'] == 'NOT_DEMONSTRATED'
    assert (out/'manifest.json').exists()
    assert result == m.verify(out)
    assert 'interval_clock_bound' in result['missing_dimensions']
    assert len({v['independently_missing'] for v in result['challenges'].values()}) == 5
    assert all(v['coverage'] == 'NOT_DEMONSTRATED' and 'SYNTHETIC' in v['kind']
               for v in result['challenges'].values())
    assert result['public_api'] == 'PUBLIC_API_NOT_RUN_SINGLE_EPISODE_LAYOUT'
    (out/'capture.json').write_text('{}')
    with pytest.raises(ValueError, match='Digest differs'):
        m.verify(out)


def test_probe_only_out_of_scope_and_excludes_auth(monkeypatch):
    response = Mock(status=200)
    response.read.return_value = b'body'
    response.getheader.return_value = 'native-id'
    connection = Mock()
    connection.getresponse.return_value = response
    monkeypatch.setattr(m.http.client, 'HTTPConnection', lambda *a, **k: connection)
    result = m.probe(1234, 'secret-password')
    assert connection.request.call_args.args == ('GET', '/complaints/complaint-456.json')
    assert 'secret-password' not in json.dumps(result)
    assert 'Authorization' not in result
    assert result['request_id'] == 'native-id'
    connection.close.assert_called_once()


def test_mocked_one_shot_orchestration(tmp_path, monkeypatch):
    """Exercise count/order/hold/QUIT without generating any native-looking findings."""
    elapsed = [100*m.NS]
    monkeypatch.setattr(m.time, 'time_ns', lambda: elapsed[0])
    monkeypatch.setattr(m.time, 'monotonic_ns', lambda: elapsed[0])
    monkeypatch.setattr(m.time, 'sleep', lambda s: elapsed.__setitem__(0, elapsed[0]+int(s*m.NS)))
    monkeypatch.setattr(m, 'freeze', lambda *args: None)
    commands = []
    def run_command(self, argv, **kw):
        commands.append((argv, kw))
        if argv[1] == 'port':
            return '127.0.0.1:1234', 'mock', {}
        if argv[1] == 'inspect':
            return '[{"State":{"Running":false}}]', 'mock', {}
        return '', 'mock', {}
    monkeypatch.setattr(m.Commands, 'run', run_command)
    monkeypatch.setattr(m.subprocess, 'run', lambda *a, **kw: Mock(stdout='hash\n'))
    process = Mock(returncode=-15)
    process.poll.return_value = None
    monkeypatch.setattr(m.subprocess, 'Popen', lambda *a, **kw: process)
    probes = []
    def probe(port, password):
        probes.append(elapsed[0])
        return {'resource_id':'complaint-456'}
    monkeypatch.setattr(m, 'probe', probe)
    monkeypatch.setattr(m, 'clock_sample', lambda commands, name, index: {'index':index, 'at':elapsed[0]})
    decisions = []
    def governed(resource, **kw):
        decisions.append((resource,kw))
        return {'policy_decision':'DENY'}
    monkeypatch.setattr(m, '_governed_action', governed)
    monkeypatch.setattr(m, 'verify', lambda out: json.loads((out/'capture.json').read_text()))
    result = m.run(tmp_path/'run')
    assert not result['errors']
    assert len(decisions) == 1 and decisions[0][0] == 'complaint-789'
    assert decisions[0][1]['bypass_enforcement'] is False
    assert [s['index'] for s in result['samples']] == list(range(12))
    assert len(probes) == 2
    assert result['hold_end']['monotonic_ns']-result['decision_return']['monotonic_ns'] == 10*m.NS
    assert sum(argv[1] == 'run' for argv, _ in commands) == 1
    assert sum(argv[1:3] == ['kill','--signal=QUIT'] for argv, _ in commands) == 1
    assert next(kw['timeout'] for argv, kw in commands if argv[1]=='wait') == 20
    assert not result['forced_cleanup']


def test_challenges_use_source_views_even_when_baseline_abstains():
    from copy import deepcopy
    view = {'available_sources':['native_snapshot','clock_samples','lifecycle','closed_snapshot','effective_configuration'],
            'capture_through_ns':10, 'required_through_ns':5, 'identity_filter':None}
    original = deepcopy(view)
    assert set(m.source_gate(view)['missing_dimensions']) == {'interval_clock_bound','logging_continuity'}
    results = m.challenge_views(view)
    assert view == original
    for result in results.values():
        assert result['omission_detected']
        assert result['independently_missing'] in m.source_gate(result['source_view'])['missing_dimensions']
        assert len(result['missing_dimensions']) == 3
    assert results['truncate_capture_through_before_horizon']['source_view']['capture_through_ns'] == 4
    assert results['identity_restricted_view']['source_view']['identity_filter'] == 'complaint-client'


def test_partial_dimension_map_cannot_substantiate():
    assert m.review_dimensions({'snapshot_binding':True})['coverage'] == 'NOT_DEMONSTRATED'
    assert m.source_gate({})['coverage'] == 'NOT_DEMONSTRATED'


def test_between_samples_wall_step_rejected_even_if_each_bracket_acceptable():
    first = dict(sample(), index=0)
    second = dict(sample(wall=101*m.NS+60_000_000), index=1)
    second['start']['monotonic_ns'] = m.NS
    second['end']['monotonic_ns'] = m.NS+100_000_000
    assert m.assess_sample(first, '100')['accepted']
    assert m.assess_sample(second, '101')['accepted']
    assert not m.cross_sample_checks([first,second])[0]['accepted']


def test_distinct_ordered_probe_validation():
    probes = [{'request_id':str(i), 'status':200, 'resource_id':'complaint-456',
               'receipt':{'monotonic_ns':t}} for i,t in [(1,1),(2,20)]]
    native = [{'request_id':str(i),'status':200,'request_method':'GET',
               'request_uri':'/complaints/complaint-456.json'} for i in (1,2)]
    capture = {'decision_start':{'monotonic_ns':5},'hold_end':{'monotonic_ns':15}}
    assert m.probes_valid(probes,native,capture)
    from copy import deepcopy
    for mutation in ['duplicate','before','after','resource']:
        bad = deepcopy(probes)
        if mutation == 'duplicate': bad[1]['request_id']='1'
        if mutation == 'before': bad[0]['receipt']['monotonic_ns']=6
        if mutation == 'after': bad[1]['receipt']['monotonic_ns']=14
        if mutation == 'resource': bad[0]['resource_id']='complaint-789'
        assert not m.probes_valid(bad,native,capture)


def test_command_stderr_is_required_even_when_empty(tmp_path):
    (tmp_path/'commands').mkdir()
    (tmp_path/'commands/001.stdout').write_text('')
    m.write(tmp_path/'commands/001.json', {'argv':[], 'start':{}, 'end':{}, 'returncode':0})
    with pytest.raises(FileNotFoundError):
        m.read_command(tmp_path,'commands/001')
    (tmp_path/'commands/001.stderr').write_text('')
    assert m.read_command(tmp_path,'commands/001')[0] == ''


def test_nested_manifest_counted_and_symlinks_rejected(tmp_path, monkeypatch):
    def fail(out, commands):
        (out/'frozen/manifest.json').write_text('{}')
        raise RuntimeError('no real capture')
    monkeypatch.setattr(m,'freeze',fail)
    out = tmp_path/'run'
    assert m.run(out)['acquisition'] == 'NOT_EVALUABLE'
    assert 'frozen/manifest.json' in json.loads((out/'manifest.json').read_text())['files']
    (out/'link').symlink_to(out/'capture.json')
    with pytest.raises(ValueError,match='Symlink'):
        m.verify(out)
