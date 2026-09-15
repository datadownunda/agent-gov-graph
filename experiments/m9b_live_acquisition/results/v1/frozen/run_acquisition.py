"""One-shot protocol-v1 acquisition. Replay is read-only; source gaps remain gaps."""
import argparse
import base64
import hashlib
import http.client
import json
import secrets
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from experiments.target_outcome.run_experiment import IMAGE, TARGET, MAPPING
from src.complaint_runtime import _governed_action
from src.authority_reconstruction import reconstruct_authority

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASELINE = '1ee92c58a6bee4a86379bcd7ea4473136aba9fe5'
NS = 1_000_000_000


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stamp():
    return {'wall_ns': time.time_ns(), 'monotonic_ns': time.monotonic_ns()}


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


class Commands:
    def __init__(self, out):
        self.out = out
        self.index = 0

    def run(self, argv, *, timeout=30, required=True):
        self.index += 1
        stem = f'commands/{self.index:03d}'
        meta = {'argv': argv, 'start': stamp(), 'timeout_seconds': timeout}
        try:
            result = subprocess.run(argv, capture_output=True, timeout=timeout)
            stdout, stderr = result.stdout, result.stderr
            meta['returncode'] = result.returncode
        except (OSError, subprocess.TimeoutExpired) as error:
            stdout = getattr(error, 'stdout', b'') or b''
            stderr = getattr(error, 'stderr', b'') or b''
            meta.update(returncode=None, error_type=type(error).__name__, error=str(error))
        meta['end'] = stamp()
        (self.out / (stem + '.stdout')).write_bytes(stdout)
        (self.out / (stem + '.stderr')).write_bytes(stderr)
        write(self.out / (stem + '.json'), meta)
        if required and meta['returncode'] != 0:
            raise RuntimeError('Command failed; preserved at ' + stem)
        return stdout.decode(errors='replace'), stem, meta


def clock_sample(commands, name, index):
    start = stamp()
    value, ref, meta = commands.run(['docker', 'exec', name, 'date', '-u', '+%s'], required=False)
    end = stamp()
    sample = {'index': index, 'start': start, 'end': end, 'date_command': ref}
    if index in (0, 11):
        sample['kernel_commands'] = [commands.run(['docker', 'exec', name, *args], required=False)[1]
                                    for args in (['adjtimex'], ['cat', '/proc/self/timens_offsets'])]
    return sample


def assess_sample(sample, text, returncode=0):
    a, b = sample['start'], sample['end']
    wall = b['wall_ns'] - a['wall_ns']
    mono = b['monotonic_ns'] - a['monotonic_ns']
    try:
        stripped = text.strip()
        if not stripped or any(c not in '-0123456789' for c in stripped):
            raise ValueError('not integer')
        source = int(stripped) * NS
    except ValueError:
        return {'accepted': False, 'reason': 'DATE_NOT_INTEGER'}
    interval = [source - b['wall_ns'], source + NS - a['wall_ns']]
    return {'accepted': returncode == 0 and 0 <= mono <= 2*NS and
            interval[0] >= -3*NS and interval[1] <= 3*NS and abs(wall-mono) <= 50_000_000,
            'offset_interval_ns': interval, 'latency_ns': mono,
            'wall_monotonic_discrepancy_ns': abs(wall-mono)}


def probe(port, password):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
    try:
        token = base64.b64encode(('complaint-client:' + password).encode()).decode()
        connection.request('GET', '/complaints/complaint-456.json', headers={'Authorization': 'Basic ' + token})
        response = connection.getresponse()
        body = response.read()
        return {'resource_id': 'complaint-456', 'status': response.status,
                'request_id': response.getheader('X-Request-ID'), 'receipt': stamp(),
                'body_bytes': len(body), 'body_sha256': hashlib.sha256(body).hexdigest()}
    finally:
        connection.close()


