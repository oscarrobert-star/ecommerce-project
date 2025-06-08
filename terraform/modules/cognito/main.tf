provider "aws" {
  region = var.aws_region
}

locals {
  common_tags = {
    Project     = "ecommerce"
    Environment = "dev"
    Owner       = "user-service"
  }
}

resource "aws_cognito_user_pool" "user_pool" {
  name = "ecommerce-user-pool"

  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_uppercase = true
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  tags = local.common_tags
}

resource "aws_cognito_user_pool_client" "user_pool_client" {
  name         = "ecommerce-user-client"
  user_pool_id = aws_cognito_user_pool.user_pool.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
  ]

  generate_secret = false

#   tags = local.common_tags
}

resource "aws_cognito_user_group" "admin_group" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.user_pool.id
  description  = "Administrators"
  precedence   = 1

#   tags = local.common_tags
}

resource "aws_cognito_user_group" "customer_group" {
  name         = "customer"
  user_pool_id = aws_cognito_user_pool.user_pool.id
  description  = "Customers"
  precedence   = 2

#   tags = local.common_tags
}
