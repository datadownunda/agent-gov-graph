"""Frozen, one-shot stock OPA experiment. Hashes establish custody, not authenticity."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/opa_producer_conformance'
BASE = '28c252337ea50e082d3c348680b7dbc54b0f0751'
IMAGE = 'openpolicyagent/opa:1.19.0'
SENTINELS = ['CALLER-SAME', '00000000-0000-4000-8000-000000000000', 'CALLER-NESTED', 'CALLER-DENY']
UUID = re.compile(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\Z')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def read(path):
    # Duplicate JSON keys cannot silently overwrite native evidence.
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError('duplicate JSON key: ' + k)
            result[k] = v
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def inputs(base):
    result = []
    for i in range(8):
        item = deepcopy(base)
        if 2 <= i < 4:
            item['decision_id'] = SENTINELS[0]
        elif 4 <= i < 6:
            item['decision_id'] = SENTINELS[1]
            item['user']['decision_id'] = SENTINELS[2]
        elif i >= 6:
            item['decision_id'] = SENTINELS[3]
            item['authorized_resource_ids'] = []
        result.append(item)
    return result


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def baseline():
    entries = git('ls-tree', '-r', '-z', BASE).split(b'\0')[:-1]
    blobs = [(entry.split(b'\t', 1)[1].decode(), entry.split(b'\t', 1)[0].split()[2]) for entry in entries]
    stream = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                            input=b'\n'.join(oid for _, oid in blobs) + b'\n',
                            check=True, capture_output=True).stdout
    offset = 0; result = {}
    for name, oid in blobs:
        end = stream.index(b'\n', offset)
        header = stream[offset:end].split()
        if header[0] != oid or header[1] != b'blob':
            raise ValueError('unexpected baseline object')
        size = int(header[2]); start = end + 1
        result[name] = digest(stream[start:start + size])
        offset = start + size + 1
    return result


def preserved(expected):
    return all((ROOT / p).is_file() and digest((ROOT / p).read_bytes()) == h for p, h in expected.items())


def argv(image, bundle):
    return ['docker', 'run', '--rm', '--network=none', '-i', '-v', f'{bundle}:/policies:ro', image,
            'exec', '--stdin-input', '--bundle', '/policies', '--decision', '/agentgov/complaints/decision',
            '--set=decision_logs.console=true', '--log-format=json']


def evaluate(out):
    """Recompute only from process-custodied raw bytes and the frozen inventory."""
    checks = {}; rows = []; errors = []
    def check(name, condition):
        checks[name] = bool(condition)
    try:
        lock = read(out / 'execution-lock.json')
        capture = read(out / 'capture.json')
        source = read(out / 'frozen/source-review.json')
        check('source_review', source.get('status') == 'SUPPORTED' and source.get('scope') == 'stock-opa-exec-1.19.0'
              and isinstance(source.get('references'), list) and bool(source['references']))
        inspect = read(out / 'runtime/inspect.stdout')
        version = (out / 'runtime/version.stdout').read_text()
        check('runtime_identity', len(inspect) == 1 and inspect[0]['Id'] == lock['image_id']
              and bool(re.fullmatch(r'sha256:[0-9a-f]{64}', lock['image_id']))
              and re.search(r'^Version: 1\.19\.0\s*$', version, re.M) is not None)
        check('preflight_exit', all(read(out / f'runtime/{n}.json')['returncode'] == 0 for n in ('inspect', 'version')))
        check('capture_complete', capture['complete'] is True and not capture['errors'] and capture['count'] == 8)
        check('baseline_preserved', lock['baseline_commit'] == BASE and preserved(lock['baseline_files']))
        check('protocol_unchanged', (out / 'frozen/PROTOCOL.md').read_bytes() == (HERE / 'PROTOCOL.md').read_bytes())
        check('frozen_files', all(digest((out / n).read_bytes()) == h for n, h in lock['frozen_files'].items()))
        expected = inputs(read(out / 'frozen/input.json'))
        for i, submitted in enumerate(expected, 1):
            folder = out / f'invocations/{i:03}'
            meta = read(folder / 'invocation.json')
            rawinput = read(folder / 'input.json')
            stdout = read(folder / 'stdout.bin')
            native = []
            for line in (folder / 'stderr.bin').read_bytes().splitlines():
                if not line.strip():
                    continue
                # Parse each event strictly through the same duplicate-key guard.
                event = json.loads(line, object_pairs_hook=_unique)
                if not isinstance(event, dict):
                    raise ValueError('non-object log event')
                if event.get('type') == 'openpolicyagent.org/decision_logs':
                    native.append(event)
            check(f'{i}:custody', meta['argv'] == argv(lock['image_id'], lock['bundle_mount'])
                  and meta['returncode'] == 0 and meta['error'] is None
                  and datetime.fromisoformat(meta['started_at']) <= datetime.fromisoformat(meta['finished_at'])
                  and rawinput == submitted)
            check(f'{i}:cardinality', isinstance(stdout, dict) and isinstance(stdout.get('result'), list)
                  and len(stdout['result']) == 1 and len(native) == 1)
            if not checks[f'{i}:cardinality']:
                continue
            output, log = stdout['result'][0], native[0]
            if not isinstance(output, dict):
                raise ValueError('non-object result record')
            oid, nid = output.get('decision_id'), log.get('decision_id')
            check(f'{i}:ids_present', isinstance(oid, str) and bool(oid) and isinstance(nid, str) and bool(nid))
            check(f'{i}:uuid', isinstance(oid, str) and isinstance(nid, str) and UUID.fullmatch(oid) and UUID.fullmatch(nid))
            check(f'{i}:id_agreement', oid == nid)
            check(f'{i}:caller_ids_differ', oid not in SENTINELS and nid not in SENTINELS)
            check(f'{i}:logged_input', log.get('input') == submitted)
            result = output.get('result')
            check(f'{i}:policy_result', isinstance(result, dict) and result == log.get('result')
                  and result.get('decision') == ('ALLOW' if i <= 6 else 'DENY')
                  and result.get('allowed') is (i <= 6))
            rows.append({'case': i, 'output_id': oid, 'native_id': nid})
        check('distinct_native_ids', len(rows) == 8 and len({r['native_id'] for r in rows if isinstance(r['native_id'], str)}) == 8)
        check('exact_pair_inputs', all((out / f'invocations/{a:03}/input.json').read_bytes() ==
                                      (out / f'invocations/{a+1:03}/input.json').read_bytes() for a in (1, 3, 5, 7)))
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        errors.append(f'{type(exc).__name__}: {exc}')
    structural = not errors and len(rows) == 8 and all(v for k, v in checks.items()
        if k not in ('distinct_native_ids',) and not k.endswith((':id_agreement', ':caller_ids_differ', ':uuid')))
    identifiers_evaluable = len(rows) == 8 and all(
        isinstance(r[key], str) and (UUID.fullmatch(r[key]) or r[key] in SENTINELS)
        for r in rows for key in ('output_id', 'native_id'))
    contradiction = any(not v for k, v in checks.items() if k == 'distinct_native_ids' or k.endswith((':id_agreement', ':caller_ids_differ')))
    verdict = 'NOT_EVALUABLE'
    if structural and identifiers_evaluable and contradiction:
        verdict = 'PRODUCER_CONTRACT_CONTRADICTED'
    elif structural and all(checks.values()):
        verdict = 'PRODUCER_CONTRACT_SUPPORTED'
    return {'verdict': verdict, 'checks': checks, 'observations': rows, 'errors': errors,
            'limitations': ['Eight finite evaluations of the archived stock exec configuration only.',
                'Output and log are two representations of one evaluation, not independent corroborations.',
                'Hashes establish custody consistency, not authentication.',
                'IDs alone establish neither execution, authenticated caller, enforcement nor target outcome.']}


def _unique(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('duplicate JSON key: ' + k)
        result[k] = v
    return result


def inventory(out):
    files = {}
    for p in out.rglob('*'):
        if p.is_symlink():
            raise ValueError('symlink in campaign')
        if p.is_file() and p != out / 'manifest.json':
            files[p.relative_to(out).as_posix()] = digest(p.read_bytes())
    return files


def verify(out):
    manifest = read(out / 'manifest.json')
    if manifest != inventory(out):
        raise ValueError('manifest mismatch (changed, missing or unlisted files)')
    lock = read(out / 'execution-lock.json')
    if lock['baseline_files'] != baseline() or not preserved(lock['baseline_files']):
        raise ValueError('baseline inventory mismatch or baseline modified')
    if (out / 'frozen/PROTOCOL.md').read_bytes() != (HERE / 'PROTOCOL.md').read_bytes():
        raise ValueError('frozen protocol differs from preregistration')
    if digest((out / 'frozen/run_experiment.py').read_bytes()) != digest(Path(__file__).read_bytes()):
        raise ValueError('verifier differs from frozen runner')
    result = evaluate(out)
    if read(out / 'result.json') != result:
        raise ValueError('saved result differs from recomputation')
    return result


def run_process(out, name, args, data=None):
    out.mkdir(parents=True, exist_ok=True)
    meta = {'argv': args, 'started_at': stamp(), 'returncode': None, 'error': None}
    dump(out / f'{name}.json', meta)
    with (out / f'{name}.stdout').open('xb') as stdout, (out / f'{name}.stderr').open('xb') as stderr:
        try:
            process = subprocess.run(args, input=data, stdout=stdout, stderr=stderr, timeout=120)
            meta['returncode'] = process.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            meta['error'] = str(exc)
    meta['finished_at'] = stamp()
    dump(out / f'{name}.json', meta)
    return meta


def capture(out, source_review):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    state = {'complete': False, 'count': 0, 'errors': []}
    try:
        frozen = out / 'frozen'; frozen.mkdir()
        copies = {'PROTOCOL.md': HERE / 'PROTOCOL.md', 'run_experiment.py': Path(__file__),
                  'tests.py': ROOT / 'tests/test_opa_producer_conformance.py', 'input.json': ROOT / 'input.json',
                  'source-review.json': source_review}
        for path in sorted(HERE.glob('*.md')):
            if path.name != 'PROTOCOL.md':
                copies[path.name] = path
        for name, path in copies.items():
            (frozen / name).write_bytes(path.read_bytes())
        for path in sorted((ROOT / 'policies').rglob('*')):
            if path.is_file():
                target = frozen / 'policies' / path.relative_to(ROOT / 'policies')
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(path.read_bytes())
        before = baseline()
        if not preserved(before):
            raise ValueError('baseline files already changed')
        meta = run_process(out / 'runtime', 'inspect', ['docker', 'image', 'inspect', IMAGE])
        if meta['returncode'] != 0 or meta['error']:
            raise ValueError('image inspection unavailable')
        identity = read(out / 'runtime/inspect.stdout')[0]['Id']
        meta = run_process(out / 'runtime', 'version', ['docker', 'run', '--rm', '--network=none', identity, 'version'])
        if meta['returncode'] != 0 or meta['error']:
            raise ValueError('runtime version unavailable')
        lock = {'baseline_commit': BASE, 'baseline_files': before, 'image_tag': IMAGE, 'image_id': identity,
                'bundle_mount': str(frozen / 'policies'), 'frozen_files': inventory(out), 'frozen_at': stamp()}
        dump(out / 'execution-lock.json', lock)
        version = (out / 'runtime/version.stdout').read_text()
        if not re.search(r'^Version: 1\.19\.0\s*$', version, re.M):
            raise ValueError('unexpected OPA version')
        for i, item in enumerate(inputs(read(frozen / 'input.json')), 1):
            folder = out / f'invocations/{i:03}'; folder.mkdir(parents=True)
            data = (frozen / 'input.json').read_bytes() if i <= 2 else (json.dumps(item, sort_keys=True, indent=2) + '\n').encode()
            (folder / 'input.json').write_bytes(data)
            meta = run_process(folder, 'invocation', argv(identity, lock['bundle_mount']), data)
            (folder / 'invocation.stdout').rename(folder / 'stdout.bin')
            (folder / 'invocation.stderr').rename(folder / 'stderr.bin')
            state['count'] += 1
            if meta['error'] or meta['returncode'] != 0:
                raise ValueError(f'invocation {i} failed; no retry')
        state['complete'] = True
    except Exception as exc:
        state['errors'].append(f'{type(exc).__name__}: {exc}')
    dump(out / 'capture.json', state)
    dump(out / 'result.json', evaluate(out))
    dump(out / 'manifest.json', inventory(out))
    return read(out / 'result.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['capture', 'verify'])
    parser.add_argument('directory', type=Path)
    parser.add_argument('--source-review', type=Path)
    args = parser.parse_args()
    if args.command == 'capture' and args.source_review is None:
        parser.error('capture requires --source-review')
    result = capture(args.directory, args.source_review) if args.command == 'capture' else verify(args.directory)
    print(json.dumps(result, indent=2))
    return 0 if result['verdict'] == 'PRODUCER_CONTRACT_SUPPORTED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