def freeze(out, commands):
    tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, check=True, capture_output=True).stdout
    paths = [ROOT / p.decode() for p in tracked.split(b'\0') if p]
    baseline = subprocess.run(['git', 'ls-tree', '-r', '--name-only', BASELINE], cwd=ROOT,
                              check=True, capture_output=True, text=True).stdout.splitlines()
    changed = subprocess.run(['git', 'diff', '--name-only', BASELINE, '--'], cwd=ROOT,
                             check=True, capture_output=True, text=True).stdout.splitlines()
    changed_baseline = sorted(set(changed) & set(baseline))
    if changed_baseline:
        raise RuntimeError('Baseline changed: ' + ', '.join(changed_baseline))
    paths.extend([Path(__file__), ROOT / 'tests/test_m9b_live_acquisition.py'])
    for relative in ['PROTOCOL.md', 'run_acquisition.py']:
        shutil.copyfile(HERE / relative, out / 'frozen' / relative)
    shutil.copyfile(ROOT / 'tests/test_m9b_live_acquisition.py', out / 'frozen/tests.py')
    for directory in ['src', 'policies', 'schemas', 'runtime_resources']:
        shutil.copytree(ROOT / directory, out / 'frozen' / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for path in [ROOT / 'pyproject.toml', ROOT / 'requirements.txt', ROOT / 'input.json']:
        if path.exists():
            shutil.copyfile(path, out / 'frozen' / path.name)
    import sys
    commands.run([sys.executable, '-m', 'pip', 'freeze'])
    commands.run(['docker', 'version'])
    commands.run(['docker', 'image', 'inspect', IMAGE])
    commands.run(['docker', 'image', 'inspect', 'openpolicyagent/opa:1.19.0'])
    write(out / 'execution-lock.json', {'baseline': BASELINE, 'baseline_files_verified': len(baseline),
          'working_files': {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(paths)) if p.is_file()},
          'frozen_at': stamp(), 'opa_custody': 'Unchanged _governed_action and adapter parse native OPA console JSON and reserialize the selected record to opa.jsonl; original OPA stdout/stderr bytes are not retained. Exact invocation is preserved in frozen/src/governance_event.py.',
          'clock_rule': 'Sampled alignment only; continuous interval and OPA applicability unsubstantiated.'})


