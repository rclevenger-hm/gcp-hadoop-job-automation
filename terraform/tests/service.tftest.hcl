mock_provider "google-beta" {}
mock_provider "google" {}
mock_provider "archive" {}
variables {
  project_id         = "hadoop-test-project"
  notification_email = "owner@example.com"
  billing_account    = "000000-000000-000000"
  cluster_profiles = {
    analytics = {
      cluster_name    = "analytics-cluster"
      allowed_callers = ["consumer@hadoop-test-project.iam.gserviceaccount.com"]
      jar_prefixes    = ["gs://your-artifacts/approved/"]
      input_prefixes  = ["gs://your-data/input/", "hdfs:///data/input/"]
      output_prefixes = ["gs://your-data/output/"]
      log_prefixes    = ["gs://your-staging/google-cloud-dataproc-metainfo/"]
    }
  }
}
