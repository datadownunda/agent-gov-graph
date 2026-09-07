"""Attach reproducible scope, full-code accounting and source-integrity receipts."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
report=json.loads((OUT/'gate-a-report.json').read_text())
benchmark=json.loads((OUT/'benchmark.json').read_text())
answers=json.loads((OUT/'query-results.json').read_text())
validation=json.loads((OUT/'validation-scope.json').read_text())
source_inventory=json.loads((OUT/'source-inventory.json').read_text())


def hash_file(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def count(paths):
    result=[]
    for p in paths:
        tree=ast.parse(p.read_text())
        logical=sum(isinstance(n,ast.stmt) and not isinstance(n,(ast.Import,ast.ImportFrom)) and not
            (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str)) for n in ast.walk(tree))
        result.append({'path':str(p.relative_to(ROOT)),'logical_statements':logical,
                       'physical_nonblank_lines':sum(bool(x.strip()) for x in p.read_text().splitlines())})
    return {'files':result,'logical_statements':sum(r['logical_statements'] for r in result)}


groups={'core':count(sorted((ROOT/'src/graph_value').glob('*.py'))),
        'experiment_harness':count(sorted((ROOT/'experiments/graph_value').glob('*.py'))),
        'tests':count(sorted((ROOT/'tests').glob('test_graph_value_*.py'))),
        'result_reproduction_scripts':count(sorted(OUT.glob('*.py')))}
full={'groups':groups,'core_plus_harness_logical_statements':groups['core']['logical_statements']+groups['experiment_harness']['logical_statements'],
      'all_new_python_including_tests_and_reproduction_logical_statements':sum(g['logical_statements'] for g in groups.values())}
changed=[f for f,h in benchmark['implementation_files'].items() if hash_file(ROOT/f)!=h]
original_changed=[p for p,h in source_inventory['files'].items() if hash_file(ROOT/p)!=h]
tracked=subprocess.run(['git','diff','--exit-code',report['source_commit'],'--'],cwd=ROOT,capture_output=True,text=True)
assert not changed and not original_changed and tracked.returncode==0
report['validation_scope']=validation
report['full_new_code_accounting']=full
report['integrity']={'frozen_protocol_matches':hash_file(ROOT/'experiments/graph_value/protocol.json')==report['protocol_sha256'],
                     'measured_code_unchanged':not changed,'original_archives_unchanged':not original_changed,
                     'all_preexisting_tracked_files_unchanged':tracked.returncode==0}
report['query_summary']={q:{'records':len(v['result']['records']),'paths':len(v['result']['paths']),
                          'affected':len(v['result'].get('affected',[])),
                          'conclusions':len(v['result'].get('conclusions',[])),
                          'equal':v['both_implementations_equal']} for q,v in answers.items()}
report['correctness_claim_scope']='The correctness gate reports executed Gate A oracles, preserved-source replay, available regression checks and paired benchmark results. It is not a claim that the unavailable full Docker-backed integration suite passed.'
report['complexity']['query_method_logical_statements']={arm:{q:next((f['functions'][q]['logical_statements'] for f in files if q in f['functions']),None) for q in ('q1','q2','q3','q4')} for arm,files in report['complexity']['arms'].items()}
report['complexity']['effort'].update({
    'elapsed_from_frozen_protocol_to_last_core_edit_seconds':max(p.stat().st_mtime for p in (ROOT/'src/graph_value').glob('*.py'))-(ROOT/'experiments/graph_value/protocol.json').stat().st_mtime,
    'elapsed_from_frozen_protocol_to_report_seconds':datetime.now(timezone.utc).timestamp()-(ROOT/'experiments/graph_value/protocol.json').stat().st_mtime,
    'baseline_active_development_seconds':None,'graph_active_development_seconds':None,
    'elapsed_time_limit':'Artifact timestamps give elapsed lab time including approvals, Docker stalls and benchmark execution; active per-arm implementation effort was not instrumented and no productivity conclusion follows.'})
report['supplementary_stress']=json.loads((OUT/'stress.json').read_text())
(OUT/'gate-a-report.json').write_text(json.dumps(report,indent=2)+'\n')
text=(OUT/'REPORT.md').read_text().split('\n## Additional evidence and validation scope')[0]
text+='\n## Additional evidence and validation scope\n\n'
text+='Thirty paired workers (10 repetitions × 3 measured tiers), with four query classes each, produced 120 matching paired query results from identical per-pair inputs. Each arm/query/tier has 100 warm observations and 10 cold repetitions.\n\n'
text+='The core correctness checks passed within their evaluated scope. **The full Docker-backed regression suite did not complete.** A pinned-image OPA version command timed out after 20 seconds; the detailed completed/excluded test scope is in validation-scope.json. No full integration pass is claimed.\n\n'
text+='The million-relationship tier was not executed: its conservative preflight estimate was about 23 GiB, beyond the frozen 4 GiB cap. It is untested, not a failed query.\n\n'
text+='| Query/result case | Records | Paths | Affected actors | Assurance conclusions |\n|---|---:|---:|---:|---:|\n'
for q,r in report['query_summary'].items():text+=f'| {q} | {r["records"]} | {r["paths"]} | {r["affected"]} | {r["conclusions"]} |\n'
text+='\nQ2/Q3 return assurance connections inside each actor/tuple result; the top-level conclusion count above is the Q4-specific endpoint list. The independent Q3 case retains alternative bases for middle and worker, while leaf loses all demonstrated support. Neither finding nor outcome prevention is inferred. Full results are in query-results.json.\n\n'
text+='| Query-specific method logical statements | Baseline | Graph |\n|---|---:|---:|\n'
for q in ('q1','q2','q3','q4'):text+=f'| {q.upper()} | {report["complexity"]["query_method_logical_statements"]["baseline"][q]} | {report["complexity"]["query_method_logical_statements"]["graph"][q]} |\n'
text+='\nNo individual query method met the 30% reduction either. Shared helpers, projector and generic traversal are additionally counted in the whole-arm totals; method LOC alone is not the decision.\n\n'
text+=f'Full new core + harness: **{full["core_plus_harness_logical_statements"]} logical statements**. Including tests and result-reproduction scripts: **{full["all_new_python_including_tests_and_reproduction_logical_statements"]}**. Core-only comparison remains 137 baseline + 157 graph + 258 shared = 552. Active development time per arm was not instrumented; elapsed lab time and limitations are disclosed rather than invented.\n\n'
text+='Supplementary full-root chains at depths 8, 16 and 32, plus competing populations of 2, 8 and 32, passed paired-result checks. Those are bounded supplementary measurements, not replacements for the main workload or new live evidence.\n\n'
text+='Cold source-to-answer is timed from worker preparation through result serialization; the separately recorded launch-to-exit measure includes process startup. Per-query CPU is cumulative worker CPU, and per-query RSS is worker high-water RSS; tier peak memory includes the controller.\n\n'
text+='Measured source code still matches the benchmark-start digests. The frozen protocol, original evidence archives and all pre-existing tracked files remain unchanged. No graph database was installed, configured, queried or modified.\n'
(OUT/'REPORT.md').write_text(text)
print(json.dumps({'full_code':{k:v for k,v in full.items() if k!='groups'},'integrity':report['integrity'],'query_summary':report['query_summary']},indent=2))
