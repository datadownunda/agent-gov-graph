"""Standalone synthetic workload. Operator redirects stderr to native evidence."""

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def produce(journal_path, policy_dir, *, count=3, interval_seconds=0):
    if count < 1 or interval_seconds < 0:
        raise ValueError("count must be positive and interval nonnegative")
    # Exclusive creation prevents accidental replacement of an earlier journal.
    with Path(journal_path).open("x", encoding="utf-8") as journal:
        for index in range(count):
            policy_input = {"user": {"id": "synthetic-requester", "roles": ["hr_investigator"]},
                            "action": "read", "authorized_resource_ids": ["complaint-456"],
                            "resource": {"id": "complaint-456", "type": "employee_complaint",
                                         "classification": "restricted"}}
            journal.write(json.dumps({"actor": policy_input["user"]["id"],
                                      "action": policy_input["action"],
                                      "resource_id": policy_input["resource"]["id"],
                                      "resource_type": policy_input["resource"]["type"],
                                      "observed_at": datetime.now(timezone.utc).isoformat()}) + "\n")
            journal.flush()
            # Inherited stderr goes straight to the operator's descriptor. Neither
            # OPA's result nor its native log is parsed, captured, or rewritten here.
            subprocess.run(["docker", "run", "--rm", "-i", "-v",
                            f"{Path(policy_dir).resolve()}:/policies:ro",
                            "openpolicyagent/opa:1.19.0", "exec", "--bundle", "/policies",
                            "--decision", "/agentgov/complaints/decision", "--stdin-input",
                            "--set=decision_logs.console=true", "--log-format=json"],
                           input=json.dumps(policy_input), text=True, stdout=subprocess.DEVNULL,
                           check=True)
            if index + 1 < count:
                time.sleep(interval_seconds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--policy-dir", required=True)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--interval-seconds", type=float, default=0)
    args = parser.parse_args()
    produce(args.journal, args.policy_dir, count=args.count, interval_seconds=args.interval_seconds)


if __name__ == "__main__":
    main()