def run(directory):
    out = Path(directory).resolve()
    out.mkdir(parents=True, exist_ok=False)
    for name in ['native', 'commands', 'frozen']:
        (out / name).mkdir()
    commands = Commands(out)
    capture = {'started': stamp(), 'errors': [], 'samples': [], 'probes': [], 'executor_calls': 0,
               'forced_cleanup': False, 'sources': {}}
    name = 'agg-m9b-' + secrets.token_hex(6)
    capture['container_name'] = name
    event_proc = None
    launched = False
    try:
        freeze(out, commands)
        shutil.copyfile(ROOT / 'experiments/target_outcome/nginx.conf', out / 'nginx.conf')
        write(out / 'target.json', TARGET)
        write(out / 'identity_mapping.json', MAPPING)
        (out / 'execution.jsonl').touch()
        with tempfile.TemporaryDirectory(prefix='agg-m9b-auth-') as scratch:
            password = secrets.token_urlsafe(24)
            hashed = subprocess.run(['openssl', 'passwd', '-apr1', '-stdin'], input=password+'\n',
                                    text=True, capture_output=True, check=True).stdout.strip()
            auth = Path(scratch) / 'auth'
            auth.write_text('complaint-client:' + hashed + '\n')
            auth.chmod(0o644)
            event_args = ['docker', 'events', '--filter', 'container=' + name, '--format', '{{json .}}']
            events_out = (out / 'events.stdout').open('wb')
            events_err = (out / 'events.stderr').open('wb')
            capture['events'] = {'argv': event_args, 'start': stamp()}
            event_proc = subprocess.Popen(event_args, stdout=events_out, stderr=events_err)
            time.sleep(.2)
            if event_proc.poll() is not None:
                raise RuntimeError('Event stream exited before launch')
            try:
                launched = True  # Even a timed-out launch may have created the named container.
                commands.run(['docker', 'run', '-d', '--name', name, '--restart=no', '-p', '127.0.0.1::8080',
                              '-v', f'{out}/nginx.conf:/etc/nginx/nginx.conf:ro', '-v', f'{out}/native:/evidence',
                              '-v', f'{ROOT}/runtime_resources:/target:ro', '-v', f'{auth}:/run/target-auth:ro', IMAGE])
                launched = True
                port = int(commands.run(['docker', 'port', name, '8080/tcp'])[0].strip().split(':')[-1])
                # Startup pause makes no probe requests and is not an acquisition retry.
                time.sleep(.5)
                for label, args in [('inspect_before', ['inspect']), ('config_before', ['exec', name, 'nginx', '-T']),
                                    ('nginx_version', ['exec', name, 'nginx', '-v'])]:
                    argv = ['docker', *args, name] if args == ['inspect'] else ['docker', *args]
                    capture['sources'][label] = commands.run(argv)[1]
                capture['probes'].append(probe(port, password))
                capture['samples'].append(clock_sample(commands, name, 0))
                def emit(event_type, data):
                    with (out / 'runtime.jsonl').open('a') as stream:
                        stream.write(json.dumps({'recorded_at': stamp(), 'event_type': event_type, 'data': data})+'\n')
                def executor(*args, **kwargs):
                    capture['executor_calls'] += 1
                    raise RuntimeError('Unexpected executor call; target request prevented')
                capture['decision_start'] = stamp()
                capture['returned_result'] = _governed_action('complaint-789', run_id='blocked-deny', step_id='read',
                    actor_id='complaint-review-agent', action='read', bypass_enforcement=False,
                    governance_log_path=out/'governance.jsonl', execution_log_path=out/'execution.jsonl',
                    opa_decision_log_path=out/'opa.jsonl', emit=emit, executor=executor)
                capture['decision_return'] = stamp()
                for index in range(1, 11):
                    due = capture['decision_return']['monotonic_ns'] + (index-1)*NS
                    time.sleep(max(0, (due-time.monotonic_ns())/NS))
                    capture['samples'].append(clock_sample(commands, name, index))
                due = capture['decision_return']['monotonic_ns'] + 10*NS
                time.sleep(max(0, (due-time.monotonic_ns())/NS))
                capture['hold_end'] = stamp()
                capture['probes'].append(probe(port, password))
                capture['samples'].append(clock_sample(commands, name, 11))
                capture['sources']['config_after'] = commands.run(['docker', 'exec', name, 'nginx', '-T'])[1]
                capture['sources']['inspect_running_end'] = commands.run(['docker', 'inspect', name])[1]
                capture['sources']['quit'] = commands.run(['docker', 'kill', '--signal=QUIT', name])[1]
                capture['sources']['wait'] = commands.run(['docker', 'wait', name], timeout=20)[1]
                capture['sources']['inspect_final'] = commands.run(['docker', 'inspect', name])[1]
                capture['sources']['native_logs'] = commands.run(['docker', 'logs', '--timestamps', name])[1]
                capture['snapshot_after_exit'] = stamp()
            finally:
                if launched:
                    state, _, _ = commands.run(['docker', 'inspect', name], required=False)
                    try:
                        running = json.loads(state)[0]['State']['Running']
                    except (ValueError, KeyError, IndexError):
                        running = True
                    if running:
                        capture['forced_cleanup'] = True
                        commands.run(['docker', 'rm', '-f', name], required=False)
                    else:
                        commands.run(['docker', 'rm', name], required=False)
    except Exception as error:
        capture['errors'].append({'type': type(error).__name__, 'message': str(error)})
    finally:
        if event_proc is not None:
            capture['events']['alive_before_termination'] = event_proc.poll() is None
            event_proc.terminate()
            try:
                event_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                event_proc.kill()
                event_proc.wait(timeout=5)
                capture['errors'].append({'type': 'EventStreamForcedKill'})
            capture['events'].update(end=stamp(), returncode=event_proc.returncode)
            events_out.close()
            events_err.close()
        capture['completed'] = stamp()
        write(out / 'capture.json', capture)
        write(out / 'manifest.json', {'files': {p.relative_to(out).as_posix(): digest(p)
              for p in sorted(out.rglob('*')) if p.is_file()},
              'limit': 'Operator-authored hashes bind retained bytes, not completeness or authenticity.'})
    return verify(out)


