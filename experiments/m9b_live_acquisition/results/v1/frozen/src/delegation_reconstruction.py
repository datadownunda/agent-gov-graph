"""Digest-bound, read-only M5 assertions. No current-registry fallback or OPA calls."""
import argparse
import json
from pathlib import Path

import jsonschema

from src.authority_reconstruction import reconstruct_authority
from src.authority_resolver import PROJECT_ROOT, instant, load_preserved_revision
from src.delegation_evidence import load_delegation_revision
from src.delegation_resolver import RULE_VERSION, resolve_delegation
from src.evidence_digest import evidence_digest


def schema():
    return json.loads((PROJECT_ROOT / 'schemas/delegation_resolution.schema.json').read_text())


def create_assertion(query, *, authority_reference, delegation_reference, history_directory, governance_event=None):
    """Build an assertion from verified archives. Caller supplies explicit time.

An optional original M4 event binds the query to its native OPA timestamp and
adds the two-time comparison; it does not enable delegated enforcement.
"""
    authority = load_preserved_revision(authority_reference, history_directory)
    delegation = load_delegation_revision(delegation_reference, history_directory)
    if delegation['authority_revision'] != authority_reference:
        raise ValueError('Delegation and assertion reference different authority revisions')
    resolution = resolve_delegation(query, authority_revision=authority, delegation_records=delegation['records'])
    assertion = {'schema_version': '1.0', 'rule_version': RULE_VERSION, 'query': dict(query),
                 'authority_revision': dict(authority_reference), 'delegation_revision': dict(delegation_reference),
                 'resolution': resolution}
    if governance_event is not None:
        m4 = reconstruct_authority(governance_event, history_directory)
        if m4['status'] not in ('VERIFIED', 'TEMPORAL_BOUNDARY_AMBIGUITY'):
            raise ValueError('Original M4 event cannot be verified')
        binding = governance_event['context']['authority_binding']
        if (binding['revision'] != authority_reference
                or governance_event['subject']['id'] != query['actor']
                or governance_event['action'] != query['action']
                or governance_event['resource']['id'] != query['resource_id']
                or governance_event['resource']['type'] != query['resource_type']
                or instant(query['effective_at']) != instant(binding['opa_decision_at'])):
            raise ValueError('Query does not match the original M4 event and authority revision')
        first_query = dict(query, effective_at=binding['authority_resolution_at'])
        first = resolve_delegation(first_query, authority_revision=authority, delegation_records=delegation['records'])
        # Candidate diagnostics do not poison an unchanged independently valid
        # basis. A change in the set of supporting bases remains explicit.
        changed = any(first[k] != resolution[k] for k in ('status', 'permission_result', 'valid_bases'))
        boundary = ('TEMPORAL_BOUNDARY_AMBIGUITY' if changed or m4['status'] == 'TEMPORAL_BOUNDARY_AMBIGUITY'
                    else 'STABLE')
        assertion['governance_binding'] = {'event_digest': evidence_digest(governance_event),
                'authority_resolution_at': binding['authority_resolution_at'],
                'opa_decision_at': binding['opa_decision_at'], 'm4_reconstruction': m4,
                'at_authority_resolution': first, 'boundary_status': boundary}
    jsonschema.validate(assertion, schema(), format_checker=jsonschema.FormatChecker())
    return assertion


def reconstruct_delegation(assertion, history_directory, *, governance_event=None):
    """Recompute; embedded candidates and chains are comparison targets only."""
    def failure(status, reason):
        return {'status': status, 'permission_result': 'NOT_EVALUABLE', 'reason': reason}
    try:
        jsonschema.validate(assertion, schema(), format_checker=jsonschema.FormatChecker())
        bound_event = 'governance_binding' in assertion
        if bound_event and governance_event is None:
            return failure('INSUFFICIENT_EVIDENCE', 'Original M4 event is required for its bound assertion')
        if not bound_event and governance_event is not None:
            return failure('EVIDENCE_DEFECT', 'Unbound assertion cannot acquire a governance event during replay')
        expected = create_assertion(assertion['query'], authority_reference=assertion['authority_revision'],
                delegation_reference=assertion['delegation_revision'], history_directory=history_directory,
                governance_event=governance_event)
        if expected != assertion:
            return failure('CONTRADICTED', 'Recorded assertion differs from reconstructed evidence')
        ambiguous = expected.get('governance_binding', {}).get('boundary_status') == 'TEMPORAL_BOUNDARY_AMBIGUITY'
        return {'status': 'TEMPORAL_BOUNDARY_AMBIGUITY' if ambiguous else 'VERIFIED',
                'permission_result': 'NOT_EVALUABLE' if ambiguous else expected['resolution']['permission_result'],
                'resolution': expected['resolution'],
                **({'governance_binding': expected['governance_binding']} if bound_event else {})}
    except FileNotFoundError:
        return failure('INSUFFICIENT_EVIDENCE', 'Required preserved evidence is missing')
    except (OSError, ValueError, TypeError, KeyError, AttributeError, jsonschema.ValidationError):
        return failure('EVIDENCE_DEFECT', 'Invalid or unverifiable evidence; no current-state fallback')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    assess = sub.add_parser('assess', help='Build an assertion from a query and preserved evidence references')
    assess.add_argument('request', help='JSON with query, authority_revision and delegation_revision')
    replay = sub.add_parser('reconstruct', help='Verify a saved M5 assertion')
    replay.add_argument('assertion')
    for command in (assess, replay):
        command.add_argument('--history-directory', required=True)
        command.add_argument('--governance-event', help='Optional original M4 governance event JSON')
    args = parser.parse_args()
    try:
        event = json.loads(Path(args.governance_event).read_text()) if args.governance_event else None
        if args.command == 'assess':
            request = json.loads(Path(args.request).read_text())
            result = create_assertion(request['query'], authority_reference=request['authority_revision'],
                    delegation_reference=request['delegation_revision'], history_directory=args.history_directory,
                    governance_event=event)
        else:
            result = reconstruct_delegation(json.loads(Path(args.assertion).read_text()), args.history_directory,
                                            governance_event=event)
    except FileNotFoundError:
        result = {'status': 'INSUFFICIENT_EVIDENCE', 'permission_result': 'NOT_EVALUABLE'}
    except (OSError, ValueError, TypeError, KeyError, AttributeError, jsonschema.ValidationError):
        result = {'status': 'EVIDENCE_DEFECT', 'permission_result': 'NOT_EVALUABLE'}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
