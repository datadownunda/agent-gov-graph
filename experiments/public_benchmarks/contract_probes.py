"""Reproducible boundary and ambiguity tests using inspected native structures."""
import ast
import collections as C
import copy
import difflib
import json
import gzip
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

from evidence_adapter import bind_decision,health_fax_fact,modus_observations
from inspect_records import ROOT,UP,OUT,records,save

def ambiguity():
    base=UP/'interbolt/runs/published/banking/D_asr_system_strict/repeat_0'
    calls=[x for x,_ in records(base/'call_records.jsonl')]
    events=[x for x,_ in records(base/'interbolt_events.jsonl') if isinstance(x.get('decision'),dict)]
    assert len(calls)==len(events)
    assert all((c['run_id'],c['tool'])==(e['decision']['run_id'],e['decision']['tool']) for c,e in zip(calls,events))
    groups=C.defaultdict(list)
    for i,c in enumerate(calls):groups[(c['run_id'],c['tool'])].append(i)
    idx=next(v for v in groups.values() if len(v)>1)
    first,second=idx[:2];c=copy.deepcopy(calls[first]);a=copy.deepcopy(events[first]);b=copy.deepcopy(events[second])
    # Sequence pairing is used ONLY to construct the test answer key. It is not
    # passed to bind_decision and is not claimed as independent ground truth.
    cases=[]
    def add(name,call,ev,expected):
        result=bind_decision(call,ev)
        assert result['binding']==expected,(name,result)
        cases.append({'case':name,'input_call':call,'input_events':ev,'result':result,
            'expected_binding':expected,'answer_key_origin':'controlled transformation of serialized harness records'})
    add('native_repeated_tool',c,[a,b],'UNPROVEN')
    add('true_record_dropped_false_unique_candidate',c,[b],'UNPROVEN')
    enhanced={**c,'decision_id':a['decision']['decision_id']}
    add('added_native_reference',enhanced,[a,b],'NATIVE_REFERENCE_BOUND')
    add('reference_target_missing',enhanced,[b],'MISSING')
    add('duplicate_reference',enhanced,[a,a,b],'CONFLICT')
    conflict=copy.deepcopy(a);conflict['decision']['tool']='different_tool'
    add('reference_content_conflict',enhanced,[conflict,b],'CONFLICT')
    skewed=copy.deepcopy(a);skewed['timestamp']='1900-01-01T00:00:00Z'
    add('clock_skew_does_not_break_reference_but_time_validity_unproven',enhanced,[b,skewed],'NATIVE_REFERENCE_BOUND')
    add('reordered_records',enhanced,[b,a],'NATIVE_REFERENCE_BOUND')
    other=copy.deepcopy(a);other['decision']['run_id']='other_run'
    add('cross_run_id_collision',enhanced,[other],'CONFLICT')
    save('ambiguity_cases.json',cases)
    return {'cases':len(cases),'passed':len(cases),
        'naive_run_tool_match_on_dropped_case':'would select the remaining wrong decision',
        'qualification':'Reference enhancement is experimental; no historical record is relabeled as natively containing it. No case yields control assurance.'}

def patch_probe():
    p=UP/'interbolt/src/interbolt_agentdojo/executor.py';old=p.read_text()
    needle='"run_id": decision.run_id,'
    assert old.count(needle)==1
    new=old.replace(needle,needle+'\n            "decision_id": decision.decision_id,')
    patches=ROOT/'patches';patches.mkdir(exist_ok=True)
    (patches/'interbolt-decision-reference.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
        fromfile='a/src/interbolt_agentdojo/executor.py',tofile='b/src/interbolt_agentdojo/executor.py')))
    # Execute the exact patched recorder method without installing agent/model dependencies.
    tree=ast.parse(new);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='InterboltToolsExecutor')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_record_call')
    ns={'json':json};exec(compile(ast.Module(body=[method],type_ignores=[]),str(p),'exec'),ns)
    with tempfile.TemporaryDirectory() as temp:
        f=Path(temp)/'calls.jsonl';self=SimpleNamespace(call_records_path=f,_seq=0)
        d=SimpleNamespace(run_id='run-a',decision_id='decision-1',contributing_labels=[],run_tainted=False)
        ns['_record_call'](self,'bank.send',{'amount':1},d)
        d.decision_id='decision-2';ns['_record_call'](self,'bank.send',{'amount':1},d)
        rows=[json.loads(s) for s in f.read_text().splitlines()]
        assert [r['decision_id'] for r in rows]==['decision-1','decision-2']
        assert [r['seq'] for r in rows]==[0,1]
    return {'test':'exact patched recorder method','passed':True,'live_interbolt_execution_tested':False,
            'upstream_modified':False,'change':'retain existing decision_id in call export'}

