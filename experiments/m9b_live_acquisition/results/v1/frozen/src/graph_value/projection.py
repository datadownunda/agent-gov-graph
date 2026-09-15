"""Derived directed multigraph. No authority conclusion or path precomputation."""
from collections import defaultdict
from src.graph_value.results import stable

RELATIONS = {
    'source':'FROM_SOURCE', 'scope':'DECLARES_SCOPE', 'control_reference':'EVALUATES_CONTROL', 'reconciliation_reference':'ATTESTS_RECONCILIATION',
    'verification_reference':'VERIFIED_USING', 'governance_ref':'FOCUSES_ON', 'focus':'FOCUSES_ON',
    'correlation_assertions':'USES_CORRELATION', 'correlation_assertion_refs':'USES_CORRELATION',
    'source_evidence':'IN_POPULATION', 'source_evidence_refs':'IN_POPULATION', 'population':'IN_POPULATION',
    'linked_endpoint':'LINKED_ENDPOINT', 'parent':'PARENT_REFERENCE', 'records':'CONTAINS_RECORD',
    'principal':'HAS_PRINCIPAL', 'delegator':'HAS_DELEGATOR', 'delegate':'HAS_DELEGATE',
    'authority_binding':'HAS_AUTHORITY_BINDING', 'authority_revision':'BOUND_TO_REVISION',
    'delegation_revision':'BOUND_TO_REVISION', 'tuple':'DESCRIBES_TUPLE', 'actor':'HAS_PRINCIPAL',
    'location':'LOCATED_IN', 'revision':'DEPENDS_ON', 'preserved_artifact':'DEPENDS_ON',
    'authority_explanation':'DEPENDS_ON', 'assessment_reference':'DEPENDS_ON', 'claims':'DEPENDS_ON', 'dependency_refs':'DEPENDS_ON', 'support_ref':'DEPENDS_ON',
    'coverage_ref':'DEPENDS_ON', 'evidence_coverage':'DEPENDS_ON', 'identity_mapping':'DEPENDS_ON',
}


class Projection:
    def __init__(self, bundle):
        self.nodes = {r['id']:r for r in bundle['records']}
        if len(self.nodes) != len(bundle['records']):
            raise ValueError('Duplicate projected identities')
        self.edges = []
        self.outgoing, self.incoming = defaultdict(list), defaultdict(list)
        self.by_type = defaultdict(list)
        self.by_property = defaultdict(list)
        for node in self.nodes.values():
            self.by_type[node['type']].append(node['id'])
            p = node['properties']
            if isinstance(p, dict):
                for field in ('authority_record_id','authority_version','delegation_id','delegation_version','principal','delegate'):
                    if isinstance(p.get(field),str):
                        self.by_property[(node['context'],field,p[field])].append(node['id'])
            for ref in node['references']:
                if ref['field'] not in RELATIONS or ref['category'] not in ('support','context','verification'):
                    raise ValueError('Unspecified projection relation')
                edge = {'source':node['id'], 'target':ref['target'], 'relation':RELATIONS[ref['field']], **ref}
                self.edges.append(edge)
                self.outgoing[node['id']].append(edge)
                self.incoming[ref['target']].append(edge)
        self.edges.sort(key=stable)
        for index in (self.outgoing,self.incoming):
            for edges in index.values():
                edges.sort(key=stable)

    def serialize(self):
        return stable({'nodes':list(self.nodes.values()),'edges':self.edges,
                       'outgoing':dict(self.outgoing),'incoming':dict(self.incoming),
                       'by_type':dict(self.by_type),
                       'by_property':[[list(k),v] for k,v in self.by_property.items()]})
