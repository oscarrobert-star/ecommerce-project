# This module is used to create API integrations for the AWS API Gateway.

# Create an HTTP API Gateway for the ecommerce project.
resource "aws_apigatewayv2_api" "http_api" {
  name          = "ecommerce-http-api"
  protocol_type = "HTTP"

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
}

# Create an API Gateway route and integration for each endpoint
resource "aws_apigatewayv2_route" "service_routes" {
  for_each = toset(var.api_endpoints)

  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = each.value
  target    = "integrations/${aws_apigatewayv2_integration.http_integration.id}"
}

# --- REGIONAL ACM CERTIFICATE CREATION AND VALIDATION ---

# 1. Create the Regional ACM certificate (uses the module's default provider region)
resource "aws_acm_certificate" "api_cert" {
  domain_name       = var.custom_api_domain_name
  validation_method = "DNS"
  
  lifecycle {
    create_before_destroy = true
  }
}

# 2. Create Route53 records for DNS validation
resource "aws_route53_record" "api_cert_validation" {
  
  for_each = {
    for dvo in aws_acm_certificate.api_cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = local.zone_id
}

# 3. Wait for Certificate Validation to complete
resource "aws_acm_certificate_validation" "api_cert_validation" {
  certificate_arn         = aws_acm_certificate.api_cert.arn
  
  validation_record_fqdns = [for r in aws_route53_record.api_cert_validation : r.fqdn]
}

# --- API GATEWAY STAGE AND LOGGING ---

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
      
      # Proxy path information
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

# --- CUSTOM DOMAIN MAPPING ---

# 4. Define the Custom Domain Name for API Gateway
resource "aws_apigatewayv2_domain_name" "custom_domain" {
  domain_name = var.custom_api_domain_name
  
  domain_name_configuration {
    # Use the regional certificate ARN that was just validated
    certificate_arn = aws_acm_certificate_validation.api_cert_validation.certificate_arn 
    endpoint_type   = "REGIONAL" 
    security_policy = "TLS_1_2"
  }

  tags = merge(var.tags, { Name = "ecommerce-api-domain" })
  
  depends_on = [aws_acm_certificate_validation.api_cert_validation]
}

# 5. Map the API and Stage to the Custom Domain
resource "aws_apigatewayv2_api_mapping" "api_mapping" {
  api_id      = aws_apigatewayv2_api.http_api.id
  domain_name = aws_apigatewayv2_domain_name.custom_domain.id
  stage       = aws_apigatewayv2_stage.default.id
}

# 6. Create the Route 53 DNS Record (Alias)
resource "aws_route53_record" "api_alias" {
  zone_id = local.zone_id
  name    = aws_apigatewayv2_domain_name.custom_domain.domain_name
  type    = "A"

  alias {
    name                   = aws_apigatewayv2_domain_name.custom_domain.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.custom_domain.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }

  depends_on = [aws_apigatewayv2_api_mapping.api_mapping]
}