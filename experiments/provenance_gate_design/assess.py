"""Offline design assessment only. Never changes M7 or writes an evidence archive."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
COHORTS = {
    'historical_legitimate': ['003','004','005','042','043','044','051','052','053','069','070','071'],
    'historical_false_exception': ['012','013','014','015','016','017','021','022','023','024','025','026','033','034','035','060','061','062'],
    'other_false_link': ['027','028','029'],
}

def read(p):
    return json.loads(p.read_text())

def qualify(checks):
    # No expected outcome, case ID, matching value or scorer truth enters P1.
    required = ['producer_identity','observation_role','origin','relationship_semantics','episode_applicability']
    failed = [k for k in required if checks[k]['status'] != 'ESTABLISHED']
    if not checks['custody_trust']['assumptions']:
        failed.append('custody_trust')
    if checks['contradiction_review']['status'] != 'ESTABLISHED':
        failed.append('contradiction_review')
    return {'eligible':not failed,'failed_requirements':failed}

def assess_edge(edge, evidence_kind, has_conflict=False):
    synthetic = evidence_kind == 'DETERMINISTIC_SYNTHETIC_FIXTURE_NO_TARGET_PROCESS'
    c = {}
    def add(k,status,basis):
        c[k]={'status':status,'basis':basis}
    if synthetic:
        add('producer_identity','CONTRADICTED','Archive manifest identifies a deterministic fixture without target process; worker.py writes source-shaped rows. Runtime/server producer claim not established.')
        add('observation_role','ESTABLISHED','Retained row locations establish which fixture-authored occurrence was consumed, not an actual native observation.')
        add('origin','CONTRADICTED','generate.py assigns/copies deterministic attempt and request identifiers. The claimed native generation/receipt did not occur in this fixture.')
        add('relationship_semantics','ASSUMED','namespace_observations and correlation labels describe simulated runtime/NGINX relationships only; truth is excluded from qualification.')
        add('episode_applicability','MISSING','No real runtime/server episode exists to which a native producer contract can be bound.')
        assumptions=['Trust preserved fixture bytes and generator provenance as synthetic only; do not promote simulated source roles into native provenance.']
    else:
        add('producer_identity','ESTABLISHED','Retained runtime/OPA and target metadata identify the bounded local producers under the recorded operator custody; not authenticated infrastructure identity.')
        add('observation_role','ESTABLISHED','Retained exact source fields and path references identify observations; how the client populated them depends on external source code.')
        add('origin','CONTRACT_ONLY','Original M6 runtime/client implementation explains UUID generation/argument forwarding or response-header receipt. Code is outside native manifest and lacks an episode execution binding.')
        add('relationship_semantics','CONTRACT_ONLY','Original code plus archived NGINX config support same-attempt or same-server-request interpretation if applicable; equality alone is not used.')
        add('episode_applicability','MISSING','No retained execution/deployment record binds the running runtime/client to the original source revision. Original source co-location and compatible records are not that binding. NGINX target metadata/configuration are a partial basis only.')
        assumptions=['Trust operator custody and faithful record preservation.', 'Trust normal behavior of a correctly identified producer and complete supplied populations only within the reviewed boundary.', 'Do not assume the missing executed-code/configuration applicability binding.']
    c['custody_trust']={'status':'ASSUMED','assumptions':assumptions,'basis':'Explicit assumptions; none fills a missing premise.'}
    add('contradiction_review','CONTRADICTED' if has_conflict else 'ESTABLISHED',
        'Supplied synthetic request-namespace observations conflict; not authenticated native observations.' if has_conflict else
        'No additional unresolved contradiction in reviewed retained origin/namespace evidence. This is a bounded review, not global completeness. Synthetic/native mismatch is separately recorded above.')
    return dict(edge=edge,evidence_kind=evidence_kind,checks=c,qualification=qualify(c))

def historical_edges(output, archive):
    view=output['reconciliation']['critical-deny']
    refs={ref for path in view['correlation_paths'] for ref in path['assertion_ids']}
    assertions={a['assertion_id']:a for bundle in output['correlations'] for a in bundle['assertions']}
    records={r['evidence_ref']:r for r in output['records']}
    result=[]
    for ref in sorted(refs):
        a=assertions[ref]; endpoints=[a['focus']['evidence_ref'],a['result']['linked_evidence'][0]['evidence_ref']]
        occurrences=[{'evidence_ref':r,'role':records[r]['role'],'location':records[r]['location']} for r in endpoints]
        field=a['rule']['parameters']['identifier_field']
        conflict=field=='request_id' and any('NATIVE_IDENTIFIER_NAMESPACE_CONFLICT' in p['basis_codes'] for p in output['attestations'][view['assertion_id']]['attestation']['exception_paths'])
        row=assess_edge({'correlation_ref':ref,'identifier_field':field,'occurrences':occurrences},read(archive/'manifest.json')['provenance'],conflict)
        row['source_basis']=[str(archive.relative_to(ROOT)/'manifest.json'),str(archive.relative_to(ROOT)/'namespace_observations.json'),'experiments/strong_link_assurance/generate.py','experiments/strong_link_assurance/worker.py']
        result.append(row)
    return result

def main():
    oldroot=ROOT/'experiments/strong_link_assurance/results/v4'
    patchedroot=ROOT/'experiments/m7_scope_gate/results/v1'
    outputs=read(patchedroot/'decisions.json'); old=read(oldroot/'metrics.json')['cases']; patched=read(patchedroot/'metrics.json')['cases']
    cases=[]
    for cohort,ids in COHORTS.items():
        for key in ids:
            output=outputs[key];edges=historical_edges(output,patchedroot/'archives'/key)
            assert len(edges)==2
            qualifies=all(e['qualification']['eligible'] for e in edges)
            view=output['reconciliation']['critical-deny'];receipt=output['attestations'][view['assertion_id']]['receipt']
            effect=receipt['facts']['prohibited_effect_established']
            cases.append({'evaluation_id':key,'cohort':cohort,'edges':edges,'p1_path_eligible':qualifies,'existing_prohibited_effect':effect,'design_exception_candidate':qualifies and effect,'before':old[key]['primary'][1],'current':patched[key]['primary'][1]})
    from src.control_attestation import attest
    live=ROOT/'experiments/target_outcome/results/v1';view=read(live/'reconciliation.json')['critical-deny'];control=read(ROOT/'experiments/control_attestation/control.json')
    attestation,receipt=attest(live,view['assertion_id'],control)
    paths=attestation['exception_paths'];assert len(paths)==1
    live_edges=[]
    for relation,field in [('governance_execution','action_attempt_id'),('execution_target','request_id')]:
        row=assess_edge({'relation':relation,'identifier_field':field,'existing_path':paths[0]},'RETAINED_LOCAL_LIVE_EPISODE')
        row['source_basis']=['experiments/target_outcome/results/v1/manifest.json','experiments/target_outcome/results/v1/runtime.jsonl','experiments/target_outcome/results/v1/opa.jsonl','experiments/target_outcome/results/v1/governance.jsonl','experiments/target_outcome/results/v1/execution.jsonl','experiments/target_outcome/results/v1/native/access.jsonl','experiments/target_outcome/results/v1/nginx.conf','experiments/target_outcome/results/v1/target_runtime.json','7da026265b75b36ebd7e3e41eb88788e6815f48d:src/complaint_runtime.py','7da026265b75b36ebd7e3e41eb88788e6815f48d:experiments/target_outcome/http_client.py']
        live_edges.append(row)
    # Scoring occurs after qualification. Frozen scorer truth never enters qualify().
    summary={cohort:{'evaluations':len(ids),'p1_eligible_paths':sum(c['p1_path_eligible'] for c in cases if c['cohort']==cohort),'restored_exceptions':sum(c['design_exception_candidate'] for c in cases if c['cohort']==cohort)} for cohort,ids in COHORTS.items()}
    live_accept=all(e['qualification']['eligible'] for e in live_edges)
    restored_false=summary['historical_false_exception']['restored_exceptions']
    verdict='PROVENANCE_RULE_FALSIFIED_FALSE_EXCEPTION_RESTORED' if restored_false else 'PROVENANCE_RULE_SUPPORTED_ON_RETAINED_CORPUS' if live_accept else 'PROVENANCE_RULE_NOT_DEMONSTRATED'
    result={'protocol_sha256':hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),'assessment_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'method':'Cited evidence-ledger design assessment; no production gate executed or receipt facts replaced. Not blinded to known prior audit.','result':verdict,'summary':summary,'live':{'edges':live_edges,'design_exception_candidate':live_accept,'current_attestation':attestation,'current_receipt':receipt},'historical_cases':cases}
    (HERE/'RESULTS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'result':verdict,'summary':summary,'live_restored':live_accept,'assessed_edges':sum(len(c['edges']) for c in cases)+len(live_edges)},indent=2))

if __name__=='__main__':main()
