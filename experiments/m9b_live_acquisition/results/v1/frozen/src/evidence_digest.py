import hashlib

import rfc8785


def evidence_digest(value):
    canonical_bytes = rfc8785.dumps(
        value
    )

    digest = hashlib.sha256(
        canonical_bytes
    ).hexdigest()

    return f"sha256:{digest}"