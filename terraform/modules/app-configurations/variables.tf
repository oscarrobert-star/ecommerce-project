variable "db_username" {
  description = "Username for the RDS database"
  type        = string
  sensitive = true
}

# variable "db_password" {
#   description = "Password for the RDS database"
#   type        = string
#   sensitive = true
# }

variable "tags" {
    description = "A map of tags to assign to resources"
    type        = map(string)
    default     = {}
}