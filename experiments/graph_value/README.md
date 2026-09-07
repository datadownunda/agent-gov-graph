# Reproduce M8 Gate A

Use Python 3.13 and a dedicated environment with this directory's requirements.
The legacy top-level requirements include Neo4j and are not the Gate A dependency
set. Docker/OPA are needed only by existing regression tests, not Gate A queries.

1. Verify `protocol.json` against SHA-256
   `c9d6cbd538303fdab07731490ce6d986c81ae56b4919593ae8c130dbe015f501`.
2. Run `python -B -m pytest -p no:cacheprovider tests/test_graph_value_*.py
   --junitxml=gate-a-tests.xml` and the existing regression suite. Do not run
   tests concurrently with benchmarks.
3. On the inspected macOS host, run `python -B -m experiments.graph_value.benchmark
   run experiments/graph_value/results/gate-a-v1`. Hardware/swap reads are required
   for resource enforcement. The runner stops rather than bypassing unavailable
   measurements. It does not clear OS caches or install/start a service.
4. Run `python -B -m experiments.graph_value.score
   experiments/graph_value/results/gate-a-v1 --correctness-xml=gate-a-tests.xml
   --regression-xml=regression.xml`.

Result JSON retains raw samples, source digests, query-result digests, CPU,
footprints, memory and reasons for skipped tiers. Source generation is deterministic
for the stored seeds; generated files are synthetic, not new live observations.
`preliminary-excluded` records an abandoned preliminary timing batch. It is not
scored; its first reference runs overlapped regression tests and later code was
corrected before the clean final run.

The low-level Catalog is an internal typed reference container, not a verifier.
External evidence enters through preserved-source adapters and unchanged replay.
Unknown M7 archive formats or missing historical M5 evidence are not invented
into usable support. Query-local removal never infers historical prevention.
