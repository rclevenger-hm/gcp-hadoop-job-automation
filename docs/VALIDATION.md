# Validation scope

## Automated checks

The Python test suite exercises validation, JWT signature/claim verification, transactional admission/replay/quotas, concurrent submissions, ownership, pagination, compare-and-swap conflicts, active versus terminal TTL, native Dataproc protobuf shapes, request-ID reuse, lost responses, cancellation races, remote identity fencing, and bounded GCS reads. HTTP tests cover authentication ordering, routes, body limits, sanitized errors, worker delivery and scheduler failures.

Firestore transaction tests use an atomic in-memory fake with rollback-on-error behavior. SDK query cursors and Dataproc requests are also constructed with the real client libraries. These tests do not claim to replace integration testing against a live Firestore database or Dataproc cluster.

## CI gates

CI installs hashed Python dependencies, runs Ruff and pytest, audits runtime packages, checks API/example/entry-point/Terraform contracts, stages the source artifact, and imports all entry points using an isolated production dependency environment. A second job validates Terraform and runs mocked plans for secure defaults, rejected negative quota, and rejected public consumers.

Terraform provider versions are locked. Mock plans verify configuration, not provider API acceptance in a real project. The manual deploy workflow repeats the checks before applying and verifies anonymous access is denied after deployment.

## Live acceptance still required

Run the read-only smoke script after deployment, verify function service identities and indexes, and inspect scheduler and Pub/Sub delivery. A real Hadoop acceptance test requires an explicitly approved existing cluster, known JAR/input fixture, unique output directory, and billing authorization. Confirm remote success, cancellation and driver-output retrieval before production use.

Repository publication performs no deployment and no live Hadoop execution. Passing CI demonstrates local behavior and infrastructure consistency, not measured production performance or a guaranteed execution outcome.
