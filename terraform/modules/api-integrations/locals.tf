locals {
  # Zone ID logic
  zone_id = var.hosted_zone_id != "" ? var.hosted_zone_id : (length(data.aws_route53_zone.selected) > 0 ? data.aws_route53_zone.selected[0].id : "")

  api_cert_dvo_map = {
    for dvo in aws_acm_certificate.api_cert.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}