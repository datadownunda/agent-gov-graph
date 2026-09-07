"""AST inventory, not a formatting/LOC optimization target.

Charge the entire graph projector, traversal engine and query layer to graph.
Charge all baseline indexes and queries to baseline. Shared semantic validation
and canonical adaptation are disclosed, as is unchanged M4/M5 reused code.
Query method sizes are descriptive only; gate scoring uses whole-arm bespoke
code to prevent extracting complexity into a convenient uncounted helper.
"""
import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
ARMS={'baseline':['src/graph_value/baseline.py'],
      'graph':['src/graph_value/projection.py','src/graph_value/traversal.py','src/graph_value/queries.py']}
SHARED=['src/graph_value/canonical.py','src/graph_value/semantics.py','src/graph_value/results.py']
REUSED=['src/authority_resolver.py','src/authority_reconstruction.py','src/delegation_resolver.py',
        'src/delegation_reconstruction.py','src/action_reconciliation.py','src/correlation_assertion.py',
        'src/control_attestation.py','src/m6_attestation_evidence.py']


def executable(node):
    return isinstance(node,ast.stmt) and not isinstance(node,(ast.Import,ast.ImportFrom)) and not (
        isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str))


def inventory(path):
    text=(ROOT/path).read_text();tree=ast.parse(text)
    functions={}
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            functions[n.name]={'logical_statements':sum(executable(x) for x in ast.walk(n)),
                'physical_lines':n.end_lineno-n.lineno+1,'loops':sum(isinstance(x,(ast.For,ast.While)) for x in ast.walk(n)),
                'self_recursive_calls':sum(isinstance(x,ast.Call) and (
                    isinstance(x.func,ast.Name) and x.func.id==n.name or
                    isinstance(x.func,ast.Attribute) and x.func.attr==n.name) for x in ast.walk(n))}
    return {'path':path,'logical_statements':sum(executable(n) for n in ast.walk(tree)),
            'physical_nonblank_lines':sum(bool(line.strip()) for line in text.splitlines()),'functions':functions}


def measure():
    arms={arm:[inventory(p) for p in paths] for arm,paths in ARMS.items()}
    shared=[inventory(p) for p in SHARED]
    totals={arm:sum(f['logical_statements'] for f in files) for arm,files in arms.items()}
    shared_total=sum(f['logical_statements'] for f in shared)
    # Function-level human-review inventory. Counts refer to routines, not to
    # textual matches for words such as cycle/path. Existing M5 is shared below.
    non_loc={
        'custom_recursion':{'baseline':0,'graph':0,'basis':'Both use iterative traversal; M5 is also iterative.'},
        'traversal_routines':{'baseline':2,'graph':1,'baseline_locations':['Baseline.dependencies','Baseline.q2'],
                              'graph_locations':['walk']},
        'cycle_handling':{'baseline':2,'graph':1,'baseline_locations':['dependencies path membership','q2 seen set'],
                          'graph_locations':['walk visited path']},
        'path_state_management':{'baseline':2,'graph':1,'baseline_locations':['dependencies todo/path/provenance','q2 descendants/seen'],
                                  'graph_locations':['walk todo/visited/provenance']},
        'topology_specific_lookups_joins':{'baseline':2,'graph':3,
            'baseline_locations':['Baseline.__init__ reverse/children/relationship/principal indexes','Baseline.q2 actor/tuple/assurance joins'],
            'graph_locations':['Projection.__init__ relation/property indexes','GraphQueries.__init__ actor evidence index','GraphQueries.q2 actor/tuple/assurance joins']},
        'inverse_query_changed_lines_functions':{'baseline':0,'graph':0,'basis':'Both accept reverse=True; test covers forward and reverse.'},
        'variable_depth_changed_lines_functions':{'baseline':0,'graph':0,'basis':'Both accept depth=None or depth=1; no code changes.'},
    }
    return {'method':'AST executable statement count; imports/docstrings excluded; semicolon statements counted separately',
            'arms':arms,'shared':shared,'reused_unchanged':[inventory(p) for p in REUSED],
            'arm_owned_topology_logical_statements':totals,'shared_logical_statements':shared_total,
            'total_new_implementation_logical_statements':sum(totals.values())+shared_total,
            'standalone_total_with_shared':{arm:n+shared_total for arm,n in totals.items()},
            'graph_reduction_fraction':1-totals['graph']/totals['baseline'],
            'non_loc':non_loc,'non_loc_improvement_count':sum(v['graph']<v['baseline'] for v in non_loc.values()),
            'attribution_limit':'Q2/Q3 semantic path validation still uses the unchanged M5 resolver in both arms. Generic graph traversal does not remove that implementation cost.',
            'effort':{'measurement':'Single-agent implementation; wall-clock development duration is not controlled engineering effort. No measured productivity claim.',
                      'module_boundary_optimization_for_threshold':False},
            'defects_found_during_development':[
                {'kind':'implementation','detail':'Q1 details aliased input records; permutation test exposed mutable output. Fixed with copied, normalized result details.'},
                {'kind':'test','detail':'Boundary fixture omitted requested tuple after adding export scope; assertion inspected export instead of read. Fixed explicit requested tuple.'}
            ]}


if __name__=='__main__':print(json.dumps(measure(),indent=2))
