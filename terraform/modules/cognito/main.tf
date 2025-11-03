provider "aws" {
  region = var.aws_region
}

locals {
  common_tags = merge({
    Project     = var.project_name
    Environment = var.environment
    Owner       = var.owner
  }, var.additional_tags)
}

resource "aws_cognito_user_pool" "user_pool" {
  name = "${var.project_name}-user-pool-${var.environment}"

  auto_verified_attributes = var.auto_verified_attributes

  password_policy {
    minimum_length    = var.password_minimum_length
    require_uppercase = var.password_require_uppercase
    require_lowercase = var.password_require_lowercase
    require_numbers   = var.password_require_numbers
    require_symbols   = var.password_require_symbols
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = var.account_recovery_mechanism
      priority = 1
    }
  }

  admin_create_user_config {
    allow_admin_create_user_only = var.admin_create_user_only
  }

  mfa_configuration = var.mfa_configuration

  dynamic "software_token_mfa_configuration" {
    for_each = var.enable_software_token_mfa ? [1] : []
    content {
      enabled = true
    }
  }

  email_configuration {
    email_sending_account = var.email_sending_account
    from_email_address    = var.from_email_address
  }

  tags = local.common_tags

  lifecycle {
    ignore_changes = [
      schema # Ignore schema changes to prevent recreation
    ]
  }
}

resource "aws_cognito_user_pool_client" "user_pool_client" {
  name         = "${var.project_name}-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.user_pool.id

  explicit_auth_flows = var.explicit_auth_flows

  generate_secret = var.generate_client_secret

  refresh_token_validity        = var.refresh_token_validity
  access_token_validity         = var.access_token_validity
  id_token_validity             = var.id_token_validity
  token_validity_units {
    refresh_token = var.token_validity_units.refresh_token
    access_token  = var.token_validity_units.access_token
    id_token      = var.token_validity_units.id_token
  }

  supported_identity_providers = var.supported_identity_providers

  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  prevent_user_existence_errors = var.prevent_user_existence_errors

  # tags = local.common_tags
}

resource "aws_cognito_user_group" "groups" {
  for_each = { for group in var.user_groups : group.name => group }

  name         = each.value.name
  user_pool_id = aws_cognito_user_pool.user_pool.id
  description  = each.value.description
  precedence   = each.value.precedence
  role_arn     = each.value.role_arn

  # tags = merge(local.common_tags, each.value.tags)
}

resource "aws_cognito_user_pool_domain" "domain" {
  count = var.domain != null ? 1 : 0

  domain       = var.domain
  user_pool_id = aws_cognito_user_pool.user_pool.id
}