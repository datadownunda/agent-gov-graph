"""Restore Git history required by the unchanged frozen M9b harness tests."""
from pathlib import Path
import subprocess

import pytest


M9B_HARNESS_TESTS = frozenset({
    'test_request_capture_replay_and_overwrite_refusal',
    'test_replay_detects_semantic_disagreement_after_valid_inventory',
    'test_failed_capture_preserves_partial_requests_and_does_not_overwrite',
    'test_replay_rejects_execution_freeze_drift',
})


def _ensure_m9b_history(root, baseline):
    """Hydrate a shallow checkout; never replace the frozen baseline or checks."""
    def git(*args):
        return subprocess.run(['git', *args], cwd=root, text=True,
                              capture_output=True, check=True)

    shallow = git('rev-parse', '--is-shallow-repository').stdout.strip()
    if shallow == 'true':
        # A locally present baseline alone cannot establish ancestry across a
        # shallow boundary. Full history is an infrastructure prerequisite.
        git('fetch', '--unshallow', '--no-tags', 'origin')
    git('cat-file', '-e', baseline + '^{commit}')


@pytest.fixture(scope='session')
def m9b_frozen_git_history():
    from experiments.m9b_coverage_substantiation import run_diagnostic as diagnostic

    _ensure_m9b_history(diagnostic.ROOT, diagnostic.BASELINE)


@pytest.fixture(autouse=True)
def m9b_harness_git_history(request):
    expected = Path(__file__).parent / 'tests/test_m9b_coverage_substantiation.py'
    if (Path(str(request.node.path)) == expected
            and request.node.originalname in M9B_HARNESS_TESTS):
        request.getfixturevalue('m9b_frozen_git_history')
