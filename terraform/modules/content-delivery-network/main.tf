# AWS provider for us-east-1 (required for CloudFront certificates)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# Create S3 buckets for each subdomain
resource "aws_s3_bucket" "websites" {
  for_each = toset(var.subdomains)
  
  bucket = "${each.key}.${var.domain_name}"
  tags = {
    Name = "${each.key}.${var.domain_name}"
  }
}

resource "aws_s3_bucket_public_access_block" "blocks" {
  for_each = aws_s3_bucket.websites

  bucket = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# OAI for each subdomain
resource "aws_cloudfront_origin_access_identity" "oais" {
  for_each = toset(var.subdomains)

  comment = "OAI for ${each.key}.${var.domain_name}"
}

# Bucket policies for each S3 bucket
resource "aws_s3_bucket_policy" "bucket_policies" {
  for_each = aws_s3_bucket.websites

  bucket = each.value.id
  policy = data.aws_iam_policy_document.s3_policies[each.key].json
}

data "aws_iam_policy_document" "s3_policies" {
  for_each = toset(var.subdomains)

  statement {
    actions = ["s3:GetObject"]
    principals {
      type        = "CanonicalUser"
      identifiers = [aws_cloudfront_origin_access_identity.oais[each.key].s3_canonical_user_id]
    }
    resources = ["${aws_s3_bucket.websites[each.key].arn}/*"]
  }

  statement {
    actions = ["s3:ListBucket"]
    principals {
      type        = "CanonicalUser"
      identifiers = [aws_cloudfront_origin_access_identity.oais[each.key].s3_canonical_user_id]
    }
    resources = [aws_s3_bucket.websites[each.key].arn]
  }
}

# INDIVIDUAL: ACM certificate for EACH subdomain
resource "aws_acm_certificate" "certs" {
  for_each  = toset(var.subdomains)
  provider = aws.us_east_1

  domain_name       = "${each.value}.${var.domain_name}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "cf-cert-${each.value}.${var.domain_name}"
  }
}

# FIXED: Certificate validation records using the local certs_map
resource "aws_route53_record" "cert_validations" {
  for_each = local.certs_map

  zone_id = local.zone_id
  
  # 🛑 FIX: Use tolist() to convert the set to a list before indexing [0]
  name    = tolist(each.value.domain_validation_options)[0].resource_record_name
  type    = tolist(each.value.domain_validation_options)[0].resource_record_type
  ttl     = 60
  records = [tolist(each.value.domain_validation_options)[0].resource_record_value]
}

# FIXED: Certificate validation
resource "aws_acm_certificate_validation" "cert_validations" {
  for_each  = local.certs_map
  provider = aws.us_east_1

  certificate_arn         = each.value.arn
  # We reference the fqdn output from the route53 record created above
  validation_record_fqdns = [aws_route53_record.cert_validations[each.key].fqdn] 
}

# Individual CloudFront distribution for EACH subdomain
resource "aws_cloudfront_distribution" "cdns" {
  for_each = toset(var.subdomains)

  enabled             = true
  is_ipv6_enabled     = true
  aliases             = ["${each.key}.${var.domain_name}"]
  default_root_object = var.index_document
  price_class         = "PriceClass_100"
  comment             = "CDN for ${each.key}.${var.domain_name}"

  origin {
    domain_name = aws_s3_bucket.websites[each.key].bucket_regional_domain_name
    origin_id   = "s3-${each.key}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.oais[each.key].cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    target_origin_id       = "s3-${each.key}"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    compress         = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  # SPA error handling
  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/${var.index_document}"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/${var.index_document}"
    error_caching_min_ttl = 0
  }

  viewer_certificate {
    # Reference the ARN from the individual certificate for this subdomain
    acm_certificate_arn      = aws_acm_certificate.certs[each.key].arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2019"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = {
    Name = "cdn-${each.key}.${var.domain_name}"
  }
}

# Route53 records for each subdomain
resource "aws_route53_record" "aliases" {
  for_each = toset(var.subdomains)

  zone_id = local.zone_id
  name    = "${each.key}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.cdns[each.key].domain_name
    zone_id                = aws_cloudfront_distribution.cdns[each.key].hosted_zone_id
    evaluate_target_health = false
  }
}

