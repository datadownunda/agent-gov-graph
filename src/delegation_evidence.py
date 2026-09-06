"""Preserve complete delegation evidence without repairing rejected records.

Envelope integrity is mandatory. Individual link defects are assessed by the
resolver so unrelated valid paths are not discarded with a malformed link.
"""
import hashlib
import json
import re
from pathlib import Path

import jsonschema

from src.authority_resolver import PROJECT_ROOT, revision_bytes


def schema():
    return json.loads((PROJECT_ROOT / 'schemas/delegation_registry.schema.json').read_text())


def validate_delegation_revision(revision):
    jsonschema.validate(revision, schema(), format_checker=jsonschema.FormatChecker())


def preserve_delegation_revision(revision, directory):
    validate_delegation_revision(revision)
    payload = revision_bytes(revision)
    digest = hashlib.sha256(payload).hexdigest()
    path = Path(directory) / (digest + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError('Delegation revision digest mismatch; refusing overwrite')
    return {'file': path.name, 'digest': 'sha256:' + digest,
            'source_id': revision['source_id'], 'source_version': revision['source_version']}


def load_delegation_revision(reference, directory):
    digest = reference.get('digest', '')
    if not isinstance(digest, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise ValueError('Invalid delegation revision digest')
    if reference.get('file') != digest[7:] + '.json':
        raise ValueError('Delegation filename must identify its digest')
    payload = (Path(directory) / reference['file']).read_bytes()
    if 'sha256:' + hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError('Delegation revision digest mismatch')
    revision = json.loads(payload)
    validate_delegation_revision(revision)
    if any(reference.get(k) != revision[k] for k in ('source_id', 'source_version')):
        raise ValueError('Delegation source reference mismatch')
    return revision
