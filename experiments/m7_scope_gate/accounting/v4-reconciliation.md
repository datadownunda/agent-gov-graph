# Frozen v4 accounting reconciliation

Read-only accounting, saved before the M7 v2 patch. Historical result: FAILED.

26 base cases have three equivalent presentations (78 evaluations), not independent replications.

21 false accepted links produce 21 false merged components and 18 false substantive exceptions. Three replacement evaluations account for all three truth-based scope-overreach acceptances.

The claimed 15 indistinguishable cases are identical at the source-row boundary. Only nine are identical at the complete worker-input boundary. Six namespace cases differ in namespace_observations, consumed only by the diagnostic sidecar in v4.

Preventability: six of 18 have a distinguishing namespace fact already supplied to the worker, but not passed into the primary M6/M7 verification path. Zero of those six have that namespace fact in the existing primary receipt. Nine of 18 are complete-input-identical to legitimate controls and cannot be selectively rejected by any deterministic code change. The other three differ in time but have no declared identifier lifetime; proximity or an invented timeout is not an admissible fix.

The three copied/different false links do not cause false exceptions: the existing target-effect resource check prevents them. Scope truth is satisfied in 15 of the 18 false-exception evaluations; their false link is execution-to-outcome, not governance-to-execution. Namespace/non-reuse/provenance assumptions must not be relabelled as missing governance scope.

A blanket missing-declaration abstention may suppress all exceptions including legitimate controls. That is conservative loss of evaluability, not selective repair or authenticated provenance.

| Evaluation | Scenario | False edge | Exceptions | G→E truth coverage | Full-input identical control | Source-row identical control |
|---|---|---|---:|---|---|---|
| 012 | reuse/replacement | governance:1 → execution:0 | 1 | [] | 003 | 003 |
| 013 | reuse/replacement | governance:1 → execution:0 | 1 | [] | 004 | 004 |
| 014 | reuse/replacement | governance:1 → execution:0 | 1 | [] | 005 | 005 |
| 015 | reuse/period | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | No |
| 016 | reuse/period | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | No |
| 017 | reuse/period | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | No |
| 021 | namespace/pooled | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | 003 |
| 022 | namespace/pooled | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | 004 |
| 023 | namespace/pooled | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | 005 |
| 024 | namespace/missing | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | 003 |
| 025 | namespace/missing | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | 004 |
| 026 | namespace/missing | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | No | 005 |
| 027 | copied/different | execution:0 → outcome:0 | 0 | [['governance:1', 'execution:0']] | No | No |
| 028 | copied/different | execution:0 → outcome:0 | 0 | [['governance:1', 'execution:0']] | No | No |
| 029 | copied/different | execution:0 → outcome:0 | 0 | [['governance:1', 'execution:0']] | No | No |
| 033 | copied/removed | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | 003 | 003 |
| 034 | copied/removed | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | 004 | 004 |
| 035 | copied/removed | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | 005 | 005 |
| 060 | fanin/withheld | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | 003 | 003 |
| 061 | fanin/withheld | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | 004 | 004 |
| 062 | fanin/withheld | execution:0 → outcome:0 | 1 | [['governance:1', 'execution:0']] | 005 | 005 |

## Evaluation 012

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "012",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:24a06c3a9102f098c3ce7b9e7f3571f56262a755fc5cc45380d1dc4493a4c2ba",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915",
      "correct": false,
      "pair": [
        "governance:1",
        "execution:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "003"
  ],
  "identical_worker_controls": [
    "003"
  ],
  "presentation": "canonical",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "reuse/replacement",
  "scope_overreach": 1,
  "truth_covered_pairs": []
}
```

## Evaluation 013

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "013",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:28b865d097460107f907fb7273d23655fd965c7f12612b5f1b8285986ff2e3bb",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429",
      "correct": false,
      "pair": [
        "governance:1",
        "execution:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "004"
  ],
  "identical_worker_controls": [
    "004"
  ],
  "presentation": "reversed",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "reuse/replacement",
  "scope_overreach": 1,
  "truth_covered_pairs": []
}
```

