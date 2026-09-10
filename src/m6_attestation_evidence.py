"""M7 read-only verification adapter for the preserved complaint M6 archive format.

The adapter reuses M6 replay. It neither discovers links nor changes M6 results.
The returned receipt is a local content-identified computation, not a signature.
"""

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
import logging
from pathlib import Path

import jsonschema

from experiments.target_outcome.run_experiment import audit, derive
from src.authority_resolver import instant, TIMESTAMP
from src.evidence_digest import evidence_digest
from src.evidence_errors import (
    EvidenceValidationError,
    EvidenceUnavailableError,
    InternalProcessingError,
)

RULE = "m6-attestation-verification/1"
LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]


FACT_FIELDS = {
    "governance",
    "reconciliation_result",
    "consistent_with_blocking",
    "target_contract_verified",
    "prohibited_effect_established",
    "relevant_correlation_ambiguous",
    "undermining_uncertainty",
    "supporting_effect_refs",
    "supporting_correlation_refs",
    "source_refs",
}


def _validate_receipt_structure(receipt):
    """Check supplied structure before computations can assume its shape."""
    required = {"receipt_id", "control_digest", "rule_version", "status", "basis_codes"}
    if not isinstance(receipt, dict) or not required <= receipt.keys():
        raise EvidenceValidationError("Incomplete verification receipt")
    if not isinstance(receipt["basis_codes"], list) or not all(
        isinstance(code, str) for code in receipt["basis_codes"]
    ):
        raise EvidenceValidationError("Invalid receipt basis")
    if receipt["status"] == "INTERNAL_ERROR":
        if (
            receipt.get("schema_version") != "1.1"
            or receipt.get("facts") is not None
            or receipt.get("coverage_assessment") is not None
        ):
            raise EvidenceValidationError("Invalid internal verification receipt")


def _validate_verified_facts(receipt):
    facts = receipt.get("facts")
    if not isinstance(facts, dict) or set(facts) != FACT_FIELDS:
        raise EvidenceValidationError("Non-allowlisted adjudication input")
    governance = facts["governance"]
    if not isinstance(governance, dict) or set(governance) != {
        "evidence_ref",
        "decision",
        "actor",
        "action",
        "resource_id",
        "resource_type",
        "observed_at",
    }:
        raise EvidenceValidationError("Non-allowlisted governance facts")
    for key in ("source_refs", "supporting_effect_refs", "supporting_correlation_refs"):
        if not isinstance(facts[key], list) or not all(
            isinstance(ref, str) for ref in facts[key]
        ):
            raise EvidenceValidationError("Invalid evidence references")
    for key in (
        "consistent_with_blocking",
        "target_contract_verified",
        "prohibited_effect_established",
        "relevant_correlation_ambiguous",
        "undermining_uncertainty",
    ):
        if type(facts[key]) is not bool:
            raise EvidenceValidationError("Invalid fact type")
    assessment = receipt.get("coverage_assessment")
    if (
        not isinstance(assessment, dict)
        or not {"control_digest", "result", "interval", "basis_codes"}
        <= assessment.keys()
    ):
        raise EvidenceValidationError("Incomplete coverage assessment")
    if assessment["result"] not in ("ADEQUATE", "INADEQUATE", "UNKNOWN"):
        raise EvidenceValidationError("Invalid coverage assessment")
    if not isinstance(assessment["basis_codes"], list) or not all(
        isinstance(code, str) for code in assessment["basis_codes"]
    ):
        raise EvidenceValidationError("Invalid coverage basis")


def validate_control(control):
    schema = json.loads((ROOT / "schemas/control_definition.schema.json").read_text())
    if (
        next(jsonschema.Draft202012Validator(schema).iter_errors(control), None)
        is not None
    ):
        raise EvidenceValidationError("Invalid supplied control")
    seconds = Decimal(control["coverage_requirement"]["post_decision_seconds"])
    if not seconds.is_finite() or seconds <= 0:
        raise EvidenceValidationError("Invalid bounded observation horizon")


def _file_digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _member(root, name):
    path = (root / name).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise EvidenceValidationError("Evidence member escapes archive") from error
    return path


def _field(value, key):
    if not isinstance(value, dict) or key not in value:
        raise EvidenceValidationError("Incomplete supplied evidence")
    return value[key]


def _coverage_instant(value):
    if (
        not isinstance(value, str)
        or not TIMESTAMP.fullmatch(value)
        or not jsonschema.FormatChecker().conforms(value, "date-time")
    ):
        raise EvidenceValidationError("Malformed supplied coverage timestamp")
    return instant(value)


