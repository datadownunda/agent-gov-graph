"""Deterministic, mutually unique field/time correlation of foreign evidence."""

import argparse
import json
from decimal import Decimal, InvalidOperation

from src.foreign_opa_evidence import FIELDS, correlation_defects, ingest_journal, ingest_opa, timestamp_ns


def _prepare(records):
    prepared = {}
    for record in records:
        ref = record["evidence_ref"]
        normalized = {field: record.get(field) for field in (*FIELDS, "observed_at")}
        normalized["defects"] = correlation_defects(record)
        if ref in prepared and prepared[ref] != normalized:
            raise ValueError("conflicting content for the same evidence reference")
        prepared[ref] = normalized
    return prepared


def correlate(opa_records, journal_records, *, window_seconds):
    try:
        window = Decimal(str(window_seconds))
    except InvalidOperation as error:
        raise ValueError("window must be finite and nonnegative") from error
    if not window.is_finite() or window < 0:
        raise ValueError("window must be finite and nonnegative")
    window_ns = window * 1_000_000_000
    opa, journal = _prepare(opa_records), _prepare(journal_records)
    candidates = {"opa": {ref: [] for ref in opa}, "journal": {ref: [] for ref in journal}}
    deltas = {}
    for left_ref, left in opa.items():
        if left["defects"]:
            continue
        for right_ref, right in journal.items():
            if right["defects"] or any(left[f] != right[f] for f in FIELDS):
                continue
            delta = timestamp_ns(left["observed_at"]) - timestamp_ns(right["observed_at"])
            if abs(delta) <= window_ns:
                candidates["opa"][left_ref].append(right_ref)
                candidates["journal"][right_ref].append(left_ref)
                deltas[(left_ref, right_ref)] = delta
    results = []
    for source, records, other in (("opa", opa, "journal"), ("journal", journal, "opa")):
        for ref, record in sorted(records.items()):
            refs = sorted(candidates[source][ref])
            if record["defects"]:
                state = "EVIDENCE_DEFECT"
            elif not refs:
                state = "UNMATCHED"
            elif len(refs) == 1 and len(candidates[other][refs[0]]) == 1:
                state = "MATCHED"
            else:
                state = "AMBIGUOUS"
            result = {"source": source, "evidence_ref": ref, "state": state,
                      "candidate_refs": refs, "defects": record["defects"],
                      "method": "exact-fields-mutually-unique-time-window-v1",
                      "window_seconds": str(window)}
            if state == "MATCHED":
                pair = (ref, refs[0]) if source == "opa" else (refs[0], ref)
                result["opa_minus_request_ns"] = deltas[pair]
            results.append(result)
    return results


def score_links(results, true_pairs):
    """Evaluator only: ground truth is never passed into correlate()."""
    truth = set(true_pairs)
    accepted = {(r["evidence_ref"], r["candidate_refs"][0]) for r in results
                if r["source"] == "opa" and r["state"] == "MATCHED"}
    correct, false = len(accepted & truth), len(accepted - truth)
    return {"accepted_links": len(accepted), "correct_accepted_links": correct,
            "false_accepted_links": false,
            "false_link_rate": false / len(accepted) if accepted else None,
            "true_pair_recovery": correct / len(truth) if truth else None,
            "record_states": {state: sum(r["state"] == state for r in results)
                              for state in ("MATCHED", "AMBIGUOUS", "UNMATCHED", "EVIDENCE_DEFECT")}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opa-log", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--window-seconds", required=True)
    args = parser.parse_args()
    opa, journal = ingest_opa(args.opa_log), ingest_journal(args.journal)
    findings = correlate(opa, journal, window_seconds=args.window_seconds)
    print(json.dumps({"evidence": opa + journal, "findings": findings}, indent=2))


if __name__ == "__main__":
    main()
