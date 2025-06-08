provider "aws" {
  region = var.aws_region
}

locals {
  tags = {
    Environment = "Staging"
    Project     = "ecommerce"
  }
}

module "vpc" {
  source = "../../modules/vpc"
  tags = local.tags
}

module "app-configurations" {
  source = "../../modules/app-configurations"
  db_username = var.db_username
  tags = local.tags
}

module "IAM" {
  source = "../../modules/IAM"
  tags = local.tags
}

module "datastore" {
  source = "../../modules/database-and-caching"
  db_name             = "ecommerce"
  db_username         = module.app-configurations.database_username
  db_password         = module.app-configurations.database_password
  db_security_group_ids = [module.vpc.database_security_group_id]
  db_subnet_group = module.vpc.database_subnet_group_name
  instance_class = "db.t3.micro"
  tags = local.tags
  node_type = "cache.t3.micro"
  subnet_ids = module.vpc.private_subnet_ids

  depends_on = [ module.app-configurations, module.vpc ]
}

module "container-resources" {
  source = "../../modules/container-resources"
  service_names = local.service_names
  repository_names = local.service_names
  cluster_name = "ecommerce-staging-cluster"
  task_execution_role_arn = module.IAM.task_execution_role_arn
  task_role_arn = module.IAM.task_role_arn
  alb_listener_arn = module.vpc.alb_listener_arn
  service_paths = local.service_paths
  task_environment = local.task_environment
  subnet_ids = module.vpc.private_subnet_ids
  security_group_ids = [module.vpc.internal_security_group_id]
  vpc_id = module.vpc.vpc_id
  tags = local.tags
  region = var.aws_region

  depends_on = [ module.datastore, module.vpc ]
}