"""M6 derived assertions. Source identities, M1/M2 rules and M4/M5 remain intact."""
from copy import deepcopy

import jsonschema

from src.authority_resolver import instant
from src.authority_reconstruction import reconstruct_authority
from src.correlation_assertion import native_assertions, composite_assertions, validate_assertion
from src.delegation_reconstruction import reconstruct_delegation, create_assertion
from src.evidence_digest import evidence_digest

RULE='action-reconciliation/1'


def _stable(record):
    return {k:v for k,v in record.items() if k!='ingested_at'}


def _replay(records, bundles):
    """Replay exactly the supplied assertion populations; never discover new links.

    Full role populations must be present. This prevents a caller from hiding an
    inconvenient duplicate within the evidence snapshot passed to reconciliation.
    Completeness outside that snapshot remains a declared coverage limitation.
    """
    edges={}; consumed=[]
    for bundle in bundles:
        assertions=bundle['assertions']; roles=bundle['roles']
        if len(roles)!=2 or len(set(roles.values()))!=2 or not set(roles.values()) <= {'governance','execution','outcome'}:
            raise ValueError('Invalid source roles')
        if not assertions:
            if any(r['role'] in roles.values() for r in records): raise ValueError('Missing population assertions')
            continue
        first=assertions[0]; params=first['rule']['parameters']
        populations={alias:[r for r in records if r['role']==role] for alias,role in roles.items()}
        common={'relationship_type':first['relationship_type'],'coverage':first['evidence_coverage']}
        if first['correlation_method']=='NATIVE_IDENTIFIER_LINKAGE' and set(roles)=={'left','right'}:
            expected=native_assertions(populations['left'],populations['right'],**params,**common)
        elif first['correlation_method']=='EXACT_COMPOSITE_LINKAGE' and set(roles)=={'opa','journal'}:
            expected=composite_assertions(populations['opa'],populations['journal'],**params,**common)
        else:
            raise ValueError('Unsupported assertion method or source labels')
        for assertion in assertions: validate_assertion(assertion)
        if sorted(assertions,key=lambda a:a['assertion_id']) != sorted(expected,key=lambda a:a['assertion_id']):
            raise ValueError('Correlation does not replay against supplied evidence population')
        for a in assertions:
            consumed.append(a)
            if a['result']['state']=='LINKED':
                x=a['focus']['evidence_ref']; y=a['result']['linked_evidence'][0]['evidence_ref']
                edges.setdefault(x,{})[y]=a['assertion_id']
                edges.setdefault(y,{})[x]=a['assertion_id']
    return edges,consumed


def _identity(a,b,mapping):
    if not isinstance(a,dict) or not isinstance(b,dict) or not a.get('id') or not b.get('id'): return 'UNKNOWN'
    if a.get('namespace')==b.get('namespace'): return 'SAME' if a==b else 'DIFFERENT'
    if mapping:
        entries=mapping.get('entries',[])
        # Mapping is explicit comparison evidence, never a matching feature.
        aa=[e['target'] for e in entries if e.get('source')==a]
        bb=[e['target'] for e in entries if e.get('source')==b]
        if len(aa)>1 or len(bb)>1: return 'UNKNOWN'
        if aa: a=aa[0]
        if bb: b=bb[0]
        if a.get('namespace')==b.get('namespace'): return 'SAME' if a==b else 'DIFFERENT'
    return 'UNKNOWN'


