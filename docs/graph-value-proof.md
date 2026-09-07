# M8 graph-value proof — Gate A

The approved protocol was written before implementation and measurements. Its
exact SHA-256 is `c9d6cbd538303fdab07731490ce6d986c81ae56b4919593ae8c130dbe015f501`.
The executable protocol is `experiments/graph_value/protocol.json`. It is never
rewritten by generation, benchmarking or scoring; a changed digest aborts them.
Source checkpoint: `b585c548a3b68e6611c1f7545f63e7bcfd05d845`.

## Architecture and evidence boundary

The graph is disposable. Original M1–M7 sources, schemas, policies, archives,
assertions, attestations and findings remain unchanged. The legacy trajectory
builder, expectation files and Neo4j writer are not used by Gate A.

The canonical adapter verifies the existing M7 archive through unchanged M6/M7
replay and exact preserved M4 revisions. The query catalog contains allowlisted
semantic records and explicit immediate references; no transitive closures,
preselected bases, experimental labels or ground truth. Source records and
queries have explicit evidence-view/revision contexts. Shared content-addressed
artifacts can connect multiple views for Q4, but never supply missing records to
a withheld reconciliation view. The low-level Catalog is a builder for verified
adapters and unit fixtures, not an external trust boundary.

Missing archives fail verification. Missing individual references remain explicit
and traversal returns incomplete. Saved hashes/receipts do not authenticate their
own contents. Contextual M5 inquiries do not become historical M6 explanations.
A recorded M6 authority explanation with no supplied original M5 assertion is
retained with an unresolved reference, not silently verified or reconstructed.

M4 complete-state conflicts, M5 independent exact-parent paths, full child-scope
and interval containment, explicit delegation/onward capability and cycle rules
remain in the unchanged M4/M5 implementation. Both arms use it for validation;
its procedural traversal and computational cost are disclosed. Graph traversal
selects candidates, not authorization conclusions. Retaining this common code
limits what the experiment can claim about graph simplification.

The baseline uses dictionaries plus reverse, relationship, child and principal
indexes. The graph uses a typed directed multigraph with incoming/outgoing and
property indexes. Neither arm is intentionally weakened. Common digest, time,
result and semantic routines are counted separately. All graph-specific engine,
query and projection code is charged to graph, regardless of module placement.

## Query contracts

- Q1: begin at an exact M7 exception; return original attestation/reconciliation,
  recorded witnesses, derived investigation paths, evidence, authority bindings,
  populations, limitations, provenance and unresolved dependencies. Additional
  traversal paths never change the recorded M6 witnesses.
- Q2: require an exact authority/delegation record, revision context and historical
  instant; return downstream actor/tuple assessments, all accepted and rejected
  bases, alternatives, and connected assurance records. Historical timestamps
  remain attached to actions; validity at query time is not validity at action time.
- Q3: filter valid demonstrated paths through one disabled relationship; preserve
  original rejected candidates/conflicts. Explicitly return whether all support
  or only one basis disappears, ALLOW actions losing historical scope support
  where both recorded M4 times agree, and assurance connections. Neither old
  exceptions nor observed effects are deleted, prevented or re-adjudicated.
- Q4: reverse transitive support, assessment-context and verification dependencies
  from a record/artifact/source/revision. Return reconciliation/attestation
  endpoints and all finite simple witnesses with dependency categories. A
  verification inventory dependency is not substantive support. Q4 independently
  qualifies for strategic value; it is not subordinate to Q3.

Relations are exactly those in `src/graph_value/projection.py:RELATIONS` and
originate in source references or record fields. Every edge carries origin and
pointer. Parallel origins are preserved. No broad ontology, new producing-system
identifiers, recommendations, UI, learning or remediation is introduced.

## Correctness and scale

The hand-authored expected file is read only by tests/scoring; workers never
import it. Both arms are scored against explicit path lists and authority
alternatives, plus unchanged M4–M7 regression and archive replay. Tests exercise
permutation, duplicate input, rebuild, conflict variants, revision isolation,
missing/tampered archives, cycle diagnostics, nanoseconds and explicit limits.
Output truncation is never treated as a complete answer.

Scale generates current-semantic M5 revision collections and small independent
M6 source populations with an explicitly shared target interpretation artifact.
Actual relationships, nodes, source bytes and output size are measured. M5
collections contain exact-parent chains, fanout and independent alternatives;
M6 dependency support crosses components through the common artifact. Q1 always
uses the original preserved live exception, not a fabricated scaled M7 finding.
This is a limitation on Q1 scale evidence. Arbitrary M7 delegation verification
is not supported by M7 and is not added here.

The main workload selects a bounded authority subtree and a shared Q4 artifact.
Full-root and population-growth cases are separate stress measurements. They do
not replace the preregistered workload. No customer-volume inference is made.

Each arm/repetition runs in a fresh process. Each query class builds its own
index with empty semantic cache, while sharing immutable verified source input.
Cold per-class time includes source verification, index construction, query and
serialization. Warm samples repeat traversal with equal immutable semantic
caching. CPU is reported cumulatively per worker; OS disk caches are uncontrolled.
Raw and aggregate metrics preserve those distinctions.

## Gates

The frozen Gate A rule requires correctness, strategic path dependence in at
least Q2/Q3/Q4, >=30% whole-arm bespoke topology-code reduction plus >=2 non-LOC
improvements, intact provenance/uncertainty, and successful offline evaluation at
100,000 relationships. LOC alone cannot pass. All new shared/projector code,
reused semantics, reverse/depth changes, effort and defects are disclosed.

Warm p95 <=5 seconds, cold source-to-answer <=120 seconds, 4 GiB or 25% physical
RAM (whichever is lower), and resource-stop rules are experiment acceptability
thresholds only, not product SLOs. The million-relationship tier is optional.

Any Gate A result is legitimate. NOT_DEMONSTRATED requires database value
NOT_TESTED. DEMONSTRATED still requires returning results to Chat before Gate B.
This implementation contains no Gate B and installs/configures no Neo4j.

The final commercial-usefulness discussion is non-scoring and identifies likely
enterprise users and decisions. It is a set of hypotheses, not market research.

## Projection representation details

Candidate and reverse-candidate membership is preserved on each correlation
assertion, with explicit population-reference edges. A separate redundant
CANDIDATE_ENDPOINT edge is not materialized: investigation output retains the
candidate structures and categorizes population paths as assessment context,
never as accepted linkage. Only LINKED_ENDPOINT can represent accepted linkage.

Edge pointers name adapter fields/selectors. Some selectors (such as normalized
scope entries and digest-selected revision members) are not literal RFC 6901
pointers into source JSON. The accompanying origin record/revision digest is the
source locator and resolves the complete original record. No graph-specific ID
is written back to a producing system.

The completed regression subset excludes Docker-dependent legacy modules. The
full suite could not finish because even a bounded OPA container version command
timed out. This is an environment validation gap, not a demonstrated M8 semantic
failure; it limits any claim of full integration validation. Exact scope and
attempt outcomes are preserved in validation-scope.json.
