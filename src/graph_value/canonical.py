"""Read-only source adapter. Direct references only; no path closures or labels.

The internal catalog preserves evidence records, embedded record pointers and
explicit reference fields. Baseline and graph get exactly the same catalog.
Original archive bytes are never query input. Inventory-only bytes are hashed
by the unchanged verifier and represented only by opaque artifact digests.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json

from src.evidence_digest import evidence_digest
from src.authority_resolver import load_preserved_revision, revision_bytes
from src.authority_reconstruction import reconstruct_authority
from src.delegation_evidence import load_delegation_revision
from src.delegation_reconstruction import reconstruct_delegation
from src.control_attestation import attest
from src.graph_value.results import stable

RULE = 'investigation-projection/1'


def digest_file(path):
    return 'sha256:' + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ident(context, kind, reference):
    return stable([context, kind, reference])


class Catalog:
    def __init__(self):
        self.records = {}
        self.contexts = {}
        self.verification = []

    def add(self, context, kind, reference, properties, *, origin=None):
        key = ident(context, kind, reference)
        body = {'id': key, 'type': kind, 'context': context, 'reference': reference,
                'properties': deepcopy(properties), 'origin': origin or reference,
                'rule': RULE, 'references': []}
        if key in self.records:
            old = self.records[key]
            if old['properties'] != body['properties']:
                raise ValueError('Conflicting content under a canonical identity')
        else:
            self.records[key] = body
        return key

    def reference(self, owner, field, target, *, category='support', pointer=None):
        # References are direct source fields, not inferred transitive relations.
        item = {'field': field, 'target': target, 'category': category,
                'origin': self.records[owner]['origin'], 'pointer': pointer or '/' + field}
        if item not in self.records[owner]['references']:
            self.records[owner]['references'].append(item)

    def artifact(self, digest, subtype='artifact'):
        # Artifact content identity is shared; record and population views are not.
        return self.add('artifacts', 'EvidenceArtifact', digest, {'digest': digest})

    def authority_pair(self, context, authority, delegations, authority_ref=None, delegation_ref=None):
        ad = authority_ref or {'digest': 'sha256:' + hashlib.sha256(revision_bytes(authority)).hexdigest(),
                               'source_id': authority['source_id'], 'source_version': authority['source_version']}
        dd = delegation_ref or {'digest': evidence_digest(delegations)}
        pair = {'authority': deepcopy(authority), 'delegations': deepcopy(delegations),
                'authority_reference': ad, 'delegation_reference': dd}
        if context in self.contexts and self.contexts[context] != pair:
            raise ValueError('Revision context cannot be replaced')
        self.contexts[context] = pair
        revision = self.add(context, 'Revision', ad['digest'], ad)
        drevision = self.add(context, 'Revision', dd['digest'], dd)
        source = self.add('sources','EvidenceSource',authority['source_id'], {'source_id':authority['source_id']}, origin=ad)
        self.reference(revision,'source',source,category='context')
        if dd.get('source_id'):
            dsource = self.add('sources','EvidenceSource',dd['source_id'], {'source_id':dd['source_id']}, origin=dd)
            self.reference(drevision,'source',dsource,category='context')
        self.reference(drevision, 'authority_revision', revision, category='context')
        self.reference(revision, 'preserved_artifact', self.artifact(ad['digest']), category='verification')
        self.reference(drevision, 'preserved_artifact', self.artifact(dd['digest']), category='verification')
        index = {}
        for kind, records, parent_revision in [('authority', authority['records'], revision), ('delegation', delegations, drevision)]:
            for r in records:
                rd = evidence_digest(r)
                prefix, version = ('authority_record_id', 'authority_version') if kind == 'authority' else ('delegation_id', 'delegation_version')
                key = self.add(context, 'AuthorityRecord' if kind == 'authority' else 'DelegationRecord',
                               rd, r, origin={'revision': self.records[parent_revision]['reference'], 'record_digest': rd})
                self.reference(parent_revision, 'records', key, category='context', pointer='/records/' + rd)
                # A whole preserved revision is needed even for one selected record.
                self.reference(key, 'revision', self.artifact(self.records[parent_revision]['reference']), category='verification')
                if isinstance(r, dict) and prefix in r and version in r:
                    index.setdefault((kind, r[prefix], r[version]), []).append(key)
                if not isinstance(r, dict):
                    continue
                for scope_index, scope in enumerate(r.get('permitted_scopes', r.get('delegated_scopes', [])) if isinstance(r.get('permitted_scopes', r.get('delegated_scopes', [])), list) else []):
                    if not isinstance(scope,dict) or not isinstance(scope.get('resource_ids'),list):
                        continue
                    for resource in scope['resource_ids']:
                        if not all(isinstance(v,str) and v for v in (scope.get('action'),scope.get('resource_type'),resource)):
                            continue
                        values = [scope['action'],scope['resource_type'],resource]
                        tkey = self.add(context,'ActionResource',values,dict(zip(('action','resource_type','resource_id'),values)),
                                         origin={'record':rd,'pointer':'/scopes/'+str(scope_index)})
                        self.reference(key,'scope',tkey,category='context',pointer='/scopes/'+str(scope_index))
                for field in ('principal', 'delegator', 'delegate'):
                    if isinstance(r.get(field), str):
                        principal = self.add(context, 'Principal', ['agent', r[field]], {'namespace': 'agent', 'id': r[field]},
                                             origin={'record':rd,'revision':self.records[parent_revision]['reference'],'pointer':'/'+field})
                        self.reference(key, field, principal, category='context')
        for r in delegations:
            if not isinstance(r, dict) or not isinstance(r.get('parent'), dict):
                continue
            child = ident(context, 'DelegationRecord', evidence_digest(r))
            p = r['parent']
            parents = index.get((p.get('kind'), p.get('record_id'), p.get('version')), [])
            for parent in parents or [ident(context, 'MissingReference', p)]:
                self.reference(child, 'parent', parent, category='context')
        return revision, drevision

    def freeze(self):
        for r in self.records.values():
            r['references'].sort(key=stable)
        return {'records': sorted(self.records.values(), key=lambda r: r['id']),
                'contexts': deepcopy(self.contexts), 'verification': deepcopy(self.verification)}


def add_reconciliation(catalog, assertion, context, *, history=None):
    aid = assertion['assertion_id']
    if evidence_digest({k:v for k,v in assertion.items() if k != 'assertion_id'}) != aid:
        raise ValueError('M6 assertion digest mismatch')
    rkey = catalog.add(context, 'Reconciliation', aid,
        {k: deepcopy(assertion[k]) for k in ('result', 'issue_codes', 'limitations', 'time_assumptions', 'correlation_paths')})
    evidence = {}
    connected = {r['evidence_ref'] for values in assertion['claims'].values() for r in values}
    for r in assertion['source_evidence']:
        allowed = ('role', 'actor', 'action', 'resource_id', 'resource_type', 'observed_at',
                   'authority_resolution_at', 'event_recorded_at', 'governance_decision',
                   'execution_disposition', 'client_success', 'target_outcome', 'defects', 'target_contract_digest')
        key = catalog.add(context, 'EvidenceRecord', r['evidence_ref'],
                          {k: deepcopy(r[k]) for k in allowed if k in r}, origin=r.get('location', r['evidence_ref']))
        evidence[r['evidence_ref']] = key
        catalog.reference(rkey, 'source_evidence', key, category='context')
        if r['evidence_ref'] in connected:
            catalog.reference(rkey, 'claims', key)
        if r['evidence_ref'] == assertion['governance_ref']:
            catalog.reference(rkey, 'governance_ref', key)
        if r.get('location', {}).get('file_digest'):
            catalog.reference(key, 'location', catalog.artifact(r['location']['file_digest']), category='verification')
        if r.get('actor'):
            principal = catalog.add(context, 'Principal', [r['actor']['namespace'], r['actor']['id']], r['actor'],
                                    origin={'evidence_ref':r['evidence_ref'],'pointer':'/actor'})
            catalog.reference(key, 'actor', principal, category='context')
        if all(r.get(k) for k in ('action', 'resource_type', 'resource_id')):
            values = [r[k] for k in ('action', 'resource_type', 'resource_id')]
            tuple_key = catalog.add(context, 'ActionResource', values, dict(zip(('action','resource_type','resource_id'), values)),
                                    origin={'evidence_ref':r['evidence_ref'],'pointer':'/action,/resource_type,/resource_id'})
            catalog.reference(key, 'tuple', tuple_key, category='context')
        if r.get('target_contract_digest'):
            catalog.reference(key, 'support_ref', catalog.artifact(r['target_contract_digest']))
        binding = r.get('raw', {}).get('context', {}).get('authority_binding') if r.get('raw') else None
        if binding:
            bkey = catalog.add(context, 'AuthorityBinding', [r['evidence_ref'], '/context/authority_binding'], binding,
                               origin={'evidence_ref': r['evidence_ref'], 'pointer': '/context/authority_binding'})
            catalog.reference(key, 'authority_binding', bkey)
            revision = binding['revision']
            catalog.records[key]['properties']['authority_revision_digest'] = revision['digest']
            catalog.reference(bkey, 'revision', catalog.artifact(revision['digest']), category='verification')
            if history is not None:
                checked = reconstruct_authority(r['raw'], history)
                catalog.verification.append({'reference':r['evidence_ref'], 'status':checked['status']})
                if checked['status'] not in ('VERIFIED','TEMPORAL_BOUNDARY_AMBIGUITY'):
                    raise ValueError('M4 reconstruction unavailable: ' + checked['status'])
                source = load_preserved_revision(revision, history)
                pair_context = stable([context, revision['digest']])
                akey, _ = catalog.authority_pair(pair_context, source, [], revision)
                catalog.reference(bkey, 'authority_revision', akey, category='context')
    for a in assertion['correlation_assertions']:
        akey = catalog.add(context, 'CorrelationAssertion', a['assertion_id'],
            {k: deepcopy(a[k]) for k in ('relationship_type','correlation_method','result','limitations','time_assumptions','rule','candidate_population','competing_candidates')})
        catalog.reference(rkey, 'correlation_assertions', akey, category='context')
        focus = a['focus']['evidence_ref']
        if focus in evidence:
            catalog.reference(akey, 'focus', evidence[focus], category='context')
        for entry in a['source_evidence']:
            ref = entry['evidence_ref']
            if ref in evidence:
                catalog.reference(akey, 'population', evidence[ref], category='context')
        if a['result']['state'] == 'LINKED':
            for ref in [focus] + [x['evidence_ref'] for x in a['result']['linked_evidence']]:
                catalog.reference(akey, 'linked_endpoint', evidence.get(ref, ident(context,'MissingReference',ref)))
    for field in ('evidence_coverage', 'identity_mapping'):
        if assertion.get(field) is not None:
            d = evidence_digest(assertion[field])
            catalog.add(context, 'EvidenceArtifact', d, assertion[field])
            catalog.reference(rkey, field, catalog.artifact(d))
    if assertion.get('authority_explanation') is not None:
        explanation = assertion['authority_explanation']
        ekey = catalog.add(context, 'DelegationAssessment', [aid, '/authority_explanation'], explanation,
                           origin={'assertion_id':aid, 'pointer':'/authority_explanation'})
        catalog.reference(rkey, 'authority_explanation', ekey)
        if explanation.get('assertion_digest'):
            catalog.reference(ekey, 'assessment_reference', ident(context,'MissingReference',explanation['assertion_digest']),category='verification')
    return rkey, evidence


def load_reference(root):
    """Verify every saved M7 assertion through unchanged M6/M7 adapters."""
    root = Path(root)
    saved = root/'experiments/control_attestation/results/v1'
    wrappers = json.loads((saved/'attestations.json').read_text())
    receipts = json.loads((saved/'verification.json').read_text())
    control = json.loads((saved/'control.json').read_text())
    catalog = Catalog()
    manifest = json.loads((saved/'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        path = (saved/name).resolve()
        path.relative_to(saved.resolve())
        if digest_file(path) != digest:
            raise ValueError('M7 archive inventory mismatch')
    for wrapper, recorded in zip(wrappers, receipts, strict=True):
        request = recorded['request']
        archive_ref = request['archive_reference']
        if archive_ref == 'repository:experiments/target_outcome/results/v1':
            archive = root/'experiments/target_outcome/results/v1'
        elif archive_ref == 'local:deterministic_fixture':
            archive = saved/'deterministic_fixture'
        else:
            raise ValueError('Unsupported archive layout')
        a, receipt = attest(archive, request['assertion_ref'], control, coverage_support=request['coverage_support'])
        if a != wrapper['attestation'] or receipt != recorded['receipt'] or receipt['status'] != 'VERIFIED':
            raise ValueError('M7 replay disagrees or evidence unavailable')
        context = a['reconciliation_reference']
        views = json.loads((archive/'reconciliation.json').read_text())
        source = next(x for x in views.values() if x['assertion_id'] == context)
        rkey, evidence = add_reconciliation(catalog, source, context, history=archive/'authority_history')
        ckey = catalog.add('controls','ControlDefinition', evidence_digest(control), control)
        akey = catalog.add(context, 'Attestation', a['assertion_id'], a)
        vkey = catalog.add(context, 'VerificationReceipt', receipt['receipt_id'],
                          {k:v for k,v in receipt.items() if k != 'facts'})
        catalog.reference(akey, 'control_reference', ckey)
        catalog.reference(akey, 'reconciliation_reference', rkey)
        catalog.reference(akey, 'verification_reference', vkey, category='verification')
        for d in receipt['dependency_refs']:
            catalog.reference(vkey, 'dependency_refs', catalog.artifact(d), category='verification')
        for ref in a['source_evidence_refs']:
            catalog.reference(akey, 'source_evidence_refs', evidence[ref], category='context')
        for ref in a['correlation_assertion_refs']:
            catalog.reference(akey, 'correlation_assertion_refs', ident(context,'CorrelationAssertion',ref))
        for field in ('support_ref','coverage_ref'):
            if a['coverage_assessment'].get(field):
                catalog.reference(akey, field, catalog.artifact(a['coverage_assessment'][field]))
        catalog.verification.append({'reference':a['assertion_id'], 'status':'VERIFIED'})
    return catalog.freeze()


def load_pair(authority_ref, delegation_ref, history, *, assessment=None, governance_event=None):
    authority = load_preserved_revision(authority_ref, history)
    delegation = load_delegation_revision(delegation_ref, history)
    if delegation['authority_revision'] != authority_ref:
        raise ValueError('Mismatched preserved revision pair')
    catalog = Catalog()
    context = stable([authority_ref['digest'], delegation_ref['digest']])
    akey, dkey = catalog.authority_pair(context, authority, delegation['records'], authority_ref, delegation_ref)
    if assessment:
        checked = reconstruct_delegation(assessment, history, governance_event=governance_event)
        if checked['status'] not in ('VERIFIED','TEMPORAL_BOUNDARY_AMBIGUITY'):
            raise ValueError('M5 replay failed: ' + checked['status'])
        key = catalog.add(context,'DelegationAssessment',evidence_digest(assessment),assessment)
        catalog.reference(key,'authority_revision',akey,category='context')
        catalog.reference(key,'delegation_revision',dkey,category='context')
    return catalog.freeze()
