# HTTP API

## Authentication

Call the canonical `https://REGION-PROJECT.cloudfunctions.net/NAME-ENV-api` URL. Mint a Google service-account ID token for that exact audience, including email. Send it in **both** `Authorization: Bearer TOKEN` and `X-Serverless-Authorization: Bearer TOKEN`. Cloud Run validates the latter; the application verifies the intact former's RS256 signature, issuer, audience, expiry, issued-at time, numeric subject, verified email, and explicit caller allowlist.

A principal must also hold `roles/run.invoker` on the API. The deployment gives it only to the service accounts listed in profiles. User OAuth access tokens and unsigned identity headers do not satisfy application authentication.

