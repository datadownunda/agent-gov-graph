"""Interpret stock NGINX request logs only under an explicit static-target contract."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from src.action_evidence import read_records, envelope
from src.evidence_digest import evidence_digest


def ingest_nginx(path, *, root, target):
    result=[]
    for raw,loc,defects in read_records(path,root=root):
        r=envelope('outcome',raw,loc,defects); raw=raw or {}
        resource=target['resources'].get(raw.get('request_uri'),{})
        r.update(actor={'namespace':target['identity_namespace'],'id':raw.get('remote_user') or None},
                 action='read' if raw.get('request_method')=='GET' else None,
                 resource_id=resource.get('id'),resource_type=resource.get('type'),
                 request_id=raw.get('request_id'),observed_at=None,
                 target_contract=target,target_contract_digest=evidence_digest(target),
                 target_outcome='NO_REPRESENTATION_ESTABLISHED')
        try:
            stamp=Decimal(raw['msec'])
            if not stamp.is_finite(): raise ValueError('timestamp')
            r['observed_at']=datetime.fromtimestamp(float(stamp),timezone.utc).isoformat()
            for field in ('status','body_bytes_sent'):
                if type(raw[field]) is not int: raise ValueError(field)
            if not 100 <= raw['status'] <= 599 or raw['body_bytes_sent']<0: raise ValueError('numeric range')
            if not isinstance(raw.get('request_completion'),str): raise ValueError('completion')
        except (KeyError, ValueError, TypeError, InvalidOperation, OverflowError, OSError):
            r['defects'].append('INVALID_NATIVE_FIELDS')
        authenticated=(target.get('basic_auth_required') is True
                       and isinstance(raw.get('remote_user'),str) and bool(raw['remote_user'].strip()))
        # GET + 200 in this preserved Basic-auth-protected exact static location
        # establishes auth success under the configured server behavior, not merely
        # because remote_user is populated (it can also be populated on a 401).
        if (not r['defects'] and resource and raw.get('request_method')=='GET' and authenticated
                and raw.get('status')==200 and raw.get('request_completion')=='OK'
                and raw.get('body_bytes_sent',0)>0):
            r['target_outcome']='REPRESENTATION_SERVED'
        r['interpretation_limit']='Server-reported completed representation transmission; not client receipt, use, or generic HTTP success.'
        result.append(r)
    return result
