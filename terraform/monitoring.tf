resource "google_monitoring_notification_channel" "operations" {
  display_name = "${local.prefix} operations"
  type         = "email"
  labels       = { email_address = var.notification_email }
  depends_on   = [google_project_service.required]
}
