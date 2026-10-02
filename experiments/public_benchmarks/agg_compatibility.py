"""Use existing, unchanged AGG validators and native assertion implementation.

Usage: python agg_compatibility.py --agg-root /path/to/agent-gov-graph
No fabricated identifiers or timestamps are sent to AGG's native linker.
"""
import argparse
import collections as C
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import sys

from inspect_records import ROOT,UP,OUT,records,save

def main(agg_root):
    sys.path.insert(0,str(agg_root))
    import jsonschema
    from src.correlation_assertion import native_assertions
    from src.evidence_digest import evidence_digest
    schema=json.loads((agg_root/'schemas/action_evidence.schema.json').read_text())
    validator=jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker())
    count=0
    with (OUT/'agg_action_evidence.jsonl').open('w') as f:
        for path in sorted((UP/'interbolt/runs/published').rglob('call_records.jsonl')):
            for r,s in records(path):
                loc={'member':s['path'],'file_digest':'sha256:'+s['file_sha256'],'line':s['line'],
                    'byte_offset':s['byte_offset'],'byte_length':s['byte_length'],'line_digest':'sha256:'+s['record_sha256']}
                event={'schema_version':'1.0','evidence_ref':evidence_digest({'source':'interbolt-call','location':loc}),
                    'role':'execution','location':loc,'raw':r,'ingested_at':datetime.now(timezone.utc).isoformat(),
                    'defects':['no per-call decision_id in native export','no event timestamp in native call record',
                               'no independently issued target outcome'],
                    'execution_disposition':'SUBMISSION_UNKNOWN','client_success':None}
                validator.validate(event);f.write(json.dumps(event)+'\n');count+=1
    base=UP/'interbolt/runs/published/banking/D_asr_system_strict/repeat_0'
    calls=list(records(base/'call_records.jsonl'))[:4]
    events=[(r,s) for r,s in records(base/'interbolt_events.jsonl') if r.get('decision')][:4]
    def wrap(raw,source,signal):
        return {'evidence_ref':evidence_digest(source),'location':source,'raw_record':raw,**signal}
    left=[wrap(r,s,{'decision_id':r.get('decision_id'),'run_id':r.get('run_id'),'tool':r.get('tool')}) for r,s in calls]
    right=[wrap(r,s,{k:r['decision'].get(k) for k in ('decision_id','run_id','tool')}) for r,s in events]
    assertions=native_assertions(left,right,identifier_field='decision_id',namespace=str(base.relative_to(ROOT)),
        issuer='Interbolt recorder as declared in public benchmark; not authenticated',required_equal_fields=('run_id','tool'))
    save('agg_interbolt_assertions.json',assertions)
    assert all(a['result']['state']=='INSUFFICIENT_EVIDENCE' for a in assertions if a['focus']['source']=='left')

    inspect=json.loads((OUT/'modus_inspection.json').read_text())
    path=ROOT/inspect['reference_issues'][0]['path']
    with gzip.open(path,'rt') as f:trace=json.load(f)
    raw_hash=hashlib.sha256(path.read_bytes()).hexdigest();left=[];right=[];scoped=[]
    for step in trace['steps']:
        if step.get('step_id') not in (93,105):continue
        sid=step['step_id']
        # Locators refer to compressed bytes plus JSON pointer, not fake JSONL offsets.
        loc={'path':str(path.relative_to(ROOT)),'file_sha256':raw_hash,'step_id':sid}
        ls=[wrap(c,{**loc,'json_pointer':f'/steps/{trace["steps"].index(step)}/tool_calls/{i}'},
             {'call_id':c['tool_call_id'],'step_id':sid}) for i,c in enumerate(step.get('tool_calls',[]))]
        rs=[wrap(o,{**loc,'json_pointer':f'/steps/{trace["steps"].index(step)}/observation/results/{i}'},
             {'call_id':o['source_call_id'],'step_id':sid}) for i,o in enumerate(step.get('observation',{}).get('results',[]))]
        left.extend(ls);right.extend(rs)
        scoped.extend(native_assertions(ls,rs,identifier_field='call_id',namespace=f'{raw_hash}/step/{sid}',
             issuer='Modus ATIF harness as declared by dataset; not authenticated',
             relationship_type='CALL_OBSERVATION_ASSOCIATION',required_equal_fields=('step_id',)))
    unscoped=native_assertions(left,right,identifier_field='call_id',namespace=f'{raw_hash}/session',
        issuer='Modus ATIF harness as declared by dataset; not authenticated',relationship_type='CALL_OBSERVATION_ASSOCIATION')
    assert all(a['result']['state']=='AMBIGUOUS' for a in unscoped)
    assert all(a['result']['state']=='LINKED' for a in scoped)
    save('agg_modus_assertions.json',{'session_scope':unscoped,'native_step_scope':scoped})
    save('agg_compatibility.json',{'agg_revision':'32500dc0725bc759f58810e273321f88220f1ac6',
        'action_evidence_schema_validated':count,'interbolt_call_focus_states':dict(C.Counter(a['result']['state'] for a in assertions if a['focus']['source']=='left')),
        'modus_session_scope_states':dict(C.Counter(a['result']['state'] for a in unscoped)),
        'modus_step_scope_states':dict(C.Counter(a['result']['state'] for a in scoped)),
        'core_modified':False,'protected_milestones_advanced':False,
        'interpretation':'LINKED retains existing AGG conditional meaning; never independent control assurance.'})
    print(f'Validated {count} native-record envelopes against AGG action_evidence; existing native assertions passed scoped checks.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--agg-root',type=Path,required=True);args=p.parse_args();main(args.agg_root.resolve())
