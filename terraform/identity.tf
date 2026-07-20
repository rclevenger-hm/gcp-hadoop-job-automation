resource "google_service_account" "runtime" {
  for_each     = local.runtime_names
  account_id   = "${local.prefix}-${each.key}"
  display_name = "Hadoop ${each.key} runtime"
}
