"""Conservative experimental contracts, not a replacement for AGG core.

References are source-scoped. A bound policy record is not an independent
execution finding. Missing facts remain null instead of invented defaults.
"""
def bind_decision(call, events):
    key=call.get('decision_id')
    if not key:
        candidates=[e for e in events if e.get('decision',{}).get('run_id')==call.get('run_id')
                    and e.get('decision',{}).get('tool')==call.get('tool')]
        return {'binding':'UNPROVEN','candidates':len(candidates),'finding':'NOT_EVALUABLE',
                'reason':'No native per-call decision reference; uniqueness is insufficient'}
    candidates=[e for e in events if e.get('decision',{}).get('decision_id')==key]
    if len(candidates)!=1:
        return {'binding':'MISSING' if not candidates else 'CONFLICT','candidates':len(candidates),
                'finding':'NOT_EVALUABLE','reason':'Expected one decision record within this source bundle'}
    d=candidates[0]['decision']
    if (d.get('run_id'),d.get('tool'))!=(call.get('run_id'),call.get('tool')):
        return {'binding':'CONFLICT','candidates':1,'finding':'NOT_EVALUABLE','reason':'Decision reference contradicts run or tool'}
    return {'binding':'NATIVE_REFERENCE_BOUND','candidates':1,'finding':'NOT_EVALUABLE',
            'decision':d.get('action'),'reason':'Reference binds harness records only; target effect and authority validity remain unproven'}

def observation(path_ref,record,kind,boundary):
    return {'schema':'agg.experimental.observation.v1','kind':kind,'source_ref':path_ref,
            'trust_boundary':boundary,'native_record':record,'control_finding':'NOT_EVALUABLE'}

def health_fax_fact(final_state):
    """Read an inspected native state field, not a task-success evaluator."""
    full=final_state.get('full_state')
    fax=full.get('faxPortal') if isinstance(full,dict) else None
    value=fax.get('faxesSent') if isinstance(fax,dict) else None
    valid=isinstance(value,int) and not isinstance(value,bool) and value>=0
    return {'native_field':'full_state.faxPortal.faxesSent','observed_value':value,
            'observation_status':'PRESENT' if valid else 'MISSING_OR_INVALID',
            'source_kind':'browser_local_storage_snapshot','finding':'NOT_EVALUABLE',
            'reason':'No externally issued delivery receipt or runtime authority evidence'}

def modus_observations(trajectory,source_ref):
    """ATIF call identifiers are scoped to their enclosing step, not global IDs."""
    for step in trajectory.get('steps',[]):
        for result in (step.get('observation') or {}).get('results',[]):
            matches=[c for c in step.get('tool_calls',[]) if c.get('tool_call_id')==result.get('source_call_id')]
            yield {'schema':'agg.experimental.observation.v1','kind':'tool_observation',
                'source_ref':source_ref,'session_id':trajectory.get('session_id'),
                'step_id':step.get('step_id'),'source_call_id':result.get('source_call_id'),
                'binding':'NATIVE_STEP_REFERENCE' if len(matches)==1 else 'NOT_EVALUABLE',
                'function_name':matches[0].get('function_name') if len(matches)==1 else None,
                'event_time':step.get('timestamp'),'native_observation':result,
                'trust_boundary':'agent_execution_harness','control_finding':'NOT_EVALUABLE'}
