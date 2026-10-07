# Future improvements

## Integration coverage

Add a dedicated ephemeral Google Cloud integration project with budget controls, a known small Hadoop fixture, and explicit manual execution. Validate Pub/Sub OIDC, Firestore contention/retries, actual driver segments and Dataproc cancellation under real API behavior.

## Workload controls

Consider per-profile concurrency, cluster capacity admission, output reservation and application-specific content-addressed artifacts. These need workload semantics; a universal safe maximum runtime or overwrite policy cannot be inferred from a JAR URI.

## Operational tooling

Add an operator-only reviewed resolution workflow for uncertain jobs, richer lag metrics, and optional Cloud Logging links for YARN/container diagnostics. Keep resolution separate from automatic resubmission and require verified native identities.
