"""Inspect native releases without interpreting run completion as control success."""
import collections as C
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
UP = ROOT / 'upstream'
OUT = ROOT / 'results'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save(name, obj):
    OUT.mkdir(exist_ok=True)
    (OUT/name).write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')

def records(path):
    """Native bytes remain authoritative; offsets include line endings."""
    data = path.read_bytes()
    file_hash = digest(data)
    offset = 0
    for i, line in enumerate(data.splitlines(keepends=True), 1):
        if line.strip():
            yield json.loads(line), {'path':str(path.relative_to(ROOT)), 'line':i,
                'byte_offset':offset, 'byte_length':len(line),
                'record_sha256':digest(line), 'file_sha256':file_hash}
        offset += len(line)

def inventory():
    manifests=[]
    for repo in sorted(UP.iterdir()):
        if not (repo/'.git').exists(): continue
        git=lambda *args: subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
        manifests.append({'name':repo.name,'url':git('remote','get-url','origin'),
            'commit':git('rev-parse','HEAD'), 'dirty':bool(git('status','--porcelain'))})
    save('sources.json',manifests)

def interbolt():
    totals=C.Counter(); groups=[]; examples=[]; fields={}
    out=OUT/'interbolt_normalized.jsonl'
    with out.open('w') as norm:
        for p in sorted((UP/'interbolt/runs/published').rglob('call_records.jsonl')):
            base=p.parent; calls=list(records(p)); events=list(records(base/'interbolt_events.jsonl'))
            ev=[(r,s) for r,s in events if isinstance(r.get('decision'),dict)]
            idx=[r for r,_ in records(base/'run_index.jsonl')]
            ids=[r['run_id'] for r in idx]; ic=C.Counter(ids)
            by_key=C.defaultdict(list); decisions=C.Counter()
            for r,s in ev:
                d=r['decision']; by_key[(d.get('run_id'),d.get('tool'))].append((r,s))
                decisions[d.get('action','unknown')]+=1
            call_keys=C.Counter((r.get('run_id'),r.get('tool')) for r,_ in calls)
            row=C.Counter(calls=len(calls),decision_events=len(ev),runs=len(idx))
            row['duplicate_run_ids']=sum(n-1 for n in ic.values() if n>1)
            row['same_order_tool_run_pairs']=sum(
                (c.get('run_id'),c.get('tool'))==(e['decision'].get('run_id'),e['decision'].get('tool'))
                for (c,_),(e,_) in zip(calls,ev))
            for r,s in calls:
                key=(r.get('run_id'),r.get('tool')); candidates=by_key[key]
                # A unique match is a candidate, never proof of causal identity.
                status='candidate_unique' if len(candidates)==1 and call_keys[key]==1 else ('unmatched' if not candidates else 'ambiguous')
                row[status]+=1
                row['calls_without_decision_id']+=int('decision_id' not in r)
                row['calls_without_timestamp']+=int('timestamp' not in r)
                row['calls_with_missing_run_index']+=int(ic[r.get('run_id')]!=1)
                fact={'source':'interbolt','record_kind':'attempt','issuer_boundary':'benchmark_harness',
                    'run_id':r.get('run_id'),'tool':r.get('tool'),'arguments':r.get('args'),
                    'native_sequence':r.get('seq'),'event_time':r.get('timestamp'),
                    'decision_id':r.get('decision_id'),'provenance':s,
                    'correlation_status':status,'candidate_count':len(candidates),
                    'control_finding':'NOT_EVALUABLE','reason':'No independently observed target effect or per-call authority receipt'}
                norm.write(json.dumps(fact)+'\n')
                fields.setdefault('call_record',sorted(r))
                if status=='ambiguous' and len(examples)<3:
                    examples.append({'source':s,'tool':r['tool'],'run_id':r['run_id'],
                        'call_count_same_run_tool':call_keys[key],
                        'decision_candidates':[e['decision'].get('decision_id') for e,_ in candidates]})
            if ev: fields['event']=sorted(ev[0][0]);fields['decision']=sorted(ev[0][0]['decision'])
            totals.update(row)
            groups.append({'directory':str(base.relative_to(ROOT)),**row,'decisions':dict(decisions)})
    save('interbolt_inspection.json',{'totals':dict(totals),'groups':groups,'fields':fields,
         'ambiguous_examples':examples,'qualification':'Candidates are not confirmed causal matches. File-order alignment is a harness property, not independent evidence.'})

