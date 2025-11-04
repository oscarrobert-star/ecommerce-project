# Lookup hosted zone if id not supplied
data "aws_route53_zone" "selected" {
  count       = var.hosted_zone_id == "" && var.hosted_zone_name != "" ? 1 : 0
  name        = var.hosted_zone_name
  private_zone = false
}