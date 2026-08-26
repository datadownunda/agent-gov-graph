package agentgov.complaints

import rego.v1

default allow := false

has_role(role) if {
    some r in input.user.roles
    r == role
}

allow if {
    input.action == "read"
    input.resource.type == "employee_complaint"
    has_role("hr_investigator")
}
deny contains "Restricted employee complaint data requires HR Investigator role" if {
    input.resource.type == "employee_complaint"
    input.resource.classification == "restricted"
    not has_role("hr_investigator")
}
decision := {
    "allowed": allow,
    "decision": decision_status,
    "reasons": deny,
    "policy": "employee_complaint_access",
    "policy_version": "1.0"
}

decision_status := "ALLOW" if {
    allow
}

decision_status := "DENY" if {
    not allow
}