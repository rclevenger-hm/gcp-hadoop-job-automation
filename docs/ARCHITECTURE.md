# Architecture and recovery

## Components

The API authenticates a Google ID token, enforces a per-subject minute quota, validates a profile, and atomically writes the job and daily usage counter. Pub/Sub carries only a tenant hash and job ID. The worker uses a Firestore version comparison to claim dispatch. A scheduled function scans 16 active shards for due work and queries Dataproc directly.

All jobs run on existing Dataproc clusters in the configured project and region. All three functions share code while their service accounts hold different permissions. Terraform does not create or change a cluster.

