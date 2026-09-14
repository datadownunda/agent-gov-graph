"""One-shot native producer capture; no matching or assurance execution."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / 'results/v1'
BASE = '435d15f4c705e9cbd55f28baee7c4e1136867b07'
IMAGE = 'nginx@sha256:dc5069ad14f19660b141b21236140b91656bf89bbc3e2417c70ae650cd66104c'
PLAN = [dict(request_number=i+1, method='GET', uri=f'/complaints/complaint-{789 if i < 6 else 456}.json',
             sent_x_request_id=v) for i, v in enumerate(['SAME-VALUE','SAME-VALUE',None,None,'VALUE-A','VALUE-B','SAME-VALUE','SAME-VALUE'])]

def stamp(): return datetime.now(timezone.utc).isoformat()
def digest(data): return hashlib.sha256(data).hexdigest()
def write(path, value): path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
def command(*args): return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()
def inventory():
    return {s: digest((ROOT/s).read_bytes()) for s in command('git','ls-files').splitlines()}

def analyze(captured, native, errors):
    rows=[]; checks={}; lines=native.splitlines(keepends=True); offset=0
    complete=len(captured)==len(lines)==8 and not errors
    for index, (c,line) in enumerate(zip(captured,lines)):
        try:
            n=json.loads(line); header=c['response'].split(b'\r\n\r\n',1)[0]
            parts=header.split(b'\r\n'); status=int(parts[0].split()[1])
            body=c['response'].split(b'\r\n\r\n',1)[1]
            lengths=[int(x.split(b':',1)[1].strip()) for x in parts[1:] if x.split(b':',1)[0].lower()==b'content-length']
            if lengths!=[len(body)]:
                complete=False; errors.append(f'incomplete or ambiguous body for request {index+1}')
            ids=[x.split(b':',1)[1].strip().decode('ascii') for x in parts[1:] if x.split(b':',1)[0].lower()==b'x-request-id']
            p=PLAN[index]; rid=n['request_id']; incoming=n['incoming_x_request_id']
            row={**p, 'observed_incoming_x_request_id':incoming,'generated_request_id':rid,
                 'returned_response_ids':ids,'status':status,
                 'generated_equals_incoming':None if p['sent_x_request_id'] is None else rid==incoming,
                 'matching_generated_id_requests':[],
                 'raw_request_ref':f'requests/{index+1:03}.http','raw_response_ref':f'responses/{index+1:03}.http',
                 'access_log_ref':{'path':'native/access.jsonl','line':index+1,'byte_offset':offset,'byte_length':len(line)}}
            checks[f'request_{index+1}']=bool(status==n['status']==200 and ids==[rid]
                and re.fullmatch('[0-9a-f]{32}',rid) and n['request_uri']==p['uri'] and n['request_method']=='GET'
                and (incoming==p['sent_x_request_id'] if p['sent_x_request_id'] is not None else incoming in ('','-'))
                and n['request_completion']=='OK' and n['body_bytes_sent']>0)
            rows.append(row)
        except (KeyError,ValueError,TypeError,UnicodeError,IndexError) as error:
            complete=False; errors.append(f'parse request {index+1}: {error}')
        offset+=len(line)
    for r in rows:
        r['matching_generated_id_requests']=[x['request_number'] for x in rows if x is not r and x['generated_request_id']==r['generated_request_id']]
    checks['capture_complete']=complete and len(rows)==8
    checks['no_duplicate_native_ids_observed']=len(rows)==8 and all(not x['matching_generated_id_requests'] for x in rows)
    for a,b in ((1,2),(7,8)):
        checks[f'pair_{a}_{b}_equal_incoming_distinct_native']=len(rows)==8 and rows[a-1]['observed_incoming_x_request_id']==rows[b-1]['observed_incoming_x_request_id']=='SAME-VALUE' and rows[a-1]['generated_request_id']!=rows[b-1]['generated_request_id']
    checks['supplied_incoming_distinct_from_native']=all(r['generated_equals_incoming'] is not True for r in rows)
    repeated=any(a['sent_x_request_id'] is not None and a['sent_x_request_id']==b['sent_x_request_id'] and a['generated_request_id']==b['generated_request_id'] for i,a in enumerate(rows) for b in rows[i+1:])
    if not checks['capture_complete']: decision='NOT_EVALUABLE'
    elif any(r['generated_equals_incoming'] for r in rows): decision='FORWARDED_AND_GENERATED_IDS_CONFLATED'
    elif not all(checks[f'request_{i}'] for i in range(1,9)): decision='NOT_EVALUABLE'
    elif repeated: decision='PRODUCER_CONTRACT_CONTRADICTED'
    elif all(checks.values()): decision='PRODUCER_CONTRACT_SUPPORTED'
    else: decision='NOT_EVALUABLE'
    return rows,checks,decision

def finalize(out, lock, captured, errors, capture):
    native=(out/'native/access.jsonl').read_bytes() if (out/'native/access.jsonl').exists() else b''
    rows,checks,decision=analyze(captured,native,list(errors))
    result={'schema_version':'1.0','campaign':'nginx-producer-conformance-v1','baseline_commit':BASE,
      'protocol_sha256':lock['protocol_sha256'],'producer_ref':'target-runtime.json','configuration_ref':'nginx.conf',
      'capture_complete':checks['capture_complete'],'errors':errors,'observations':rows,'checks':checks,
      'decision':decision,'decision_reasons':[k for k,v in checks.items() if not v] or ['All preregistered checks passed'],
      'limitations':['Finite eight-request observation; no cryptographic uniqueness or collision impossibility claim.','Custody hashes do not authenticate producers.','Historical FAILED and scores remain unchanged.']}
    write(out/'capture.json',capture); write(out/'result.json',result)
    before=lock['tracked_inventory']; changed=[p for p,h in before.items() if not (ROOT/p).exists() or digest((ROOT/p).read_bytes())!=h]
    write(out/'preservation.json',{'baseline_commit':BASE,'tracked_files_checked':len(before),'changed':changed,
       'historical_strong_link_files_checked':sum(p.startswith('experiments/strong_link_assurance/results/') for p in before),
       'status':'VERIFIED' if not changed else 'FAILED'})
    table='|Request|URI|Incoming (native observation)|Native ID|Returned ID|Equals incoming|Other requests with native ID|\n|---|---|---|---|---|---|---|\n'
    for r in rows:
        table+='|'+ '|'.join(str(x) for x in (r['request_number'],r['uri'],repr(r['observed_incoming_x_request_id']),r['generated_request_id'],r['returned_response_ids'],r['generated_equals_incoming'],r['matching_generated_id_requests']))+'|\n'
    report=f'# NGINX producer conformance\n\n**{decision}**\n\nBaseline: {BASE}\n\nProtocol SHA-256: {lock["protocol_sha256"]}\n\n'+table
    report+='\n'+('No duplicate native $request_id values observed across the eight captured requests.' if checks['no_duplicate_native_ids_observed'] else 'The no-duplicate observation check did not pass.')+'\n\nChecks and failures: '+json.dumps(checks)+'\n\nErrors: '+json.dumps(errors)+'\n'
    report+='''
## Repository representation analysis

The existing target_outcome/nginx.conf logs $request_id and returns it as X-Request-ID. http_client.py reads that response header and sends no selected request ID. Existing raw logs plus preserved code/configuration identify that meaning, but do not record incoming request-ID headers. This campaign preserves both fields independently.

src/action_evidence.py retains raw records while exposing execution request_id. src/target_outcome_evidence.py retains raw records and target contract while exposing outcome request_id. Normalization omits structured generation/observation semantics; it does not destructively discard raw fields. src/correlation_assertion.py uses a caller-selected field and declared issuer/namespace, not verified generation provenance. schemas/action_evidence.schema.json retains raw evidence but does not require identifier provenance. A minimal field annotation referencing the producer field, observation direction and preserved configuration could suffice for this fixed chain; no generic subsystem or matcher change is justified by this campaign alone.

## Historical implications

If the producer contract is supported, deliberate copied/recycled native IDs in copied/different, copied/removed, copied/identical and reuse/period are not demonstrated behavior of this stock NGINX contract. This does not rule out random collisions, false client records, collector faults or altered producers. Runtime action_attempt_id reuse, namespace loss and aggregate-outcome semantics are not tested here. Incoming/forwarded identifier reuse remains possible, as the repeated incoming values demonstrate. No historical inputs, scorer truth, scores, protocol or FAILED verdict are changed. If this campaign is not supported, these implications remain conditional and require investigation of the preserved unexpected evidence.

No authentication, cryptographic uniqueness, general error-frequency, governance coverage or control-effectiveness claim follows.
'''
    (out/'REPORT.md').write_text(report)
    write(out/'manifest.json',{'files':{p.relative_to(out).as_posix():{'sha256':digest(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}})

def run(out=OUT):
    assert command('git','rev-parse','HEAD')==BASE
    out.mkdir(parents=True,exist_ok=False)
    for d in ('native','requests','responses'): (out/d).mkdir()
    protocol=(HERE/'PROTOCOL.md').read_bytes(); (out/'PROTOCOL.md').write_bytes(protocol)
    source=(ROOT/'experiments/target_outcome/nginx.conf').read_text()
    config=source.replace('      \'"request_id":', '      \'"incoming_x_request_id":"$http_x_request_id",\'\n      \'"request_id":')
    assert config!=source and config.count('$http_x_request_id')==1
    (out/'nginx.conf').write_text(config); write(out/'requests.json',PLAN)
    lock={'baseline_commit':BASE,'frozen_at':stamp(),'protocol_sha256':digest(protocol),'image':IMAGE,
      'implementation':{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in [HERE/'run_experiment.py',HERE/'result.schema.json',HERE/'README.md',ROOT/'tests/test_nginx_producer_conformance.py']},
      'configuration_sha256':digest(config.encode()),'resources':{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in (ROOT/'runtime_resources').rglob('*') if p.is_file()},'tracked_inventory':inventory()}
    write(out/'execution-lock.json',lock)
    captured=[]; errors=[]; capture={'started_at':stamp(),'requests':[]}; launched=False; name='agg-nginx-provenance-'+secrets.token_hex(5)
    try:
        with tempfile.TemporaryDirectory(prefix='agg-nginx-provenance-') as tmp:
            password=secrets.token_urlsafe(24)
            hashed=subprocess.run(['openssl','passwd','-apr1','-stdin'],input=password+'\n',text=True,capture_output=True,check=True).stdout.strip()
            auth=Path(tmp)/'auth'; auth.write_text('complaint-client:'+hashed+'\n'); auth.chmod(0o644)
            command('docker','run','-d','--name',name,'-p','127.0.0.1::8080','-v',f'{out}/nginx.conf:/etc/nginx/nginx.conf:ro','-v',f'{out}/native:/evidence','-v',f'{ROOT}/runtime_resources:/target:ro','-v',f'{auth}:/run/target-auth:ro',IMAGE); launched=True
            port=int(command('docker','port',name,'8080/tcp').split(':')[-1])
            details=json.loads(command('docker','image','inspect',IMAGE))[0]
            version=subprocess.run(['docker','exec',name,'nginx','-v'],capture_output=True,text=True,check=True).stderr.strip()
            (out/'nginx-T.txt').write_text(command('docker','exec',name,'nginx','-T'))
            assert command('docker','exec',name,'cat','/etc/nginx/nginx.conf')==config.strip()
            write(out/'target-runtime.json',{'image':IMAGE,'image_id':details['Id'],'repo_digests':details['RepoDigests'],'nginx_version':version,'port':port,'configuration_sha256':digest(config.encode()),'recorded_before_requests_at':stamp()})
            for p in PLAN:
                i=p['request_number']; started=stamp()
                base=f'GET {p["uri"]} HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n'
                if p['sent_x_request_id'] is not None: base+=f'X-Request-ID: {p["sent_x_request_id"]}\r\n'
                (out/f'requests/{i:03}.http').write_bytes((base+'Authorization: [REDACTED EPHEMERAL BASIC CREDENTIAL]\r\n\r\n').encode())
                token=base64.b64encode(('complaint-client:'+password).encode()).decode()
                response=b''
                try:
                    with socket.create_connection(('127.0.0.1',port),timeout=10) as sock:
                        sock.sendall((base+'Authorization: Basic '+token+'\r\n\r\n').encode())
                        while True:
                            chunk=sock.recv(65536)
                            if not chunk: break
                            response+=chunk
                finally:
                    (out/f'responses/{i:03}.http').write_bytes(response)
                captured.append({'response':response})
                for _ in range(100):
                    count=len((out/'native/access.jsonl').read_bytes().splitlines()) if (out/'native/access.jsonl').exists() else 0
                    if count>=i: break
                    time.sleep(.05)
                if count!=i: raise RuntimeError(f'Expected exactly {i} access rows; observed {count}')
                capture['requests'].append({'request_number':i,'started_at':started,'finished_at':stamp(),'native_rows_after_request':count})
            command('docker','exec',name,'nginx','-s','quit'); command('docker','wait',name)
    except Exception as error:
        errors.append(f'{type(error).__name__}: {error}')
    finally:
        if launched:
            try: command('docker','rm','-f',name)
            except Exception as error: errors.append(f'cleanup: {error}')
        capture['finished_at']=stamp(); finalize(out,lock,captured,errors,capture)
    verify(out)

def verify(out=OUT):
    import jsonschema
    manifest=json.loads((out/'manifest.json').read_text())['files']
    assert set(manifest)=={p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name!='manifest.json'}
    for p,h in manifest.items():
        data=(out/p).read_bytes(); assert digest(data)==h['sha256'] and len(data)==h['bytes'],p
    result=json.loads((out/'result.json').read_text()); schema=json.loads((HERE/'result.schema.json').read_text())
    jsonschema.Draft202012Validator.check_schema(schema); jsonschema.validate(result,schema)
    lock=json.loads((out/'execution-lock.json').read_text()); assert digest((out/'PROTOCOL.md').read_bytes())==lock['protocol_sha256']==result['protocol_sha256']
    assert digest((out/'nginx.conf').read_bytes())==lock['configuration_sha256']
    for p,h in {**lock['implementation'],**lock['resources'],**lock['tracked_inventory']}.items(): assert digest((ROOT/p).read_bytes())==h,p
    captured=[{'response':p.read_bytes()} for p in sorted((out/'responses').glob('*.http'))]
    rows,checks,decision=analyze(captured,(out/'native/access.jsonl').read_bytes() if (out/'native/access.jsonl').exists() else b'',list(result['errors']))
    assert (rows,checks,decision)==(result['observations'],result['checks'],result['decision'])
    print(json.dumps({'status':'VERIFIED','decision':decision,'protocol_sha256':lock['protocol_sha256'],'artifacts':len(manifest)}))

if __name__=='__main__':
    {'run':run,'verify':verify}[sys.argv[1]]()
