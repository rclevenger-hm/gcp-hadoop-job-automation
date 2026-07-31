resource "google_monitoring_notification_channel" "operations" {
  display_name = "${local.prefix} operations"
  type         = "email"
  labels       = { email_address = var.notification_email }
  depends_on   = [google_project_service.required]
}
resource "google_monitoring_alert_policy" "errors" {
  display_name = "${local.prefix} function errors"
  combiner     = "OR"
  conditions {
    display_name = "Five server errors in five minutes"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND resource.label.service_name = starts_with(\"${local.prefix}-\") AND metric.type = \"run.googleapis.com/request_count\" AND metric.label.response_code_class = \"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 4
      duration        = "0s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }
  notification_channels = [google_monitoring_notification_channel.operations.name]
  depends_on            = [google_project_service.required]
}
