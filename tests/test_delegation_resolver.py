"""Each candidate must independently prove the complete proposed tuple."""
from copy import deepcopy

import pytest

from src.delegation_resolver import resolve_delegation

T = '2026-09-05T12:00:00Z'
START = '2026-09-05T00:00:00Z'
END = '2026-09-06T00:00:00Z'


def scope(*resources, action='read', kind='employee_complaint'):
    return {'action': action, 'resource_type': kind, 'resource_ids': list(resources)}


def authority(principal='root', **changes):
    return {'authority_record_id': principal + '-authority', 'authority_version': '1',
            'principal': principal, 'roles': ['hr_investigator'],
            'permitted_scopes': [scope('complaint-456', 'complaint-789')],
            'valid_from': START, 'valid_to': END, 'delegation_permitted': True} | changes


def authorities(*records):
    return {'schema_version': '2.0', 'source_id': 'test-authority', 'source_version': '1', 'records': list(records)}


def parent(kind='authority', record_id='root-authority', version='1'):
    return {'kind': kind, 'record_id': record_id, 'version': version}


def delegation(**changes):
    return {'delegation_id': 'd1', 'delegation_version': '1', 'delegator': 'root', 'delegate': 'worker',
            'parent': parent(), 'delegated_scopes': [scope('complaint-456')],
            'valid_from': START, 'valid_to': END, 'onward_delegation': False} | changes


def query(actor='worker', **changes):
    return {'actor': actor, 'action': 'read', 'resource_type': 'employee_complaint',
            'resource_id': 'complaint-456', 'effective_at': T} | changes


def solve(*links, roots=None, requested=None):
    return resolve_delegation(requested or query(), authority_revision=authorities(*(roots if roots is not None else [authority()])),
                              delegation_records=list(links))


def issues(result):
    return {i['code'] for c in result['candidates'] for i in c['issues']}


def test_existing_direct_authority_without_delegation_capability():
    root = authority('worker')
    del root['delegation_permitted']
    result = solve(roots=[root])
    assert result['status'] == 'RESOLVED'
    assert result['permission_result'] == 'PERMITTED'
    assert [b['authority_kind'] for b in result['valid_bases']] == ['DIRECT']


def test_valid_one_hop_keeps_identities_separate_and_does_not_inherit_roles():
    result = solve(delegation())
    assert result['status'] == 'RESOLVED'
    basis = result['valid_bases'][0]
    assert basis['proposed_actor'] == 'worker'
    assert basis['root_principal'] == 'root'
    assert basis['authority_kind'] == 'DELEGATED'
    assert basis['chain'] == [parent(), parent('delegation', 'd1')]
    assert 'roles' not in basis


def test_two_hops_narrow_without_merging():
    a = delegation(delegate='middle', onward_delegation=True,
                   delegated_scopes=[scope('complaint-456', 'complaint-789')])
    b = delegation(delegation_id='d2', delegator='middle', parent=parent('delegation', 'd1'))
    result = solve(a, b)
    assert result['permission_result'] == 'PERMITTED'
    assert len(result['valid_bases'][0]['chain']) == 3
    assert result['valid_bases'][0]['effective_scopes'] == [scope('complaint-456')]


