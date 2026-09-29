# Contributing

## Development

Use Python 3.13, an isolated environment, and the hashed development requirements. Run Ruff, pytest, the contract checker, the source builder, and Terraform formatting/validation/mocked tests before proposing a change. Keep runtime dependencies in `requirements.in` and regenerate both lockfiles using pip-tools with hashes.

## Behavioral changes

Preserve tenant ownership, transaction read-before-write rules, CAS version checks, and stable native IDs across ambiguous retries. Add meaningful regression tests for cancellation or recovery changes. Keep API, examples, profile validation and Terraform variables consistent. Do not claim exactly-once Hadoop side effects.

