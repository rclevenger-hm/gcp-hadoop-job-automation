# HTTP API

## Authentication

Call the canonical `https://REGION-PROJECT.cloudfunctions.net/NAME-ENV-api` URL. Mint a Google service-account ID token for that exact audience, including email. Send it in **both** `Authorization: Bearer TOKEN` and `X-Serverless-Authorization: Bearer TOKEN`. Cloud Run validates the latter; the application verifies the intact former's RS256 signature, issuer, audience, expiry, issued-at time, numeric subject, verified email, and explicit caller allowlist.

A principal must also hold `roles/run.invoker` on the API. The deployment gives it only to the service accounts listed in profiles. User OAuth access tokens and unsigned identity headers do not satisfy application authentication.

## Requests

`POST /jobs` requires JSON, the four OCI job fields, a profile, and `Idempotency-Key` of 8–128 letters, digits, dots, underscores, colons or hyphens. Optional `arguments` is an ordered array appended after input and output. The example is in `examples/job.json`.

Body limit: 65,536 bytes. Each primary job field: at most 4,096 characters. Arguments: up to 20 strings of at most 1,024 characters each. The aggregate JAR/class/input/output/argument length is capped at 10,240 characters as an application compatibility limit. Controls, invalid Unicode, unknown fields, noncanonical URIs, and equal input/output paths are rejected.

Approved directory prefixes end in `/`; prefix matching is case sensitive and does not decode percent escapes. GCS is required for JARs and driver output. Inputs/outputs can use configured GCS or HDFS prefixes. Java arguments are passed as SDK data without invoking a shell.

## Routes and responses

| Method and path | Result |
|---|---|
| `POST /jobs` | 202 new admission; 200 replay |
| `GET /jobs?limit=20&status=RUNNING&cursor=...` | Owned retained jobs and `next_cursor` |
| `GET /jobs/{job_id}` | Persisted owned job summary |
| `POST /jobs/{job_id}/cancel` | 202 pending remote cancellation; 200 cancelled before first attempt or already cancelled |
| `GET /jobs/{job_id}/logs` | Bounded GCS driver output |
| `GET /usage` | UTC date, admitted jobs, daily limit |

Summaries include logical ID, profile, state, timestamps, native Dataproc ID and available cancellation/review fields. Request contents, internal profiles, email addresses, and native SDK errors are not returned. Status is a persisted observation and can lag native execution by polling and backlog delay.

