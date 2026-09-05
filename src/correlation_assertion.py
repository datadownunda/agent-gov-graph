"""Reviewable evidentiary assertions; no control-effectiveness interpretation."""

import argparse
import copy
import json
from pathlib import Path

import jsonschema

from src.evidence_correlation import correlate
from src.evidence_digest import evidence_digest
from src.foreign_opa_evidence import FIELDS, ingest_journal, ingest_opa


SCHEMA = Path(__file__).resolve().parents[1] / "schemas/correlation_assertion.schema.json"
VERSION = "1.0"


def validate_assertion(assertion):
    jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text())).validate(assertion)
    refs = {(r["source"], r["evidence_ref"]) for r in assertion["source_evidence"]}
    if len(refs) != len(assertion["source_evidence"]):
        raise ValueError("duplicate source-qualified evidence references")
    population_refs = set()
    for population in assertion["candidate_population"]["sources"]:
        if population["count"] != len(population["evidence_refs"]):
            raise ValueError("population count does not agree with its references")
        population_refs.update((population["source"], ref) for ref in population["evidence_refs"])
    if population_refs != refs:
        raise ValueError("population and supplied evidence references disagree")
    referenced = [assertion["focus"], *assertion["result"]["linked_evidence"]]
    for candidate in assertion["competing_candidates"]:
        referenced.extend([candidate, *candidate["reverse_candidate_refs"]])
    if any((r["source"], r["evidence_ref"]) not in refs for r in referenced):
        raise ValueError("unresolved assertion evidence reference")
    if assertion["candidate_population"]["snapshot_digest"] != evidence_digest(assertion["source_evidence"]):
        raise ValueError("population snapshot digest does not agree with evidence")
    body = {key: value for key, value in assertion.items() if key != "assertion_id"}
    if assertion["assertion_id"] != evidence_digest(body):
        raise ValueError("assertion content does not agree with assertion_id")


def _get(record, path):
    value = record
    for part in path.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def _records(records):
    result = {}
    for record in records:
        ref = record.get("evidence_ref")
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError("source evidence requires a nonblank evidence_ref")
        stable = {key: value for key, value in record.items() if key != "ingested_at"}
        if ref in result and result[ref] != stable:
            raise ValueError("conflicting evidence under the same source reference")
        result[ref] = copy.deepcopy(stable)
    return result


def _coverage(declared):
    if declared is None:
        return {"completeness": "UNKNOWN", "basis": "Only supplied evidence is available; completeness is not verified.",
                "interval_start": None, "interval_end": None}
    return copy.deepcopy(declared)


def _assemble(populations, findings, *, relationship_type, method, signals, time,
              rule, coverage, limitations):
    sources = list(populations)
    lookup = {(r["source"], r["evidence_ref"]): r for r in findings}
    evidence = []
    for source, records in populations.items():
        for ref, record in sorted(records.items()):
            evidence.append({"source": source, "evidence_ref": ref,
                             "content_digest": evidence_digest(record),
                             "location": copy.deepcopy(record.get("location")),
                             "observed_signals": {s["field"]: _get(record, s["field"]) for s in signals}})
    population = {"scope": "SUPPLIED_SNAPSHOT_ONLY", "sources": [
        {"source": source, "count": len(records), "evidence_refs": sorted(records)}
        for source, records in populations.items()], "snapshot_digest": evidence_digest(evidence)}
    assertions = []
    for finding in findings:
        source = finding["source"]
        other = next(s for s in sources if s != source)
        candidates = [{"source": other, "evidence_ref": ref,
                       "reverse_candidate_refs": [
                           {"source": source, "evidence_ref": reverse}
                           for reverse in lookup[(other, ref)]["candidate_refs"]]}
                      for ref in finding["candidate_refs"]]
        mapped = {"MATCHED": "LINKED", "EVIDENCE_DEFECT": "INSUFFICIENT_EVIDENCE"}
        state = mapped.get(finding["state"], finding["state"])
        reasons = {
            "LINKED": "Mutually unique candidate under the declared rule; conditional linkage, not proven identity.",
            "AMBIGUOUS": "Candidate competition exists on one or both sides.",
            "UNMATCHED": "No candidate satisfies this rule within the supplied snapshot.",
            "CONTRADICTED": "Native identifier candidate violates an explicitly required equality invariant.",
            "INSUFFICIENT_EVIDENCE": "Required evidence is missing or malformed; linkage cannot be evaluated.",
        }
        assertion = {
            "schema_version": VERSION, "relationship_type": relationship_type,
            "correlation_method": method,
            "focus": {"source": source, "evidence_ref": finding["evidence_ref"]},
            "source_evidence": evidence, "signals_used": signals,
            "candidate_population": population, "competing_candidates": candidates,
            "result": {"state": state, "reason": reasons[state],
                       "linked_evidence": [{"source": other, "evidence_ref": finding["candidate_refs"][0]}]
                       if state == "LINKED" else [],
                       "defects": finding.get("defects", []), "conflicts": finding.get("conflicts", [])},
            "evidence_coverage": _coverage(coverage), "time_assumptions": time,
            "rule": rule, "limitations": limitations,
            "method_output": copy.deepcopy(finding),
        }
        assertion["assertion_id"] = evidence_digest(assertion)
        validate_assertion(assertion)
        assertions.append(copy.deepcopy(assertion))
    return assertions


