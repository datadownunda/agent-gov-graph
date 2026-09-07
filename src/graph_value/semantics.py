"""M4/M5 remain the authority. Shared cost is disclosed, not credited to graph."""
from src.delegation_resolver import resolve_delegation, tuples
from src.authority_resolver import instant
from src.graph_value.results import ref_key


class AuthoritySemantics:
    def __init__(self, contexts):
        self.contexts = contexts
        self.cache = {}

    def assess(self, context, actor, requested, at):
        instant(at)
        key = (context, actor, tuple(requested), at)
        if key not in self.cache:
            pair = self.contexts[context]
            self.cache[key] = resolve_delegation(
                dict(actor=actor, action=requested[0], resource_type=requested[1],
                     resource_id=requested[2], effective_at=at),
                authority_revision=pair['authority'], delegation_records=pair['delegations'])
        return self.cache[key]

    def requested_tuples(self, context, requested):
        if requested is not None:
            if len(requested) != 3 or not all(isinstance(x, str) and x for x in requested):
                raise ValueError('Explicit nonempty action/resource tuple required')
            return [tuple(requested)]
        pair = self.contexts[context]
        values = set()
        for record in pair['authority']['records'] + pair['delegations']:
            if isinstance(record, dict):
                try:
                    values.update(tuples(record.get('permitted_scopes', record.get('delegated_scopes', []))))
                except (TypeError, KeyError):
                    pass  # Resolver retains malformed records as evidence issues.
        return sorted(values)

    def resolve_ref(self, context, selected):
        ref_key(selected)
        pair = self.contexts[context]
        records = pair['authority']['records'] if selected['kind'] == 'authority' else pair['delegations']
        prefix, version = ('authority_record_id', 'authority_version') if selected['kind'] == 'authority' else ('delegation_id', 'delegation_version')
        if selected['kind'] not in ('authority', 'delegation'):
            raise ValueError('Invalid relationship kind')
        return [r for r in records if isinstance(r, dict) and
                r.get(prefix) == selected['record_id'] and r.get(version) == selected['version']]
