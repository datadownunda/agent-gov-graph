"""M9a-i decision boundary: observation-only input, no archive or scorer imports."""
import json
import sys

from src.evidence_correlation import correlate

ROLES = ('governance', 'execution', 'outcome')
FIELDS = {'evidence_ref', 'actor', 'action', 'resource_id', 'resource_type', 'observed_at'}
EDGES = (('governance', 'execution'), ('execution', 'outcome'))


def validate_case(case):
    if not isinstance(case, dict) or set(case) != set(ROLES):
        raise ValueError('Non-allowlisted case')
    refs = set()
    for role in ROLES:
        if not isinstance(case[role], list):
            raise ValueError('Population must be a list')
        for record in case[role]:
            if (not isinstance(record, dict) or set(record) != FIELDS
                    or any(type(v) is not str for v in record.values())):
                raise ValueError('Non-allowlisted observation')
            ref = record['evidence_ref']
            if not ref.strip() or ref in refs:
                raise ValueError('References must be unique source-local addresses')
            refs.add(ref)


def decide(case):
    """No labels, truth, eligibility flags, paths or raw records accepted.

    This fixed-corpus gate cannot be opened by a caller. No independent evidence
    of clock bounds and population non-replacement is available in this protocol.
    A future gate would require a separately reviewed protocol, not a boolean.
    """
    validate_case(case)
    edges = {a + '-' + b: correlate(case[a], case[b], window_seconds='1')
             for a, b in EDGES}
    accepted = [{r['evidence_ref']: r['candidate_refs'][0] for r in findings
                 if r['source'] == 'opa' and r['state'] == 'MATCHED'}
                for findings in edges.values()]
    paths = [[g, e, accepted[1][e]] for g, e in sorted(accepted[0].items())
             if e in accepted[1]]
    return {'edges': edges, 'candidate_paths': paths,
            'downstream': [{'governance_ref': g['evidence_ref'], 'status': 'ABSTAIN',
                            'finding': None, 'm6_invoked': False, 'm7_invoked': False,
                            'basis_codes': ['CLOCK_BOUNDS_NOT_SUBSTANTIATED',
                                            'POPULATION_NON_REPLACEMENT_NOT_SUBSTANTIATED']}
                           for g in sorted(case['governance'], key=lambda r: r['evidence_ref'])]}


def main():
    payload = json.load(sys.stdin)
    if not isinstance(payload, list):
        raise ValueError('Expected unlabelled case list')
    print(json.dumps([decide(case) for case in payload], sort_keys=True))


if __name__ == '__main__':
    main()
