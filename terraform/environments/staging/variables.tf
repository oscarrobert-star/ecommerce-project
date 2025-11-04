variable "aws_region" {
  description = "AWS region for the staging environment"
  type        = string
  default     = "us-east-2"
  
}

variable "db_username" {
  description = "Username for the RDS database"
  type        = string
  sensitive = true
  default     = "ecommerce_admin"
}

variable "db_password" {
  description = "Password for the RDS database"
  type        = string
  sensitive = true
  default     = "strongPassword!23"
}

variable "env" {
    description = "Environment name (e.g., dev, staging, prod)"
    type        = string
    default     = "dev"
  
}

variable "image_bucket_name" {
  description = "S3 bucket name for storing product images"
  type        = string
  default     = ""
  
}