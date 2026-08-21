variable "project_id" {
  type = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Use an existing GCP project ID."
  }
}
variable "name" {
  type    = string
  default = "hadoop"
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{3,11}$", var.name))
    error_message = "Use 4–12 lowercase letters, digits, or hyphens, starting with a letter."
  }
}
variable "environment" {
  type    = string
  default = "dev"
  validation {
    condition     = contains(["dev", "stage", "prod"], var.environment)
    error_message = "Choose dev, stage, or prod."
  }
}
variable "region" {
  type    = string
  default = "us-central1"
}
variable "firestore_location" {
  type    = string
  default = "us-central1"
}
variable "notification_email" {
  type = string
  validation {
    condition     = can(regex("^[^@ ]+@[^@ ]+\\.[^@ ]+$", var.notification_email))
    error_message = "Provide an operational notification email."
  }
}
variable "billing_account" {
  type = string
  validation {
    condition     = can(regex("^[A-Z0-9]{6}-[A-Z0-9]{6}-[A-Z0-9]{6}$", var.billing_account))
    error_message = "Provide the billing account ID for a project-filtered budget."
  }
}
variable "monthly_budget" {
  type    = number
  default = 100
  validation {
    condition     = var.monthly_budget >= 1 && floor(var.monthly_budget) == var.monthly_budget
    error_message = "Use a positive whole budget amount in the billing account currency."
  }
}
variable "budget_currency" {
  type    = string
  default = "USD"
  validation {
    condition     = can(regex("^[A-Z]{3}$", var.budget_currency))
    error_message = "Use the billing account ISO currency code."
  }
}
variable "daily_job_limit" {
  type    = number
  default = 100
  validation {
    condition     = var.daily_job_limit >= 1 && var.daily_job_limit <= 100000 && floor(var.daily_job_limit) == var.daily_job_limit
    error_message = "Daily limit must be an integer from 1 to 100000."
  }
}
variable "requests_per_minute" {
  type    = number
  default = 60
  validation {
    condition     = var.requests_per_minute >= 1 && var.requests_per_minute <= 1000 && floor(var.requests_per_minute) == var.requests_per_minute
    error_message = "Minute limit must be an integer from 1 to 1000."
  }
}
variable "retention_days" {
  type    = number
  default = 30
  validation {
    condition     = var.retention_days >= 1 && var.retention_days <= 365 && floor(var.retention_days) == var.retention_days
    error_message = "Retention must be 1–365 whole days."
  }
}
