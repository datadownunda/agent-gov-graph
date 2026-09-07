"""Graph queries. All graph engine/projector complexity is charged to this arm."""
from src.graph_value.projection import Projection
from src.graph_value.traversal import walk
from src.graph_value.semantics import AuthoritySemantics
from src.graph_value.results import result, ref_key, authority_delta, record_details


class GraphQueries:
    def __init__(self, bundle):
        self.graph = Projection(bundle)
        self.semantics = AuthoritySemantics(bundle['contexts'])
        self.actor_evidence = {}
        for key in self.graph.by_type['EvidenceRecord']:
            node = self.graph.nodes[key]
            p = node['properties']
            if p.get('actor'):
                self.actor_evidence.setdefault((node['context'],p['actor']['namespace'],p['actor']['id']),[]).append(key)
                if p.get('authority_revision_digest'):
                    self.actor_evidence.setdefault((p['authority_revision_digest'],p['actor']['namespace'],p['actor']['id']),[]).append(key)

    def dependencies(self, start, **options):
        return walk(self.graph,start,**options)

    def q1(self, attestation, **options):
        r = self.graph.nodes[attestation]
        if r['type'] != 'Attestation' or r['properties']['finding'] != 'CONTROL_EFFECTIVENESS_EXCEPTION':
            raise ValueError('Q1 requires an M7 exception')
        out = walk(self.graph,attestation,**options)
        out['query'] = 'Q1'
        out['details'] = record_details(self.graph.nodes,out['records'])
        out['interpretation'] = 'Recorded witnesses and derived investigation paths; no new finding.'
        return out

    def q4(self, evidence, **options):
        out = walk(self.graph,evidence,reverse=True,**options)
        out['query'] = 'Q4'
        conclusions = {k for k in out['records'] if self.graph.nodes[k]['type'] in ('Reconciliation','Attestation')}
        out['conclusions'] = sorted(conclusions)
        out['paths'] = [p for p in out['paths'] if p['records'][-1] in conclusions]
        out['interpretation'] = 'Dependency requires review/reverification, not a changed finding.'
        return out

    def q2(self, context, selected, at, requested=None):
        self.semantics.resolve_ref(context,selected)
        field, version = ('authority_record_id','authority_version') if selected['kind']=='authority' else ('delegation_id','delegation_version')
        starts = [k for k in self.graph.by_property.get((context,field,selected['record_id']),[])
                  if self.graph.nodes[k]['properties'].get(version)==selected['version']]
        if not starts:
            return result('Q2',complete=False,unresolved=[selected],affected=[])
        seen, actors = set(), set()
        complete = True
        for start in starts:
            descendants = walk(self.graph,start,reverse=True,relations={'PARENT_REFERENCE'})
            complete = complete and descendants['complete']
            seen.update(descendants['records'])
        for key in seen:
            p = self.graph.nodes[key]['properties']
            actor = p.get('principal',p.get('delegate'))
            if isinstance(actor,str) and actor:
                actors.add(actor)
        affected, authority_paths = [], []
        for actor in sorted(actors):
            for requested_tuple in self.semantics.requested_tuples(context,requested):
                assessment = self.semantics.assess(context,actor,requested_tuple,at)
                for candidate in assessment['candidates']:
                    authority_paths.append({'context':context,'actor':actor,'tuple':list(requested_tuple),
                        'chain':candidate['chain'],'status':candidate['status'],
                        'permission_result':candidate['permission_result']})
                    for reference in candidate['chain']:
                        rf,rv = ('authority_record_id','authority_version') if reference['kind']=='authority' else ('delegation_id','delegation_version')
                        seen.update(k for k in self.graph.by_property.get((context,rf,reference['record_id']),[])
                                    if self.graph.nodes[k]['properties'].get(rv)==reference['version'])

                connected = []
                revision = self.semantics.contexts[context]['authority_reference']['digest']
                for key in sorted(set(self.actor_evidence.get((context,'agent',actor),[]) + self.actor_evidence.get((revision,'agent',actor),[]))):
                    p = self.graph.nodes[key]['properties']
                    if tuple(p.get(k) for k in ('action','resource_type','resource_id')) == requested_tuple:
                        related = self.q4(key)
                        connected.append({'evidence':key,'conclusions':related['conclusions'],
                                          'decision':p.get('governance_decision'),'observed_at':p.get('observed_at'),
                                          'authority_resolution_at':p.get('authority_resolution_at'),
                                          'connection':'contextual; not a new historical support assertion'})
                affected.append({'actor':actor,'tuple':list(requested_tuple),'at':at,
                                 **authority_delta(assessment,ref_key(selected)),'connected':connected})
        return result('Q2',seen,authority_paths,affected=affected,context=context,selected=selected,complete=complete)

    def q3(self, context, selected, at, requested=None):
        out = self.q2(context,selected,at,requested)
        out['query'] = 'Q3'
        legitimate = []
        for row in out['affected']:
            for action in row['connected']:
                if action['decision']=='ALLOW' and action['observed_at']:
                    assessment = self.semantics.assess(context,row['actor'],row['tuple'],action['observed_at'])
                    change = authority_delta(assessment,ref_key(selected))
                    earlier = self.semantics.assess(context,row['actor'],row['tuple'], action.get('authority_resolution_at') or action['observed_at'])
                    boundary_stable = all(earlier[k] == assessment[k] for k in ('status','permission_result','valid_bases'))
                    if change['loses_all_demonstrated_support'] and boundary_stable:
                        legitimate.append(action['evidence'])
        out['otherwise_legitimate_actions_losing_support'] = sorted(set(legitimate))
        out['exception_associated_paths_lost'] = []
        out['affected_assurance_conclusions'] = []
        out['affected_agents_resources'] = []
        for row in out['affected']:
            if not row['lost']:
                continue
            out['affected_agents_resources'].append({'actor':row['actor'],'tuple':row['tuple'],
                'loses_all_demonstrated_support':row['loses_all_demonstrated_support']})
            for action in row['connected']:
                for conclusion in action['conclusions']:
                    out['affected_assurance_conclusions'].append(conclusion)
                    node = self.graph.nodes[conclusion]
                    if node['type']=='Attestation' and node['properties'].get('finding')=='CONTROL_EFFECTIVENESS_EXCEPTION':
                        out['exception_associated_paths_lost'].append({'attestation':conclusion,
                            'actor':row['actor'],'tuple':row['tuple'],'lost_authority_bases':row['lost']})
        out['affected_assurance_conclusions'] = sorted(set(out['affected_assurance_conclusions']))
        out['historical_findings_unchanged'] = True
        out['prevention_inferred'] = False
        return out
