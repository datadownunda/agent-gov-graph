# Observation Boundary

Agent Gov Graph v0.1 derives runtime governance findings by reconciling evidence from instrumented governance and execution components.

## What the current implementation can observe

The current runtime harness can distinguish:

- a governed action that was allowed and executed
- a denied action where no execution effect was observed
- a denied action where execution nevertheless occurred
- a governed action type that executed without a governance decision, when the execution was independently recorded by the instrumented resource layer

These observations support detection of enforcement and coverage failures within the available evidence boundary.

## Known blind spot

The current execution evidence source is cooperating application instrumentation.

If an action bypasses both:

1. governance interception, and
2. the instrumented execution path,

no governance or execution evidence is produced.

In that situation Agent Gov Graph cannot determine that the action occurred and therefore cannot classify it as a coverage or enforcement failure.

## Demonstrated adversarial case

A direct filesystem read of the synthetic restricted complaint resource was performed without invoking either the governance runtime or the instrumented complaint store.

The resource read succeeded.

Before the read:

- governance events: 1
- execution events: 1

After the read:

- governance events: 1
- execution events: 1

The reconciler output was unchanged.

This demonstrates that current coverage findings are bounded by the observation sources available to Agent Gov Graph.

## Architectural implication

Broader claims of runtime coverage will require an observation source that is independent of the cooperating governance and application instrumentation.

A future runtime or infrastructure telemetry layer, potentially using OpenTelemetry or equivalent mechanisms, should be evaluated for this purpose.

This is not a current v0.1 dependency.
