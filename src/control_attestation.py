"""Fixed single-action control adjudication. No source matching or enforcement."""

from copy import deepcopy
import json
import logging
from pathlib import Path

import jsonschema

from src.evidence_digest import evidence_digest
from src.evidence_errors import EvidenceValidationError, InternalProcessingError
from src.m6_attestation_evidence import (
    validate_control,
    verify_m6,
    _validate_receipt_structure,
    _validate_verified_facts,
)

ROOT = Path(__file__).resolve().parents[1]
RULE = "control-attestation/1"
LOGGER = logging.getLogger(__name__)

LIMITATIONS = [
    "This finding concerns exactly one evaluated reconciliation/action and its declared observation boundary; no population-wide inference.",
    "REPRESENTATION_SERVED means the configured target reports serving representation bytes; it does not establish downstream consumption, interpretation or use.",
    "A target-effect exception is not root-cause attribution and makes no claim about why the effect occurred.",
    "A positive finding is conditional on the specific observation interval, capture evidence and clock bounds, not unlimited future prevention.",
    "Content identity and deterministic replay are not cryptographic provenance authentication.",
]


def validate_attestation(assertion):
    schema = json.loads((ROOT / "schemas/control_attestation.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    if next(validator.iter_errors(assertion), None) is not None:
        raise EvidenceValidationError("Invalid supplied attestation")
    if assertion["assertion_id"] != evidence_digest(
        {k: v for k, v in assertion.items() if k != "assertion_id"}
    ):
        raise EvidenceValidationError("Attestation content identity mismatch")


def _internal_attestation():
    """Fresh operational result: no partial facts, coverage conclusion or finding."""
    result = {
        "schema_version": "1.1",
        "rule_version": RULE,
        "control_reference": {"content_digest": None},
        "reconciliation_reference": None,
        "verification_reference": None,
        "scope": {"cardinality": "SINGLE_ACTION"},
        "source_evidence_refs": [],
        "correlation_assertion_refs": [],
        "coverage_assessment": None,
        "evaluation_status": "INTERNAL_ERROR",
        "finding": None,
        "basis_codes": ["ADJUDICATOR_INTERNAL_ERROR"],
        "limitations": [
            "Agent Gov Graph failed to complete processing; no conclusion about evidence, coverage or control effectiveness."
        ],
    }
    result["assertion_id"] = evidence_digest(result)
    validate_attestation(result)
    return result


def adjudicate(control, receipt):
    """Apply the fixed rule; unexpected failures carry no assurance finding."""
    try:
        return _adjudicate(control, receipt)
    except Exception:
        LOGGER.exception("M7 adjudicator processing failed")
        try:
            return _internal_attestation()
        except Exception as error:
            raise InternalProcessingError(
                "Cannot construct internal-error attestation"
            ) from error


def _adjudicate(control, receipt):
    """Pure rule on a locally verified, allowlisted receipt.

    External callers use attest(), which recomputes verification from the archive.
    A receipt hash is not a signature or a substitute for that verification.
    """
    out = {
        "schema_version": "1.0",
        "rule_version": RULE,
        "control_reference": {"content_digest": evidence_digest(control)},
        "reconciliation_reference": (
            receipt.get("reconciliation_ref") if isinstance(receipt, dict) else None
        ),
        "verification_reference": (
            receipt.get("receipt_id") if isinstance(receipt, dict) else None
        ),
        "scope": {"cardinality": "SINGLE_ACTION"},
        "source_evidence_refs": [],
        "correlation_assertion_refs": [],
        "coverage_assessment": (
            deepcopy(receipt.get("coverage_assessment"))
            if isinstance(receipt, dict)
            else None
        ),
        "evaluation_status": "NOT_EVALUABLE",
        "finding": None,
        "basis_codes": [],
        "limitations": list(LIMITATIONS),
    }

    def finish(status, finding, codes):
        # Generated output is a processing boundary, never supplied evidence.
        try:
            result = deepcopy(out)
            result.update(
                evaluation_status=status,
                finding=finding,
                basis_codes=sorted(set(codes)),
            )
            result["assertion_id"] = evidence_digest(result)
            validate_attestation(result)
            return result
        except Exception as error:
            raise InternalProcessingError("Generated attestation failed") from error

    def abstain(codes):
        return finish(
            "INSUFFICIENT_EVIDENCE", "CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED", codes
        )

    try:
        validate_control(control)
        _validate_receipt_structure(receipt)
        if (
            receipt["receipt_id"]
            != evidence_digest({k: v for k, v in receipt.items() if k != "receipt_id"})
            or (
                receipt["status"] != "INTERNAL_ERROR"
                and receipt["control_digest"] != evidence_digest(control)
            )
            or receipt["rule_version"] != "m6-attestation-verification/1"
        ):
            raise EvidenceValidationError("Receipt/control mismatch")
        out["control_reference"].update(
            control_id=control["control_id"], control_version=control["control_version"]
        )
        if receipt["status"] == "INTERNAL_ERROR":
            raise InternalProcessingError("M6 verification could not complete")
        if receipt["status"] == "EVIDENCE_DEFECT":
            return finish(
                "NOT_EVALUABLE",
                None,
                receipt["basis_codes"] or ["EVIDENCE_INTEGRITY_DEFECT"],
            )
        if receipt["status"] == "INSUFFICIENT_EVIDENCE":
            return abstain(receipt["basis_codes"])
        if receipt["status"] != "VERIFIED":
            raise EvidenceValidationError("Invalid verification state")
        _validate_verified_facts(receipt)
        facts = receipt["facts"]
        g = facts["governance"]
        assessment = receipt["coverage_assessment"]
        if assessment["control_digest"] != evidence_digest(control):
            raise EvidenceValidationError("Coverage/control mismatch")
        out["scope"].update(
            {
                k: deepcopy(g[k])
                for k in ("actor", "action", "resource_id", "resource_type")
            }
        )
        out["scope"].update(
            governance_evidence_ref=g["evidence_ref"],
            target_id=control["prohibited_target_effect"]["target_id"],
            observation_interval=deepcopy(assessment["interval"]),
        )
        out["source_evidence_refs"] = deepcopy(facts["source_refs"])
        out["correlation_assertion_refs"] = deepcopy(
            facts["supporting_correlation_refs"]
        )
        outside_control_scope = any(
            g[key] != control["scope"][key] for key in ("action", "resource_type")
        )
        control_not_applicable = g["decision"] == "ALLOW" or outside_control_scope
        if control_not_applicable:
            return finish(
                "NOT_APPLICABLE",
                None,
                ["CONTROL_GOVERNANCE_CONDITION_OR_SCOPE_NOT_APPLICABLE"],
            )
        if g["decision"] != "DENY":
            return abstain(["GOVERNANCE_DENY_NOT_ESTABLISHED"])
        if facts["reconciliation_result"] == "NOT_EVALUABLE":
            return finish("NOT_EVALUABLE", None, ["M6_NOT_EVALUABLE"])
        if not facts["target_contract_verified"]:
            return abstain(["TARGET_OBSERVATION_SEMANTICS_NOT_ESTABLISHED"])
        if facts["relevant_correlation_ambiguous"]:
            return abstain(["REQUIRED_CORRELATION_UNRESOLVED"])
        # Positive observation and negative coverage deliberately have different gates.
        if facts["prohibited_effect_established"]:
            if (
                not facts["supporting_effect_refs"]
                or not facts["supporting_correlation_refs"]
            ):
                return abstain(["TARGET_EFFECT_LINKAGE_NOT_ESTABLISHED"])
            return finish(
                "EVALUATED",
                "CONTROL_EFFECTIVENESS_EXCEPTION",
                ["DENY_ESTABLISHED", "CORRELATED_PROHIBITED_TARGET_EFFECT"],
            )
        positive_coverage_gates_satisfied = (
            assessment["result"] == "ADEQUATE"
            and facts["consistent_with_blocking"]
            and not facts["undermining_uncertainty"]
        )
        if positive_coverage_gates_satisfied:
            return finish(
                "EVALUATED",
                "CONTROL_EFFECTIVE",
                [
                    "DENY_ESTABLISHED",
                    "BOUNDED_TARGET_COVERAGE_ADEQUATE",
                    "NO_PROHIBITED_EFFECT_IN_EVALUATED_OBSERVATIONS",
                ],
            )
        return abstain(
            assessment["basis_codes"] + ["EFFECTIVENESS_GATES_NOT_SATISFIED"]
        )
    except EvidenceValidationError:
        return finish(
            "NOT_EVALUABLE", None, ["INVALID_CONTROL_OR_VERIFICATION_RECEIPT"]
        )


def attest(archive, assertion_id, control, *, coverage_support=None):
    receipt = verify_m6(
        archive, assertion_id, control, coverage_support=coverage_support
    )
    return adjudicate(control, receipt), receipt


def reconstruct_attestation(saved, archive, control, *, coverage_support=None):
    """Replay verified evidence, keeping invalid input separate from replay bugs."""
    try:
        try:
            validate_attestation(saved)
        except EvidenceValidationError:
            return {"status": "EVIDENCE_DEFECT", "basis_codes": ["INVALID_ATTESTATION"]}
        expected, receipt = attest(
            archive,
            saved["reconciliation_reference"],
            control,
            coverage_support=coverage_support,
        )
        if (
            receipt["status"] == "INTERNAL_ERROR"
            or expected["evaluation_status"] == "INTERNAL_ERROR"
        ):
            return {
                "schema_version": "1.1",
                "status": "INTERNAL_ERROR",
                "finding": None,
                "basis_codes": ["ATTESTATION_REPLAY_INTERNAL_ERROR"],
            }
        if receipt["status"] != "VERIFIED":
            return {"status": receipt["status"], "basis_codes": receipt["basis_codes"]}
        if expected != saved:
            return {
                "status": "EVIDENCE_DEFECT",
                "basis_codes": ["ATTESTATION_REPLAY_DISAGREEMENT"],
            }
        return {
            "status": "VERIFIED",
            "evaluation_status": expected["evaluation_status"],
            "finding": expected["finding"],
        }
    except InternalProcessingError:
        # A fresh failure artifact could not be safely built upstream.
        # Preserve the typed failure and its cause; do not manufacture a report.
        raise
    except Exception:
        LOGGER.exception("M7 replay processing failed")
        return {
            "schema_version": "1.1",
            "status": "INTERNAL_ERROR",
            "finding": None,
            "basis_codes": ["ATTESTATION_REPLAY_INTERNAL_ERROR"],
        }