## Evaluation 014

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "014",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:8aeb4f924d3f274b2e24e5788763382ebd6d778ae3abc93308b274503ad2312b",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f"
          ],
          "evidence_ref": "sha256:02f8888617ce24aac28b018632b0a32f5ee04e8e5587486a53002bd06b3a49ef"
        },
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f",
            "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec"
          ],
          "evidence_ref": "sha256:c9756c9a5c53b919f07219371724f91c586cd258d9774984ab089659bef11164"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f",
      "correct": false,
      "pair": [
        "governance:1",
        "execution:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "005"
  ],
  "identical_worker_controls": [
    "005"
  ],
  "presentation": "renamed",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "reuse/replacement",
  "scope_overreach": 1,
  "truth_covered_pairs": []
}
```

## Evaluation 015

Timestamp differs, but no declared identifier lifetime makes it invalid. Scope gating cannot selectively reject the false outcome link; new lifetime/non-reuse evidence needed.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "015",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:aea2ab455011b4bd1228b0eb2b68365c778ac9e5eb243f3cb473574ebed0b74e",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915",
            "sha256:6b603b34acb08b3ab44a6d75866519356a59ee7ce60b3ad777988a1d244e37a8"
          ],
          "evidence_ref": "sha256:59010a456390aa575287945b924e166dfe94048ad23227164725aebd6f66e0d3"
        },
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:6b603b34acb08b3ab44a6d75866519356a59ee7ce60b3ad777988a1d244e37a8",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [],
  "identical_worker_controls": [],
  "presentation": "canonical",
  "prevention": "Timestamp differs, but no declared identifier lifetime makes it invalid. Scope gating cannot selectively reject the false outcome link; new lifetime/non-reuse evidence needed.",
  "scenario": "reuse/period",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 016

Timestamp differs, but no declared identifier lifetime makes it invalid. Scope gating cannot selectively reject the false outcome link; new lifetime/non-reuse evidence needed.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "016",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:e6349e8349742024151cff9298938595026c29f98e5cc4596a0565da2e131d35",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429",
            "sha256:6b603b34acb08b3ab44a6d75866519356a59ee7ce60b3ad777988a1d244e37a8"
          ],
          "evidence_ref": "sha256:59010a456390aa575287945b924e166dfe94048ad23227164725aebd6f66e0d3"
        },
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:6b603b34acb08b3ab44a6d75866519356a59ee7ce60b3ad777988a1d244e37a8",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [],
  "identical_worker_controls": [],
  "presentation": "reversed",
  "prevention": "Timestamp differs, but no declared identifier lifetime makes it invalid. Scope gating cannot selectively reject the false outcome link; new lifetime/non-reuse evidence needed.",
  "scenario": "reuse/period",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 017

Timestamp differs, but no declared identifier lifetime makes it invalid. Scope gating cannot selectively reject the false outcome link; new lifetime/non-reuse evidence needed.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "017",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:341847003fe6f1f6eaca38610deb7401b17b596f10cc21c382509b7b8561c560",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f"
          ],
          "evidence_ref": "sha256:02f8888617ce24aac28b018632b0a32f5ee04e8e5587486a53002bd06b3a49ef"
        },
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f",
            "sha256:963a604c905e26d573769f3905ac2cf16dd23d7574b83760d3b6a889307bc1c9"
          ],
          "evidence_ref": "sha256:abd72aa8daaf28f58378e04fc70b642b19f063ca3a5339156b343875391c8863"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:963a604c905e26d573769f3905ac2cf16dd23d7574b83760d3b6a889307bc1c9",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [],
  "identical_worker_controls": [],
  "presentation": "renamed",
  "prevention": "Timestamp differs, but no declared identifier lifetime makes it invalid. Scope gating cannot selectively reject the false outcome link; new lifetime/non-reuse evidence needed.",
  "scenario": "reuse/period",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 021

Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "021",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:24a06c3a9102f098c3ce7b9e7f3571f56262a755fc5cc45380d1dc4493a4c2ba",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "003"
  ],
  "identical_worker_controls": [],
  "presentation": "canonical",
  "prevention": "Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.",
  "scenario": "namespace/pooled",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 022

Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "022",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:28b865d097460107f907fb7273d23655fd965c7f12612b5f1b8285986ff2e3bb",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "004"
  ],
  "identical_worker_controls": [],
  "presentation": "reversed",
  "prevention": "Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.",
  "scenario": "namespace/pooled",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 023

Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "023",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:8aeb4f924d3f274b2e24e5788763382ebd6d778ae3abc93308b274503ad2312b",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f"
          ],
          "evidence_ref": "sha256:02f8888617ce24aac28b018632b0a32f5ee04e8e5587486a53002bd06b3a49ef"
        },
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f",
            "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec"
          ],
          "evidence_ref": "sha256:c9756c9a5c53b919f07219371724f91c586cd258d9774984ab089659bef11164"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "005"
  ],
  "identical_worker_controls": [],
  "presentation": "renamed",
  "prevention": "Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.",
  "scenario": "namespace/pooled",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 024

Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "024",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:24a06c3a9102f098c3ce7b9e7f3571f56262a755fc5cc45380d1dc4493a4c2ba",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "003"
  ],
  "identical_worker_controls": [],
  "presentation": "canonical",
  "prevention": "Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.",
  "scenario": "namespace/missing",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 025

Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "025",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:28b865d097460107f907fb7273d23655fd965c7f12612b5f1b8285986ff2e3bb",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "004"
  ],
  "identical_worker_controls": [],
  "presentation": "reversed",
  "prevention": "Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.",
  "scenario": "namespace/missing",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 026

Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "026",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:8aeb4f924d3f274b2e24e5788763382ebd6d778ae3abc93308b274503ad2312b",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f"
          ],
          "evidence_ref": "sha256:02f8888617ce24aac28b018632b0a32f5ee04e8e5587486a53002bd06b3a49ef"
        },
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f",
            "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec"
          ],
          "evidence_ref": "sha256:c9756c9a5c53b919f07219371724f91c586cd258d9774984ab089659bef11164"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "005"
  ],
  "identical_worker_controls": [],
  "presentation": "renamed",
  "prevention": "Worker namespace observations distinguish this case; primary M6/M7 currently omit them. Declaration qualification can abstain; missing declarations must not be invented.",
  "scenario": "namespace/missing",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 027

Resource difference already prevents a substantive exception; false identity acceptance remains.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "027",
  "false_exception_witnesses": [],
  "false_links": [
    {
      "assertion_id": "sha256:a1fa57a051ee46b46d7baeacd7f75d8e3db053ae8d959950dca8c6b5a139934a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [],
  "identical_worker_controls": [],
  "presentation": "canonical",
  "prevention": "Resource difference already prevents a substantive exception; false identity acceptance remains.",
  "scenario": "copied/different",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 028

Resource difference already prevents a substantive exception; false identity acceptance remains.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "028",
  "false_exception_witnesses": [],
  "false_links": [
    {
      "assertion_id": "sha256:a1fa57a051ee46b46d7baeacd7f75d8e3db053ae8d959950dca8c6b5a139934a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [],
  "identical_worker_controls": [],
  "presentation": "reversed",
  "prevention": "Resource difference already prevents a substantive exception; false identity acceptance remains.",
  "scenario": "copied/different",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 029

Resource difference already prevents a substantive exception; false identity acceptance remains.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "029",
  "false_exception_witnesses": [],
  "false_links": [
    {
      "assertion_id": "sha256:65ef389ca798b2abd1357b48c7898b76db36e5c1978efc8805b1ace788e35d5e",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [],
  "identical_worker_controls": [],
  "presentation": "renamed",
  "prevention": "Resource difference already prevents a substantive exception; false identity acceptance remains.",
  "scenario": "copied/different",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 033

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "033",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:24a06c3a9102f098c3ce7b9e7f3571f56262a755fc5cc45380d1dc4493a4c2ba",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "003"
  ],
  "identical_worker_controls": [
    "003"
  ],
  "presentation": "canonical",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "copied/removed",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 034

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "034",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:28b865d097460107f907fb7273d23655fd965c7f12612b5f1b8285986ff2e3bb",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "004"
  ],
  "identical_worker_controls": [
    "004"
  ],
  "presentation": "reversed",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "copied/removed",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 035

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "035",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:8aeb4f924d3f274b2e24e5788763382ebd6d778ae3abc93308b274503ad2312b",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f"
          ],
          "evidence_ref": "sha256:02f8888617ce24aac28b018632b0a32f5ee04e8e5587486a53002bd06b3a49ef"
        },
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f",
            "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec"
          ],
          "evidence_ref": "sha256:c9756c9a5c53b919f07219371724f91c586cd258d9774984ab089659bef11164"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "005"
  ],
  "identical_worker_controls": [
    "005"
  ],
  "presentation": "renamed",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "copied/removed",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 060

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "060",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:24a06c3a9102f098c3ce7b9e7f3571f56262a755fc5cc45380d1dc4493a4c2ba",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:967ee2d94718cdfce81c76e8b59f6a006591e0973430aa7c3b1001aed4b12915",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "003"
  ],
  "identical_worker_controls": [
    "003"
  ],
  "presentation": "canonical",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "fanin/withheld",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 061

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "061",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:28b865d097460107f907fb7273d23655fd965c7f12612b5f1b8285986ff2e3bb",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429"
          ],
          "evidence_ref": "sha256:6dec02d19b2eaaacdd3a3aa6a6e6f3a899a25c767e7a443d4b71e3df2e85f6f9"
        },
        {
          "assertion_ids": [
            "sha256:5ee0353f0824bbdf50636f16d8084df9b5f3a58ac35f1a443871d75eb6210429",
            "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a"
          ],
          "evidence_ref": "sha256:be95991b631d07b49d2a1181fb08503be1f5d85ee74a2187aef7018b2f68f369"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:38035c8c83e881565a370eea8b42a0717975b4d5d61f4214ccd530677ee0e46a",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "004"
  ],
  "identical_worker_controls": [
    "004"
  ],
  "presentation": "reversed",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "fanin/withheld",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```

