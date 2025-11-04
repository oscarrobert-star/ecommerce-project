provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1" # Only for ACM certificates
}

locals {
  tags = {
    Environment = "Staging"
    Project     = "ecommerce"
  }
}

module "vpc" {
  source = "../../modules/vpc"
  tags   = local.tags
}

module "app-configurations" {
  source      = "../../modules/app-configurations"
  db_username = var.db_username
  tags        = local.tags
}

module "IAM" {
  source = "../../modules/IAM"
  tags   = local.tags
  aws_region = var.aws_region

  depends_on = [module.datastore, module.app-configurations]
}

module "datastore" {
  source                  = "../../modules/database-and-caching"
  db_name                 = "ecommerce"
  db_username             = var.db_username
  db_security_group_ids   = [module.vpc.database_security_group_id]
  db_subnet_group         = module.vpc.database_subnet_group_name
  redis_subnet_group_name = module.vpc.redis_subnet_group_name
  instance_class          = "db.t3.micro"
  tags                    = local.tags
  node_type               = "cache.t3.micro"
  subnet_ids              = module.vpc.private_subnet_ids
  depends_on              = [module.app-configurations, module.vpc]
}

module "container-resources" {
  source           = "../../modules/container-resources"
  service_names    = local.service_names
  repository_names = local.service_names
  cluster_name     = "ecommerce-staging-cluster"
  # task_execution_role_arn = module.IAM.task_execution_role_arn
  secrets            = local.secrets
  task_role_arn      = module.IAM.task_role_arn
  alb_listener_arn   = module.vpc.alb_listener_arn
  service_paths      = local.service_paths
  task_environment   = local.task_environment
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.vpc.internal_security_group_id]
  vpc_id             = module.vpc.vpc_id
  tags               = local.tags
  region             = var.aws_region

  depends_on = [module.datastore, module.cognito]
}

module "api-integrations" {
  source                 = "../../modules/api-integrations"
  load_balancer_arn      = module.vpc.alb_listener_arn
  vpc_link_id            = module.vpc.vpc_link_id
  hosted_zone_name       = local.hosted_zone_name
  custom_api_domain_name = var.env != "production" ? "api.${var.env}.${local.domain_name}" : "api.${local.domain_name}"
  cors_allowed_origins = [
    "https://shop.${local.domain_name}",
    "https://admin.${local.domain_name}",
    "https://api.${var.env}.${local.domain_name}",
    "https://api.${local.domain_name}"
  ]

  depends_on    = [module.container-resources]
  api_endpoints = local.api_endpoint
  tags          = local.tags
}

module "cognito" {
  source = "../../modules/cognito"

  environment  = "dev"
  project_name = "ecommerce"

  # Development-specific settings
  password_minimum_length  = 6
  password_require_symbols = false
  mfa_configuration        = "OFF"

  callback_urls = [
    # "http://admin.localhost",
    # "http://client.localhost",
  ]
}

module "web-application" {
  source           = "../../modules/content-delivery-network"
  domain_name      = local.domain_name
  subdomains       = local.subdomains
  hosted_zone_name = local.hosted_zone_name
  index_document   = "index.html"
}