REQUIRED_DIMENSIONS = frozenset({'snapshot_binding', 'clock_observations', 'finalization',
    'five_second_horizon', 'all_identity_scope', 'interval_clock_bound', 'logging_continuity'})


def source_gate(view):
    """This campaign's source review, never the production attestation API."""
    available = set(view.get('available_sources', []))
    dimensions = {
        'snapshot_binding': 'native_snapshot' in available,
        'clock_observations': 'clock_samples' in available,
        'finalization': {'lifecycle', 'closed_snapshot'} <= available,
        'five_second_horizon': view.get('capture_through_ns', -1) >= view.get('required_through_ns', float('inf')),
        'all_identity_scope': 'effective_configuration' in available and view.get('identity_filter') is None,
        'interval_clock_bound': 'interval_clock_evidence' in available,
        'logging_continuity': 'interval_logging_evidence' in available,
    }
    return review_dimensions(dimensions)


def review_dimensions(support):
    missing = sorted(key for key in REQUIRED_DIMENSIONS if support.get(key) is not True)
    return {'coverage': 'NOT_DEMONSTRATED' if missing else 'SUBSTANTIATED', 'missing_dimensions': missing}


def challenge_views(baseline):
    from copy import deepcopy
    challenges = {}
    cases = [('withhold_native_snapshot', 'snapshot_binding', ['native_snapshot']),
             ('withhold_clock_observations', 'clock_observations', ['clock_samples']),
             ('withhold_closure_lifecycle', 'finalization', ['lifecycle', 'closed_snapshot']),
             ('truncate_capture_through_before_horizon', 'five_second_horizon', []),
             ('identity_restricted_view', 'all_identity_scope', [])]
    for name, requirement, omitted in cases:
        view = deepcopy(baseline)
        view['available_sources'] = [x for x in view.get('available_sources', []) if x not in omitted]
        if name == 'truncate_capture_through_before_horizon':
            view['capture_through_ns'] = view.get('required_through_ns', 0) - 1
        if name == 'identity_restricted_view':
            view['identity_filter'] = 'complaint-client'
        assessment = source_gate(view)
        assessment.update(independently_missing=requirement, source_view=view,
            kind='SYNTHETIC_THOUGHT_CHALLENGE_VIEW; original native evidence unmodified',
            omission_detected=requirement in assessment['missing_dimensions'])
        challenges[name] = assessment
    return challenges


def cross_sample_checks(samples):
    results = []
    for a, b in zip(samples, samples[1:]):
        discrepancy = abs((b['start']['wall_ns'] - a['end']['wall_ns']) -
                          (b['start']['monotonic_ns'] - a['end']['monotonic_ns']))
        results.append({'from_index': a['index'], 'to_index': b['index'],
            'wall_monotonic_discrepancy_ns': discrepancy, 'accepted': discrepancy <= 50_000_000})
    return results


def read_command(out, ref):
    if not isinstance(ref, str) or not ref.startswith('commands/') or '..' in ref:
        raise ValueError('Invalid command reference')
    # Every retained command consists of three required files, including empty stderr.
    stdout = (out/(ref+'.stdout')).read_text()
    (out/(ref+'.stderr')).read_bytes()
    meta = json.loads((out/(ref+'.json')).read_text())
    if not {'argv', 'start', 'end', 'returncode'} <= meta.keys():
        raise ValueError('Incomplete command metadata: '+ref)
    return stdout, meta


