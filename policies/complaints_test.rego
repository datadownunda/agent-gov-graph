package aigov.complaints

import rego.v1

test_manager_restricted_complaint_is_denied if {
    not allow with input as {
        "user": {
            "roles": ["manager"]
        },
        "action": "read",
        "resource": {
            "type": "employee_complaint",
            "classification": "restricted"
        }
    }
}
test_hr_investigator_restricted_complaint_is_allowed if {
    allow with input as {
        "user": {
            "roles": ["hr_investigator"]
        },
        "action": "read",
        "resource": {
            "type": "employee_complaint",
            "classification": "restricted"
        }
    }
}
test_unknown_role_is_denied if {
    not allow with input as {
        "user": {
            "roles": ["contractor"]
        },
        "action": "read",
        "resource": {
            "type": "employee_complaint",
            "classification": "restricted"
        }
    }
}
test_wrong_action_is_denied if {
    not allow with input as {
        "user": {
            "roles": ["hr_investigator"]
        },
        "action": "delete",
        "resource": {
            "type": "employee_complaint",
            "classification": "restricted"
        }
    }
}
test_denied_decision_contains_status_and_reason if {
    result := decision with input as {
        "user": {
            "roles": ["manager"]
        },
        "action": "read",
        "resource": {
            "type": "employee_complaint",
            "classification": "restricted"
        }
    }

    result.allowed == false
    result.decision == "DENY"
    "Restricted employee complaint data requires HR Investigator role" in result.reasons
    result.policy == "employee_complaint_access"
    result.policy_version == "1.0"
}