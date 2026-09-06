import json
from copy import deepcopy

import pytest

from src.authority_resolver import preserve_revision
from src.delegation_evidence import preserve_delegation_revision, load_delegation_revision
from src.delegation_reconstruction import create_assertion, reconstruct_delegation
from test_delegation_resolver import authority, authorities, delegation, query


def evidence(tmp_path, links=None):
    ref = preserve_revision(authorities(authority()), tmp_path)
    source = {'schema_version': '1.0', 'source_id': 'test-delegation', 'source_version': '1',
              'authority_revision': ref, 'records': [delegation()] if links is None else links}
    dref = preserve_delegation_revision(source, tmp_path)
    return ref, dref, source


def test_preservation_idempotent_and_content_verified(tmp_path):
    ref, dref, source = evidence(tmp_path)
    assert preserve_delegation_revision(source, tmp_path) == dref
    assert load_delegation_revision(dref, tmp_path) == source
    (tmp_path/dref['file']).write_text('{}')
    with pytest.raises(ValueError):
        load_delegation_revision(dref, tmp_path)
    with pytest.raises(ValueError):
        preserve_delegation_revision(source, tmp_path)


def test_current_registry_mutation_does_not_affect_reconstruction(tmp_path):
    ref, dref, source = evidence(tmp_path)
    assertion = create_assertion(query(), authority_reference=ref, delegation_reference=dref, history_directory=tmp_path)
    before = reconstruct_delegation(assertion, tmp_path)
    assert before['status'] == 'VERIFIED'
    assert before['resolution']['permission_result'] == 'PERMITTED'
    source['records'] = []
    source['source_version'] = '2'
    (tmp_path/'current.json').write_text(json.dumps(source))
    preserve_delegation_revision(source, tmp_path)
    assert reconstruct_delegation(assertion, tmp_path) == before


@pytest.mark.parametrize('which,tamper', [('authority', False), ('delegation', False), ('authority', True), ('delegation', True)])
def test_missing_or_tampered_evidence_cannot_use_embedded_result(tmp_path, which, tamper):
    ref, dref, _ = evidence(tmp_path)
    assertion = create_assertion(query(), authority_reference=ref, delegation_reference=dref, history_directory=tmp_path)
    path = tmp_path/(ref if which == 'authority' else dref)['file']
    if tamper:
        path.write_text('{}')
    else:
        path.unlink()
    result = reconstruct_delegation(assertion, tmp_path)
    assert result['status'] == ('EVIDENCE_DEFECT' if tamper else 'INSUFFICIENT_EVIDENCE')
    assert result['permission_result'] == 'NOT_EVALUABLE'


def test_mismatched_pair_and_changed_assertion_are_rejected(tmp_path):
    ref, dref, _ = evidence(tmp_path)
    assertion = create_assertion(query(), authority_reference=ref, delegation_reference=dref, history_directory=tmp_path)
    altered = deepcopy(assertion)
    altered['resolution']['valid_bases'] = []
    assert reconstruct_delegation(altered, tmp_path)['status'] == 'CONTRADICTED'
    other_ref = preserve_revision(authorities(authority(delegation_permitted=False)), tmp_path)
    altered = deepcopy(assertion)
    altered['authority_revision'] = other_ref
    assert reconstruct_delegation(altered, tmp_path)['status'] == 'EVIDENCE_DEFECT'


def test_whole_revision_preserves_bad_candidates_alongside_valid_basis(tmp_path):
    ref, dref, _ = evidence(tmp_path, [delegation(), delegation(delegation_id='bad', onward_delegation='yes')])
    assertion = create_assertion(query(), authority_reference=ref, delegation_reference=dref, history_directory=tmp_path)
    result = reconstruct_delegation(assertion, tmp_path)
    assert result['status'] == 'VERIFIED'
    assert result['resolution']['permission_result'] == 'PERMITTED'
    assert len(result['resolution']['candidates']) == 2


