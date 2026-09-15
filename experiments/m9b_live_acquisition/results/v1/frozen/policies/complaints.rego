package agentgov.complaints

import rego.v1

default allow := false

has_role(role) if {
    some r in input.user.roles
    r == role
}
resource_authorized if {
    some resource_id in input.authorized_resource_ids
    resource_id == input.resource.id
}

allow if {
    input.action == "read"
    input.resource.type == "employee_complaint"
    has_role("hr_investigator")
    resource_authorized
}
deny contains "Restricted employee complaint data requires HR Investigator role" if {
    input.resource.type == "employee_complaint"
    input.resource.classification == "restricted"
    not has_role("hr_investigator")
}
deny contains "Requested complaint is outside the authorized workflow scope" if {
    input.action == "read"
    input.resource.type == "employee_complaint"
    has_role("hr_investigator")
    not resource_authorized
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