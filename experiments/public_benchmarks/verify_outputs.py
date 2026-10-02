"""Verify provenance pointers and measured outcomes, without regenerating results."""
import collections as C
import hashlib
import json
from pathlib import Path
from inspect_records import ROOT,UP,OUT,save

def main():
    count=0;cache={}
    for line in (OUT/'interbolt_normalized.jsonl').read_text().splitlines():
        x=json.loads(line);s=x['provenance'];p=ROOT/s['path']
        if p not in cache:cache[p]=p.read_bytes()
        data=cache[p];raw=data[s['byte_offset']:s['byte_offset']+s['byte_length']]
        assert hashlib.sha256(raw).hexdigest()==s['record_sha256']
        assert hashlib.sha256(data).hexdigest()==s['file_sha256']
        assert json.loads(raw)['tool']==x['tool'];count+=1
    rows=json.loads((OUT/'workflow_summary.json').read_text())
    assert len(rows)==30
    for row in rows:
        p=ROOT/row['directory']
        client=[json.loads(s) for s in (p/'client_attempts.jsonl').read_text().splitlines()]
        target=[json.loads(s) for s in (p/'target_observations.jsonl').read_text().splitlines()]
        truth=[json.loads(s) for s in (p/'oracle_pairings.jsonl').read_text().splitlines()]
        assert len(client)==len(target)==len(truth)==row['calls']
        assert all(c['tool']==t['tool'] and c['arguments_sha256']==t['arguments_sha256'] for c,t in zip(client,target))
        for before,after in zip(target,target[1:]):assert before['after_sha256']==after['before_sha256']
        if row['domain']=='counsel':assert row['native_verdict']['passed']==(row['variant']=='reference')
        else:assert row['same_final_state_as_reference']==(row['variant']!='omit_last')
    matches=[]
    for p in sorted((ROOT/'generated/counsel/hf/tasks').glob('*.json')):
        assert p.read_bytes()==(UP/'counsel/tasks'/p.name).read_bytes();matches.append(p.name)
    for name in ['world.py','scoring.py','contracts.py']:
        assert (UP/'counsel/world'/name).read_bytes()==(UP/'counsel-builder/benchmark/counselbench100/runtime'/name).read_bytes()
    save('validation.json',{'native_record_provenance_checks':count,'workflow_cases_checked':len(rows),
        'workflow_calls_checked':sum(x['calls'] for x in rows),'counsel_generated_tasks_identical_to_public_data':matches,
        'counsel_runtime_files_identical':3,'status':'PASS'})
    print('Source offsets/hashes, target-state continuity and expected workflow findings verified.')

if __name__=='__main__':main()