def m4_event(ref, source, actor='root', resolution_at='2026-09-05T12:00:00Z', opa_at='2026-09-05T12:00:01Z'):
    from src.authority_resolver import resolve_authority, boundary_status
    from src.governance_event import build_event
    first = resolve_authority(actor, effective_at=resolution_at, registry_revision=source)
    second = resolve_authority(actor, effective_at=opa_at, registry_revision=source)
    policy_input = {'user': {'id': actor, 'roles': first['basis']['roles']}, 'action': 'read',
                    'resource': {'id': 'complaint-456', 'type': 'employee_complaint', 'classification': 'restricted'}}
    decision = {'allowed': True, 'decision': 'ALLOW', 'policy': 'employee_complaint_access', 'policy_version': '1.0', 'reasons': []}
    binding = {'rule_version': 'temporal-authority/1', 'authority_resolution_at': resolution_at,
               'opa_decision_at': opa_at, 'revision': ref, 'at_resolution': first, 'at_opa_decision': second,
               'status': boundary_status(first, second)}
    return build_event(policy_input, decision, context={'authority_binding': binding})


def test_m4_event_times_preserved_and_changed_basis_set_is_ambiguous(tmp_path):
    from test_delegation_resolver import parent
    source = authorities(authority(), authority('upstream'))
    ref = preserve_revision(source, tmp_path)
    dsource = {'schema_version': '1.0', 'source_id': 'test-delegation', 'source_version': '1',
               'authority_revision': ref, 'records': [delegation(delegate='root', delegator='upstream',
                   parent=parent(record_id='upstream-authority'), valid_from='2026-09-05T12:00:00.000000001Z')]}
    dref = preserve_delegation_revision(dsource, tmp_path)
    event = m4_event(ref, source)
    assertion = create_assertion(query('root', effective_at='2026-09-05T12:00:01Z'),
                    authority_reference=ref, delegation_reference=dref, history_directory=tmp_path, governance_event=event)
    assert assertion['governance_binding']['authority_resolution_at'] != assertion['governance_binding']['opa_decision_at']
    assert assertion['resolution']['status'] == 'MULTIPLE_VALID_BASES'
    assert assertion['governance_binding']['at_authority_resolution']['status'] == 'RESOLVED'
    audit = reconstruct_delegation(assertion, tmp_path, governance_event=event)
    assert audit['status'] == 'TEMPORAL_BOUNDARY_AMBIGUITY'
    assert audit['permission_result'] == 'NOT_EVALUABLE'
    assert reconstruct_delegation(assertion, tmp_path)['status'] == 'INSUFFICIENT_EVIDENCE'


def test_m4_boundary_ambiguity_cannot_be_bypassed_by_m5(tmp_path):
    source = authorities(authority(valid_to='2026-09-05T12:00:00.000000001Z'),
                         authority(authority_version='2', valid_from='2026-09-05T12:00:00.000000001Z'))
    ref = preserve_revision(source, tmp_path)
    dref = preserve_delegation_revision({'schema_version':'1.0','source_id':'test','source_version':'1',
                                        'authority_revision':ref,'records':[]}, tmp_path)
    event = m4_event(ref, source)
    assertion = create_assertion(query('root', effective_at='2026-09-05T12:00:01Z'), authority_reference=ref,
                                 delegation_reference=dref, history_directory=tmp_path, governance_event=event)
    assert assertion['governance_binding']['m4_reconstruction']['status'] == 'TEMPORAL_BOUNDARY_AMBIGUITY'
    assert reconstruct_delegation(assertion, tmp_path, governance_event=event)['status'] == 'TEMPORAL_BOUNDARY_AMBIGUITY'


def test_changes_to_rejected_path_do_not_poison_stable_basis(tmp_path):
    from test_delegation_resolver import parent
    source = authorities(authority())
    ref = preserve_revision(source, tmp_path)
    dref = preserve_delegation_revision({'schema_version':'1.0','source_id':'test','source_version':'1',
        'authority_revision':ref,'records':[delegation(delegate='root', parent=parent('delegation', 'missing'),
                                                     valid_from='2026-09-05T12:00:00.000000001Z')]}, tmp_path)
    event = m4_event(ref, source)
    assertion = create_assertion(query('root', effective_at='2026-09-05T12:00:01Z'), authority_reference=ref,
                                 delegation_reference=dref, history_directory=tmp_path, governance_event=event)
    assert assertion['governance_binding']['boundary_status'] == 'STABLE'
    audit = reconstruct_delegation(assertion, tmp_path, governance_event=event)
    assert audit['status'] == 'VERIFIED'
    assert audit['permission_result'] == 'PERMITTED'


@pytest.mark.parametrize('change', [{'actor':'other'}, {'resource_id':'complaint-789'}, {'action':'export'},
                                    {'effective_at':'2026-09-05T12:00:02Z'}])
