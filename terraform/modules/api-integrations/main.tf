# This module is used to create API integrations for the AWS API Gateway.
# It includes the creation of API Gateway HTTP API, API Gateway Resource, API Gateway Method, and API Gateway Integration.
# Let's include AWS load balancer and API Gateway resources in this module.

# Create an HTTP API Gateway for the ecommerce project.
resource "aws_apigatewayv2_api" "http_api" {
  name          = "ecommerce-http-api"
  protocol_type = "HTTP"

  # Merge user-defined tags with a specific Name tag for identification.
  tags = merge(var.tags, { Name = "ecommerce-http-api" })
}

# Create an HTTP_PROXY integration between the API Gateway and the AWS Load Balancer.
resource "aws_apigatewayv2_integration" "http_integration" {
  api_id             = aws_apigatewayv2_api.http_api.id
  integration_type   = "HTTP_PROXY"
  integration_uri    = var.load_balancer_arn
  integration_method = "ANY"
  connection_type    = "VPC_LINK"
  connection_id      = var.vpc_link_id

  request_parameters = {
    "overwrite:path" = "$request.path"
  }

  # Merge user-defined tags with a specific Name tag for identification.
  # tags = merge(var.tags, { Name = "ecommerce-http-integration" })
}

# Example: Create routes and integrations for multiple endpoints (cart, order, etc.)
# Create an API Gateway route and integration for each endpoint
resource "aws_apigatewayv2_route" "service_routes" {
  for_each = toset(var.api_endpoints)

  api_id    = aws_apigatewayv2_api.http_api.id
  # route_key = "ANY ${each.value}/{proxy+}"
  route_key = each.value
  target    = "integrations/${aws_apigatewayv2_integration.http_integration.id}"
}

# Optionally, create a stage to deploy the routes
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "dev"
  auto_deploy = true

  # Enable access logging for this stage
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      # Request identification
      requestId     = "$context.requestId"
      requestTime   = "$context.requestTime"
      ip            = "$context.identity.sourceIp"
      
      # Routing information
      routeKey      = "$context.routeKey"
      path          = "$context.path"
      resourcePath  = "$context.resourcePath"
      
      # Integration details
      status            = "$context.status"
      integrationError = "$context.integration.error"
      responseLatency   = "$context.responseLatency"
      
      # Proxy path information (corrected)
      proxyPath     = "$request.path.proxy"  

      httpMethod         = "$context.httpMethod"
      integrationLatency = "$context.integrationLatency"
      protocol           = "$context.protocol"
      responseLength     = "$context.responseLength"
    })
  }

  tags = merge(var.tags, { Name = "ecommerce-dev-stage" })
}

resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${aws_apigatewayv2_api.http_api.name}"
  retention_in_days = 3

  tags = merge(var.tags, { Name = "api-gateway-logs" })
}