## Evaluation 062

Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.

Exact false links, merged components, truth coverage, and contributing exception paths:

```json
{
  "evaluation_id": "062",
  "false_exception_witnesses": [
    {
      "attestation_id": "sha256:8aeb4f924d3f274b2e24e5788763382ebd6d778ae3abc93308b274503ad2312b",
      "correlation_paths": [
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f"
          ],
          "evidence_ref": "sha256:02f8888617ce24aac28b018632b0a32f5ee04e8e5587486a53002bd06b3a49ef"
        },
        {
          "assertion_ids": [
            "sha256:2fc8a5dae7859f9d73e80914921668ce512f4aa9ad63991db0bc22fffaba3f9f",
            "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec"
          ],
          "evidence_ref": "sha256:c9756c9a5c53b919f07219371724f91c586cd258d9774984ab089659bef11164"
        }
      ],
      "governance": "governance:1",
      "kind": "FALSE_EXCEPTION",
      "outcomes": [
        "outcome:0"
      ]
    }
  ],
  "false_links": [
    {
      "assertion_id": "sha256:c6efbb70eab4599b028233c0278e872f5d3906e133cd91136203c1ebdd60e0ec",
      "correct": false,
      "pair": [
        "execution:0",
        "outcome:0"
      ]
    }
  ],
  "false_merge_components": [
    [
      "governance:1",
      "execution:0",
      "outcome:0"
    ]
  ],
  "identical_source_row_controls": [
    "005"
  ],
  "identical_worker_controls": [
    "005"
  ],
  "presentation": "renamed",
  "prevention": "Not selectively preventable: complete worker input equals legitimate control. New distinguishing evidence required.",
  "scenario": "fanin/withheld",
  "scope_overreach": 0,
  "truth_covered_pairs": [
    [
      "governance:1",
      "execution:0"
    ]
  ]
}
```
