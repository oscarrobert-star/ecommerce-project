locals {
  # Zone ID logic
  zone_id = var.hosted_zone_id != "" ? var.hosted_zone_id : (length(data.aws_route53_zone.selected) > 0 ? data.aws_route53_zone.selected[0].id : "")
  
  # Convert set to map for certificates (using 'each.key' which is the subdomain name)
  certs_map = { for subdomain_name in var.subdomains : subdomain_name => aws_acm_certificate.certs[subdomain_name] }
}