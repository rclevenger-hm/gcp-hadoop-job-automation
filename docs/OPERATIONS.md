# Operations

## Routine checks

Monitor function 5xx rates, Pub/Sub dead letters, scheduler delivery, and `NEEDS_REVIEW` state alerts. Confirm notification email channels. Inspect Cloud Logging events `api_request`, `api_error`, `worker_error`, `reconcile_complete`, and `job_state`. The request ID is returned in `X-Request-Id`.

Use the API's status/history/usage endpoints for caller-visible state. Query native Dataproc status as an operator when diagnosing a discrepancy. The control plane polls each minute but the 120-second lease, shard limits and backlog can extend visible latency.

