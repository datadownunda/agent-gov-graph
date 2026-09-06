"""Pure, deterministic delegation assessment. No OPA or executor integration.

M4 owns direct/root authority semantics. Every delegation has exactly one
parent. Multiple independently valid bases are retained, never merged or ranked.
"""
import hashlib
import json

import jsonschema

from src.authority_resolver import (
    PROJECT_ROOT, authority_basis, instant, resolve_authority, revision_bytes, validate_revision,
)
from src.delegation_evidence import schema as delegation_schema

RULE_VERSION = 'delegation/1'


def record_ref(record, kind):
    prefix = 'authority_record' if kind == 'authority' else 'delegation'
    version = 'authority_version' if kind == 'authority' else 'delegation_version'
    return {'kind': kind, 'record_id': record[prefix + '_id'], 'version': record[version]}


def ref_key(ref):
    return ref['record_id'], ref['version']


def tuples(scopes):
    return {(s['action'], s['resource_type'], resource) for s in scopes for resource in s['resource_ids']}


def normalized_scopes(scopes):
    return authority_basis({'roles': [], 'permitted_scopes': scopes})['permitted_scopes']


def eligible(record, at):
    return instant(record['valid_from']) <= at and (record['valid_to'] is None or at < instant(record['valid_to']))


def interval_contained(child, upstream):
    return (instant(child['valid_from']) >= instant(upstream['valid_from'])
            and (upstream['valid_to'] is None or (child['valid_to'] is not None
                 and instant(child['valid_to']) <= instant(upstream['valid_to']))))


def candidate(kind, actor, terminal):
    return {'authority_kind': kind, 'proposed_actor': actor, 'root_principal': None,
            'terminal': terminal, 'chain': [], 'status': 'RESOLVED',
            'permission_result': 'NOT_EVALUABLE', 'effective_scopes': [], 'issues': []}


def add_issue(path, code, ref, detail):
    issue = {'code': code, 'record': ref, 'detail': detail}
    if issue not in path['issues']:
        path['issues'].append(issue)


def finish(path, requested):
    path['issues'].sort(key=lambda issue: revision_bytes(issue))
    codes = {issue['code'] for issue in path['issues']}
    if codes:
        path['status'] = next(iter(codes)) if len(codes) == 1 else 'DELEGATION_REJECTED'
        path['permission_result'] = 'NOT_EVALUABLE'
        # An invalid chain must not expose an apparently usable derived scope.
        path['effective_scopes'] = []
    else:
        path['permission_result'] = 'PERMITTED' if requested in tuples(path['effective_scopes']) else 'NOT_PERMITTED'
    return path


