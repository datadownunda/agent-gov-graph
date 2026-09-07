"""Frozen-protocol offline benchmark. No oracle/ground truth in workers.

One fresh worker per arm/repetition. Each query class gets a new index and empty
semantic cache; source validation is common immutable work included in every
cold source-to-answer figure. OS filesystem caches are uncontrolled.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL=ROOT/'experiments/graph_value/protocol.json'
FROZEN='c9d6cbd538303fdab07731490ce6d986c81ae56b4919593ae8c130dbe015f501'


def protocol():
    if hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()!=FROZEN:
        raise ValueError('Frozen protocol changed')
    return json.loads(PROTOCOL.read_text())


def rss_bytes():
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform=='darwin' else value*1024


def percentile(values,p):
    ordered=sorted(values)
    return ordered[max(0,math.ceil(len(ordered)*p)-1)]


def machine():
    physical=int(subprocess.check_output(['sysctl','-n','hw.memsize'],text=True))
    swap=subprocess.check_output(['sysctl','vm.swapusage'],text=True).strip()
    import re
    used=float(re.search(r'used = ([0-9.]+)M',swap).group(1))*1024**2
    return {'platform':platform.platform(),'python':sys.version,'physical_memory_bytes':physical,
            'logical_cpus':os.cpu_count(),'swap':swap,'swap_used_bytes':int(used),
            'free_disk_bytes':shutil.disk_usage(ROOT).free}


def worker(source_path,arm):
    started=time.perf_counter()
    from src.graph_value.canonical import load_reference
    from src.graph_value.baseline import Baseline
    from src.graph_value.queries import GraphQueries
    from src.graph_value.results import stable
    from experiments.graph_value.generate import prepare,workload
    p=protocol()
    source=json.loads(Path(source_path).read_text())
    reference=load_reference(ROOT)
    bundle=prepare(source,reference=reference)
    queries=workload(bundle)
    prepared=time.perf_counter()-started
    implementation=Baseline if arm=='baseline' else GraphQueries
    result={'arm':arm,'common_verification_seconds':prepared,'queries':{},
            'source_bytes':Path(source_path).stat().st_size,'records':len(bundle['records']),
            'relationships':sum(len(r['references']) for r in bundle['records']),
            'contexts':len(bundle['contexts']),'seed':source.get('seed'),
            'source_sha256':hashlib.sha256(Path(source_path).read_bytes()).hexdigest()}
    for q,args in queries.items():
        index_start=time.perf_counter()
        engine=implementation(bundle)
        loaded=time.perf_counter()-index_start
        fn=getattr(engine,q.lower())
        cold_start=time.perf_counter();cold=fn(**args);serialized=stable(cold)
        cold_seconds=time.perf_counter()-cold_start
        timings=[]
        for _ in range(p['warm_observations_per_query']//p['cold_repetitions']):
            before=time.perf_counter();answer=fn(**args);payload=stable(answer)
            timings.append(time.perf_counter()-before)
            if payload!=serialized: raise ValueError('Non-deterministic warm query')
        index_serialized=(stable({'records':list(engine.records.values()),'reverse':dict(engine.reverse),
                                'children':dict(engine.children),
                                'relationships':[[list(k),v] for k,v in engine.relationships.items()],
                                'principals':[[list(k),v] for k,v in engine.principals.items()]})
                          if arm=='baseline' else engine.graph.serialize())
        usage=resource.getrusage(resource.RUSAGE_SELF)
        result['queries'][q]={'index_or_projection_seconds':loaded,'cold_query_seconds':cold_seconds,
            'cold_source_to_answer_seconds':prepared+loaded+cold_seconds,
            'warm_seconds':timings,'result_bytes':len(serialized.encode()),
            'result_digest':hashlib.sha256(serialized.encode()).hexdigest(),
            'complete':answer['complete'],'output_cardinality':len(answer['records']),
            'path_count':len(answer['paths']),'conclusion_count':len(answer.get('conclusions',[])),
            'serialized_index_bytes':len(index_serialized.encode()),'peak_process_tree_rss_bytes':rss_bytes(),
            'user_cpu_seconds':usage.ru_utime,'system_cpu_seconds':usage.ru_stime}
        del engine,index_serialized
    result['worker_wall_seconds']=time.perf_counter()-started
    result['peak_process_tree_rss_bytes']=rss_bytes()
    print(stable(result))


def execute_worker(source,arm,cap,timeout):
    launch=time.perf_counter()
    proc=subprocess.Popen([sys.executable,'-B','-m','experiments.graph_value.benchmark','worker',str(source),'--arm',arm],
                          cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    peak=0
    stopped=None
    while proc.poll() is None:
        if time.perf_counter()-launch>timeout:
            stopped='RUN_TIMEOUT';proc.kill();break
        try:
            current=int(subprocess.check_output(['ps','-o','rss=','-p',str(proc.pid)],text=True).strip())*1024
            peak=max(peak,current)
            if current+rss_bytes()>cap:
                stopped='PROCESS_TREE_MEMORY_CAP';proc.kill();break
        except (ValueError,subprocess.CalledProcessError):pass
        time.sleep(.1)
        # Read result pipes once exit is observed; worker output is compact (<64K).
    stdout,stderr=proc.communicate()
    if stopped or proc.returncode:
        return {'arm':arm,'stopped':stopped or 'WORKER_ERROR','stderr':stderr[-4000:],
                'wall_seconds':time.perf_counter()-launch,'peak_process_tree_rss_bytes':peak+rss_bytes()}
    value=json.loads(stdout)
    value['launch_to_exit_seconds']=time.perf_counter()-launch
    value['peak_process_tree_rss_bytes']=max(peak,value['peak_process_tree_rss_bytes'])+rss_bytes()
    return value


def run(output,tiers):
    from experiments.graph_value.generate import make_source,prepare
    from src.graph_value.results import stable
    p=protocol();output.mkdir(parents=True,exist_ok=True)
    before=machine();cap=min(p['experimental_offline_thresholds_not_product_slos']['max_rss_bytes'],int(before['physical_memory_bytes']*.25))
    report={'protocol_sha256':FROZEN,'machine':before,'memory_cap_bytes':cap,'tiers':[],
            'cold_definition':p['cold_definition'],'threshold_kind':'experimental offline acceptability, not product SLO',
            'implementation_files':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for folder in ('src/graph_value','experiments/graph_value') for f in sorted((ROOT/folder).glob('*.py'))},
            'reference_limitation':'Q1 uses preserved live exception at each tier. Scale increases M5 records and synthetic M6 conclusions; it does not invent delegated M7 attestations.'}
    # Fixed structure has approximately 345 references per component (48 links).
    # Count actual references; never report nominal tier as actual cardinality.
    pilot=prepare(make_source(1))
    per_component=sum(len(r['references']) for r in pilot['records'])
    for target in tiers:
        now=machine()
        count=1 if target==0 else max(1,math.ceil(target/per_component))
        # Conservative 24 KiB per relationship; double buffer and parent included.
        estimated=max(1,target)*24576+rss_bytes()
        entry={'target_relationships':target or 'reference','components':count,
               'preflight':now,'estimated_peak_bytes':estimated,'runs':[]}
        report['tiers'].append(entry)
        if now['free_disk_bytes']<p['experimental_offline_thresholds_not_product_slos']['minimum_free_disk_bytes'] or estimated>cap:
            entry['status']='SKIPPED_RESOURCE_PREFLIGHT'
            (output/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
            break
        # Existing swap is not attributed to this experiment. A 256 MiB increase
        # stops continuation conservatively; unrelated system activity may cause it.
        if now['swap_used_bytes']>before['swap_used_bytes']+256*1024**2:
            entry['status']='STOPPED_SWAP_GROWTH'
            (output/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
            break
        sources=[]
        for seed in p['seeds']:
            path=output/f'source-{target}-{seed}.json'
            source=make_source(count,seed);source['seed']=seed
            path.write_text(stable(source)+'\n');sources.append(path)
        for repetition in range(p['cold_repetitions']):
            source=sources[repetition%len(sources)]
            for arm in (['baseline','graph'] if repetition%2==0 else ['graph','baseline']):
                value=execute_worker(source,arm,cap,p['experimental_offline_thresholds_not_product_slos']['run_timeout_seconds'])
                value['repetition']=repetition
                entry['runs'].append(value)
                print(f'{target or "reference"} repetition {repetition+1} {arm}: {value.get("stopped", "completed")}',flush=True)
                (output/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
                if value.get('stopped'):
                    entry['status']='STOPPED';break
            if entry.get('status')=='STOPPED':break
        entry.setdefault('status','MEASURED')
        entry['postflight']=machine()
        (output/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n')
        if entry['status']=='STOPPED':break
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['worker','run'])
    parser.add_argument('path',type=Path);parser.add_argument('--arm',choices=['baseline','graph'])
    parser.add_argument('--tiers',default='0,10000,100000,1000000')
    args=parser.parse_args()
    if args.command=='worker':worker(args.path,args.arm)
    else:run(args.path,[int(t) for t in args.tiers.split(',')])


if __name__=='__main__':main()
