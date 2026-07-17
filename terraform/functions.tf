resource "google_cloudfunctions2_function" "service" {
  for_each = local.runtime_names
  name     = "${local.prefix}-${each.key}"
  location = var.region
  build_config {
    runtime         = "python313"
    entry_point     = each.key
    service_account = google_service_account.build.id
    source {
      storage_source {
        bucket = google_storage_bucket.source.name
        object = google_storage_bucket_object.source.name
      }
    }
  }
  service_config {
    available_memory                 = "512M"
    available_cpu                    = "1"
    min_instance_count               = 0
    max_instance_count               = each.key == "reconcile" ? 1 : var.maximum_instances
    max_instance_request_concurrency = each.key == "api" ? 4 : 1
    timeout_seconds                  = each.key == "reconcile" ? 120 : 60
    service_account_email            = google_service_account.runtime[each.key].email
    ingress_settings                 = "ALLOW_ALL"
    all_traffic_on_latest_revision   = true
    environment_variables = merge(local.common_env, each.key == "api" ? {
      TOKEN_AUDIENCE        = local.api_url
      ALLOWED_CALLER_EMAILS = join(",", sort(tolist(local.consumers)))
    } : {})
  }
  labels     = local.labels
  depends_on = [google_project_service.required, google_project_iam_member.build, google_storage_bucket_iam_member.build_source, google_project_iam_member.database, google_project_iam_member.dataproc, google_storage_bucket_iam_member.logs, google_pubsub_topic_iam_member.publisher]
}
resource "google_cloud_run_service_iam_member" "consumers" {
  for_each = local.consumers
  location = var.region
  service  = google_cloudfunctions2_function.service["api"].name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${each.value}"
}
