# Costs and limits

## Main cost drivers

The existing Dataproc cluster usually dominates cost and continues billing according to its own lifecycle. This service never starts or stops clusters. Cloud Run invocations, builds/artifact storage, Pub/Sub delivery, Firestore reads/writes/indexes/PITR, Cloud Scheduler, logging and monitoring add control-plane costs. GCS driver reads and network egress depend on usage.

No fixed dollar estimate is embedded because prices, machine types, regions and workloads differ. Consult the Google Cloud pricing calculator with the actual cluster and expected job/traffic volumes.

