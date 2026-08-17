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
run "secure_defaults" {
  command = plan
  assert {
    condition     = google_storage_bucket.source.public_access_prevention == "enforced" && google_storage_bucket.source.uniform_bucket_level_access && !google_storage_bucket.source.force_destroy
    error_message = "Source artifacts must remain private and protected."
  }
  assert {
    condition     = google_firestore_database.data.delete_protection_state == "DELETE_PROTECTION_ENABLED" && google_firestore_database.data.deletion_policy == "ABANDON" && google_firestore_database.data.point_in_time_recovery_enablement == "POINT_IN_TIME_RECOVERY_ENABLED"
    error_message = "Firestore needs deletion and recovery safeguards."
  }
  assert {
    condition     = google_cloudfunctions2_function.service["worker"].service_config[0].timeout_seconds < google_pubsub_subscription.jobs.ack_deadline_seconds
    error_message = "Worker execution must end before redelivery."
  }
  assert {
    condition     = google_pubsub_subscription.jobs.dead_letter_policy[0].max_delivery_attempts == 5
    error_message = "Pub/Sub must retain exhausted messages."
  }
  assert {
    condition     = alltrue([for binding in google_cloud_run_service_iam_member.consumers : startswith(binding.member, "serviceAccount:")])
    error_message = "Only explicit service accounts may invoke the API."
  }
  assert {
    condition     = google_cloudfunctions2_function.service["api"].service_config[0].environment_variables["TOKEN_AUDIENCE"] == "https://us-central1-hadoop-test-project.cloudfunctions.net/hadoop-dev-api"
    error_message = "Application audience must match the canonical endpoint."
  }
  assert {
    condition     = alltrue([for role in google_project_iam_custom_role.dataproc : !contains(role.permissions, "dataproc.clusters.delete") && !contains(role.permissions, "dataproc.jobs.delete")]) && !contains(google_project_iam_custom_role.dataproc["api"].permissions, "dataproc.jobs.create")
    error_message = "Runtimes must not delete clusters/jobs or submit through the API identity."
  }
  assert {
    condition     = google_cloudfunctions2_function.service["api"].build_config[0].runtime == "python313" && google_cloud_scheduler_job.reconcile.schedule == "* * * * *"
    error_message = "Use supported Python and minute reconciliation."
  }
  assert {
    condition     = google_storage_bucket_iam_member.logs["your-staging"].condition[0].expression == "resource.name.startsWith(\"projects/_/buckets/your-staging/objects/google-cloud-dataproc-metainfo/\")"
    error_message = "Driver log grants must be prefix-scoped."
  }
}
run "reject_unbounded_quota" {
  command = plan
  variables { daily_job_limit = -1 }
  expect_failures = [var.daily_job_limit]
}
run "reject_public_consumers" {
  command = plan
  variables {
    cluster_profiles = {
      analytics = {
        cluster_name    = "analytics-cluster"
        allowed_callers = ["allUsers"]
        jar_prefixes    = ["gs://your-artifacts/approved/"]
        input_prefixes  = ["gs://your-data/input/"]
        output_prefixes = ["gs://your-data/output/"]
        log_prefixes    = ["gs://your-staging/logs/"]
      }
    }
  }
  expect_failures = [var.cluster_profiles]
}
