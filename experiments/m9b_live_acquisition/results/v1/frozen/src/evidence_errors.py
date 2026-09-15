"""Local M7 boundary errors, also used by explicit M6 archive audit rejections.

These types describe why processing stopped, not which Python operation failed.
They must not be used to wrap arbitrary computation or generated-output errors.
"""


class EvidenceValidationError(ValueError):
    """An explicit check rejected supplied evidence or a supplied control."""


class EvidenceUnavailableError(EvidenceValidationError):
    """A read of a referenced evidence file established that it is unavailable."""


class InternalProcessingError(RuntimeError):
    """Agent Gov Graph could not complete processing; no evidentiary inference."""
