variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ecommerce"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "user-service"
}

variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

variable "auto_verified_attributes" {
  description = "Attributes that should be auto-verified"
  type        = list(string)
  default     = ["email"]
}

variable "password_minimum_length" {
  description = "Minimum password length"
  type        = number
  default     = 8
}

variable "password_require_uppercase" {
  description = "Require uppercase letters in password"
  type        = bool
  default     = true
}

variable "password_require_lowercase" {
  description = "Require lowercase letters in password"
  type        = bool
  default     = true
}

variable "password_require_numbers" {
  description = "Require numbers in password"
  type        = bool
  default     = true
}

variable "password_require_symbols" {
  description = "Require symbols in password"
  type        = bool
  default     = false
}

variable "account_recovery_mechanism" {
  description = "Account recovery mechanism"
  type        = string
  default     = "verified_email"
}

variable "admin_create_user_only" {
  description = "Only allow admin to create users"
  type        = bool
  default     = false
}

variable "mfa_configuration" {
  description = "MFA configuration (OFF, ON, OPTIONAL)"
  type        = string
  default     = "OFF"
}

variable "enable_software_token_mfa" {
  description = "Enable software token MFA"
  type        = bool
  default     = false
}

variable "email_sending_account" {
  description = "Email sending account (COGNITO_DEFAULT or DEVELOPER)"
  type        = string
  default     = "COGNITO_DEFAULT"
}

variable "from_email_address" {
  description = "From email address for emails"
  type        = string
  default     = null
}

variable "explicit_auth_flows" {
  description = "Explicit authentication flows"
  type        = list(string)
  default = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
  ]
}

variable "generate_client_secret" {
  description = "Generate client secret"
  type        = bool
  default     = false
}

variable "refresh_token_validity" {
  description = "Refresh token validity in hours"
  type        = number
  default     = 30
}

variable "access_token_validity" {
  description = "Access token validity in hours"
  type        = number
  default     = 1
}

variable "id_token_validity" {
  description = "ID token validity in hours"
  type        = number
  default     = 1
}

variable "token_validity_units" {
  description = "Token validity units"
  type        = object({
    refresh_token = string
    access_token  = string
    id_token      = string
  })
  default = {
    refresh_token = "days"
    access_token  = "hours"
    id_token      = "hours"
  }
}

variable "supported_identity_providers" {
  description = "Supported identity providers"
  type        = list(string)
  default     = ["COGNITO"]
}

variable "callback_urls" {
  description = "Callback URLs for OAuth flows"
  type        = list(string)
  default     = []
}

variable "logout_urls" {
  description = "Logout URLs"
  type        = list(string)
  default     = []
}

variable "prevent_user_existence_errors" {
  description = "Prevent user existence errors"
  type        = string
  default     = "ENABLED"
}

variable "user_groups" {
  description = "List of user groups to create"
  type = list(object({
    name        = string
    description = string
    precedence  = number
    role_arn    = string
    tags        = map(string)
  }))
  default = [
    {
      name        = "admin"
      description = "Administrators"
      precedence  = 1
      role_arn    = null
      tags        = {}
    },
    {
      name        = "customer"
      description = "Customers"
      precedence  = 2
      role_arn    = null
      tags        = {}
    }
  ]
}

variable "domain" {
  description = "Custom domain for Cognito"
  type        = string
  default     = null
}