def modus():
    counts=C.Counter();schemas=C.Counter();steps=C.Counter();all_fields=set(); agent_fields=set(); extras=set();sample=[]
    call_ids=0; missing_refs=0; failed_commands=0;trace_failures=0;bad=[];reference_issues=[];terminations=C.Counter();step_ref_issues=0
    for p in sorted((UP/'modus-trajectories').rglob('trajectory.json.gz')):
        try:
            with gzip.open(p,'rt') as f: obj=json.load(f)
        except Exception as e:bad.append({'path':str(p.relative_to(ROOT)),'error':str(e)});continue
        counts[p.relative_to(UP/'modus-trajectories').parts[0]]+=1
        schemas[obj.get('schema_version','missing')]+=1
        terminations[str(obj.get('extra',{}).get('termination_reason'))]+=1
        all_fields.update(obj); agent_fields.update(obj.get('agent',{})); extras.update(obj.get('extra',{}))
        ids=C.Counter(c.get('tool_call_id') for s in obj.get('steps',[]) for c in s.get('tool_calls',[]))
        local_fail=0
        for s in obj.get('steps',[]):
            steps[s.get('source','unknown')]+=1
            step_ids=C.Counter(c.get('tool_call_id') for c in s.get('tool_calls',[]))
            for ob in (s.get('observation') or {}).get('results',[]):
                call_ids+=1; missing_refs+=int(ids[ob.get('source_call_id')]!=1)
                step_ref_issues+=int(step_ids[ob.get('source_call_id')]!=1)
                if ids[ob.get('source_call_id')]!=1:
                    reference_issues.append({'path':str(p.relative_to(ROOT)),'step_id':s.get('step_id'),
                         'source_call_id':ob.get('source_call_id'),'matching_calls_in_session':ids[ob.get('source_call_id')]})
                try: content=json.loads(ob.get('content',''))
                except (TypeError,ValueError): continue
                if isinstance(content,dict) and isinstance(content.get('exit_code'),int) and content['exit_code']!=0:
                    failed_commands+=1;local_fail+=1
        trace_failures+=bool(local_fail)
        if len(sample)<4 or (local_fail and not any(x['nonzero_exit_observations'] for x in sample)):
            sample.append({'path':str(p.relative_to(ROOT)),'sha256':digest(p.read_bytes()),
                'session_id':obj.get('session_id'),'steps':len(obj.get('steps',[])),
                'nonzero_exit_observations':local_fail,'first_step_fields':sorted(obj['steps'][0])})
    save('modus_inspection.json',{'traces':dict(counts),'schemas':dict(schemas),'step_sources':dict(steps),
        'top_level_fields':sorted(all_fields),'agent_fields':sorted(agent_fields),'extra_fields':sorted(extras),
        'observation_results':call_ids,'nonunique_or_missing_source_call_reference':missing_refs,
        'nonzero_exit_observations':failed_commands,'traces_with_nonzero_exit_observation':trace_failures,
        'nonunique_or_missing_reference_within_step':step_ref_issues,
        'parse_errors':bad,'samples':sample,'reference_issues':reference_issues,'termination_reasons':dict(terminations),
        'interpretation':'Nonzero command exits are tool-level failures, not proof of failed audit tasks. No verdict is inferred from completion text.'})

def other_formats():
    cp=UP/'counsel/trajectories';fields=C.Counter();n=0
    for p in sorted(cp.glob('*.jsonl')):
        for r,s in records(p):n+=1;fields.update(r.keys())
    tasks=json.loads((UP/'masdrift/dataset/pilot_tasks_mas.json').read_text())
    health=C.Counter();types=C.Counter();health_fields=set()
    for p in (UP/'healthadmin/benchmark/v3/tasks').rglob('*.json'):
        x=json.loads(p.read_text());health[p.parent.name]+=1;health_fields.update(x)
        types.update(e.get('type','unknown') for e in x.get('evals',[]))
    save('formats.json',{'counsel':{'files':len(list(cp.glob('*.jsonl'))),'records':n,'field_occurrences':dict(fields),
         'origin':'published reference/oracle trajectories; not model attempts'},
         'masdrift':{'dataset_type':type(tasks).__name__,'task_count':len(tasks['tasks']),
             'task_fields':sorted(tasks['tasks'][0]),'top_level_fields':sorted(tasks)},
         'healthadmin_v3':{'tasks_by_directory':dict(health),'evaluation_types':dict(types),'task_fields':sorted(health_fields)}})

if __name__=='__main__':
    OUT.mkdir(exist_ok=True);inventory();interbolt();modus();other_formats()
    print('Inspection outputs saved to results/')
