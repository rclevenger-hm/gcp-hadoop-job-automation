# Validation scope

## Automated checks

The Python test suite exercises validation, JWT signature/claim verification, transactional admission/replay/quotas, concurrent submissions, ownership, pagination, compare-and-swap conflicts, active versus terminal TTL, native Dataproc protobuf shapes, request-ID reuse, lost responses, cancellation races, remote identity fencing, and bounded GCS reads. HTTP tests cover authentication ordering, routes, body limits, sanitized errors, worker delivery and scheduler failures.

Firestore transaction tests use an atomic in-memory fake with rollback-on-error behavior. SDK query cursors and Dataproc requests are also constructed with the real client libraries. These tests do not claim to replace integration testing against a live Firestore database or Dataproc cluster.

