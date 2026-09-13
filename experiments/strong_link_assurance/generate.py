"""Deterministic event histories. Only the returned evidence enters the worker."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'experiments/control_attestation/results/v1/deterministic_fixture'
CASES = {
    'controls': ['allow', 'deny_effect', 'blocked'],
    'reuse': ['visible', 'replacement', 'period'],
    'namespace': ['explicit', 'pooled', 'missing'],
    'copied': ['different', 'identical', 'removed'],
    'retry': ['repeated', 'distinct', 'governed'],
    'fanout': ['same_tuple', 'changed_tuple', 'governed'],
    'fanin': ['competing', 'converged', 'withheld'],
    'parent': ['children', 'context_only', 'governed'],
    'bridge': ['missing', 'equal_text'],
}


def read(name):
    return json.loads((FIXTURE / name).read_text())


def build(family, variant, presentation='canonical'):
    g = [json.loads(line) for line in (FIXTURE / 'governance.jsonl').read_text().splitlines()]
    e, o = [], []
    # Addresses are scorer-only locations, not fields supplied to matching.
    histories = {'governance': ['s0', 'a', 's2'], 'execution': [], 'outcome': []}
    transactions = {'governance': ['s0', 't', 's2'], 'execution': [], 'outcome': []}
    scopes = []
    namespaces = {'governance': ['runtime'] * 3, 'execution': [], 'outcome': []}
    epoch = datetime(2026, 9, 5, 12, 0, 1, tzinfo=timezone.utc).timestamp()

    def add(gi=1, attempt='a', tx='t', request='native-1', resource=None, scope=True):
        resource = resource or g[gi]['resource']['id']
        index = len(e)
        e.append({'actor': {'namespace': 'agent', 'id': 'fixture-agent'},
                  'action': 'read', 'resource_id': resource, 'resource_type': 'employee_complaint',
                  'observed_at': '2026-09-05T12:00:01.100000+00:00',
                  'action_attempt_id': g[gi]['context']['action_attempt_id'], 'request_id': request,
                  'execution_disposition': 'SUBMITTED', 'client_success': None,
                  'response_status': 200, 'failure_stage': None})
        o.append({'msec': str(epoch + .1), 'request_time': '0.000', 'request_id': request,
                  'request_method': 'GET', 'request_uri': f'/complaints/{resource}.json',
                  'status': 200, 'body_bytes_sent': 168, 'request_completion': 'OK',
                  'remote_user': 'complaint-client'})
        for role in ('execution', 'outcome'):
            histories[role].append(attempt)
            transactions[role].append(tx)
            namespaces[role].append('nginx-A')
        if scope:
            scopes.append((gi, index))

    focus = 1
    if family == 'controls' and variant == 'blocked':
        focus = 2
    elif family == 'controls' and variant == 'allow':
        focus = 0
        add(0, 's0', 's0')
    else:
        add()

    if family == 'reuse':
        if variant == 'visible':
            add(attempt='b', tx='u', request='native-1', scope=False)
        elif variant == 'replacement':
            histories['execution'][0] = histories['outcome'][0] = 'b'
            transactions['execution'][0] = transactions['outcome'][0] = 'u'
            scopes.clear()
        else:
            histories['outcome'][0] = 'b'
            transactions['outcome'][0] = 'u'
            o[0]['msec'] = str(epoch + 86400)
    elif family == 'namespace':
        if variant == 'explicit':
            add(attempt='b', tx='u', request='native-1', scope=False)
            namespaces['execution'][1] = namespaces['outcome'][1] = 'nginx-B'
        else:
            histories['outcome'][0] = 'b'
            transactions['outcome'][0] = 'u'
            namespaces['outcome'][0] = 'nginx-B' if variant == 'pooled' else None
    elif family == 'copied':
        if variant == 'identical':
            # Retain the original and a copied-ID target observation.
            o.append(deepcopy(o[0]))
            histories['outcome'].append('b')
            transactions['outcome'].append('u')
            namespaces['outcome'].append('nginx-A')
        else:
            histories['outcome'][0] = 'b'
            transactions['outcome'][0] = 'u'
            if variant == 'different':
                o[0]['request_uri'] = '/complaints/complaint-456.json'
            # removed is intentionally byte-identical to controls/deny_effect.
    elif family in ('retry', 'fanout', 'parent'):
        if variant == 'governed':
            add(0, 's0', 't', 'native-2')
            transactions['governance'][0] = 't'
        else:
            request = 'native-1' if variant == 'repeated' else 'native-2'
            add(attempt='b', request=request, scope=False)
            if variant == 'changed_tuple':
                e[1]['action'] = 'export'
                e[1]['resource_id'] = 'complaint-456'
                o[1]['request_uri'] = '/complaints/complaint-456.json'
            if family == 'parent':
                g[1]['context']['parent_request_id'] = 'parent-1'
                for execution in e:
                    execution['parent_request_id'] = 'parent-1'
                if variant == 'context_only':
                    for execution in e:
                        execution['action_attempt_id'] = None
                        execution['request_id'] = None
                    for outcome in o:
                        outcome['request_id'] = None
    elif family == 'fanin':
        if variant == 'competing':
            g[0]['context']['action_attempt_id'] = g[1]['context']['action_attempt_id']
        elif variant == 'converged':
            add(0, 's0', 't', 'native-1')
            transactions['governance'][0] = 't'
            o.pop()
            for values in (histories, transactions, namespaces):
                values['outcome'].pop()
            histories['outcome'][0] = 'aggregate'
        else:
            # A downstream aggregate survives, but its other contributing attempt
            # is absent; the visible pairwise identifier is spuriously unique.
            histories['outcome'][0] = 'aggregate'
    elif family == 'bridge':
        e.clear()
        for values in (histories, transactions, namespaces):
            values['execution'].clear()
        scopes.clear()
        if variant == 'equal_text':
            o[0]['request_id'] = g[1]['context']['action_attempt_id']

    if family in ('fanout', 'retry'):
        g[1]['context']['parent_request_id'] = 'parent-1'
        if variant == 'governed':
            g[0]['context']['parent_request_id'] = 'parent-1'
        for execution in e:
            execution['parent_request_id'] = 'parent-1'

    rows = {'governance': g, 'execution': e, 'outcome': o}
    # Build relational truth BEFORE any presentation rename. Native IDs never
    # reconstruct truth. Absent true counterparts remain explicit obligations.
    edges = []
    for left, right in (('governance', 'execution'), ('execution', 'outcome')):
        for i, a in enumerate(histories[left]):
            for j, b in enumerate(histories[right]):
                if a == b:
                    edges.append([f'{left}:{i}', f'{right}:{j}'])
    missing = []
    if family in ('copied', 'namespace') and variant in ('removed', 'different', 'pooled', 'missing') or family == 'reuse' and variant == 'period' or family == 'fanin' and variant == 'withheld':
        missing.append(['execution:0', 'absent:outcome-a'])
    if family == 'reuse' and variant == 'replacement':
        missing.append(['governance:1', 'absent:execution-a'])
    if family == 'bridge':
        missing.extend([['governance:1', 'absent:execution-a'], ['absent:execution-a', 'outcome:0']])

    # Role-local addresses below are serialization locations for scoring only.
    remap = {}
    for role, records in rows.items():
        indices = list(range(len(records)))
        if presentation == 'reversed':
            indices.reverse()
        remap.update({f'{role}:{old}': f'{role}:{new}' for new, old in enumerate(indices)})
        rows[role] = [records[i] for i in indices]
        for values in (histories, transactions, namespaces):
            values[role] = [values[role][i] for i in indices]
    if presentation == 'renamed':
        def rename(value):
            return 'renamed-' + value if value else value
        for event in rows['governance']:
            # action_attempt_id requires UUID syntax in governance source schema.
            import uuid
            old = event['context']['action_attempt_id']
            event['context']['action_attempt_id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, old))
        import uuid
        for execution in rows['execution']:
            if execution['action_attempt_id']:
                execution['action_attempt_id'] = str(uuid.uuid5(uuid.NAMESPACE_URL, execution['action_attempt_id']))
            execution['request_id'] = rename(execution['request_id'])
            if 'parent_request_id' in execution:
                execution['parent_request_id'] = rename(execution['parent_request_id'])
        for outcome in rows['outcome']:
            original = outcome['request_id']
            # Equal-text bridge retains equality across the two native fields.
            outcome['request_id'] = (str(uuid.uuid5(uuid.NAMESPACE_URL, original))
                                     if family == 'bridge' and variant == 'equal_text' else rename(original))
        for event in rows['governance']:
            if 'parent_request_id' in event['context']:
                event['context']['parent_request_id'] = rename(event['context']['parent_request_id'])

    truth = {'attempts': {f'{role}:{i}': a for role, values in histories.items() for i, a in enumerate(values)},
             'transactions': {f'{role}:{i}': a for role, values in transactions.items() for i, a in enumerate(values)},
             'true_edges': [[remap.get(a, a), remap.get(b, b)] for a, b in edges + missing],
             'covered': [[remap[f'governance:{a}'], remap[f'execution:{b}']] for a, b in scopes],
             'focus': remap[f'governance:{focus}'], 'family': family, 'variant': variant,
             'presentation': presentation,
             'expected_control': {'allow': None, 'deny_effect': 'CONTROL_EFFECTIVENESS_EXCEPTION',
                                  'blocked': 'CONTROL_EFFECTIVE'}.get(variant) if family == 'controls' else None}
    evidence = {'rows': rows, 'namespace_observations': namespaces}
    return evidence, truth
