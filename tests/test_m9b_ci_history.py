"""CI checkout prerequisites; these tests make no empirical assurance claim."""
import importlib.util
from pathlib import Path
import subprocess

import pytest


spec = importlib.util.spec_from_file_location(
    'm9b_ci_history', Path(__file__).resolve().parents[1] / 'conftest.py')
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def test_history_hydration_failure_is_not_suppressed(tmp_path):
    origin = tmp_path / 'origin'
    origin.mkdir()
    git(origin, 'init')
    git(origin, '-c', 'user.name=CI Test', '-c', 'user.email=ci@example.invalid',
        'commit', '--allow-empty', '-m', 'baseline')
    baseline = git(origin, 'rev-parse', 'HEAD')
    git(origin, '-c', 'user.name=CI Test', '-c', 'user.email=ci@example.invalid',
        'commit', '--allow-empty', '-m', 'head')
    clone = tmp_path / 'shallow'
    git(tmp_path, 'clone', '--depth=1', origin.as_uri(), str(clone))
    git(clone, 'remote', 'set-url', 'origin', str(tmp_path / 'missing-origin'))
    with pytest.raises(subprocess.CalledProcessError):
        history._ensure_m9b_history(clone, baseline)
    assert git(clone, 'rev-parse', '--is-shallow-repository') == 'true'


def test_history_hydration_keeps_exact_baseline_and_worktree(tmp_path):
    origin = tmp_path / 'origin'
    origin.mkdir()
    git(origin, 'init')
    (origin / 'protected').write_text('baseline')
    git(origin, 'add', 'protected')
    git(origin, '-c', 'user.name=CI Test', '-c', 'user.email=ci@example.invalid',
        'commit', '-m', 'baseline')
    baseline = git(origin, 'rev-parse', 'HEAD')
    (origin / 'protected').write_text('committed modification')
    git(origin, 'add', 'protected')
    git(origin, '-c', 'user.name=CI Test', '-c', 'user.email=ci@example.invalid',
        'commit', '-m', 'head')
    clone = tmp_path / 'shallow'
    git(tmp_path, 'clone', '--depth=1', origin.as_uri(), str(clone))
    before = git(clone, 'rev-parse', 'HEAD')
    history._ensure_m9b_history(clone, baseline)
    assert git(clone, 'rev-parse', '--is-shallow-repository') == 'false'
    assert git(clone, 'rev-parse', 'HEAD') == before
    assert git(clone, 'diff', '--name-only', '--diff-filter=DMRTUXB', baseline) == 'protected'
    assert (clone / 'protected').read_text() == 'committed modification'
