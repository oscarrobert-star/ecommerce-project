variable "domain_name" {
  type        = string
  description = "Base domain (example.com)"
}

variable "subdomains" {
  type        = list(string)
  default     = ["www", "admin", "app"]
  description = "List of subdomains to create"
}

variable "hosted_zone_id" {
  type        = string
  default     = ""
  description = "Route53 hosted zone ID"
}

variable "hosted_zone_name" {
  type        = string
  default     = ""
  description = "Route53 hosted zone name"
}

variable "index_document" {
  type    = string
  default = "index.html"
}

variable "error_document" {
  type    = string
  default = "error.html"
}