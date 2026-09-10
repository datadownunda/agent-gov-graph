"""Controlled M6 experiment and read-only audit. No live model calls."""
import argparse
import hashlib
import json
import secrets
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

from experiments.target_outcome.http_client import request
from src.action_evidence import ingest_governance, ingest_execution, now, verify_location
from src.action_reconciliation import reconcile
from src.authority_reconstruction import reconstruct_authority
from src.complaint_runtime import _governed_action
from src.correlation_assertion import native_assertions
from src.evidence_digest import evidence_digest
from src.evidence_errors import EvidenceValidationError
from src.target_outcome_evidence import ingest_nginx

ROOT=Path(__file__).resolve().parents[2]
IMAGE='nginx@sha256:dc5069ad14f19660b141b21236140b91656bf89bbc3e2417c70ae650cd66104c'
TARGET={'target_id':'complaints-static-v1','identity_namespace':'nginx-basic:complaints-static-v1',
        'basic_auth_required':True,'resources':{f'/complaints/{r}.json':{'id':r,'type':'employee_complaint'}
            for r in ('complaint-456','complaint-789')}}
MAPPING={'version':'1','basis':'Cooperative experiment operator maps one synthetic Basic-auth account to one runtime agent.',
         'entries':[{'source':{'namespace':TARGET['identity_namespace'],'id':'complaint-client'},
                     'target':{'namespace':'agent','id':'complaint-review-agent'}}]}


def write(path,obj):
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def docker(*args,**kw):
    return subprocess.run(['docker',*args],text=True,capture_output=True,check=True,**kw).stdout.strip()


def correlate(records):
    bundles=[]
    for a,b,field,issuer,namespace in [('governance','execution','action_attempt_id','Agent Gov Graph runtime','runtime action attempts'),
                                      ('execution','outcome','request_id','NGINX','complaints-static-v1 request IDs')]:
        bundles.append({'roles':{'left':a,'right':b},'assertions':native_assertions(
            [r for r in records if r['role']==a],[r for r in records if r['role']==b],
            identifier_field=field,namespace=namespace,issuer=issuer,relationship_type='SAME_ACTION')})
    return bundles


def derive(directory):
    target=json.loads((directory/'target.json').read_text())
    mapping=json.loads((directory/'identity_mapping.json').read_text())
    g=ingest_governance(directory/'governance.jsonl',root=directory)
    e=ingest_execution(directory/'execution.jsonl',root=directory)
    o=ingest_nginx(directory/'native/access.jsonl',root=directory,target=target)
    records=g+e+o; correlations=correlate(records)
    views={}
    for name in ('allow','critical-deny','blocked-deny'):
        event=next(r for r in g if r['raw']['context']['run_id']==name)
        # Full captured population remains in all assertions; run_id selects only
        # the governance focus for reporting, never candidate linkage.
        views[name]=reconcile(records,correlations,governance_ref=event['evidence_ref'],identity_mapping=mapping)
    critical=next(r for r in g if r['raw']['context']['run_id']=='critical-deny')
    withheld=g+o
    views['execution-withheld']=reconcile(withheld,correlate(withheld),governance_ref=critical['evidence_ref'],identity_mapping=mapping)
    # Separately declared idle interval: negative conclusion has only local scope.
    coverage=json.loads((directory/'blocked_coverage.json').read_text())
    blocked=next(r for r in g if r['raw']['context']['run_id']=='blocked-deny')
    from src.authority_resolver import instant
    interval=[r for r in records if r['role']!='governance' and r.get('observed_at') and
              instant(coverage['interval_start'])<=instant(r['observed_at'])<=instant(coverage['interval_end'])]
    bounded=[blocked]+interval
    views['blocked-bounded']=reconcile(bounded,correlate(bounded),governance_ref=blocked['evidence_ref'],
                                       coverage=coverage,identity_mapping=mapping)
    return records,correlations,views


def audit(directory):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text())
    for member,digest in manifest['files'].items():
        p=(directory/member).resolve();p.relative_to(directory.resolve())
        if 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()!=digest: raise EvidenceValidationError('Changed evidence: '+member)
    records,correlations,views=derive(directory)
    if not all(verify_location(r,directory) for r in records): raise EvidenceValidationError('Source location integrity failed')
    if json.loads((directory/'correlations.json').read_text())!=correlations: raise EvidenceValidationError('Correlation replay differs')
    if json.loads((directory/'reconciliation.json').read_text())!=views: raise EvidenceValidationError('Reconciliation replay differs')
    authority=[reconstruct_authority(r['raw'],directory/'authority_history') for r in records if r['role']=='governance']
    if any(a['status']!='VERIFIED' for a in authority): raise EvidenceValidationError('M4 reconstruction failed')
    for r in records:
        validate('action_evidence',r)
    for v in views.values(): validate('reconciliation_assertion',v)
    validate('observation_coverage',json.loads((directory/'blocked_coverage.json').read_text()))
    return {'status':'VERIFIED','raw_records':len(records),'authority_reconstructions':len(authority),
            'results':{name:v['result'] for name,v in views.items()},
            'limitations':'Manifest and digests verify preserved content, not external provenance authenticity.'}


def validate(name,value):
    import jsonschema
    jsonschema.validate(value,json.loads((ROOT/'schemas'/f'{name}.schema.json').read_text()),format_checker=jsonschema.FormatChecker())


