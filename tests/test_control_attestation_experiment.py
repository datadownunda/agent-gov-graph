import json
from pathlib import Path

from experiments.control_attestation.run_experiment import create_positive_fixture, run, audit_results
from src.control_attestation import attest

ROOT=Path(__file__).resolve().parents[1]


def test_positive_fixture_and_saved_replay(tmp_path):
    c=json.loads((ROOT/'experiments/control_attestation/control.json').read_text())
    fixture=tmp_path/'fixture'
    ref=create_positive_fixture(fixture,c)
    a,r=attest(fixture,ref,c,coverage_support='coverage_observations.json')
    assert r['coverage_assessment']['result']=='ADEQUATE'
    assert a['finding']=='CONTROL_EFFECTIVE'
    assert attest(fixture,ref,c)[0]['finding']=='CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'


def test_experiment_does_not_manufacture_live_positive(tmp_path):
    result=run(tmp_path/'result')
    assert result['live_control_effective_demonstrated'] is False
    assert result['deterministic_positive_rule_demonstrated'] is True
    assert audit_results(tmp_path/'result')==result


def revise_fixture_support(directory,change):
    import hashlib
    p=directory/'coverage_observations.json'
    data=json.loads(p.read_text())
    change(data)
    p.write_text(json.dumps(data))
    manifest=json.loads((directory/'manifest.json').read_text())
    manifest['files']['coverage_observations.json']='sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
    (directory/'manifest.json').write_text(json.dumps(manifest))


def test_control_specific_scope_capture_clocks_and_candidates(tmp_path):
    c=json.loads((ROOT/'experiments/control_attestation/control.json').read_text())
    mutations=[lambda s:s.update(target_id='different-target'),
               lambda s:s['scope'].update(resource_id='another-resource'),
               lambda s:s['scope'].update(action='export'),
               lambda s:s.update(identity_scope='GOVERNED_ACTOR_ONLY'),
               lambda s:s['capture'].update(available=False),
               lambda s:s['capture'].update(finalized=False),
               lambda s:s['capture'].update(through='2026-09-05T12:00:04Z'),
               lambda s:s['clocks'].update(maximum_offset_seconds='10'),
               lambda s:s['clocks'].update(basis=''),
               lambda s:s.update(unresolved_gaps=True),
               lambda s:s.update(candidate_ambiguity=True)]
    for index,mutation in enumerate(mutations):
        fixture=tmp_path/str(index)
        ref=create_positive_fixture(fixture,c)
        revise_fixture_support(fixture,mutation)
        a,r=attest(fixture,ref,c,coverage_support='coverage_observations.json')
        assert r['status']=='VERIFIED'
        assert r['coverage_assessment']['result'] in ('INADEQUATE','UNKNOWN')
        assert a['finding']=='CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED'


def test_fixture_generation_is_deterministic(tmp_path):
    c=json.loads((ROOT/'experiments/control_attestation/control.json').read_text())
    a,b=tmp_path/'a',tmp_path/'b'
    assert create_positive_fixture(a,c)==create_positive_fixture(b,c)
    assert {p.relative_to(a):p.read_bytes() for p in a.rglob('*') if p.is_file()}=={
           p.relative_to(b):p.read_bytes() for p in b.rglob('*') if p.is_file()}
