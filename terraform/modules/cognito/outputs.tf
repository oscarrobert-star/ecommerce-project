output "user_pool_id" {
  description = "The ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.id
}

output "user_pool_arn" {
  description = "The ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.arn
}

output "user_pool_endpoint" {
  description = "The endpoint name of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.endpoint
}

output "client_id" {
  description = "The ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.user_pool_client.id
}

output "client_secret" {
  description = "The client secret of the Cognito User Pool Client (if generated)"
  value       = aws_cognito_user_pool_client.user_pool_client.client_secret
  sensitive   = true
}

output "user_group_ids" {
  description = "Map of user group names to their IDs"
  value       = { for k, v in aws_cognito_user_group.groups : k => v.id }
}

output "domain" {
  description = "The domain of the Cognito User Pool"
  value       = try(aws_cognito_user_pool_domain.domain[0].domain, null)
}

output "domain_cloudfront_distribution" {
  description = "The CloudFront distribution for the custom domain"
  value       = try(aws_cognito_user_pool_domain.domain[0].cloudfront_distribution_arn, null)
}