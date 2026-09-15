# Identifier provenance necessity decision — protocol v1

Baseline: 1c555013e7140135075e9deebedcd1dc9da47dd7. This is a decision milestone, not approval to implement a production representation. Prior producer findings and historical FAILED results remain fixed.

## Claim under examination

The combined NGINX and OPA findings require explicit identifier generation and observation context for defensible assurance interpretation. Determine separately whether the existing raw evidence, configuration, declared issuer/namespace and limitations already support the required investigation; whether a bounded documentation/annotation convention would suffice; and whether a new production representation is necessary now. A demonstrated need for context is not proof of a need for schema or matcher changes.

## Frozen comparison and evidence rules

Compare three alternatives: A, existing raw evidence and current declarations/limitations; B, an evidence-backed field interpretation note referencing existing captures and configuration, with unknowns explicit; C, a new machine-readable production representation. Assess each against the same six questions: where the value was observed, who generated or supplied it, which namespace/configuration scopes the interpretation, which relationship it supports, what evidence supports those statements, and what remains unknown.

Use these fixed cases: NGINX incoming header versus native request ID; NGINX response header versus access-log ID; OPA stock exec output versus decision-log ID; SDK/custom-runtime supplied ID (source-reviewed only); caller recording a returned OPA ID against execution (hypothetical); and missing producer/configuration context (withholding thought experiment). Do not relabel hypothetical or source-only cases as new observed independent evidence. No live producer campaign or historical rescoring. Evaluate every case for all alternatives, including cases the candidate cannot resolve.

Inspect the actual adapters and native_assertions behavior to identify what is retained versus missing. An executable diagnostic, if needed, may use synthetic fixtures with the unchanged matcher to show an existing output boundary; it is not a producer experiment or proof of improved assurance. Record file/line references and the exact baseline. Existing LINKED status must be interpreted with existing limitations; do not invent a current control-effectiveness false-positive defect.

## Criteria, falsification and verdicts

Context necessity is supported only if at least one named case admits materially different defensible interpretations at equal identifier value depending on evidenced producer/observation semantics. It is not supported merely by similar field names.

Production necessity is supported only if a concrete current or next protected assurance/investigation operation cannot be expressed safely with A or B, C resolves that operation using available ordinary evidence rather than assertions manufactured by AGG, and the additional collection/maintenance cost is necessary. A smaller successful alternative falsifies the necessity claim for C now. Unknown evidence must remain unknown in all alternatives: representation cannot authenticate producer identity, prove configuration applicability, establish execution or turn two views of one transaction into independent evidence.

Allowed decision outcomes: PRODUCTION_REPRESENTATION_JUSTIFIED (all production necessity criteria met, proposal only); CONTEXT_NEEDED_PRODUCTION_DEFERRED (interpretation need established, A/B sufficient for current scope or C benefit unproven); NO_ADDITIONAL_CONTEXT_JUSTIFIED; or NOT_DEMONSTRATED (evidence insufficient/conflicting to decide). Record negative findings and rejected alternatives. Do not claim causal efficacy of a documentation convention without an evaluation of its users.

## Protected boundaries and stop conditions

Additive decision documentation/diagnostic artifacts only; all baseline files unchanged. No production schemas, matching, runtime, policies, graph, new technology, generic ontology or scope engine. No advance to M9b or M9a-ii within this milestone. Freeze this protocol before delegated comparison. Preserve its criteria after analysis exists. Pause for substantive architecture/product choice, material thesis/commercial implication, protocol/claim change, destructive operation or significant public claim. Deliver a reviewable recommendation before requesting any such approval.

## Completion

Provide evidence matrix, alternatives assessment, precise recommendation with limits and plain-English milestone briefing. Validate cited paths and preservation of the baseline; execute relevant existing tests if a behavioral diagnostic is used, not a redundant full producer campaign. Prepare a clean Git checkpoint with intended files only. Record CI status accurately; publication of a significant new conclusion requires owner review under the operating model. No implementation is implied by a recommendation.
