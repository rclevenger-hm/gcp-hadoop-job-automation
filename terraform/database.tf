resource "google_firestore_database" "data" {
  project                           = var.project_id
  name                              = local.prefix
  location_id                       = var.firestore_location
  type                              = "FIRESTORE_NATIVE"
  concurrency_mode                  = "PESSIMISTIC"
  delete_protection_state           = "DELETE_PROTECTION_ENABLED"
  deletion_policy                   = "ABANDON"
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_ENABLED"
  depends_on                        = [google_project_service.required]
}
resource "google_firestore_field" "expiry" {
  project    = var.project_id
  database   = google_firestore_database.data.name
  collection = "items"
  field      = "expiresOn"
  ttl_config {}
  index_config {}
}
