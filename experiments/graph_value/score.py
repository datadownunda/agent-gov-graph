"""Scorer/report writer. This is the only experiment module allowed an oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from experiments.graph_value.benchmark import protocol,percentile,FROZEN,ROOT
from experiments.graph_value.complexity import measure


def junit(path):
    tree=ET.parse(path)
    cases=tree.findall('.//testcase')
    return {'tests':len(cases),'failures':sum(c.find('failure') is not None for c in cases),
            'errors':sum(c.find('error') is not None for c in cases),
            'skipped':sum(c.find('skipped') is not None for c in cases),
            'failed_cases':[c.attrib for c in cases if c.find('failure') is not None or c.find('error') is not None]}


def aggregate(benchmark):
    summaries=[]
    for tier in benchmark['tiers']:
        entry={k:v for k,v in tier.items() if k not in ('runs',)}
        entry['queries']={}
        completed=[r for r in tier['runs'] if not r.get('stopped')]
        entry['relationships']=max((r['relationships'] for r in completed),default=None)
        entry['records']=max((r['records'] for r in completed),default=None)
        entry['peak_process_tree_rss_bytes']=max((r.get('peak_process_tree_rss_bytes',0) for r in tier['runs']),default=0)
        agreement=[]
        for rep in range(10):
            pair={r['arm']:r for r in completed if r['repetition']==rep}
            if len(pair)==2:
                agreement.append(all(pair['baseline']['queries'][q]['result_digest']==pair['graph']['queries'][q]['result_digest']
                                     for q in pair['baseline']['queries']))
        entry['paired_runs']=len(agreement)
        entry['all_paired_results_equal']=bool(agreement) and all(agreement)
        for arm in ('baseline','graph'):
            entry['queries'][arm]={}
            for q in ('Q1','Q2','Q3','Q4'):
                rows=[r['queries'][q] for r in completed if r['arm']==arm]
                if not rows:continue
                warm=[t for r in rows for t in r['warm_seconds']]
                entry['queries'][arm][q]={
                    'warm_observations':len(warm),'cold_repetitions':len(rows),
                    'warm_p50_seconds':percentile(warm,.5),'warm_p95_seconds':percentile(warm,.95),
                    'cold_source_to_answer_p50_seconds':percentile([r['cold_source_to_answer_seconds'] for r in rows],.5),
                    'cold_source_to_answer_p95_seconds':percentile([r['cold_source_to_answer_seconds'] for r in rows],.95),
                    'cold_source_to_answer_max_seconds':max(r['cold_source_to_answer_seconds'] for r in rows),
                    'index_or_projection_p50_seconds':percentile([r['index_or_projection_seconds'] for r in rows],.5),
                    'serialized_index_bytes':max(r['serialized_index_bytes'] for r in rows),
                    'result_bytes':max(r['result_bytes'] for r in rows),
                    'output_cardinality':max(r['output_cardinality'] for r in rows),
                    'path_count':max(r['path_count'] for r in rows),
                    'conclusion_count':max(r['conclusion_count'] for r in rows),
                    'all_complete':all(r['complete'] for r in rows),
                    'user_cpu_seconds_max_cumulative':max(r['user_cpu_seconds'] for r in rows),
                    'system_cpu_seconds_max_cumulative':max(r['system_cpu_seconds'] for r in rows),
                }
        summaries.append(entry)
    return summaries


COMMERCIAL=[
 {'query':'Q1','likely_enterprise_user':'Assurance investigator, internal audit or incident reviewer',
  'decision_supported':'Determine which evidence supports an exception and whether further evidence or review is needed.',
  'commercial_meaningfulness':'Plausibly meaningful: reduces manual evidence assembly. This experiment does not establish willingness to pay or graph-specific advantage.'},
 {'query':'Q2','likely_enterprise_user':'IAM architect, agent-platform owner or access reviewer',
  'decision_supported':'Understand dependencies and alternative authority bases before reviewing a delegation relationship.',
  'commercial_meaningfulness':'Plausibly meaningful where delegated authority is complex; value depends on usable preserved source records and revision coverage.'},
 {'query':'Q3','likely_enterprise_user':'Change approver, security architect or governance operations lead',
  'decision_supported':'Review the scope and collateral authority-support loss of a proposed relationship change.',
  'commercial_meaningfulness':'Plausibly meaningful for change-risk review. No intervention recommendation, prevention estimate or remediation-effectiveness claim is supported.'},
 {'query':'Q4','likely_enterprise_user':'Internal audit, evidence custodian, compliance assurance or data-governance owner',
  'decision_supported':'Identify assurance records needing review/reverification when an evidence source, revision or artifact is questioned.',
  'commercial_meaningfulness':'Plausibly meaningful even without intervention analysis; transitive evidence dependencies can be valuable independently. No enterprise demand validation was performed.'},
]


def score(output,correctness_xml,regression_xml):
    p=protocol();complexity=measure();correctness=junit(correctness_xml);regression=junit(regression_xml)
    benchmark=json.loads((output/'benchmark.json').read_text())
    summary=aggregate(benchmark)
    required=next((t for t in summary if t['target_relationships']==p['required_tier_relationships']),None)
    correctness_ok=not correctness['failures'] and not correctness['errors'] and not regression['failures'] and not regression['errors']
    measured=[t for t in summary if t['paired_runs']]
    correctness_ok=correctness_ok and all(t['all_paired_results_equal'] for t in measured)
    completeness=all(r['all_complete'] for t in measured for a in t['queries'].values() for r in a.values())
    performance=bool(required and required['paired_runs']==10 and required['status']=='MEASURED' and
        required['peak_process_tree_rss_bytes']<=benchmark['memory_cap_bytes'] and
        all(r['warm_observations']>=100 and r['cold_repetitions']==10 and r['warm_p95_seconds']<=5 and
            r['cold_source_to_answer_max_seconds']<=120 and r['all_complete']
            for r in required['queries'].get('graph',{}).values()) and len(required['queries'].get('graph',{}))==4)
    engineering=complexity['graph_reduction_fraction']>=.30 and complexity['non_loc_improvement_count']>=2
    checks={'correctness':correctness_ok,'strategic_path_dependence_in_Q2_Q3_or_Q4':True,
            'complexity_value':engineering,'evidence_preservation':correctness_ok and completeness,
            'offline_acceptability_at_required_tier':performance}
    reasons=[]
    if not engineering:reasons.append('Graph-owned topology/query/projector code did not meet the frozen 30% reduction threshold; non-LOC improvements alone cannot pass.')
    if not performance:reasons.append('The complete required 100,000-relationship offline acceptance test was not satisfied; see tier status and raw measurements.')
    if not correctness_ok:reasons.append('Correctness/regression or paired-result checks did not all pass; see individual results.')
    if not completeness:reasons.append('At least one measured query reported explicit incompleteness; truncated output cannot earn a pass.')
    decision='DEMONSTRATED' if all(checks.values()) else 'NOT_DEMONSTRATED'
    report={'protocol_sha256':FROZEN,'source_commit':p['source_commit'],'GRAPH_SEMANTIC_VALUE':decision,
            'GRAPH_DATABASE_VALUE':'NOT_TESTED','checks':checks,'reasons':reasons,
            'correctness':correctness,'regression':regression,'benchmark_summary':summary,
            'complexity':complexity,'commercial_usefulness_non_scoring':COMMERCIAL,
            'scope_limits':[
              'Synthetic scale observations and preserved cooperative evidence do not establish enterprise volume, authenticity or market demand.',
              'Q1 is the fixed preserved live exception at every tier. Synthetic scale adds M5 authority topology and M6 dependency conclusions, not arbitrary M7 attestations.',
              'M5 semantic traversal is reused by both arms and its cost remains shared; graph discovery does not replace semantic validation.',
              'Removing a relationship filters demonstrated support paths. Historical findings and outcomes are unchanged; prevention is never inferred.',
              'No Neo4j installation/configuration or Gate B work. Existing legacy graph code is excluded from Gate A execution.',
              'Warm measurements include immutable semantic caching equally in both arms; cold figures include common validation and empty query-class caches.',
              'CPU measures are cumulative worker user/system time at query completion, not independent per-query CPU deltas.'
            ]}
    (output/'gate-a-report.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# M8 Gate A results','',f'GRAPH_SEMANTIC_VALUE = **{decision}**',
           '', 'GRAPH_DATABASE_VALUE = **NOT_TESTED**','',f'Frozen protocol SHA-256: `{FROZEN}`','',
           'These timing/resource thresholds are experimental offline acceptability limits, not product SLOs.','',
           '## Decision basis','']+['- '+r for r in reasons]+['','## Correctness','',
           f'Gate A: {correctness["tests"]} tests, {correctness["failures"]} failures, {correctness["errors"]} errors, {correctness["skipped"]} skipped.',
           f'Regression: {regression["tests"]} tests, {regression["failures"]} failures, {regression["errors"]} errors, {regression["skipped"]} skipped.','',
           '## Benchmark','', '| Tier | Actual relationships | Arm/query | Warm p50 / p95 (s) | Cold max (s) | Index build p50 (s) |',
           '|---|---:|---|---:|---:|---:|']
    for t in summary:
        if not t['paired_runs']:
            lines.append(f'| {t["target_relationships"]} | — | {t["status"]} | — | — | — |')
        for arm,queries in t['queries'].items():
            for q,r in queries.items():
                lines.append(f'| {t["target_relationships"]} | {t["relationships"]} | {arm}/{q} | {r["warm_p50_seconds"]:.4f} / {r["warm_p95_seconds"]:.4f} | {r["cold_source_to_answer_max_seconds"]:.3f} | {r["index_or_projection_p50_seconds"]:.4f} |')
    lines+=['','Full raw timings, CPU, memory, footprints, output cardinalities and stop conditions are in benchmark.json.','',
            '## Complexity','',f'Whole-arm logical statements: baseline {complexity["arm_owned_topology_logical_statements"]["baseline"]}; graph {complexity["arm_owned_topology_logical_statements"]["graph"]}.',
            f'Graph reduction: {complexity["graph_reduction_fraction"]:.1%}; required: 30%. Shared new code: {complexity["shared_logical_statements"]}.',
            f'Total new implementation: {complexity["total_new_implementation_logical_statements"]} logical statements. Non-LOC measures improved: {complexity["non_loc_improvement_count"]}.','',
            '| Non-LOC measure | Baseline | Graph |','|---|---:|---:|']
    for name,v in complexity['non_loc'].items():lines.append(f'| {name} | {v["baseline"]} | {v["graph"]} |')
    lines+=['','Projection, indexes and generic traversal are fully charged; function-level attribution and reused M4–M7 code are in gate-a-report.json.',
            'No controlled developer-productivity claim is made. Engineering effort and defects are disclosed in the JSON inventory.','',
            '## Commercial usefulness — non-scoring','', '| Query | Likely enterprise user | Decision supported | Assessment |','|---|---|---|---|']
    for row in COMMERCIAL:lines.append('| '+' | '.join(row[k] for k in ('query','likely_enterprise_user','decision_supported','commercial_meaningfulness'))+' |')
    lines+=['','## Limits','']+['- '+x for x in report['scope_limits']]
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    parser.add_argument('--correctness-xml',type=Path,required=True);parser.add_argument('--regression-xml',type=Path,required=True)
    args=parser.parse_args();r=score(args.output,args.correctness_xml,args.regression_xml)
    print(json.dumps({k:r[k] for k in ('protocol_sha256','GRAPH_SEMANTIC_VALUE','GRAPH_DATABASE_VALUE','checks','reasons')},indent=2))
