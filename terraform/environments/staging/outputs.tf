output "vpc_id" {
  description = "The ID of the VPC created in the staging environment"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs in the staging environment"
  value       = module.vpc.public_subnet_ids
}
output "private_subnet_ids" {
  description = "List of private subnet IDs in the staging environment"
  value       = module.vpc.private_subnet_ids
}
output "alb_security_group_id" {
  description = "The security group ID for the Application Load Balancer in the staging environment"
  value       = module.vpc.alb_security_group_id
}
output "internal_security_group_id" {
  description = "The security group ID for internal resources in the staging environment"
  value       = module.vpc.internal_security_group_id
}

output "redis_endpoint" {
  description = "The endpoint for the Redis service in the staging environment"
  value       = module.datastore.redis_endpoint
}

output "database_endpoint" {
  description = "The endpoint for the RDS database in the staging environment"
  value       = module.datastore.db_instance_endpoint
  
}