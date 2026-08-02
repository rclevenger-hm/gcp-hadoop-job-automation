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
resource "google_monitoring_alert_policy" "dead_letter" {
  display_name = "${local.prefix} dead-letter messages"
  combiner     = "OR"
  conditions {
    display_name = "Messages require inspection"
    condition_threshold {
      filter          = "resource.type = \"pubsub_subscription\" AND resource.label.subscription_id = \"${google_pubsub_subscription.dead_letter.name}\" AND metric.type = \"pubsub.googleapis.com/subscription/num_undelivered_messages\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "60s"
    }
  }
  notification_channels = [google_monitoring_notification_channel.operations.name]
}
resource "google_billing_budget" "service" {
  billing_account = var.billing_account
  display_name    = "${local.prefix} project budget"
  budget_filter { projects = ["projects/${data.google_project.current.number}"] }
  amount {
    specified_amount {
      currency_code = var.budget_currency
      units         = tostring(var.monthly_budget)
    }
  }
  threshold_rules { threshold_percent = 0.8 }
  threshold_rules {
    threshold_percent = 1
    spend_basis       = "FORECASTED_SPEND"
  }
  all_updates_rule {
    monitoring_notification_channels = [google_monitoring_notification_channel.operations.name]
    disable_default_iam_recipients   = false
  }
  depends_on = [google_project_service.required]
}

resource "google_logging_metric" "review" {
  name   = "${local.prefix}-review"
  filter = "resource.type=cloud_run_revision AND resource.labels.service_name=~\"^${local.prefix}-\" AND jsonPayload.event=\"job_state\" AND jsonPayload.status=\"NEEDS_REVIEW\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
  depends_on = [google_project_service.required]
}
resource "google_monitoring_alert_policy" "review" {
  display_name = "${local.prefix} jobs need review"
  combiner     = "OR"
  conditions {
    display_name = "Uncertain remote job requires operator review"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"logging.googleapis.com/user/${google_logging_metric.review.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }
  notification_channels = [google_monitoring_notification_channel.operations.name]
}