def _explain(g,e,assertion,history):
    if not assertion or not history or not g.get('raw'):
        return {'status':'INSUFFICIENT_EVIDENCE','valid_explanatory_bases':[]}
    m4=reconstruct_authority(g['raw'],history)
    replay=reconstruct_delegation(assertion,history)
    detail={'m4':m4,'m5':replay,'assertion_digest':evidence_digest(assertion),'valid_explanatory_bases':[]}
    if m4['status']!='VERIFIED' or replay['status']!='VERIFIED':
        return dict(detail,status='INSUFFICIENT_EVIDENCE')
    binding=g['raw']['context']['authority_binding']; query=assertion['query']
    expected={'actor':e['actor']['id'],'action':e['action'],'resource_id':e['resource_id'],
              'resource_type':e['resource_type'],'effective_at':binding['opa_decision_at']}
    if (query!=expected or e['actor']['namespace']!='agent' or g['actor']['namespace']!='agent'
            or assertion['authority_revision']!=binding['revision']):
        return dict(detail,status='INSUFFICIENT_EVIDENCE')
    # Reuse M5 for both M4 times. A chain that changes across the decision boundary
    # cannot silently become an explanation by choosing the favorable time.
    earlier=create_assertion(dict(query,effective_at=binding['authority_resolution_at']),
            authority_reference=assertion['authority_revision'],delegation_reference=assertion['delegation_revision'],
            history_directory=history)['resolution']
    later=replay['resolution']
    if any(earlier[k]!=later[k] for k in ('status','permission_result','valid_bases')):
        return dict(detail,status='TEMPORAL_BOUNDARY_AMBIGUITY')
    roots={(r['authority_record_id'],r['authority_version']) for r in m4['at_opa_decision']['record_refs']}
    bases=[b for b in later['valid_bases'] if b['authority_kind']=='DELEGATED'
           and b['root_principal']==g['actor']['id'] and b['chain']
           and (b['chain'][0]['record_id'],b['chain'][0]['version']) in roots]
    detail['valid_explanatory_bases']=bases
    if bases: return dict(detail,status='EXPLAINED')
    # A known rejected candidate can support unexplained divergence. Missing or
    # defective evidence cannot be turned into evidence of unauthorized behavior.
    unknown={'INSUFFICIENT_EVIDENCE','EVIDENCE_DEFECT','DELEGATION_CHAIN_BROKEN','DELEGATION_CONFLICT'}
    if later['status'] in unknown or any(c['status'] in unknown for c in later['candidates']):
        return dict(detail,status='INSUFFICIENT_EVIDENCE')
    return dict(detail,status='UNEXPLAINED')


def _coverage_captures(coverage,g):
    try:
        return (coverage['roles']=={'execution':'CAPTURED','outcome':'CAPTURED'}
                and bool(coverage['basis']) and coverage['scope']=={k:g[k] for k in ('actor','action','resource_id','resource_type')}
                and instant(coverage['interval_start'])<=instant(g['observed_at'])<=instant(coverage['interval_end']))
    except (KeyError,ValueError,TypeError): return False


