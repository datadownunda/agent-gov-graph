"""Shared output contract; no traversal or authority selection."""
import json
from copy import deepcopy


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def result(query, records=(), paths=(), **details):
    return {'query': query, 'complete': True, 'records': sorted(set(records)),
            'paths': sorted(paths, key=stable), 'cycles': [], 'unresolved': [], **details}


def ref_key(ref):
    return (ref['kind'], ref['record_id'], ref['version'])


def authority_delta(resolution, removed):
    """Disable a relationship, not the evidence establishing a conflict."""
    lost, remaining = [], []
    for basis in resolution['valid_bases']:
        destination = lost if removed in [ref_key(r) for r in basis['chain']] else remaining
        destination.append(basis)
    return {'lost': lost, 'remaining': remaining,
            'loses_all_demonstrated_support': bool(lost) and not remaining,
            'resolution': resolution}


def record_details(records, keys):
    details = deepcopy([records[k] for k in keys])
    for r in details:
        r["references"].sort(key=stable)
    return details
