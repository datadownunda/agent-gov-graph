"""Standalone HTTP client evidence producer. Never reads or writes target logs."""
import base64
import json
from datetime import datetime, timezone
from http.client import HTTPConnection
from pathlib import Path


def request(host, port, *, resource_id, actor_id, action_attempt_id, log_path,
            username, password, fail_finalization=False, method='GET', authenticated=True):
    record={'actor':{'namespace':'agent','id':actor_id},'action':'read',
            'resource_id':resource_id,'resource_type':'employee_complaint',
            'observed_at':datetime.now(timezone.utc).isoformat(), 'action_attempt_id':action_attempt_id,
            'request_id':None,'execution_disposition':'SUBMISSION_UNKNOWN', 'client_success':None,
            'response_status':None,'failure_stage':None}
    connection=HTTPConnection(host,port,timeout=10)
    try:
        headers={}
        if authenticated:
            headers['Authorization']='Basic '+base64.b64encode((username+':'+password).encode()).decode()
        connection.request(method,'/complaints/'+resource_id+'.json',headers=headers)
        record['execution_disposition']='SUBMITTED'
        response=connection.getresponse()
        # Server-issued ID, never generated or transmitted as a request ID by us.
        record['request_id']=response.getheader('X-Request-ID')
        record['response_status']=response.status
        body=response.read()
        record['response_body_bytes_received']=len(body)
        if fail_finalization:
            record['failure_stage']='CLIENT_FINALIZATION_FAILED'
            raise RuntimeError('Controlled failure after response reception; client success deliberately unrecorded')
        if response.status!=200:
            record['client_success']=False
            raise RuntimeError('HTTP response did not return the complaint')
        complaint=json.loads(body)
        record['client_success']=True
        return complaint
    except Exception:
        record['failure_stage']=record['failure_stage'] or 'REQUEST_OR_RESPONSE_FAILURE'
        raise
    finally:
        connection.close()
        with Path(log_path).open('a') as stream: stream.write(json.dumps(record)+'\n')
