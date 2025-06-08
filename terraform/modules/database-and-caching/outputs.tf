output "db_instance_endpoint" {
    description = "The connection endpoint for the RDS instance"
    value       = aws_db_instance.postgres.endpoint
}

output "db_instance_identifier" {
    description = "The RDS instance identifier"
    value       = aws_db_instance.postgres.id
}

output "db_instance_arn" {
    description = "The ARN of the RDS instance"
    value       = aws_db_instance.postgres.arn
}

output "redis_endpoint" {
    description = "The connection endpoint for the Redis instance"
    value = aws_elasticache_serverless_cache.ecommerce.endpoint
  
}