def composite_assertions(opa_records, journal_records, *, window_seconds,
                         relationship_type="REQUEST_DECISION_ASSOCIATION", coverage=None):
    populations = {"opa": _records(opa_records), "journal": _records(journal_records)}
    findings = correlate(list(populations["opa"].values()), list(populations["journal"].values()),
                         window_seconds=window_seconds)
    signals = [{"field": field, "operator": "EXACT_EQUALITY", "role": "CANDIDATE_SELECTION"} for field in FIELDS]
    signals.append({"field": "observed_at", "operator": "ABSOLUTE_TIME_WINDOW", "role": "CANDIDATE_SELECTION"})
    return _assemble(populations, findings, relationship_type=relationship_type,
                     method="EXACT_COMPOSITE_LINKAGE", signals=signals, coverage=coverage,
                     time={"used_for_matching": True, "window_seconds": str(window_seconds),
                           "boundary": "INCLUSIVE_ABSOLUTE_DIFFERENCE", "timestamp_field": "observed_at",
                           "clock_skew_verified": False, "offset_applied_ns": 0,
                           "assumptions": ["OPA decision time and request observation time are comparable.",
                                           "The window must accommodate latency and clock offset; neither is independently verified."]},
                     rule={"name": "exact-fields-mutually-unique-time-window-v1", "version": "1",
                           "assertion_adapter_version": VERSION, "parameters": {"window_seconds": str(window_seconds)}},
                     limitations=["Evidence coverage is a caller declaration, not a completeness check.",
                                  "Mutual uniqueness does not exclude missing originals or plausible impostors.",
                                  "Hashes identify supplied content; they do not authenticate provenance.",
                                  "No execution or control-effectiveness conclusion is implied."])


def native_assertions(left_records, right_records, *, identifier_field, namespace, issuer,
                      relationship_type="SAME_POLICY_EVALUATION", required_equal_fields=(), coverage=None):
    """Link existing issuer-native IDs in a caller-declared common namespace.

    This function never creates or supplies identifiers to source systems.
    Extra invariants are explicit checks after native candidate selection.
    """
    if any(not isinstance(value, str) or not value.strip() for value in (identifier_field, namespace, issuer)):
        raise ValueError("native identifier field, namespace, and issuer must be explicitly declared")
    if any(not isinstance(field, str) or not field.strip() for field in required_equal_fields):
        raise ValueError("invariant fields must be nonblank paths")
    populations = {"left": _records(left_records), "right": _records(right_records)}
    candidates = {side: {} for side in populations}
    for side, records in populations.items():
        other = "right" if side == "left" else "left"
        for ref, record in records.items():
            value = _get(record, identifier_field)
            candidates[side][ref] = sorted(r for r, candidate in populations[other].items()
                                            if isinstance(value, str) and value.strip()
                                            and value == _get(candidate, identifier_field))
    findings = []
    for side, records in populations.items():
        other = "right" if side == "left" else "left"
        for ref, record in sorted(records.items()):
            refs, defects, conflicts = candidates[side][ref], [], []
            value = _get(record, identifier_field)
            if not isinstance(value, str) or not value.strip():
                state = "INSUFFICIENT_EVIDENCE"
                defects.append("Missing or invalid native identifier")
            elif not refs:
                state = "UNMATCHED"
            elif len(refs) != 1 or len(candidates[other][refs[0]]) != 1:
                state = "AMBIGUOUS"
            else:
                candidate = populations[other][refs[0]]
                for field in required_equal_fields:
                    a, b = _get(record, field), _get(candidate, field)
                    if a is None or b is None or a == "" or b == "":
                        defects.append(f"Missing required invariant: {field}")
                    elif a != b:
                        conflicts.append({"field": field, "focus_value": a, "candidate_value": b})
                state = "CONTRADICTED" if conflicts else "INSUFFICIENT_EVIDENCE" if defects else "LINKED"
            findings.append({"source": side, "evidence_ref": ref, "state": state,
                             "candidate_refs": refs, "defects": defects, "conflicts": conflicts})
    signals = [{"field": identifier_field, "operator": "EXACT_EQUALITY", "role": "CANDIDATE_SELECTION"}]
    signals += [{"field": f, "operator": "EXACT_EQUALITY", "role": "REQUIRED_INVARIANT"} for f in required_equal_fields]
    return _assemble(populations, findings, relationship_type=relationship_type,
                     method="NATIVE_IDENTIFIER_LINKAGE", signals=signals, coverage=coverage,
                     time={"used_for_matching": False, "window_seconds": None, "boundary": "NOT_APPLIED",
                           "timestamp_field": None, "clock_skew_verified": False, "offset_applied_ns": 0,
                           "assumptions": ["No time constraint is applied; identifier scope and non-reuse are caller assumptions."]},
                     rule={"name": "native-identifier-mutual-uniqueness", "version": "1",
                           "assertion_adapter_version": VERSION,
                           "parameters": {"identifier_field": identifier_field, "namespace": namespace,
                                          "issuer": issuer, "required_equal_fields": list(required_equal_fields)}},
                     limitations=["Issuer, shared namespace, and identifier non-reuse are declared, not authenticated.",
                                  "An identifier value may be copied, reused, or incorrectly recorded.",
                                  "Contradiction refers to declared invariants; it does not independently establish causal truth.",
                                  "Population is limited to supplied evidence; omitted duplicates may change linkage.",
                                  "No execution or control-effectiveness conclusion is implied."])


def main():
    parser = argparse.ArgumentParser(description="Emit composite assertions from existing foreign evidence")
    parser.add_argument("--opa-log", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--window-seconds", required=True)
    args = parser.parse_args()
    print(json.dumps(composite_assertions(ingest_opa(args.opa_log), ingest_journal(args.journal),
                                         window_seconds=args.window_seconds), indent=2))


if __name__ == "__main__":
    main()
