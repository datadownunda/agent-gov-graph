"""Deterministic semantic source fixtures. No expected results in query inputs.

Scale source consists of preserved M5 revision pairs and independent M6 source
populations; M7 coverage is provided by the unchanged reference archive. Scale
M6 assertions are generated/replayed with existing M6, never invented findings.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import random
import time

from src.authority_resolver import revision_bytes
from src.correlation_assertion import native_assertions
from src.action_reconciliation import reconcile
from src.evidence_digest import evidence_digest
from src.graph_value.canonical import Catalog, add_reconciliation, load_reference
from src.graph_value.results import stable

AT = '2026-09-05T12:00:00Z'
START, END = '2026-09-05T00:00:00Z', '2026-09-06T00:00:00Z'


def scope():
    return [{'action':'read','resource_type':'employee_complaint','resource_ids':['complaint-456']}]


def root_record(name):
    return {'authority_record_id':name+'-authority','authority_version':'1','principal':name,
            'roles':['hr_investigator'],'permitted_scopes':scope(),'valid_from':START,'valid_to':END,
            'delegation_permitted':True}


def delegation(name, delegator, delegate, parent_kind, parent_id, **changes):
    return {'delegation_id':name,'delegation_version':'1','delegator':delegator,'delegate':delegate,
            'parent':{'kind':parent_kind,'record_id':parent_id,'version':'1'},'delegated_scopes':scope(),
            'valid_from':START,'valid_to':END,'onward_delegation':True, **changes}


def component(index, count=48, seed=8):
    prefix = f's{seed}-c{index}'
    a, b = prefix+'-root', prefix+'-alternative'
    authority = {'schema_version':'2.0','source_id':prefix,'source_version':'1',
                 'records':[root_record(a),root_record(b)]}
    links = [delegation(prefix+'-entry',a,prefix+'-middle','authority',a+'-authority'),
             delegation(prefix+'-alternate',b,prefix+'-middle','authority',b+'-authority')]
    for i in range(count):
        # A forest with a shared ancestor, separate alternative grants, and
        # variable-depth branches. Each record has exactly one exact parent.
        parent = links[0] if i%6 == 0 else links[-1]
        links.append(delegation(prefix+f'-d{i}',parent['delegate'],prefix+f'-agent{i}',
                                'delegation',parent['delegation_id']))
        if i%12 == 0:
            links.append(delegation(prefix+f'-alt{i}',prefix+'-middle',prefix+f'-agent{i}',
                                    'delegation',prefix+'-alternate'))
    return authority, links


def action_source(actor, source_id):
    records = []
    for role in ('governance','execution','outcome'):
        raw = {'producer_record':source_id+'-'+role,'actor':actor,'action':'read','resource':'complaint-456'}
        raw_bytes = (stable(raw)+'\n').encode()
        fd = 'sha256:'+hashlib.sha256(raw_bytes).hexdigest()
        location = {'member':role+'.jsonl','file_digest':fd,'line':1,'byte_offset':0,
                    'byte_length':len(raw_bytes),'line_digest':fd}
        record = {'schema_version':'1.0','role':role,'location':location,'raw':raw,
                  'ingested_at':AT,'observed_at':AT,'defects':[],
                  'evidence_ref':evidence_digest({'role':role,'location':location}),
                  'actor':{'namespace':'agent','id':actor},'action':'read',
                  'resource_type':'employee_complaint','resource_id':'complaint-456',
                  'action_attempt_id':source_id+'-attempt','request_id':source_id+'-request'}
        if role=='governance': record['governance_decision']='ALLOW'
        if role=='execution': record.update(execution_disposition='SUBMITTED',client_success=True)
        if role=='outcome': record['target_outcome']='REPRESENTATION_SERVED'
        records.append(record)
    return records


def correlations(records):
    result = []
    for left,right,field in [('governance','execution','action_attempt_id'),('execution','outcome','request_id')]:
        result.append({'roles':{'left':left,'right':right},'assertions':native_assertions(
            [r for r in records if r['role']==left],[r for r in records if r['role']==right],
            identifier_field=field,namespace='declared-synthetic-source',issuer='deterministic fixture',
            relationship_type='SAME_ACTION')})
    return result


def make_source(components, seed=8, depth=48):
    return {'version':'gate-a-source/1', 'components':[
        {'authority':a,'delegations':d,'action_records':action_source(d[-1]['delegate'],a['source_id'])}
        for a,d in (component(i,depth,seed) for i in range(components))]}


def prepare(source, *, reference=None):
    catalog = Catalog()
    # The shared artifact is the existing scope/interpretation contract of these
    # synthetic observations. Every record explicitly carries this reference.
    contract = {'target_id':'deterministic-complaint-target','effect':'REPRESENTATION_SERVED',
                'boundary':'synthetic target observation; no live process or client-consumption claim'}
    contract_digest = evidence_digest(contract)
    artifact = catalog.artifact(contract_digest)
    for c in source['components']:
        authority, delegation_records = c['authority'],c['delegations']
        # The revision context itself is content-addressed; source order irrelevant.
        context = stable([authority['source_id'],evidence_digest(authority),evidence_digest(delegation_records)])
        _, dkey = catalog.authority_pair(context,authority,delegation_records)
        records = deepcopy(c['action_records'])
        for r in records:
            # Check original synthetic record locations, not merely an asserted hash.
            raw_bytes = (stable(r['raw'])+'\n').encode()
            expected = 'sha256:'+hashlib.sha256(raw_bytes).hexdigest()
            if expected != r['location']['file_digest'] or expected != r['location']['line_digest']:
                raise ValueError('Synthetic source bytes mismatch')
            if r['evidence_ref'] != evidence_digest({'role':r['role'],'location':r['location']}):
                raise ValueError('Synthetic evidence reference mismatch')
            if r['role']=='outcome': r['target_contract_digest']=contract_digest
        corr = correlations(records)
        assertion = reconcile(records,corr,governance_ref=records[0]['evidence_ref'])
        rkey, evidence = add_reconciliation(catalog,assertion,context)
        catalog.reference(evidence[records[-1]['evidence_ref']],'support_ref',artifact)
        # The pair supplies a separate contextual authority inquiry. Do not add
        # it as M6 authority_explanation or mutate the M6 assertion.
        catalog.verification.append({'reference':assertion['assertion_id'],'status':'REPLAYED_SYNTHETIC_M6'})
    bundle = catalog.freeze()
    if reference:
        bundle['records'] += reference['records']
        bundle['contexts'].update(reference['contexts'])
        bundle['verification'] += reference['verification']
    return bundle


def workload(bundle):
    exception = next(r['id'] for r in bundle['records'] if r['type']=='Attestation' and
                     r['properties']['finding']=='CONTROL_EFFECTIVENESS_EXCEPTION')
    context = next(k for k,v in bundle['contexts'].items() if v['delegations'])
    d = bundle['contexts'][context]['delegations'][0]
    selected = {'kind':'delegation','record_id':d['delegation_id'],'version':d['delegation_version']}
    # Select a bounded subtree for cold offline investigation; root-wide fanout
    # is a separate stress workload, not silently substituted for this query.
    if len(bundle['contexts'][context]['delegations']) > 12:
        d = bundle['contexts'][context]['delegations'][-4]
        selected = {'kind':'delegation','record_id':d['delegation_id'],'version':d['delegation_version']}
    shared = next(r['id'] for r in bundle['records'] if r['type']=='EvidenceArtifact' and
                  r['reference']==evidence_digest({'target_id':'deterministic-complaint-target',
                    'effect':'REPRESENTATION_SERVED','boundary':'synthetic target observation; no live process or client-consumption claim'}))
    return {'Q1':{'attestation':exception},'Q2':{'context':context,'selected':selected,'at':AT},
            'Q3':{'context':context,'selected':selected,'at':AT},'Q4':{'evidence':shared}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--components',type=int,default=1)
    parser.add_argument('--seed',type=int,default=8)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(stable(make_source(args.components,args.seed))+'\n')


if __name__=='__main__': main()
