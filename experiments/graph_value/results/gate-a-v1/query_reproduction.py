"""Reproduce complete query answers and a separately scored counterfactual case."""
import hashlib
import json
from pathlib import Path
import sys
from src.graph_value.canonical import load_reference
from src.graph_value.baseline import Baseline
from src.graph_value.queries import GraphQueries
from src.graph_value.results import stable
from experiments.graph_value.generate import prepare,workload,AT

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
source=json.loads((OUT/'source-100000-8.json').read_text())
bundle=prepare(source,reference=load_reference(ROOT))
a,g=Baseline(bundle),GraphQueries(bundle)
answers={}
for q,args in workload(bundle).items():
    left,right=getattr(a,q.lower())(**args),getattr(g,q.lower())(**args)
    assert left==right and left['complete']
    answers[q]={'input':args,'both_implementations_equal':True,
                'result_sha256':hashlib.sha256(stable(left).encode()).hexdigest(),'result':left}
sys.path.insert(0,str(ROOT/'tests'))
from test_graph_value_queries import authority_fixture,oracle
b=authority_fixture();a,g=Baseline(b),GraphQueries(b)
args={'context':'pair','selected':{'kind':'delegation','record_id':'d1','version':'1'},'at':AT}
x,y=a.q3(**args),g.q3(**args)
observed={r['actor']:{k:[[ref['record_id'] for ref in p['chain']] for p in r[k]] for k in ('lost','remaining')} for r in x['affected']}
assert observed==oracle()['authority'] and x==y
answers['independent_counterfactual_case']={'input':args,'both_implementations_equal':True,
    'independent_oracle_passed':True,'result':x}
(OUT/'query-results.json').write_text(json.dumps(answers,indent=2)+'\n')
print({q:{'records':len(v['result']['records']),'paths':len(v['result']['paths']),
          'affected':len(v['result'].get('affected',[])),'conclusions':len(v['result'].get('conclusions',[]))} for q,v in answers.items()})