@pytest.mark.parametrize('changes,code', [
    ({'delegated_scopes': [scope('complaint-456', action='export')]}, 'DELEGATION_SCOPE_EXCEEDED'),
    ({'delegated_scopes': [scope('unknown')]}, 'DELEGATION_SCOPE_EXCEEDED'),
    ({'delegated_scopes': [scope('complaint-456', kind='other')]}, 'DELEGATION_SCOPE_EXCEEDED'),
    ({'valid_to': None}, 'DELEGATION_VALIDITY_EXCEEDED'),
    ({'valid_from': '2026-09-04T00:00:00Z'}, 'DELEGATION_VALIDITY_EXCEEDED'),
    ({'valid_to': T}, 'DELEGATION_EXPIRED'),
    ({'valid_from': '2026-09-05T13:00:00Z'}, 'DELEGATION_NOT_YET_VALID'),
    ({'parent': parent('delegation', 'missing')}, 'DELEGATION_CHAIN_BROKEN'),
    ({'delegator': 'impostor'}, 'DELEGATION_CHAIN_BROKEN'),
    ({'onward_delegation': 'yes'}, 'EVIDENCE_DEFECT'),
    ({'valid_from': 'bad'}, 'EVIDENCE_DEFECT'),
])
def test_path_failure_is_not_permission_denial(changes, code):
    result = solve(delegation(**changes))
    assert code in issues(result)
    assert result['permission_result'] == 'NOT_EVALUABLE'
    assert result['valid_bases'] == []


def test_root_cannot_delegate_by_merely_possessing_scope():
    missing = authority()
    del missing['delegation_permitted']
    for root in [authority(delegation_permitted=False), missing]:
        result = solve(delegation(), roots=[root])
        assert 'DELEGATION_NOT_PERMITTED' in issues(result)


def test_onward_permission_required_at_every_link():
    a = delegation(delegate='middle')
    b = delegation(delegation_id='d2', delegator='middle', parent=parent('delegation', 'd1'))
    assert 'ONWARD_DELEGATION_NOT_PERMITTED' in issues(solve(a, b))


def test_upstream_expiry_and_root_revocation_invalidate_descendants():
    a = delegation(delegate='middle', onward_delegation=True, valid_to=T)
    b = delegation(delegation_id='d2', delegator='middle', parent=parent('delegation', 'd1'))
    assert 'DELEGATION_EXPIRED' in issues(solve(a, b))
    result = solve(delegation(), roots=[authority(valid_to=T), authority(authority_version='2',
                    valid_from=T, permitted_scopes=[], delegation_permitted=False)])
    assert result['permission_result'] == 'NOT_EVALUABLE'
    assert 'DELEGATION_EXPIRED' in issues(result)


def test_cycles_are_explicit():
    a = delegation(delegator='middle', parent=parent('delegation', 'd2'))
    b = delegation(delegation_id='d2', delegate='middle', delegator='worker', parent=parent('delegation', 'd1'))
    assert 'DELEGATION_CYCLE' in issues(solve(a, b))
    assert 'DELEGATION_CYCLE' in issues(solve(delegation(delegator='worker')))


def test_no_direct_or_delegated_evidence():
    result = solve()
    assert result['status'] == 'INSUFFICIENT_EVIDENCE'
    assert result['permission_result'] == 'NOT_EVALUABLE'


def test_valid_chain_outside_proposal_is_not_permitted():
    result = solve(delegation(delegated_scopes=[scope('complaint-789')]))
    assert result['status'] == 'RESOLVED'
    assert result['permission_result'] == 'NOT_PERMITTED'
    assert result['valid_bases'] == []
    assert result['candidates'][0]['status'] == 'RESOLVED'


def test_multiple_valid_delegated_bases_are_not_conflict():
    result = solve(delegation(), delegation(delegation_id='independent'))
    assert result['status'] == 'MULTIPLE_VALID_BASES'
    assert len(result['valid_bases']) == 2
    assert result['permission_result'] == 'PERMITTED'
    assert not issues(result)
    assert 'preferred_basis' not in result


def test_direct_and_delegated_bases_coexist():
    result = solve(delegation(), roots=[authority(), authority('worker')])
    assert result['status'] == 'MULTIPLE_VALID_BASES'
    assert {b['authority_kind'] for b in result['valid_bases']} == {'DIRECT', 'DELEGATED'}


def test_equivalent_direct_records_preserved_as_bases_under_m4():
    a = authority('worker')
    b = a | {'authority_record_id': 'equivalent'}
    assert solve(roots=[a, b])['status'] == 'MULTIPLE_VALID_BASES'


