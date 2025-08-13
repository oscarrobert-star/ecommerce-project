# terraform/modules/api-integrations/outputs.tf
output "http_api_id" {
  description = "The ID of the HTTP API Gateway"
  value       = aws_apigatewayv2_api.http_api.id
}

output "http_api_endpoint" {
  description = "The endpoint URL of the HTTP API Gateway"
  value       = aws_apigatewayv2_api.http_api
}