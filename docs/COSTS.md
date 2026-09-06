# Costs and limits

## Main cost drivers

The existing Dataproc cluster usually dominates cost and continues billing according to its own lifecycle. This service never starts or stops clusters. Cloud Run invocations, builds/artifact storage, Pub/Sub delivery, Firestore reads/writes/indexes/PITR, Cloud Scheduler, logging and monitoring add control-plane costs. GCS driver reads and network egress depend on usage.

No fixed dollar estimate is embedded because prices, machine types, regions and workloads differ. Consult the Google Cloud pricing calculator with the actual cluster and expected job/traffic volumes.

## Built-in controls

Defaults are 100 newly admitted jobs per UTC day per subject, 60 API requests per minute per subject, 30 days of terminal metadata retention, at most five API/worker instances, and one reconciler instance. The worker submits at most five times using the same native identifiers within a 24-hour admission window. These limits bound control-plane activity; they do not bound the duration or resource consumption of an admitted Hadoop job.

Source artifacts are versioned and retained; manage their older versions intentionally. Existing cluster log and output buckets are outside this stack. Firestore active records have no TTL, so investigate stalled or uncertain jobs rather than accumulating them indefinitely.

