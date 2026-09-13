import ast
from pathlib import Path
from experiments.strong_link_assurance.generate import build
from experiments.strong_link_assurance.scope import assess
from experiments.strong_link_assurance.score import ratio
from src.correlation_assertion import native_assertions


def test_worker_has_no_scorer_import():
    path = Path('experiments/strong_link_assurance/worker.py')
    tree = ast.parse(path.read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not any('score' in (name or '') or 'generate' in (name or '') for name in imports)


def test_undefined_precision_is_not_success():
    assert ratio(0, 0) is None


def test_transaction_membership_does_not_establish_scope():
    g = {'role': 'governance', 'evidence_ref': 'g', 'raw': {'context': {'parent_request_id': 'p'}},
         'actor': 'actor', 'action': 'read', 'resource_id': 'r', 'resource_type': 'complaint'}
    e = dict(g, role='execution', evidence_ref='e', raw={'parent_request_id': 'p'})
    result = assess([g, e], [])[0]
    assert result['state'] == 'LINKAGE_CORRECT_SCOPE_NOT_ESTABLISHED'
    assert result['coverage_accepted'] is False
    assert result['relationship_type'] == 'TRANSACTION_MEMBERSHIP'


def test_namespace_parameter_alone_does_not_qualify_record_namespace():
    left = [{'evidence_ref': 'e', 'request_id': 'same', 'namespace': 'A'}]
    right = [{'evidence_ref': 'o', 'request_id': 'same', 'namespace': 'B'}]
    raw = native_assertions(left, right, identifier_field='request_id', namespace='declared', issuer='declared')
    checked = native_assertions(left, right, identifier_field='request_id', namespace='declared', issuer='declared', required_equal_fields=['namespace'])
    assert raw[0]['result']['state'] == 'LINKED'
    assert checked[0]['result']['state'] == 'CONTRADICTED'


def test_parent_topology_uses_distinct_child_ids():
    e, _ = build('parent', 'children')
    assert len({r['request_id'] for r in e['rows']['execution']}) == 2
    assert len({r['parent_request_id'] for r in e['rows']['execution']}) == 1