@pytest.mark.parametrize('bad', [
    delegation(delegation_id='bad', delegated_scopes=[scope('unknown')]),
    delegation(delegation_id='bad', parent=parent('delegation', 'missing')),
    delegation(delegation_id='bad', onward_delegation='bad'),
])
def test_invalid_path_does_not_poison_independent_valid_basis(bad):
    result = solve(delegation(), bad)
    assert result['status'] == 'RESOLVED'
    assert len(result['valid_bases']) == 1
    assert issues(result)
    assert len(result['candidates']) == 2


def test_conflicting_identity_cannot_be_resolved_by_pinning_or_poison_other_path():
    bad = delegation(delegation_id='conflicted')
    contradicts = bad | {'delegated_scopes': [scope('complaint-789')]}
    result = solve(bad, contradicts, delegation())
    assert result['permission_result'] == 'PERMITTED'
    assert len(result['valid_bases']) == 1
    assert 'DELEGATION_CONFLICT' in issues(result)
    child = delegation(delegation_id='child', delegator='worker', delegate='leaf', parent=parent('delegation', 'conflicted'))
    assert 'DELEGATION_CONFLICT' in issues(solve(bad, contradicts, child, requested=query('leaf')))


def test_overlapping_versions_of_same_link_are_conflict_not_independent_grants():
    result = solve(delegation(), delegation(delegation_version='2', parent=parent(record_id='different')))
    assert 'DELEGATION_CONFLICT' in issues(result)
    assert not result['valid_bases']


def test_different_parents_with_distinct_delegation_ids_are_independent():
    a = delegation()
    b = delegation(delegation_id='d2', delegator='root2', parent=parent(record_id='root2-authority'))
    assert solve(a, b, roots=[authority(), authority('root2')])['status'] == 'MULTIPLE_VALID_BASES'


def test_no_cross_path_tuple_assembly_or_scope_union():
    a = delegation(delegated_scopes=[scope('complaint-789')])
    b = delegation(delegation_id='d2', delegated_scopes=[scope('complaint-456', action='export')])
    roots = [authority(permitted_scopes=[scope('complaint-789'), scope('complaint-456', action='export')])]
    result = solve(a, b, roots=roots)
    assert result['permission_result'] == 'NOT_PERMITTED'
    assert result['valid_bases'] == []


def test_parent_scopes_not_merged_to_legitimize_expanded_child():
    a = delegation(delegate='middle')
    sibling = delegation(delegation_id='sibling', delegate='middle', delegated_scopes=[scope('complaint-789')])
    child = delegation(delegation_id='child', delegator='middle', parent=parent('delegation', 'd1'),
                       delegated_scopes=[scope('complaint-456', 'complaint-789')])
    assert 'DELEGATION_SCOPE_EXCEEDED' in issues(solve(a, sibling, child))


def test_m4_root_conflict_not_bypassed_but_unrelated_root_can_support_actor():
    bad_root = authority(permitted_scopes=[] , authority_record_id='conflicting')
    good = delegation(delegation_id='good', delegator='root2', parent=parent(record_id='root2-authority'))
    result = solve(delegation(), good, roots=[authority(), bad_root, authority('root2')])
    assert len(result['valid_bases']) == 1
    assert 'DELEGATION_CONFLICT' in issues(result)


def test_conflicting_root_delegation_capability_only_affects_derived_path():
    root = authority()
    other = root | {'authority_record_id': 'other', 'delegation_permitted': False}
    result = solve(delegation(), roots=[root, other])
    assert 'DELEGATION_CONFLICT' in issues(result)
    direct = solve(roots=[root, other], requested=query('root'))
    assert direct['status'] == 'MULTIPLE_VALID_BASES'


