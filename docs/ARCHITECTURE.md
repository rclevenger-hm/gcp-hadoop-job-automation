# Architecture and recovery

## Components

The API authenticates a Google ID token, enforces a per-subject minute quota, validates a profile, and atomically writes the job and daily usage counter. Pub/Sub carries only a tenant hash and job ID. The worker uses a Firestore version comparison to claim dispatch. A scheduled function scans 16 active shards for due work and queries Dataproc directly.

All jobs run on existing Dataproc clusters in the configured project and region. All three functions share code while their service accounts hold different permissions. Terraform does not create or change a cluster.

## Admission identity

`job_id = SHA256(tenant + ':' + Idempotency-Key)`, where the tenant hashes the canonical Google issuer and numeric token subject. The document ID hashes tenant and job ID again. A transaction reads the job and daily counter before any writes. Same-key equivalent normalized payloads return the existing record; different payloads return 409. The quota increments only for a newly created job.

A random UUID is created outside the transaction callback and persisted as `submission_id`. The Dataproc job ID includes a service prefix, a portion of the logical ID, and that UUID. If a terminal record is eventually deleted by TTL, reusing its key receives a new native identity. Before physical deletion, an expired record returns `EXPIRED_KEY` and callers must choose a fresh key.

## State transitions

Normal flow is `QUEUED → SUBMITTING → SUBMITTED → RUNNING → SUCCEEDED/FAILED`. Dataproc can complete between polls, so intermediate states may be skipped. A pre-dispatch cancellation with zero attempts becomes `CANCELLED`; later cancellation records `CANCEL_REQUESTED` until Dataproc confirms its terminal state. A successful completion can win a cancellation race.

Ambiguous submissions become `SUBMISSION_UNKNOWN`. After a 120-second grace period, reconciliation performs exact-ID lookup. A matching result attaches the remote UUID. A missing unconfirmed result can return to `QUEUED` with the same request UUID and job ID, at most five attempts within the original 24-hour admission window. No retry generates a new native identity. Cancelled ambiguous jobs are searched but never resubmitted.

