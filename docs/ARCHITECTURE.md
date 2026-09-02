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

## Remote identity and uncertainty

Before trusting any remote result, the adapter checks project, native job ID, cluster name, submission label, JAR URI, main class, and arguments. After the first attachment it additionally checks `job_uuid`, because native job IDs can be reused over time. A mismatch or disappearance of a previously attached job becomes `NEEDS_REVIEW`. No matching-job list scan or heuristic adoption occurs.

Dataproc documents request-ID deduplication but does not specify an unlimited deduplication lifetime. Native IDs, bounded retries, and UUID fencing reduce duplicate risk; they do not guarantee exactly-once application effects. Jobs must make output handling safe, and operators must not delete/recreate remote IDs while automation is active. Dataproc cancellation is addressed by job ID, so deletion/recreation between verification and cancellation remains an administrative race; runtime roles cannot delete jobs.

## Leases and concurrency

Every mutation compares the stored version in a Firestore transaction. Polling moves `next_check` forward by 120 seconds before remote calls. Concurrent cancellation changes the version so stale status writes fail. Attachment retries read the newest cancellation intent. Shard order rotates each minute, with 25 records per shard and a deadline reserve; this is a bounded control plane, not an unlimited scheduler.

A queue publication failure leaves durable `QUEUED` metadata that the reconciler can re-enqueue. Pub/Sub duplicate delivery cannot claim a nonqueued job. A worker crash before or after the remote call recovers through exact lookup and the persisted native identifiers.

