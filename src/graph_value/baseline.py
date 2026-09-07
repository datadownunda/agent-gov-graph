"""Fair indexed JSON/direct-reference baseline. No graph projector imports."""
from collections import defaultdict
from src.graph_value.results import result, stable, ref_key, authority_delta, record_details
from src.graph_value.semantics import AuthoritySemantics


class Baseline:
    def __init__(self, bundle):
        self.records = {r['id']: r for r in bundle['records']}
        if len(self.records) != len(bundle['records']):
            raise ValueError('Duplicate canonical identities')
        self.reverse = defaultdict(list)
        self.children = defaultdict(list)
        self.relationships = defaultdict(list)
        self.principals = defaultdict(list)
        self.semantics = AuthoritySemantics(bundle['contexts'])
        for r in self.records.values():
            for ref in r['references']:
                self.reverse[ref['target']].append((r['id'], ref))
                if ref['field'] == 'parent':
                    self.children[ref['target']].append(r['id'])
            p = r['properties']
            if r['type'] in ('AuthorityRecord', 'DelegationRecord') and isinstance(p, dict):
                kind = 'authority' if r['type'] == 'AuthorityRecord' else 'delegation'
                id_field, version = ('authority_record_id','authority_version') if kind == 'authority' else ('delegation_id','delegation_version')
                if id_field in p and version in p:
                    self.relationships[(r['context'], kind, p[id_field], p[version])].append(r['id'])
            if r['type'] == 'EvidenceRecord' and p.get('actor'):
                self.principals[(r['context'], p['actor']['namespace'], p['actor']['id'])].append(r['id'])
                if p.get('authority_revision_digest'):
                    self.principals[(p['authority_revision_digest'],p['actor']['namespace'],p['actor']['id'])].append(r['id'])
        for values in self.reverse.values():
            values.sort(key=stable)

    def dependencies(self, start, *, reverse=False, depth=None, limit=10000):
        if start not in self.records:
            return result('DEPENDENCIES', complete=False, unresolved=[start])
        todo = [(start, [start], [], [], [])]
        nodes, paths, cycles, missing = {start}, [], [], set()
        complete = True
        while todo:
            node, path, fields, categories, provenance = todo.pop()
            if depth is not None and len(fields) >= depth:
                continue
            refs = self.reverse.get(node, []) if reverse else [(r['target'],r) for r in self.records[node]['references']]
            for other, ref in refs:
                witness = {'records': path + [other], 'fields':fields + [ref['field']],
                           'categories':categories + [ref['category']], 'origins': [],
                           'edge_provenance':provenance + [{'origin':ref['origin'],'pointer':ref['pointer']}]}
                # Every hop includes its originating record/reference pointer.
                witness['origins'] = [self.records[x]['origin'] for x in witness['records'] if x in self.records]
                if other in path:
                    cycles.append(witness)
                    continue
                if other not in self.records:
                    missing.add(other)
                    continue
                nodes.add(other)
                paths.append(witness)
                if len(paths) >= limit:
                    complete = False
                    todo.clear()
                    break
                todo.append((other, witness['records'], witness['fields'], witness['categories'], witness['edge_provenance']))
        return result('DEPENDENCIES', nodes, paths, cycles=sorted(cycles,key=stable),
                      unresolved=sorted(missing), complete=complete and not missing)

    def q1(self, attestation, **options):
        record = self.records[attestation]
        if record['type'] != 'Attestation' or record['properties']['finding'] != 'CONTROL_EFFECTIVENESS_EXCEPTION':
            raise ValueError('Q1 requires an M7 exception')
        out = self.dependencies(attestation, **options)
        out['query'] = 'Q1'
        out['details'] = record_details(self.records,out['records'])
        out['interpretation'] = 'Recorded witnesses and derived investigation paths; no new finding.'
        return out

    def q4(self, evidence, **options):
        out = self.dependencies(evidence, reverse=True, **options)
        out['query'] = 'Q4'
        conclusions = {k for k in out['records'] if self.records[k]['type'] in ('Reconciliation','Attestation')}
        out['conclusions'] = sorted(conclusions)
        out['paths'] = [p for p in out['paths'] if p['records'][-1] in conclusions]
        out['interpretation'] = 'Dependency requires review/reverification, not a changed finding.'
        return out

    def q2(self, context, selected, at, requested=None):
        self.semantics.resolve_ref(context, selected)
        starts = self.relationships.get((context, *ref_key(selected)), [])
        if not starts:
            return result('Q2', complete=False, unresolved=[selected], affected=[])
        todo, seen, actors = list(starts), set(), set()
        while todo:
            key = todo.pop()
            if key in seen:
                continue
            seen.add(key)
            p = self.records[key]['properties']
            actor = p.get('principal', p.get('delegate'))
            if isinstance(actor, str) and actor:
                actors.add(actor)
            todo.extend(self.children.get(key, []))
        affected, authority_paths = [], []
        for actor in sorted(actors):
            for requested_tuple in self.semantics.requested_tuples(context, requested):
                assessment = self.semantics.assess(context, actor, requested_tuple, at)
                for candidate in assessment['candidates']:
                    authority_paths.append({'context':context,'actor':actor,'tuple':list(requested_tuple),
                        'chain':candidate['chain'],'status':candidate['status'],
                        'permission_result':candidate['permission_result']})
                    for reference in candidate['chain']:
                        seen.update(self.relationships.get((context,*ref_key(reference)),[]))

                delta = authority_delta(assessment, ref_key(selected))
                connected = []
                revision = self.semantics.contexts[context]['authority_reference']['digest']
                for key in sorted(set(self.principals.get((context, 'agent', actor), []) + self.principals.get((revision, 'agent', actor), []))):
                    p = self.records[key]['properties']
                    if tuple(p.get(k) for k in ('action','resource_type','resource_id')) == requested_tuple:
                        related = self.q4(key)
                        connected.append({'evidence':key, 'conclusions':related['conclusions'],
                                          'decision':p.get('governance_decision'), 'observed_at':p.get('observed_at'),
                                          'authority_resolution_at':p.get('authority_resolution_at'),
                                          'connection':'contextual; not a new historical support assertion'})
                affected.append({'actor':actor, 'tuple':list(requested_tuple), 'at':at,
                                 **delta, 'connected':connected})
        return result('Q2', seen, authority_paths, affected=affected, context=context, selected=selected)

    def q3(self, context, selected, at, requested=None):
        out = self.q2(context, selected, at, requested)
        out['query'] = 'Q3'
        legitimate = []
        for row in out['affected']:
            for action in row['connected']:
                if action['decision'] == 'ALLOW' and action['observed_at']:
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
                    node = self.records[conclusion]
                    if node['type']=='Attestation' and node['properties'].get('finding')=='CONTROL_EFFECTIVENESS_EXCEPTION':
                        out['exception_associated_paths_lost'].append({'attestation':conclusion,
                            'actor':row['actor'],'tuple':row['tuple'],'lost_authority_bases':row['lost']})
        out['affected_assurance_conclusions'] = sorted(set(out['affected_assurance_conclusions']))
        out['historical_findings_unchanged'] = True
        out['prevention_inferred'] = False
        return out
