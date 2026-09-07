"""Bounded supplementary stress checks; not substitutes for frozen main tiers.
Run from repository root with the Gate A Python environment after benchmarking.
"""
import json
import resource
import signal
import time
from pathlib import Path
from copy import deepcopy
from src.graph_value.canonical import Catalog,add_reconciliation
from src.graph_value.baseline import Baseline
from src.graph_value.queries import GraphQueries
from src.graph_value.results import stable
from experiments.graph_value.generate import root_record,delegation,AT,action_source,correlations
from src.action_reconciliation import reconcile


def timeout(signum,frame):raise TimeoutError('Supplementary 120 second limit')
signal.signal(signal.SIGALRM,timeout)
signal.alarm(120)
rows=[]
try:
    for depth in (8,16,32):
        source={'schema_version':'2.0','source_id':'stress','source_version':'1',
                'records':[root_record('root'),root_record('other')]}
        links=[]
        for i in range(depth):
            links.append(delegation('d'+str(i),'root' if i==0 else 'a'+str(i-1),'a'+str(i),
                                    'authority' if i==0 else 'delegation','root-authority' if i==0 else 'd'+str(i-1)))
        links.append(delegation('alternative','other','a'+str(depth-1),'authority','other-authority'))
        c=Catalog();c.authority_pair('stress',source,links);b=c.freeze();answers=[]
        for arm,engine in [('baseline',Baseline),('graph',GraphQueries)]:
            start=time.perf_counter();e=engine(b)
            answer=e.q3('stress',{'kind':'delegation','record_id':'d0','version':'1'},AT)
            rows.append({'case':'root-wide-chain','depth':depth,'arm':arm,'seconds':time.perf_counter()-start,
                         'complete':answer['complete'],'affected_actors':len(answer['affected']),
                         'actors_losing_all_support':sum(r['loses_all_demonstrated_support'] for r in answer['affected'])})
            assert len(answer['affected'])==depth
            assert sum(r['loses_all_demonstrated_support'] for r in answer['affected'])==depth-1
            answers.append(answer)
        assert answers[0]==answers[1]
    for size in (2,8,32):
        records=action_source('actor','population')
        for i in range(size-1):
            r=deepcopy(records[-1]);r['evidence_ref']='extra-'+str(i);records.append(r)
        started=time.perf_counter();corr=correlations(records)
        a=reconcile(records,corr,governance_ref=records[0]['evidence_ref'])
        prepare_seconds=time.perf_counter()-started
        assert a['result']=='INSUFFICIENT_EVIDENCE'
        c=Catalog();key,_=add_reconciliation(c,a,'population');b=c.freeze();answers=[]
        for arm,engine in [('baseline',Baseline),('graph',GraphQueries)]:
            start=time.perf_counter();answer=engine(b).dependencies(key)
            rows.append({'case':'competing-population','population_size':size,'arm':arm,
                         'common_prepare_seconds':prepare_seconds,'seconds':time.perf_counter()-start,
                         'source_bytes':len(stable(records).encode()),'assertion_bytes':len(stable(a).encode()),
                         'complete':answer['complete'],'paths':len(answer['paths']), 'm6_result':a['result']})
            answers.append(answer)
        assert answers[0]==answers[1]
    status='PASS'
except TimeoutError:
    status='STOPPED_TIMEOUT'
finally:
    signal.alarm(0)
usage=resource.getrusage(resource.RUSAGE_SELF)
Path(__file__).with_name('stress.json').write_text(json.dumps({'status':status,'scoring':'supplementary only',
    'rows':rows,'peak_rss_bytes':usage.ru_maxrss,'user_cpu_seconds':usage.ru_utime,'system_cpu_seconds':usage.ru_stime},indent=2)+'\n')
print(status)
