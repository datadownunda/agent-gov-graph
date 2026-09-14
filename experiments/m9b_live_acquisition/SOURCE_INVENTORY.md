# Pre-capture source inventory

Read-only inventory before the live campaign found Docker Desktop on LinuxKit 6.12.76, with the existing pinned NGINX image available. That image supplies BusyBox 1.37.0 `date`, read-only default `adjtimex`, and `/proc/self/timens_offsets`. The capability probe's time-namespace offsets were zero; this is not a measurement of OPA/NGINX/host UTC agreement or a guarantee throughout a later capture. No clock-changing command was run.

The macOS host has `sntp` and `systemsetup`, but no interval-specific synchronization record has been established for the future episode. Availability of a synchronization utility does not substantiate a clock bound. The approved protocol therefore measures bracketed sample intervals and retains raw kernel clock diagnostics, while requiring any unsupported interval-wide timing claim to remain unknown.

Ordinary evidence available for this bounded local attempt includes Docker image/container inspection, lifecycle events, effective `nginx -T`, container stdout/stderr, graceful process exit, and NGINX's unfiltered native access file. Availability of each API is not proof its eventual capture will be complete. The runner must preserve actual observations and failures rather than pre-populating successful support booleans.

The original `experiments/target_outcome/nginx.conf` logs warnings to stderr and access rows to the native file. Its bytes must remain unchanged. Warning silence alone does not establish that logging operated continuously; a configuration snapshot alone does not prove applicability throughout the interval.

The actual `_governed_action` path preserves authority history, governance, runtime emissions and the parsed OPA decision-log record. Its existing OPA adapter serializes the record again; it does not retain original stdout/stderr bytes. This custody limit is retained, not silently relabelled as original native byte capture.

Compatibility inspection found that the existing M6 `derive` path requires three actual scenario focuses (`allow`, `critical-deny`, `blocked-deny`). A single-DENY acquisition does not satisfy that archive layout. The public attestation API is therefore not invoked on a fabricated compatible archive; source eligibility and API compatibility are reported separately. A consumer generalization requires its own review after this acquisition.

Trust boundary: one operator controls Docker, the synthetic policy input, target deployment and capture. These are real producer processes, not independently administered enterprise systems. No new collector, framework, database, signing infrastructure, policy engine or production instrumentation is introduced.
