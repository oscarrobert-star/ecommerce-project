output "db_instance_endpoint" {
    description = "The connection endpoint for the RDS instance"
    value       = aws_db_instance.postgres.address
}

output "db_instance_identifier" {
    description = "The RDS instance identifier"
    value       = aws_db_instance.postgres.id
}

output "db_instance_arn" {
    description = "The ARN of the RDS instance"
    value       = aws_db_instance.postgres.arn
}

output "db_password_secret_arn" {
  value = aws_db_instance.postgres.master_user_secret[0].secret_arn
  description = "The ARN of the secret containing the RDS instance password"
}
# output "redis_endpoint" {
#     description = "The connection endpoint for the Redis instance"
#     value = aws_elasticache_serverless_cache.ecommerce.endpoint
  
# }

output "redis_endpoint" {
    description = "The connection endpoint for the Redis cluster"
    value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}