def masdrift():
    sys.path.insert(0,str(UP/'masdrift'))
    from authorization_policy import make_rule,AuthorizationPolicy,AuthorizationStageState,monitor_authorization_call
    from tracing import Recorder
    rule=make_rule(tool='payment.send',scope='recipient=approved-vendor',stage='post_approval')
    policy=AuthorizationPolicy(rules={rule.tool:rule});state=AuthorizationStageState()
    tool={'name':rule.tool};args={'recipient':'approved-vendor'}
    def matcher(rule,spec,args):return ('match','fixture exact recipient') if args.get('recipient')=='approved-vendor' else ('mismatch','fixture recipient mismatch')
    checks=[]
    def assess(name,args,lineage):
        a=monitor_authorization_call(policy,state,tool,args,matcher,lineage_id=lineage)
        checks.append({'case':name,**a.audit_dict(state.version)});return a.formal_verdict
    assert assess('before_confirmation',args,'delegation-a')=='Require Confirmation'
    state.approved_rule_ids.add(rule.rule_id);state.approved_scope_fingerprints[rule.rule_id]=rule.scope_clause_fingerprint
    state.approved_lineages[rule.rule_id]='delegation-a';state.version+=1
    state.evidence.append({'rule_id':rule.rule_id,'source':'fixture_confirmation',
        'lineage_id':'delegation-a','scope_fingerprint':rule.scope_clause_fingerprint,
        'evidence':'synthetic fixture, not an actual human approval'})
    assert assess('approved_lineage',args,'delegation-a')=='Allow'
    assert assess('different_lineage',args,'delegation-b')=='Require Confirmation'
    assert assess('wrong_recipient',{'recipient':'other'},'delegation-a')=='Deny'
    exported=state.to_dict();export_has_lineage='approved_lineages' in exported
    recorder=Recorder('agg-format-probe','synthetic-contract-probe')
    recorder.add_tool_call(agent='fixture-agent',tool=rule.tool,args=args,result={'value':'x'*1800})
    save('masdrift_contract_probe.json',{'origin':'AGG synthetic inputs passed through native classes; not a model rollout',
         'policy':policy.to_dict(),'assessments':checks,'stage_export':exported,
         'stage_export_includes_approved_lineages':export_has_lineage,'trace':recorder.tool_calls,
         'qualification':'Native approve_rule also records lineage_id inside evidence; omission of the map is not proof that lineage is unavailable.',
         'remaining':'No independent grant issuer, revocation receipt or target execution evidence'})
    return {'cases':4,'passed':4,'approved_lineages_omitted_from_stage_export':not export_has_lineage}

def health():
    cases=[{}, {'full_state':{}}, {'full_state':{'faxPortal':{'faxesSent':0}}},
           {'full_state':{'faxPortal':{'faxesSent':1}}}, {'full_state':{'faxPortal':{'faxesSent':'1'}}}]
    results=[health_fax_fact(c) for c in cases]
    assert [r['observation_status'] for r in results]==['MISSING_OR_INVALID','MISSING_OR_INVALID','PRESENT','PRESENT','MISSING_OR_INVALID']
    assert all(r['finding']=='NOT_EVALUABLE' for r in results)
    path=UP/'healthadmin/harness/evaluators/jmespath_evaluator.py'
    spec=importlib.util.spec_from_file_location('native_health_jmes',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    task=json.loads((UP/'healthadmin/benchmark/v3/tasks/dme/fax-easy-1.json').read_text())
    criterion=next(e for e in task['evals'] if e.get('query')=='full_state.faxPortal.faxesSent')
    native=[module.JMESPathEvaluator().evaluate(criterion,c) for c in cases]
    assert [r[0] for r in native]==[False,False,False,True,False]
    save('health_state_probe.json',{'origin':'synthetic fixtures tested by native evaluator; no GUI agent run',
         'criterion':criterion,'cases':[{'input':c,'result':r,'native_evaluator':n} for c,r,n in zip(cases,results,native)]})
    return {'cases':5,'passed':5,'gui_run_performed':False}

def modus_join():
    report=json.loads((OUT/'modus_inspection.json').read_text())
    p=ROOT/report['reference_issues'][0]['path']
    with gzip.open(p,'rt') as f:trace=json.load(f)
    normalized=list(modus_observations(trace,str(p.relative_to(ROOT))))
    assert all(x['binding']=='NATIVE_STEP_REFERENCE' for x in normalized)
    repeated=[x for x in normalized if x['source_call_id']=='call_1007102']
    assert {x['step_id'] for x in repeated}=={93,105}
    save('modus_join_probe.json',{'source':str(p.relative_to(ROOT)),
         'observations':len(normalized),'all_bound_within_step':True,
         'repeated_id_distinguished_by_steps':[{'step_id':x['step_id'],'source_call_id':x['source_call_id']} for x in repeated],
         'qualification':'Successful structural binding, not independent outcome corroboration'})
    return {'native_trace_observations':len(normalized),'repeated_call_id_step_scoping_passed':True}

if __name__=='__main__':
    summary={'ambiguity':ambiguity(),'interbolt_patch':patch_probe(),'masdrift':masdrift(),'health':health(),'modus_join':modus_join()}
    save('probe_summary.json',summary);print(json.dumps(summary,indent=2))