def test_order_and_exact_duplicates_do_not_change_assessment():
    links = [delegation(), delegation(delegation_id='other'), delegation(delegation_id='bad', parent=parent('delegation', 'missing'))]
    assert solve(*links) == solve(*reversed(links), deepcopy(links[0]))


def test_nanosecond_and_timezone_boundaries_reuse_m4():
    a = delegation(valid_to='2026-09-05T12:00:00.000000002Z')
    assert solve(a, requested=query(effective_at='2026-09-05T08:00:00.000000001-04:00'))['permission_result'] == 'PERMITTED'
    assert 'DELEGATION_EXPIRED' in issues(solve(a, requested=query(effective_at='2026-09-05T12:00:00.000000002Z')))


def test_equivalent_overlapping_versions_are_not_false_conflicts():
    result = solve(delegation(), delegation(delegation_version='2', valid_to='2026-09-05T18:00:00Z'))
    assert result['status'] == 'MULTIPLE_VALID_BASES'
    assert len(result['valid_bases']) == 2
    assert not issues(result)


def test_unassignable_malformed_record_remains_visible_without_poisoning_basis():
    result = solve(delegation(), {'unexpected': 'raw evidence'})
    assert result['permission_result'] == 'PERMITTED'
    assert result['evidence_issues'][0]['code'] == 'EVIDENCE_DEFECT'


def test_direct_nonpermission_does_not_override_valid_delegated_scope():
    result = solve(delegation(), roots=[authority(), authority('worker', permitted_scopes=[])])
    assert result['status'] == 'RESOLVED'
    assert result['permission_result'] == 'PERMITTED'
    assert [c['permission_result'] for c in result['candidates'] if c['authority_kind'] == 'DIRECT'] == ['NOT_PERMITTED']


def test_rejected_path_does_not_become_not_permitted_when_another_path_lacks_scope():
    result = solve(delegation(delegated_scopes=[scope('complaint-789')]),
                   delegation(delegation_id='bad', parent=parent('delegation', 'missing')))
    assert result['permission_result'] == 'NOT_EVALUABLE'
    assert 'DELEGATION_CHAIN_BROKEN' in issues(result)


def test_invalid_query_and_timestamp_are_rejected_explicitly():
    import jsonschema
    for changes in [{'actor':''}, {'action':''}, {'effective_at':'bad'}, {'effective_at':'2026-09-05T12:00:00'}]:
        with pytest.raises((ValueError, jsonschema.ValidationError)):
            solve(requested=query(**changes))


def test_full_child_scope_is_rejected_even_when_proposed_tuple_fits_parent():
    result = solve(delegation(delegated_scopes=[scope('complaint-456', 'not-authorized')]))
    assert 'DELEGATION_SCOPE_EXCEEDED' in issues(result)
    assert result['permission_result'] == 'NOT_EVALUABLE'


def test_missing_exact_root_cannot_be_replaced_by_same_principal_authority():
    result = solve(delegation(parent=parent(version='missing-version')))
    assert 'DELEGATION_CHAIN_BROKEN' in issues(result)
    assert not result['valid_bases']


def test_three_hops_check_onward_permission_at_middle_link():
    a = delegation(delegate='middle1', onward_delegation=True)
    b = delegation(delegation_id='d2', delegate='middle2', delegator='middle1',
                   parent=parent('delegation', 'd1'), onward_delegation=False)
    c = delegation(delegation_id='d3', delegator='middle2', parent=parent('delegation', 'd2'))
    assert 'ONWARD_DELEGATION_NOT_PERMITTED' in issues(solve(a, b, c))
    assert solve(a, b | {'onward_delegation': True}, c)['permission_result'] == 'PERMITTED'


def test_parent_delegate_identity_must_match_child_delegator():
    a = delegation(delegate='actual-middle', onward_delegation=True)
    child = delegation(delegation_id='child', delegator='impostor-middle', parent=parent('delegation', 'd1'))
    assert 'DELEGATION_CHAIN_BROKEN' in issues(solve(a, child))
