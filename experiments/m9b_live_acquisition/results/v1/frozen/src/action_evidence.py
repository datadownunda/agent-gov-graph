"""Read-only, portable source references for M6. Digests identify, not authenticate."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.authority_resolver import instant
from src.evidence_digest import evidence_digest


def now():
    return datetime.now(timezone.utc).isoformat()


def read_records(path, *, root):
    path, root = Path(path), Path(root).resolve()
    member = path.resolve().relative_to(root).as_posix()
    data = path.read_bytes()
    file_digest = 'sha256:' + hashlib.sha256(data).hexdigest()
    offset = 0
    for number, line in enumerate(data.splitlines(keepends=True), 1):
        location = {'member':member, 'file_digest':file_digest, 'line':number,
                    'byte_offset':offset, 'byte_length':len(line),
                    'line_digest':'sha256:' + hashlib.sha256(line).hexdigest()}
        offset += len(line)
        try:
            raw=json.loads(line)
            if not isinstance(raw, dict):
                raise ValueError('not an object')
            defects=[]
        except (ValueError, UnicodeDecodeError):
            raw=None; defects=['MALFORMED_SOURCE_RECORD']
        yield raw, location, defects


def verify_location(record, root):
    try:
        loc=record['location']; root=Path(root).resolve(); p=(root/loc['member']).resolve()
        p.relative_to(root)
        data=p.read_bytes(); part=data[loc['byte_offset']:loc['byte_offset']+loc['byte_length']]
        return ('sha256:'+hashlib.sha256(data).hexdigest()==loc['file_digest']
                and 'sha256:'+hashlib.sha256(part).hexdigest()==loc['line_digest']
                and data.splitlines(keepends=True)[loc['line']-1]==part)
    except (OSError, KeyError, ValueError, TypeError, IndexError):
        return False


def envelope(role, raw, location, defects):
    return {'schema_version':'1.0','role':role, 'evidence_ref':evidence_digest({'role':role,'location':location}),
            'location':location,'raw':raw,'ingested_at':now(),'defects':list(defects)}


def check_fields(record):
    for field in ('action','resource_id','resource_type'):
        if not isinstance(record.get(field), str) or not record[field].strip():
            record['defects'].append('INVALID_'+field.upper())
    actor=record.get('actor')
    if not isinstance(actor,dict) or any(not isinstance(actor.get(k),str) or not actor[k].strip() for k in ('namespace','id')):
        record['defects'].append('INVALID_ACTOR')
    try:
        instant(record.get('observed_at'))
    except (ValueError, TypeError):
        record['defects'].append('INVALID_TIMESTAMP')
    return record


def ingest_governance(path, *, root):
    result=[]
    for raw,loc,defects in read_records(path,root=root):
        r=envelope('governance',raw,loc,defects); raw=raw or {}
        def part(name):
            value=raw.get(name,{})
            if not isinstance(value,dict):
                r['defects'].append('INVALID_'+name.upper());return {}
            return value
        context=part('context');subject=part('subject');resource=part('resource');decision=part('decision')
        binding=context.get('authority_binding',{})
        if not isinstance(binding,dict):
            r['defects'].append('INVALID_AUTHORITY_BINDING');binding={}
        r.update(actor={'namespace':'agent','id':subject.get('id')},action=raw.get('action'),
                 resource_id=resource.get('id'),resource_type=resource.get('type'),
                 governance_decision=decision.get('status'),
                 action_attempt_id=context.get('action_attempt_id'),
                 observed_at=binding.get('opa_decision_at'), authority_resolution_at=binding.get('authority_resolution_at'),
                 event_recorded_at=raw.get('timestamp'))
        if r['governance_decision'] not in ('ALLOW','DENY'):
            r['defects'].append('INVALID_GOVERNANCE_DECISION')
        result.append(check_fields(r))
    return result


def ingest_execution(path, *, root):
    result=[]
    for raw,loc,defects in read_records(path,root=root):
        r=envelope('execution',raw,loc,defects); raw=raw or {}
        for field in ('actor','action','resource_id','resource_type','observed_at','action_attempt_id',
                      'request_id','execution_disposition','client_success','response_status','failure_stage'):
            r[field]=raw.get(field)
        if r['execution_disposition'] not in ('SUBMITTED','SUBMISSION_UNKNOWN','NOT_SUBMITTED'):
            r['defects'].append('INVALID_EXECUTION_DISPOSITION')
        if r['client_success'] is not None and type(r['client_success']) is not bool:
            r['defects'].append('INVALID_CLIENT_SUCCESS')
        result.append(check_fields(r))
    return result
