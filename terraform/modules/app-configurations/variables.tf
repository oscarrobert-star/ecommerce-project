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

variable "env" {
    description = "Environment name (e.g., dev, staging, prod)"
    type        = string
    default     = "dev"
  
}

variable "payment_callback_url" {
  description = "URL for payment callback"
  type        = string
  default     = "https://api.ecommerce.com/payments/callback"
}

variable "paystack_secret_key" {
  description = "Paystack secret key for payment processing"
  type        = string
  sensitive   = true
  default     = "sk_test_3d3a69512e465c85fb29b3bedc14ab77d6b943ae"
  
}