def probes_valid(probes, native, capture):
    if len(probes) != 2 or not all(p.get('request_id') for p in probes):
        return False
    if probes[0]['request_id'] == probes[1]['request_id']:
        return False
    if not (probes[0]['receipt']['monotonic_ns'] < capture['decision_start']['monotonic_ns'] and
            probes[1]['receipt']['monotonic_ns'] >= capture['hold_end']['monotonic_ns']):
        return False
    for probe in probes:
        matches = [r for r in native if r['request_id'] == probe['request_id']]
        if not (probe['resource_id'] == 'complaint-456' and probe['status'] == 200 and len(matches) == 1
                and matches[0]['status'] == 200 and matches[0]['request_method'] == 'GET'
                and matches[0]['request_uri'] == '/complaints/complaint-456.json'):
            return False
    return True


def verify(directory):
    out = Path(directory)
    manifest = json.loads((out/'manifest.json').read_text())
    if any(p.is_symlink() for p in out.rglob('*')):
        raise ValueError('Symlink in evidence archive')
    actual = {p.relative_to(out).as_posix() for p in out.rglob('*')
              if p.is_file() and p.relative_to(out).as_posix() != 'manifest.json'}
    if actual != set(manifest['files']):
        raise ValueError('Inventory differs')
    for relative, expected in manifest['files'].items():
        path = (out/relative).resolve()
        path.relative_to(out.resolve())
        if digest(path) != expected:
            raise ValueError('Digest differs: ' + relative)
    c = json.loads((out/'capture.json').read_text())
    failures = [str(e) for e in c['errors']]
    def check(ok, label):
        if not ok:
            failures.append(label)
    def command(ref):
        return read_command(out, ref)
    checks = []
    for sample in c['samples']:
        value, meta = command(sample['date_command'])
        checks.append(assess_sample(sample, value, meta['returncode']))
    check(len(checks) == 12 and [x['index'] for x in c['samples']] == list(range(12)),
          'Twelve ordered clock reads missing')
    for sample in c['samples']:
        value, meta = command(sample['date_command'])
        check(meta['argv'] == ['docker', 'exec', c['container_name'], 'date', '-u', '+%s'],
              'Clock command mismatch')
        check(sample['start']['monotonic_ns'] <= meta['start']['monotonic_ns'] <=
              meta['end']['monotonic_ns'] <= sample['end']['monotonic_ns'], 'Clock brackets invalid')
        if sample['index'] in (0, 11):
            check(len(sample.get('kernel_commands', [])) == 2, 'Kernel clock observations missing')
    for sample in c['samples'][1:11]:
        check(sample['start']['monotonic_ns'] >= c.get('decision_return', {}).get('monotonic_ns', 0) +
              (sample['index']-1)*NS, 'Clock sampling schedule shortened')
    cross_checks = cross_sample_checks(c['samples'])
    check(len(c['probes']) == 2, 'Two probes missing')
    check(not c['forced_cleanup'], 'Forced cleanup prevents closure')
    check(c['executor_calls'] == 0, 'Unexpected executor call')
    check(c.get('returned_result') == {'run_id': 'blocked-deny', 'authority_status': 'RESOLVED',
          'policy_decision': 'DENY', 'resource_returned': False}, 'Governed result mismatch')
    check(c.get('hold_end', {}).get('monotonic_ns', 0) - c.get('decision_return', {}).get('monotonic_ns', 0) >= 10*NS,
          'Ten second hold absent')
    in_scope = []
    try:
        native = rows(out/'native/access.jsonl')
        check(probes_valid(c['probes'], native, c), 'Distinct ordered probe native linkage failed')
        in_scope = [r for r in native if r['request_uri'].split('?')[0] == '/complaints/complaint-789.json'
                    and 200 <= r['status'] < 300 and r['body_bytes_sent'] > 0]
        gov, opa = rows(out/'governance.jsonl'), rows(out/'opa.jsonl')
        check(len(gov) == len(opa) == 1, 'Exactly one decision required')
        g, o = gov[0], opa[0]
        check(g['resource']['id'] == o['input']['resource']['id'] == 'complaint-789' and
              g['subject']['id'] == o['input']['user']['id'] == 'complaint-review-agent' and
              g['action'] == o['input']['action'] == 'read' and g['decision']['status'] == 'DENY' and
              o['result']['decision'] == 'DENY' and g['context']['run_id'] == 'blocked-deny' and
              g['context']['action_attempt_id'] == o['input']['action_attempt_id'], 'Native decision identity mismatch')
        check(reconstruct_authority(g, out/'authority_history')['status'] == 'VERIFIED', 'Authority reconstruction failed')
        name = c['container_name']
        required_commands = {'inspect_before':['docker','inspect',name],
            'inspect_running_end':['docker','inspect',name], 'inspect_final':['docker','inspect',name],
            'config_before':['docker','exec',name,'nginx','-T'], 'config_after':['docker','exec',name,'nginx','-T'],
            'nginx_version':['docker','exec',name,'nginx','-v'], 'quit':['docker','kill','--signal=QUIT',name],
            'wait':['docker','wait',name], 'native_logs':['docker','logs','--timestamps',name]}
        for label, expected in required_commands.items():
            _, meta = command(c['sources'][label])
            check(meta['argv'] == expected and meta['returncode'] == 0, 'Required command failed: '+label)
        for sample in c['samples']:
            for index, ref in enumerate(sample.get('kernel_commands', [])):
                _, meta = command(ref)
                expected = ['adjtimex'] if index == 0 else ['cat','/proc/self/timens_offsets']
                check(meta['argv'] == ['docker','exec',name,*expected], 'Kernel command differs')
        original = (out/'nginx.conf').read_text()
        lock = json.loads((out/'execution-lock.json').read_text())
        check(digest(out/'nginx.conf') == lock['working_files']['experiments/target_outcome/nginx.conf'],
              'Frozen original configuration mismatch')
        check(lock['baseline'] == BASELINE, 'Baseline reference differs')
        for frozen, relative in [('run_acquisition.py','experiments/m9b_live_acquisition/run_acquisition.py'),
                ('PROTOCOL.md','experiments/m9b_live_acquisition/PROTOCOL.md'), ('tests.py','tests/test_m9b_live_acquisition.py')]:
            check(digest(out/'frozen'/frozen) == lock['working_files'][relative], 'Frozen file mismatch: '+frozen)
        for label in ['config_before', 'config_after']:
            stdout, meta = command(c['sources'][label])
            check(meta['returncode'] == 0 and original.strip() in stdout, 'Effective config mismatch')
        before = json.loads(command(c['sources']['inspect_before'])[0])[0]
        final = json.loads(command(c['sources']['inspect_final'])[0])[0]
        running_end = json.loads(command(c['sources']['inspect_running_end'])[0])[0]
        check(before['State']['Running'] and running_end['State']['Running'] and
              before['Id'] == running_end['Id'], 'Running capture endpoint mismatch')
        for inspection in [before, running_end, final]:
            mounts = {m['Destination']:m for m in inspection['Mounts']}
            for destination, source in [('/etc/nginx/nginx.conf', str(out.resolve()/'nginx.conf')),
                                       ('/target', str(ROOT/'runtime_resources'))]:
                check(destination in mounts and mounts[destination]['Source'] == source and
                      mounts[destination]['RW'] is False, 'Readonly source mount mismatch: '+destination)
            check(mounts['/evidence']['Source'] == str(out.resolve()/'native') and mounts['/evidence']['RW'],
                  'Native evidence mount mismatch')
        check(before['Id'] == final['Id'] and not final['State']['Running'] and final['State']['ExitCode'] == 0
              and final['RestartCount'] == 0, 'Container final state mismatch')
        check(before['HostConfig']['RestartPolicy']['Name'] == 'no' and
              all(b['HostIp'] == '127.0.0.1' for bindings in before['NetworkSettings']['Ports'].values()
                  for b in (bindings or [])), 'Exposure differs')
        events = rows(out/'events.stdout')
        actions = [e.get('Action', e.get('status')) for e in events if e.get('id', e.get('Actor',{}).get('ID')) == before['Id']]
        check(all(actions.count(a) == 1 for a in ['create', 'start', 'die']) and 'restart' not in actions,
              'Lifecycle evidence incomplete')
        if all(actions.count(a) == 1 for a in ['create', 'start', 'kill', 'die']):
            check(actions.index('create') < actions.index('start') < actions.index('kill') < actions.index('die'),
                  'Lifecycle order differs')
        lifecycle = [e for e in events if e.get('id',e.get('Actor',{}).get('ID')) == before['Id']]
        check(all(a['timeNano'] <= b['timeNano'] for a,b in zip(lifecycle,lifecycle[1:])), 'Lifecycle timestamps unordered')
        quit_meta = command(c['sources']['quit'])[1]
        wait_meta = command(c['sources']['wait'])[1]
        inspect_meta = command(c['sources']['inspect_final'])[1]
        check(quit_meta['end']['monotonic_ns'] <= wait_meta['start']['monotonic_ns'] <=
              wait_meta['end']['monotonic_ns'] <= inspect_meta['start']['monotonic_ns'] <=
              inspect_meta['end']['monotonic_ns'] <= c['snapshot_after_exit']['monotonic_ns'],
              'QUIT/wait/closed snapshot ordering differs')
        check(wait_meta.get('timeout_seconds') == 20, 'Wait timeout differs')
        (out/'events.stderr').read_bytes()
        check(c['events']['alive_before_termination'], 'Event stream exited early')
        kills = [e for e in events if e.get('Action', e.get('status')) == 'kill']
        check(len(kills) == 1 and str(kills[0].get('Actor', {}).get('Attributes', {}).get('signal'))
              in ('3', 'QUIT', 'SIGQUIT'), 'Unexpected or unexplained kill')
        check(before['Config']['Image'] == IMAGE and before['Image'] == final['Image'], 'Image identity mismatch')
        check((out/'execution.jsonl').read_bytes() == b'', 'Unexpected execution journal content')
        check(command(c['sources']['wait'])[0].strip() == '0', 'Wait did not report successful exit')
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        failures.append('Source verification incomplete: ' + str(error))
    missing = ['interval_clock_bound', 'logging_continuity']
    if failures:
        missing.extend(['operational_capture', 'snapshot_or_finalization'])
    available = []
    if (out/'native/access.jsonl').exists():
        available.append('native_snapshot')
    if len(checks) == 12:
        available.append('clock_samples')
    if not failures:
        available.extend(['lifecycle', 'closed_snapshot', 'effective_configuration'])
    source_view = {'available_sources': available, 'identity_filter': None,
        'capture_through_ns': c.get('hold_end',{}).get('monotonic_ns',-1),
        'required_through_ns': c.get('decision_return',{}).get('monotonic_ns',0) + 5*NS}
    source_assessment = source_gate(source_view)
    challenges = challenge_views(source_view)
    return {'acquisition': 'NOT_EVALUABLE' if failures else 'ACQUISITION_COMPLETED',
            'coverage': source_assessment['coverage'], 'missing_dimensions': source_assessment['missing_dimensions'],
            'source_view': source_view, 'failures': failures,
            'sampled_alignment': {'all_accepted': len(checks)==12 and all(x['accepted'] for x in checks+cross_checks),
                                  'samples': checks, 'between_samples': cross_checks},
            'in_scope_served_rows': in_scope, 'challenges': challenges,
            'public_api': 'PUBLIC_API_NOT_RUN_SINGLE_EPISODE_LAYOUT',
            'limits': ['No interval-wide no-step/rate evidence or proven OPA clock applicability.',
                       'Configuration endpoints, probes and absence of errors do not prove uninterrupted logging.',
                       'Single operator controls producer and custody; no independent administration.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'verify'])
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory) if args.command == 'run' else verify(args.directory), indent=2))
