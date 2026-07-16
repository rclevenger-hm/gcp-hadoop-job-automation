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
resource "google_firestore_index" "history" {
  project    = var.project_id
  database   = google_firestore_database.data.name
  collection = "items"
  fields {
    field_path = "tenant"
    order      = "ASCENDING"
  }
  fields {
    field_path = "kind"
    order      = "ASCENDING"
  }
  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }
  fields {
    field_path = "__name__"
    order      = "DESCENDING"
  }
}
resource "google_firestore_index" "status_history" {
  project    = var.project_id
  database   = google_firestore_database.data.name
  collection = "items"
  fields {
    field_path = "tenant"
    order      = "ASCENDING"
  }
  fields {
    field_path = "kind"
    order      = "ASCENDING"
  }
  fields {
    field_path = "status"
    order      = "ASCENDING"
  }
  fields {
    field_path = "created_at"
    order      = "DESCENDING"
  }
  fields {
    field_path = "__name__"
    order      = "DESCENDING"
  }
}
resource "google_firestore_index" "active" {
  project    = var.project_id
  database   = google_firestore_database.data.name
  collection = "items"
  fields {
    field_path = "active_shard"
    order      = "ASCENDING"
  }
  fields {
    field_path = "next_check"
    order      = "ASCENDING"
  }
  fields {
    field_path = "__name__"
    order      = "ASCENDING"
  }
}

resource "google_firestore_field" "unindexed_payloads" {
  for_each   = toset(["request", "profile"])
  project    = var.project_id
  database   = google_firestore_database.data.name
  collection = "items"
  field      = each.value
  index_config {}
}