def reconcile(records, correlations, *, governance_ref, coverage=None, identity_mapping=None,
              delegation_assertion=None, history_directory=None):
    """Derive one action assertion using only replayed explicit linkage paths."""
    records=sorted(deepcopy(records),key=lambda r:r['evidence_ref'])
    out={'schema_version':'1.0','rule_version':RULE,'governance_ref':governance_ref,
         'source_evidence':[_stable(r) for r in records], 'correlation_assertions':[], 'correlation_paths':[],
         'claims':{role:[] for role in ('governance','execution','outcome')},'comparisons':[],
         'issue_codes':[],'result':'INSUFFICIENT_EVIDENCE', 'authority_explanation':None,
         'evidence_coverage':deepcopy(coverage), 'identity_mapping':deepcopy(identity_mapping),
         'identity_mapping_digest':evidence_digest(identity_mapping) if identity_mapping else None,
         'time_assumptions':{'decision_clock':'OPA native timestamp; authority_resolution_at stays separate',
                             'target_clock':'NGINX request completion clock; cross-system synchronization is not proven'},
         'limitations':['Linkage is conditional on supplied populations and asserted issuer namespace/non-reuse.',
                        'Content digests do not authenticate producers or prove completeness.',
                        'Absent records are not proof of absent activity. Coverage is declared, bounded evidence.',
                        'REPRESENTATION_SERVED does not establish client receipt or use.',
                        'No root cause or control-effectiveness interpretation.']}
    def finish(status):
        out['result']=status;out['issue_codes']=sorted(set(out['issue_codes']))
        out['assertion_id']=evidence_digest(out)
        return out
    issues=out['issue_codes']
    try:
        lookup={r['evidence_ref']:r for r in records}
        if len(lookup)!=len(records): raise ValueError('Duplicate evidence references')
        g=lookup[governance_ref]
        if g['role']!='governance': raise ValueError('Not governance')
        edges,assertions=_replay(records,correlations)
        out['correlation_assertions']=sorted(assertions,key=lambda a:a['assertion_id'])
    except (KeyError,ValueError,TypeError,StopIteration,jsonschema.ValidationError):
        issues.append('CORRELATION_NOT_VERIFIABLE');return finish('NOT_EVALUABLE')
    # Traverse accepted assertions, not record fields or independently discovered joins.
    paths={governance_ref:[]}; todo=[governance_ref]
    while todo:
        ref=todo.pop(0)
        for other,aid in sorted(edges.get(ref,{}).items()):
            if other not in paths:
                paths[other]=paths[ref]+[aid];todo.append(other)
    for ref,path in sorted(paths.items()):
        out['claims'][lookup[ref]['role']].append(_stable(lookup[ref]))
        if path: out['correlation_paths'].append({'evidence_ref':ref,'assertion_ids':path})
    for a in assertions:
        if a['focus']['evidence_ref'] in paths and a['result']['state'] != 'LINKED':
            issues.append('CORRELATION_'+a['result']['state'])
    if any(r.get('defects') for ref,r in lookup.items() if ref in paths):
        issues.append('SOURCE_EVIDENCE_DEFECT');return finish('NOT_EVALUABLE')
    if len(out['claims']['governance'])!=1 or any(len(out['claims'][k])>1 for k in ('execution','outcome')):
        issues.append('COMPETING_ACTION_CLAIMS');return finish('INSUFFICIENT_EVIDENCE')
    e=next(iter(out['claims']['execution']),None);o=next(iter(out['claims']['outcome']),None)
    if not e: issues.append('EXECUTION_EVIDENCE_MISSING')
    if not o: issues.append('OUTCOME_EVIDENCE_MISSING')
    if any(r['evidence_ref'] not in paths for r in records): issues.append('UNLINKED_EVIDENCE_PRESENT')
    difference=False; unknown=False; actor_difference=False
    for a,b in ((g,e),(g,o),(e,o)):
        if a is None or b is None: continue
        for field in ('actor','action','resource_id','resource_type'):
            x,y=a.get(field),b.get(field)
            rel=_identity(x,y,identity_mapping) if field=='actor' else ('UNKNOWN' if x is None or y is None else 'SAME' if x==y else 'DIFFERENT')
            out['comparisons'].append({'left_ref':a['evidence_ref'],'right_ref':b['evidence_ref'],
                                      'dimension':field,'left':x,'right':y,'relation':rel})
            if rel=='UNKNOWN': unknown=True;issues.append('UNRESOLVED_'+field.upper())
            if rel=='DIFFERENT':
                issues.append(field.upper()+'_DIVERGENCE')
                if field=='actor' and a['role']=='governance': actor_difference=True
                else: difference=True
    decision=g.get('governance_decision')
    if decision not in ('ALLOW','DENY'): issues.append('GOVERNANCE_NOT_EVALUABLE');return finish('NOT_EVALUABLE')
    effect=bool(o and o.get('target_outcome')=='REPRESENTATION_SERVED')
    # A different tuple is a divergence; do not call an unrelated effect the denied effect.
    governed_effect=effect and all(o.get(f)==g.get(f) for f in ('action','resource_id','resource_type'))
    if decision=='DENY' and governed_effect: issues.append('GOVERNANCE_OUTCOME_CONTRADICTION')
    if decision=='DENY' and e and e.get('execution_disposition')=='SUBMITTED': issues.append('DENY_WITH_SUBMITTED_EXECUTION')
    if effect and e and e.get('execution_disposition')=='NOT_SUBMITTED': issues.append('EXECUTION_OUTCOME_CONTRADICTION')
    if any(i in issues for i in ('GOVERNANCE_OUTCOME_CONTRADICTION','DENY_WITH_SUBMITTED_EXECUTION','EXECUTION_OUTCOME_CONTRADICTION')):
        return finish('CONTRADICTION')
    if actor_difference:
        explanation=_explain(g,e,delegation_assertion,history_directory) if e else {'status':'INSUFFICIENT_EVIDENCE','valid_explanatory_bases':[]}
        out['authority_explanation']=explanation
        if explanation['status']=='UNEXPLAINED': difference=True
        elif explanation['status']!='EXPLAINED': unknown=True;issues.append('AUTHORITY_EXPLANATION_INSUFFICIENT')
    if decision=='DENY' and not e and not o:
        if not any(r['role'] in ('execution','outcome') for r in records) and _coverage_captures(coverage,g):
            issues.append('CONSISTENT_WITH_BLOCKING');return finish('CONSISTENT')
        issues.append('OBSERVATION_COVERAGE_INSUFFICIENT');return finish('INSUFFICIENT_EVIDENCE')
    if not e or not o or unknown: return finish('INSUFFICIENT_EVIDENCE')
    if not effect or e.get('execution_disposition')!='SUBMITTED':
        issues.append('TARGET_EFFECT_OR_EXECUTION_NOT_ESTABLISHED');return finish('INSUFFICIENT_EVIDENCE')
    if difference: return finish('UNEXPLAINED_DIVERGENCE')
    return finish('EXPLAINED_DIVERGENCE' if actor_difference else 'CONSISTENT')