def resolve_delegation(query, *, authority_revision, delegation_records):
    """Assess supplied evidence; use create_assertion for digest-bound evidence.

Unverifiable authority collections retain M4's collection-level defect behavior.
Link-level defects are local. Unknown/unassignable raw entries remain visible in
`evidence_issues` even when they cannot be attached to an actor candidate.
"""
    contract = json.loads((PROJECT_ROOT / 'schemas/delegation_resolution.schema.json').read_text())
    jsonschema.validate(query, contract['$defs']['query'], format_checker=jsonschema.FormatChecker())
    at = instant(query['effective_at'])
    actor = query['actor']
    requested = query['action'], query['resource_type'], query['resource_id']
    direct = resolve_authority(actor, effective_at=query['effective_at'], registry_revision=authority_revision)
    result = {'rule_version': RULE_VERSION, 'query': dict(query), 'status': 'INSUFFICIENT_EVIDENCE',
              'permission_result': 'NOT_EVALUABLE', 'candidates': [], 'valid_bases': [],
              'evidence_issues': [], 'direct_authority': direct}
    try:
        validate_revision(authority_revision)
    except (ValueError, TypeError, KeyError, jsonschema.ValidationError):
        result['status'] = 'EVIDENCE_DEFECT'
        return result
    if not isinstance(delegation_records, list):
        result['status'] = 'EVIDENCE_DEFECT'
        return result

    authority_index = {(r['authority_record_id'], r['authority_version']): r for r in authority_revision['records']}
    roots = {}

    def root_resolution(principal):
        if principal not in roots:
            roots[principal] = resolve_authority(principal, effective_at=query['effective_at'], registry_revision=authority_revision)
        return roots[principal]

    # Exact duplicate input records do not manufacture extra bases.
    raw_records = {revision_bytes(r): r for r in delegation_records}
    links, invalid, evidence_issues = {}, set(), []
    record_contract = delegation_schema()['$defs']['record']
    for payload, record in sorted(raw_records.items()):
        key = None
        if isinstance(record, dict) and all(isinstance(record.get(k), str) and record[k]
                                           for k in ('delegation_id', 'delegation_version')):
            key = record['delegation_id'], record['delegation_version']
            links.setdefault(key, []).append(record)
        try:
            jsonschema.validate(record, record_contract, format_checker=jsonschema.FormatChecker())
            start = instant(record['valid_from'])
            if record['valid_to'] is not None and instant(record['valid_to']) <= start:
                raise ValueError('Invalid delegation validity interval')
        except (ValueError, TypeError, KeyError, jsonschema.ValidationError):
            if key is not None:
                invalid.add(key)
            evidence_issues.append({'code': 'EVIDENCE_DEFECT',
                                    'record_digest': 'sha256:' + hashlib.sha256(payload).hexdigest(),
                                    'detail': 'Malformed delegation record retained in preserved revision'})
    result['evidence_issues'] = evidence_issues
    conflicting = {key for key, variants in links.items() if len(variants) > 1}
    # Different IDs are independent. Overlapping versions of the SAME logical
    # delegation conflict only when their effective meaning is contradictory.
    # Equivalent versions remain separate supporting references; no latest wins.
    active_versions = {}
    for key, variants in links.items():
        if key not in invalid and any(eligible(r, at) for r in variants):
            active_versions.setdefault(key[0], set()).add(key)
    for keys in active_versions.values():
        meanings = {revision_bytes({
            'delegator': r['delegator'], 'delegate': r['delegate'], 'parent': r['parent'],
            'delegated_scopes': normalized_scopes(r['delegated_scopes']),
            'onward_delegation': r['onward_delegation']})
            for key in keys for r in links[key] if eligible(r, at)}
        if len(meanings) > 1:
            conflicting.update(keys)

    if direct['status'] == 'RESOLVED':
        for ref in direct['record_refs']:
            record = authority_index[(ref['authority_record_id'], ref['authority_version'])]
            terminal = record_ref(record, 'authority')
            path = candidate('DIRECT', actor, terminal)
            path.update(root_principal=actor, chain=[terminal], effective_scopes=authority_basis(record)['permitted_scopes'])
            result['candidates'].append(finish(path, requested))
    elif direct['status'] != 'INSUFFICIENT_EVIDENCE':
        for ref in direct['record_refs']:
            path = candidate('DIRECT', actor, {'kind': 'authority', 'record_id': ref['authority_record_id'], 'version': ref['authority_version']})
            add_issue(path, 'AUTHORITY_CONFLICT', path['terminal'], 'M4 direct authority is not resolved')
            result['candidates'].append(finish(path, requested))

    for terminal_key, variants in sorted(links.items()):
        if not any(r.get('delegate') == actor for r in variants):
            continue
        terminal = {'kind': 'delegation', 'record_id': terminal_key[0], 'version': terminal_key[1]}
        path = candidate('DELEGATED', actor, terminal)
        current = terminal
        seen_refs, seen_actors = set(), {actor}
        child = None
        reverse_chain = []
        while current['kind'] == 'delegation':
            key = ref_key(current)
            if key in seen_refs:
                add_issue(path, 'DELEGATION_CYCLE', current, 'Repeated delegation reference in ancestry')
                break
            seen_refs.add(key)
            reverse_chain.append(current)
            if key not in links:
                add_issue(path, 'DELEGATION_CHAIN_BROKEN', current, 'Exact parent delegation is missing')
                break
            if key in conflicting:
                add_issue(path, 'DELEGATION_CONFLICT', current, 'Contradictory identity contents or contradictory overlapping versions of one delegation')
                break
            if key in invalid:
                add_issue(path, 'EVIDENCE_DEFECT', current, 'Malformed delegation link')
                break
            link = links[key][0]
            if not eligible(link, at):
                code = 'DELEGATION_NOT_YET_VALID' if at < instant(link['valid_from']) else 'DELEGATION_EXPIRED'
                add_issue(path, code, current, 'Delegation is not effective at the historical timestamp')
            if link['delegator'] in seen_actors:
                add_issue(path, 'DELEGATION_CYCLE', current, 'Delegation returns to an ancestor identity')
                break
            seen_actors.add(link['delegator'])
            if child is None:
                path['effective_scopes'] = normalized_scopes(link['delegated_scopes'])
            else:
                if child['delegator'] != link['delegate']:
                    add_issue(path, 'DELEGATION_CHAIN_BROKEN', current, 'Parent delegate differs from child delegator')
                if not link['onward_delegation']:
                    add_issue(path, 'ONWARD_DELEGATION_NOT_PERMITTED', current, 'Parent forbids onward delegation')
                check_narrowing(path, child, link, link['delegated_scopes'], current)
            child = link
            current = link['parent']
        else:
            reverse_chain.append(current)
            root = authority_index.get(ref_key(current))
            if root is None:
                add_issue(path, 'DELEGATION_CHAIN_BROKEN', current, 'Exact root authority record is missing')
            else:
                path['root_principal'] = root['principal']
                if root['principal'] != child['delegator']:
                    add_issue(path, 'DELEGATION_CHAIN_BROKEN', current, 'Root principal differs from delegator')
                if not eligible(root, at):
                    code = 'DELEGATION_NOT_YET_VALID' if at < instant(root['valid_from']) else 'DELEGATION_EXPIRED'
                    add_issue(path, code, current, 'Root authority is not effective at the historical timestamp')
                resolved = root_resolution(root['principal'])
                if resolved['status'] == 'CONFLICT':
                    add_issue(path, 'DELEGATION_CONFLICT', current, 'M4 root authority has conflicting effective states')
                elif resolved['status'] != 'RESOLVED':
                    add_issue(path, 'INSUFFICIENT_EVIDENCE', current, 'M4 cannot resolve effective root authority')
                else:
                    effective = [authority_index[(r['authority_record_id'], r['authority_version'])] for r in resolved['record_refs']]
                    if len({r.get('delegation_permitted', False) for r in effective}) > 1:
                        add_issue(path, 'DELEGATION_CONFLICT', current, 'Effective root states disagree about delegation capability')
                if not root.get('delegation_permitted', False):
                    add_issue(path, 'DELEGATION_NOT_PERMITTED', current, 'Root lacks explicit delegation capability')
                check_narrowing(path, child, root, root['permitted_scopes'], current)
        path['chain'] = list(reversed(reverse_chain))
        result['candidates'].append(finish(path, requested))

    result['candidates'].sort(key=lambda c: revision_bytes(c['terminal']))
    result['valid_bases'] = [c for c in result['candidates'] if c['status'] == 'RESOLVED' and c['permission_result'] == 'PERMITTED']
    if result['valid_bases']:
        result['status'] = 'MULTIPLE_VALID_BASES' if len(result['valid_bases']) > 1 else 'RESOLVED'
        result['permission_result'] = 'PERMITTED'
    elif any(c['issues'] for c in result['candidates']) or evidence_issues:
        codes = {i['code'] for c in result['candidates'] for i in c['issues']}
        codes.update(i['code'] for i in evidence_issues)
        result['status'] = next(iter(codes)) if len(codes) == 1 else 'DELEGATION_REJECTED'
    elif result['candidates']:
        result.update(status='RESOLVED', permission_result='NOT_PERMITTED')
    return result


def check_narrowing(path, child, upstream, upstream_scopes, reference):
    if not tuples(child['delegated_scopes']) <= tuples(upstream_scopes):
        add_issue(path, 'DELEGATION_SCOPE_EXCEEDED', reference, 'Entire child scope must be a subset of its one parent')
    if not interval_contained(child, upstream):
        add_issue(path, 'DELEGATION_VALIDITY_EXCEEDED', reference, 'Child validity must be contained in parent validity; no clipping')