def test_m4_query_identity_and_time_cannot_be_substituted(tmp_path, change):
    ref, dref, _ = evidence(tmp_path)
    event = m4_event(ref, authorities(authority()))
    with pytest.raises(ValueError):
        create_assertion(query('root', effective_at='2026-09-05T12:00:01Z') | change, authority_reference=ref,
                         delegation_reference=dref, history_directory=tmp_path, governance_event=event)


def test_no_current_registry_reads_during_reconstruction(tmp_path, monkeypatch):
    from src import authority_resolver
    ref, dref, _ = evidence(tmp_path)
    assertion = create_assertion(query(), authority_reference=ref, delegation_reference=dref, history_directory=tmp_path)
    original = authority_resolver.load_authority_source
    def schema_only(path=authority_resolver.AUTHORITY_SOURCE_PATH):
        assert str(path).endswith('.schema.json'), 'Read a current registry'
        return original(path)
    monkeypatch.setattr(authority_resolver, 'load_authority_source', schema_only)
    assert reconstruct_delegation(assertion, tmp_path)['status'] == 'VERIFIED'


def test_audit_preserves_multiple_valid_bases(tmp_path):
    ref, dref, _ = evidence(tmp_path, [delegation(), delegation(delegation_id='independent')])
    assertion = create_assertion(query(), authority_reference=ref, delegation_reference=dref, history_directory=tmp_path)
    audit = reconstruct_delegation(assertion, tmp_path)
    assert audit['status'] == 'VERIFIED'
    assert audit['resolution']['status'] == 'MULTIPLE_VALID_BASES'
    assert len(audit['resolution']['valid_bases']) == 2


def test_bad_references_and_unknown_rule_fail_explicitly(tmp_path):
    ref, dref, _ = evidence(tmp_path)
    assertion = create_assertion(query(), authority_reference=ref, delegation_reference=dref, history_directory=tmp_path)
    for bad_ref in [dref | {'file': '../current.json'}, dref | {'source_version': 'other'}]:
        with pytest.raises(ValueError):
            load_delegation_revision(bad_ref, tmp_path)
    altered = deepcopy(assertion)
    altered['rule_version'] = 'future-rule'
    assert reconstruct_delegation(altered, tmp_path)['status'] == 'EVIDENCE_DEFECT'


def test_cli_assess_and_reconstruct_without_opa_or_current_state(tmp_path):
    import subprocess
    import sys
    ref, dref, _ = evidence(tmp_path)
    request_path = tmp_path/'request.json'
    request_path.write_text(json.dumps({'query':query(),'authority_revision':ref,'delegation_revision':dref}))
    command = [sys.executable, '-m', 'src.delegation_reconstruction']
    result = subprocess.run(command + ['assess', str(request_path), '--history-directory', str(tmp_path)],
                            check=True, capture_output=True, text=True)
    assertion = json.loads(result.stdout)
    assertion_path = tmp_path/'assertion.json'
    assertion_path.write_text(json.dumps(assertion))
    replay = subprocess.run(command + ['reconstruct', str(assertion_path), '--history-directory', str(tmp_path)],
                            check=True, capture_output=True, text=True)
    assert json.loads(replay.stdout)['status'] == 'VERIFIED'


def test_changed_original_event_digest_cannot_verify(tmp_path):
    ref, dref, _ = evidence(tmp_path)
    event = m4_event(ref, authorities(authority()))
    assertion = create_assertion(query('root', effective_at='2026-09-05T12:00:01Z'), authority_reference=ref,
                                 delegation_reference=dref, history_directory=tmp_path, governance_event=event)
    changed = deepcopy(event)
    changed['event_id'] = 'different-event'
    assert reconstruct_delegation(assertion, tmp_path, governance_event=changed)['status'] == 'CONTRADICTED'


def test_negative_assessment_can_be_verified_without_becoming_permission(tmp_path):
    from test_delegation_resolver import parent
    ref, dref, _ = evidence(tmp_path, [delegation(parent=parent('delegation', 'missing'))])
    assertion = create_assertion(query(), authority_reference=ref, delegation_reference=dref, history_directory=tmp_path)
    audit = reconstruct_delegation(assertion, tmp_path)
    assert audit['status'] == 'VERIFIED'
    assert audit['permission_result'] == 'NOT_EVALUABLE'
    assert audit['resolution']['status'] == 'DELEGATION_CHAIN_BROKEN'
