# M9b coverage substantiation

Overall result: **NOT_DEMONSTRATED on the available evidence**. The source gate failed; the seven-case synthetic diagnostic completed. No replacement live campaign was run. This is a completed source-gate assessment, not a demonstration of live coverage or completion of the broader coverage-acquisition objective.

Baseline `6f765ebe6f5452d8b9ee85bd609771b301bd503f`; [protocol](PROTOCOL.md) preregistered in `67d45d6`; diagnostic and source review frozen in `f954d28` with a clean working tree before the first public-API campaign. The five-second horizon and existing production behavior remain unchanged.

## Source gate

The [four-family evidence review](EVIDENCE_REVIEW.md) found no eligible real target episode. The preserved blocked target episode's declared interval ends nominally **0.113120417 seconds** after its native OPA decision, short of the required five seconds even before accounting for unsubstantiated clock uncertainty. Its available records also do not substantiate the required capture continuity/finalization and clock bounds. These timestamp differences are not independently verified physical elapsed times.

The deterministic positive archive is explicitly synthetic. NGINX conformance captures requests without the required DENY episode, and OPA conformance captures decisions without a target interval. Combining those campaigns would invent coverage for an episode none observed. Existing digests preserve content identity, not source completeness or authenticity.

## Public-API diagnostic

The unchanged `src.control_attestation.attest` entry point evaluated seven labelled scratch variants of the existing deterministic fixture. Labels are not adjudicator inputs. Five variants changed exactly one support field and updated that copied file's manifest digest; every native, governance and reconciliation byte remained unchanged. Missing support omitted the API argument while leaving the copied archive intact. Thus the wrong-snapshot case passed file-inventory consistency and reached the specific snapshot-binding check.

| Case | Coverage / verification result | Finding |
| --- | --- | --- |
| Original synthetic fixture | ADEQUATE / VERIFIED | CONTROL_EFFECTIVE — semantic positive only |
| Missing supplied support | UNKNOWN / VERIFIED | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |
| Capture through shortened to decision time | INADEQUATE / VERIFIED | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |
| Identity scope restricted to governed actor | INADEQUATE / VERIFIED | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |
| Native snapshot digest mismatch | EVIDENCE_DEFECT | No finding; NOT_EVALUABLE |
| Clock basis says no measurement exists, numeric zero retained | ADEQUATE / VERIFIED | CONTROL_EFFECTIVE — trusted-declaration boundary |
| Unresolved gaps true | INADEQUATE / VERIFIED | CONTROL_EFFECTIVENESS_NOT_DEMONSTRATED |

Exact requests, mutations, full attestations, receipts, copied archives, freeze hashes and [summary](results/v1/summary.json) are preserved in `results/v1`. The unmeasured clock basis was exactly: `No clock offset measurement exists; zero is an unsupported declaration.`

The clock case was preregistered as characterization of the trust boundary, not as an authenticity guarantee the API claimed to enforce. Its acceptance does not establish a live compromised source or falsify a promised authentication feature. It does show why acceptance cannot substitute for source substantiation. The public verifier checks a numeric bound and nonempty basis; the semantic truth of that basis still requires evidence outside that check. No post-hoc prose parser or new production gate was added.

All five required negative cases prevented effectiveness. This does not rescue the failed source gate. The synthetic positive demonstrates the conditional decision rule only. The overall verdict is NOT_DEMONSTRATED, not SUBSTANTIATED or a newly falsified broad project thesis.

## Replay

From a full checkout containing the baseline and freeze commits:

```sh
python -B -m experiments.m9b_coverage_substantiation.run_diagnostic audit experiments/m9b_coverage_substantiation/results/v1
```

Replay uses the existing Python requirements, re-evaluates fresh scratch copies through the public API, and compares full outputs without changing the archive. It runs no native producers and requires no Docker access. It verifies inventory and frozen dependencies as well as the outputs. Hashes remain unauthenticated content checks.

## Milestone briefing

**Goal.** Determine whether existing evidence substantively supports the fixed five-second negative-observation claim, separately from whether support declarations satisfy the API.

**Accomplished.** Reviewed four evidence families, documented the exact missing dimensions, ran seven public-API cases after freeze, and preserved their outputs. Prepared a concrete [bounded acquisition proposal](ACQUISITION_PROPOSAL.md).

**Challenges.** Available native records do not span the required episode. An accepted nonempty clock explanation can explicitly disclaim measurement; well-formed support is not substantiated support. Updating only copied support/manifest bytes was necessary to test semantics rather than generic tamper rejection. No producer results or criteria were changed to obtain a positive.

**Technical impact.** Additive audit, diagnostic, tests and artifacts only. No production schema, matching, runtime, policy, coverage semantics or attestation rule changed. Every baseline file and historical FAILED result is preserved.

**Product impact.** A credible positive finding needs substantiated scope, continuity, completion and timing evidence. Current conditional API acceptance cannot itself supply those facts. This narrows what the project can claim; it does not establish that the general assurance thesis is false.

**GTM/commercial impact.** Access to ordinary capture and clock evidence may be an adoption constraint and source of review effort. Those costs and buyer acceptability remain unmeasured. Neither a new platform nor a claim of live verified effectiveness is justified by this result.

**Unknowns.** Whether the existing local environment can supply defensible native lifecycle/finalization and clock observations for a new five-second episode; whether those assumptions are acceptable to practitioners; and how readily enterprise owners can export analogous evidence. Independent administration remains outside the local experiment's demonstrated boundary.

**Next recommended milestone.** Continue M9b with the separately scoped bounded local evidence acquisition using existing OPA and NGINX, ordinary lifecycle/log records and justified clock observations. Freeze exact source availability, margins, finalization and omission challenges before capture. Do not advance to M9a-ii.

**Checkpoint.** See [validation](VALIDATION.md) and delivery briefing for the final commit and exact publication/CI state. The branch depends on the prior unmerged checkpoints. Publishing this negative result and initiating the proposed acquisition are separate owner decisions under the operating model.