def run(directory):
    directory=Path(directory).resolve()
    directory.mkdir(parents=True,exist_ok=False)
    (directory/'native').mkdir()
    write(directory/'target.json',TARGET);write(directory/'identity_mapping.json',MAPPING)
    shutil.copyfile(ROOT/'experiments/target_outcome/nginx.conf',directory/'nginx.conf')
    (directory/'execution.jsonl').touch()
    started=now()
    with tempfile.TemporaryDirectory(prefix='agg-m6-') as scratch:
        scratch=Path(scratch);password=secrets.token_urlsafe(24)
        hashed=subprocess.run(['openssl','passwd','-apr1','-stdin'],input=password+'\n',text=True,capture_output=True,check=True).stdout.strip()
        (scratch/'auth').write_text('complaint-client:'+hashed+'\n');(scratch/'auth').chmod(0o644)
        name='agg-m6-'+secrets.token_hex(6)
        launched=False
        try:
            docker('run','-d','--name',name,'-p','127.0.0.1::8080',
                '-v',f'{directory}/nginx.conf:/etc/nginx/nginx.conf:ro',
                '-v',f'{directory}/native:/evidence',
                '-v',f'{ROOT}/runtime_resources:/target:ro',
                '-v',f'{scratch}/auth:/run/target-auth:ro',IMAGE)
            launched=True
            port=int(docker('port',name,'8080/tcp').split(':')[-1])
            for _ in range(50):
                try:
                    with socket.create_connection(('127.0.0.1',port),timeout=.2):pass
                    break
                except OSError:time.sleep(.1)
            image_details=json.loads(docker('image','inspect',IMAGE))[0]
            write(directory/'target_runtime.json',{'image':IMAGE,'image_id':image_details['Id'],
                 'repo_digests':image_details['RepoDigests'],'nginx_version':subprocess.run(
                  ['docker','exec',name,'nginx','-v'],text=True,capture_output=True,check=True).stderr.strip(),
                 'custody':'NGINX writes native/access.jsonl directly through a bind mount. Ingestion occurs after graceful stop.',
                 'auth':'Ephemeral synthetic Basic-auth password/hash excluded from artifacts.',
                 'config_digest': 'sha256:'+hashlib.sha256((directory/'nginx.conf').read_bytes()).hexdigest(),
                 'static_resources':{p.name:'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (ROOT/'runtime_resources/complaints').glob('*.json')}})
            for scenario,resource,bypass,failure in [('allow','complaint-456',False,False),
                       ('critical-deny','complaint-789',True,True),('blocked-deny','complaint-789',False,False)]:
                # Ensure interval separation is explicit for the negative view.
                time.sleep(.05)
                interval_start=now()
                def executor(resource_id,**kw):
                    return request('127.0.0.1',port,resource_id=resource_id,actor_id=kw['actor_id'],
                        action_attempt_id=kw['action_attempt_id'],log_path=kw['log_path'],
                        username='complaint-client',password=password,fail_finalization=failure)
                def emit(event_type,data):
                    with (directory/'runtime.jsonl').open('a') as stream:
                        stream.write(json.dumps({'recorded_at':now(),'event_type':event_type,'data':data})+'\n')
                try:
                    _governed_action(resource,run_id=scenario,step_id='read',actor_id='complaint-review-agent',
                        bypass_enforcement=bypass,governance_log_path=directory/'governance.jsonl',
                        execution_log_path=directory/'execution.jsonl',opa_decision_log_path=directory/'opa.jsonl',
                        emit=emit,executor=executor)
                except RuntimeError:
                    if not failure:raise
                if scenario=='blocked-deny':
                    write(directory/'blocked_coverage.json',{'schema_version':'1.0','interval_start':interval_start,'interval_end':now(),
                        'roles':{'execution':'CAPTURED','outcome':'CAPTURED'},
                        'scope':{'actor':{'namespace':'agent','id':'complaint-review-agent'},'action':'read',
                                 'resource_id':resource,'resource_type':'employee_complaint'},
                        'basis':'Sequential controlled idle interval, client journal active, NGINX logging active; native log flushed on graceful stop. Operator declaration, not enterprise completeness proof.'})
            docker('stop',name)
            docker('rm',name);launched=False
        finally:
            if launched:subprocess.run(['docker','rm','-f',name],capture_output=True)
    records,correlations,views=derive(directory)
    write(directory/'correlations.json',correlations);write(directory/'reconciliation.json',views)
    # Ground truth is separate and never read by derive/reconcile.
    write(directory/'ground_truth.json',{'scenario_design':{
        'allow':'OPA ALLOW; HTTP read; client success recorded.',
        'critical-deny':'OPA DENY; existing explicit test bypass submits HTTP GET; client receives body and server request ID then injected finalization failure leaves success null.',
        'blocked-deny':'Normal runtime DENY gate; no HTTP executor call.',
        'execution-withheld':'All execution claims intentionally omitted from analysis only. No original evidence deleted.'},
        'synthetic_assumptions':['Resources, credentials, identity mapping, proposals, bypass and failure injection are operator-controlled.',
                                'NGINX and OPA are real processes; target native records are not authored by the client or AGG.']})
    write(directory/'manifest.json',{'schema_version':'1.0','started_at':started,'completed_at':now(),
        'files':{p.relative_to(directory).as_posix():'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(directory.rglob('*')) if p.is_file()},
        'integrity_limit':'Self-authored inventory; content integrity is not authenticated provenance.'})
    return audit(directory)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['run','audit']);parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.directory) if args.command=='run' else audit(args.directory),indent=2))


if __name__=='__main__':main()
