"""Scripted native-tool replay with separate client and target-process collectors.

No model calls. Both collectors share an administrator and are NOT independent
organizations. The parent retains oracle pairings only for later measurement.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
UP=ROOT/'upstream'
OUT=ROOT/'results/workflows'

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
def sha(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def append(path,x):
    with path.open('a') as f:f.write(canonical(x)+'\n')
def dump(path,x):path.write_text(json.dumps(x,indent=2,default=str)+'\n')
def serial(x):
    if hasattr(x,'model_dump'):return x.model_dump(mode='json')
    if isinstance(x,list):return [serial(v) for v in x]
    if isinstance(x,dict):return {k:serial(v) for k,v in x.items()}
    return x

def worker():
    cfg=json.loads(sys.stdin.readline());dest=Path(cfg['dest']);domain=cfg['domain']
    if domain=='itsm':
        sys.path.insert(0,str(UP/'itsm/src'))
        from enterprise_worlds.domains.itsm.environment import get_tasks,get_environment
        from enterprise_worlds.utils.clock import set_now
        t=next(t for t in get_tasks() if t.id==cfg['task_id']);set_now(t.current_time)
        env=get_environment(seed_db=t.seed_db,org_ids=t.org_ids,org_id=t.org_id,
            acting_user_id=t.acting_user_id,db_delta=t.initial_state_delta)
        snapshot=lambda:env.tools.db.model_dump(mode='json')
        call=lambda n,a:serial(env.make_tool_call(n,**a))
        dump(dest/'policy_snapshot.json',{'kind':'static_policy_not_runtime_decision','text':env.get_policy(),
            'acting_user_id_from_task':t.acting_user_id,'org_ids':t.org_ids})
    else:
        sys.path.insert(0,str(UP/'counsel-builder/benchmark/counselbench100'))
        from runtime.world import CounselWorld
        from builder import verification_token
        task=Path(cfg['task_dir'])
        env=CounselWorld(task/'environment/documents',dest/'output',dest/'native',task/'environment/world/spec.json')
        # Internal snapshot: target-owned state, not a provider-issued audit API.
        snapshot=lambda:{'mutations':copy.deepcopy(env._mutations),'rejected_mutations':copy.deepcopy(env._rejected_mutations)}
        call=env.call_tool
        dump(dest/'policy_snapshot.json',{'kind':'static_spec_not_runtime_decision',
            'spec_sha256':hashlib.sha256((task/'environment/world/spec.json').read_bytes()).hexdigest()})
    before=snapshot();dump(dest/'initial_state.json',before)
    print(json.dumps({'ready':True}),flush=True)
    for seq,line in enumerate(sys.stdin):
        req=json.loads(line)
        if req.get('finish'):
            dump(dest/'final_state.json',snapshot())
            verdict=env.verify(verification_token(cfg['task_id'])) if domain=='counsel' else {'final_state_sha256':sha(snapshot())}
            dump(dest/'native_verdict.json',verdict)
            print(canonical(verdict),flush=True);break
        started=time.time_ns();error=None
        try:result=call(req['tool'],req['arguments'])
        except Exception as e:result=None;error=type(e).__name__+': '+str(e)
        after=snapshot()
        changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
        row={'source':'target_process_collector','pid':os.getpid(),'target_sequence':seq,
            'observation_time_ns':time.time_ns(),'started_ns':started,'tool':req['tool'],
            'arguments_sha256':sha(req['arguments']),'result_sha256':sha(result),'error':error,
            'native_is_error':bool(isinstance(result,dict) and result.get('isError')),
            'before_sha256':sha(before),'after_sha256':sha(after),'changed_sections':changed,
            'changed_values':{k:after.get(k) for k in changed},'trust_boundary':'single_administrator'}
        append(dest/'target_observations.jsonl',row);before=after
        print(canonical({'result_sha256':sha(result),'error':error,'native_is_error':row['native_is_error']}),flush=True)

def run_case(domain,task_id,actions,variant,task_dir=None):
    dest=OUT/domain/task_id/variant;dest.mkdir(parents=True,exist_ok=True)
    for name in ['client_attempts.jsonl','target_observations.jsonl','oracle_pairings.jsonl']:
        (dest/name).write_text('')
    cfg={'domain':domain,'task_id':task_id,'dest':str(dest),'task_dir':str(task_dir) if task_dir else None}
    p=subprocess.Popen([sys.executable,__file__,'--worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    p.stdin.write(canonical(cfg)+'\n');p.stdin.flush()
    if not json.loads(p.stdout.readline()).get('ready'):raise RuntimeError('worker not ready')
    errors=0
    for i,a in enumerate(actions):
        req={'tool':a.get('name',a.get('tool')),'arguments':a['arguments']}
        append(dest/'client_attempts.jsonl',{'source':'scripted_client','client_sequence':i,
            'observed_at_ns':time.time_ns(),'tool':req['tool'],'arguments_sha256':sha(req['arguments']),
            'actor_kind':'reference_script_not_model','trust_boundary':'single_administrator'})
        p.stdin.write(canonical(req)+'\n');p.stdin.flush();result=json.loads(p.stdout.readline())
        errors+=bool(result.get('error') or result.get('native_is_error'))
        append(dest/'oracle_pairings.jsonl',{'client_sequence':i,'target_sequence':i,
            'basis':'serialized_driver_acknowledgement','evaluator_only':True})
    p.stdin.write('{"finish":true}\n');p.stdin.flush();verdict=json.loads(p.stdout.readline())
    p.stdin.close();p.wait(timeout=30)
    if p.returncode:raise RuntimeError(f'worker exit {p.returncode}')
    return {'domain':domain,'task_id':task_id,'variant':variant,'calls':len(actions),
         'tool_errors':errors,'native_verdict':verdict,'directory':str(dest.relative_to(ROOT))}

def main():
    OUT.mkdir(parents=True,exist_ok=True);results=[]
    sys.path.insert(0,str(UP/'itsm/src'))
    from enterprise_worlds.domains.itsm.environment import get_tasks
    for t in get_tasks()[:5]:
        actions=[{'name':a.name,'arguments':a.arguments} for a in t.evaluation_criteria.actions]
        baseline=run_case('itsm',t.id,actions,'reference')
        expected=baseline['native_verdict']['final_state_sha256']
        for row in [baseline,run_case('itsm',t.id,actions[:-1],'omit_last'),run_case('itsm',t.id,actions+[actions[-1]],'retry_last')]:
            row['same_final_state_as_reference']=row['native_verdict']['final_state_sha256']==expected
            row['qualification']='Exact state comparison only; no NL judge or authorization verdict'
            results.append(row)
    sys.path.insert(0,str(UP/'counsel-builder/benchmark/counselbench100'))
    from builder import MATTERS,build_material,create_task_pack
    generated=ROOT/'generated/counsel'
    for i,m in enumerate(MATTERS[:5]):
        material=build_material(m,i)
        create_task_pack(generated/'tasks',generated/'hf',m,i,material)
        task_id=material['task_id'];actions=material['reference_calls']
        writes=[a for a in actions if a.get('phase','').startswith('state-transition')]
        rest=[a for a in actions if a not in writes]
        missing=list(actions);idx=next(i for i,a in enumerate(missing) if a.get('phase','').startswith('postwrite-readback'));missing.pop(idx)
        for variant,calls in [('reference',actions),('write_before_read',writes+rest),('missing_readback',missing)]:
            results.append(run_case('counsel',task_id,calls,variant,generated/'tasks'/task_id))
    dump(ROOT/'results/workflow_summary.json',results)
    print(f'Collected {len(results)} scripted workflow replays')

if __name__=='__main__':
    if '--worker' in sys.argv:worker()
    else:main()