def _clock_offset(value):
    # Restrict the expected failure boundary to parsing the supplied scalar.
    # Arithmetic using that value is performed outside this boundary.
    if not isinstance(value, (str, int, float, Decimal)):
        raise EvidenceValidationError("Malformed supplied clock bound")
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise EvidenceValidationError("Malformed supplied clock bound") from error


def _read_bytes(path):
    try:
        return path.read_bytes()
    except FileNotFoundError as error:
        raise EvidenceUnavailableError("Referenced evidence unavailable") from error
    except OSError as error:
        raise EvidenceValidationError("Referenced evidence unreadable") from error


def _read_json(path):
    payload = _read_bytes(path)
    try:
        return json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise EvidenceValidationError("Malformed supplied JSON evidence") from error


def _evidence_file_digest(path):
    payload = _read_bytes(path)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_manifest(manifest):
    files = _field(manifest, "files")
    if not isinstance(files, dict) or not all(
        isinstance(name, str) and isinstance(digest, str)
        for name, digest in files.items()
    ):
        raise EvidenceValidationError("Malformed supplied evidence inventory")


def _validate_archive_inputs(root):
    """Validate supplied adapter declarations before asking M6 to process them.

    This is input validation, not a second reconciliation or correlation path.
    Schema loading and validator failures are internal; returned input errors
    establish malformed supplied evidence.
    """
    target = _read_json(root / "target.json")
    resources = _field(target, "resources")
    if not isinstance(resources, dict) or not all(
        isinstance(resource, dict) for resource in resources.values()
    ):
        raise EvidenceValidationError("Malformed target resource mapping")
    _field(target, "identity_namespace")
    _field(_read_json(root / "target_runtime.json"), "config_digest")
    for member, expected_type in (
        ("identity_mapping.json", dict),
        ("correlations.json", list),
        ("reconciliation.json", dict),
    ):
        if not isinstance(_read_json(root / member), expected_type):
            raise EvidenceValidationError("Malformed supplied M6 archive member")
    coverage = _read_json(root / "blocked_coverage.json")
    schema = json.loads((ROOT / "schemas/observation_coverage.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    if next(validator.iter_errors(coverage), None) is not None:
        raise EvidenceValidationError("Malformed supplied observation coverage")


def _internal_receipt():
    # Never reuse a partly populated receipt after a processing failure.
    receipt = {
        "schema_version": "1.1",
        "rule_version": RULE,
        "status": "INTERNAL_ERROR",
        "control_digest": None,
        "reconciliation_ref": None,
        "archive_digest": None,
        "facts": None,
        "coverage_assessment": None,
        "basis_codes": ["M6_VERIFICATION_INTERNAL_ERROR"],
        "dependency_refs": [],
        "limitations": [
            "Agent Gov Graph failed to complete verification; no evidentiary or coverage conclusion."
        ],
    }
    receipt["receipt_id"] = evidence_digest(receipt)
    _validate_receipt_structure(receipt)
    body = {key: value for key, value in receipt.items() if key != "receipt_id"}
    if receipt["receipt_id"] != evidence_digest(body):
        raise InternalProcessingError("Internal verification receipt identity mismatch")
    return receipt


def verify_m6(archive, assertion_id, control, *, coverage_support=None):
    try:
        return _verify_m6(
            archive, assertion_id, control, coverage_support=coverage_support
        )
    except Exception:
        LOGGER.exception("M7 evidence verification processing failed")
        try:
            return _internal_receipt()
        except Exception as error:
            raise InternalProcessingError(
                "Cannot construct internal-error verification receipt"
            ) from error


def _coverage(control, assertion, support, contract_digest):
    """Specific to DENY preventing representation serving at this static target."""
    coverage = assertion["evidence_coverage"]
    assessment = {
        "control_digest": evidence_digest(control),
        "result": "UNKNOWN",
        "basis_codes": [],
        "interval": None,
        "support_ref": evidence_digest(support) if support else None,
        "coverage_ref": evidence_digest(coverage) if coverage else None,
    }
    codes = assessment["basis_codes"]
    if not coverage:
        codes.append("TARGET_COVERAGE_UNKNOWN")
        return assessment
    assessment["interval"] = {
        "start": coverage["interval_start"],
        "end": coverage["interval_end"],
    }
    g = assertion["claims"]["governance"][0]
    inadequate = False
    try:
        start, end, decision = (
            _coverage_instant(_field(coverage, "interval_start")),
            _coverage_instant(_field(coverage, "interval_end")),
            _coverage_instant(g["observed_at"]),
        )
        horizon = Decimal(control["coverage_requirement"]["post_decision_seconds"])
        if start > decision or end < decision + horizon:
            codes.append("CONTROL_OBSERVATION_HORIZON_INADEQUATE")
            inadequate = True
        if coverage["roles"].get("outcome") != "CAPTURED":
            codes.append("TARGET_CAPTURE_UNAVAILABLE")
            inadequate = True
        if coverage["scope"] != {
            key: g[key] for key in ("actor", "action", "resource_id", "resource_type")
        }:
            codes.append("CONTROL_SCOPE_MISMATCH")
            inadequate = True
        if not support:
            codes.extend(
                [
                    "CAPTURE_FINALIZATION_NOT_SUBSTANTIATED",
                    "CLOCK_ASSUMPTIONS_NOT_SUBSTANTIATED",
                ]
            )
        else:
            expected = {
                "action": g["action"],
                "resource_id": g["resource_id"],
                "resource_type": g["resource_type"],
            }
            if (
                _field(support, "control_digest") != evidence_digest(control)
                or _field(support, "reconciliation_ref") != assertion["assertion_id"]
                or _field(support, "target_contract_digest") != contract_digest
                or _field(support, "target_id")
                != control["prohibited_target_effect"]["target_id"]
                or _field(support, "scope") != expected
                or _field(support, "identity_scope") != "ALL_TARGET_IDENTITIES"
            ):
                codes.append("CONTROL_COVERAGE_BINDING_MISMATCH")
                inadequate = True
            offset = _clock_offset(
                _field(_field(support, "clocks"), "maximum_offset_seconds")
            )
            if (
                not offset.is_finite()
                or offset < 0
                or not _field(_field(support, "clocks"), "basis")
            ):
                raise EvidenceValidationError("Unsubstantiated clock bound")
            capture = _field(support, "capture")
            # Bounds apply to capture, including possible clock offset. No timestamp
            # adjustment is supplied to a correlator or to M6.
            if (
                _field(capture, "available") is not True
                or _field(capture, "finalized") is not True
                or _coverage_instant(_field(capture, "from")) > start - offset
                or _coverage_instant(_field(capture, "through")) < end + offset
                or _coverage_instant(_field(capture, "finalized_at"))
                < _coverage_instant(_field(capture, "through"))
            ):
                codes.append("TARGET_CAPTURE_INTERVAL_OR_FINALIZATION_INADEQUATE")
                inadequate = True
            if (
                _field(support, "unresolved_gaps") is not False
                or _field(support, "candidate_ambiguity") is not False
            ):
                codes.append("UNRESOLVED_OBSERVATION_GAPS_OR_CANDIDATES")
                inadequate = True
            if not codes:
                codes.append("BOUNDED_TARGET_COVERAGE_ADEQUATE")
                assessment["result"] = "ADEQUATE"
    except EvidenceValidationError:
        codes.append("CONTROL_COVERAGE_SUPPORT_INSUFFICIENT")
    if inadequate:
        assessment["result"] = "INADEQUATE"
    assessment["basis_codes"] = sorted(set(codes))
    return assessment


def _project(assertion, control, target, target_verified):
    """Only allowlisted M6 fields. No raw data, run IDs, filenames or prose labels."""
    governors = assertion["claims"]["governance"]
    if len(governors) != 1:
        raise EvidenceValidationError("Exactly one governed action is required")
    g = governors[0]
    governance = {
        key: deepcopy(g[key])
        for key in (
            "evidence_ref",
            "actor",
            "action",
            "resource_id",
            "resource_type",
            "observed_at",
        )
    }
    governance["decision"] = g["governance_decision"]
    connected = {
        g["evidence_ref"],
        *[p["evidence_ref"] for p in assertion["correlation_paths"]],
    }
    ambiguous = any(
        a["focus"]["evidence_ref"] in connected
        and a["result"]["state"]
        in ("AMBIGUOUS", "CONTRADICTED", "INSUFFICIENT_EVIDENCE")
        for a in assertion["correlation_assertions"]
    )
    linked_ids = {
        a["assertion_id"]
        for a in assertion["correlation_assertions"]
        if a["result"]["state"] == "LINKED"
    }
    paths = {
        p["evidence_ref"]: p["assertion_ids"] for p in assertion["correlation_paths"]
    }
    effect_refs, correlation_refs = [], set()
    for outcome in assertion["claims"]["outcome"]:
        path = paths.get(outcome["evidence_ref"], [])
        if (
            outcome.get("target_outcome") == "REPRESENTATION_SERVED"
            and all(
                outcome.get(f) == g.get(f)
                for f in ("action", "resource_id", "resource_type")
            )
            and outcome.get("target_contract_digest") == evidence_digest(target)
            and path
            and set(path) <= linked_ids
            and not outcome.get("defects")
        ):
            effect_refs.append(outcome["evidence_ref"])
            correlation_refs.update(path)
    benign_absence = {
        "CONSISTENT_WITH_BLOCKING",
        "CORRELATION_UNMATCHED",
        "EXECUTION_EVIDENCE_MISSING",
        "OUTCOME_EVIDENCE_MISSING",
    }
    uncertainty = assertion["result"] != "CONSISTENT" or bool(
        set(assertion["issue_codes"]) - benign_absence
    )
    return {
        "governance": governance,
        "reconciliation_result": assertion["result"],
        "consistent_with_blocking": "CONSISTENT_WITH_BLOCKING"
        in assertion["issue_codes"],
        "target_contract_verified": target_verified,
        "prohibited_effect_established": bool(effect_refs),
        "relevant_correlation_ambiguous": ambiguous,
        "undermining_uncertainty": uncertainty,
        "supporting_effect_refs": sorted(effect_refs),
        "supporting_correlation_refs": sorted(correlation_refs),
        "source_refs": sorted(r["evidence_ref"] for r in assertion["source_evidence"]),
    }


def _verify_m6(archive, assertion_id, control, *, coverage_support=None):
    """Verify a stored assertion by opaque ID against the unchanged M6 adapter.

    coverage_support is an optional archive member containing affirmative,
    control-specific observations; it is never an instruction to mark adequate.
    The archive layout is intentionally limited to the existing complaint M6
    format. Unavailable or unsupported evidence is not guessed into a new path.
    """
    receipt = {
        "schema_version": "1.0",
        "rule_version": RULE,
        "status": "EVIDENCE_DEFECT",
        "control_digest": evidence_digest(control),
        "reconciliation_ref": assertion_id,
        "archive_digest": None,
        "facts": None,
        "coverage_assessment": None,
        "basis_codes": [],
        "dependency_refs": [],
        "limitations": [
            "Archive and receipt digests identify content; they do not authenticate producers.",
            "Coverage observations remain evidence subject to their stated provenance and clock assumptions.",
        ],
    }
    try:
        validate_control(control)
        root = Path(archive).resolve()
        manifest = _read_json(root / "manifest.json")
        receipt["archive_digest"] = evidence_digest(manifest)
        _validate_manifest(manifest)
        # Precheck failures without disclosing file/scenario labels to adjudication.
        for member, digest in manifest["files"].items():
            if _evidence_file_digest(_member(root, member)) != digest:
                raise EvidenceValidationError("Archive integrity defect")
        _validate_archive_inputs(root)
        audit(root)  # Existing M6 source ingestion, correlation and reconstruction.
        _, _, replayed = derive(root)
        matches = [a for a in replayed.values() if a["assertion_id"] == assertion_id]
        if len(matches) != 1:
            raise EvidenceValidationError(
                "Stored assertion is missing or not uniquely replayable"
            )
        assertion = matches[0]
        body = {k: v for k, v in assertion.items() if k != "assertion_id"}
        if evidence_digest(body) != assertion_id:
            raise InternalProcessingError("Generated M6 content identity mismatch")
        target = _read_json(root / "target.json")
        runtime = _read_json(root / "target_runtime.json")
        # The interpretation is pinned to the inspected M6 static target config.
        known_config = ROOT / "experiments/target_outcome/nginx.conf"
        target_verified = (
            target.get("target_id") == control["prohibited_target_effect"]["target_id"]
            and evidence_digest(target)
            == control["prohibited_target_effect"]["target_contract_digest"]
            and _field(runtime, "config_digest")
            == _evidence_file_digest(root / "nginx.conf")
            == _file_digest(known_config)
            and target.get("basic_auth_required") is True
        )
        support = None
        if coverage_support is not None:
            if coverage_support not in manifest["files"]:
                raise EvidenceValidationError("Coverage support is not preserved")
            support = _read_json(_member(root, coverage_support))
            if _field(_field(support, "capture"), "native_file_digest") != _field(
                manifest["files"], "native/access.jsonl"
            ):
                raise EvidenceValidationError(
                    "Coverage describes a different target snapshot"
                )
        facts = _project(assertion, control, target, target_verified)
        assessment = _coverage(control, assertion, support, evidence_digest(target))
        receipt.update(
            status="VERIFIED",
            facts=facts,
            coverage_assessment=assessment,
            dependency_refs=sorted(set(manifest["files"].values())),
        )
    except EvidenceUnavailableError:
        receipt.update(
            status="INSUFFICIENT_EVIDENCE",
            basis_codes=["REFERENCED_EVIDENCE_UNAVAILABLE"],
        )
    except EvidenceValidationError:
        receipt.update(
            status="EVIDENCE_DEFECT",
            basis_codes=["REFERENCED_EVIDENCE_OR_CONTROL_INTEGRITY_DEFECT"],
        )
    receipt["receipt_id"] = evidence_digest(receipt)
    _validate_receipt_structure(receipt)
    if receipt["status"] == "VERIFIED":
        _validate_verified_facts(receipt)
    return receipt
