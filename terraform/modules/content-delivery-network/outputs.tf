output "bucket_names" {
  description = "Map of subdomain to S3 bucket names"
  value = {
    for subdomain, bucket in aws_s3_bucket.websites : subdomain => bucket.bucket
  }
}

output "cloudfront_domains" {
  description = "Map of subdomain to CloudFront domain names"
  value = {
    for subdomain, distribution in aws_cloudfront_distribution.cdns : subdomain => distribution.domain_name
  }
}

output "cloudfront_arns" {
  description = "Map of subdomain to CloudFront distribution ARNs"
  value = {
    for subdomain, distribution in aws_cloudfront_distribution.cdns : subdomain => distribution.arn
  }
}

output "acm_certificate_arns" {
  description = "Map of subdomain to ACM certificate ARNs"
  value = {
    for subdomain, cert in aws_acm_certificate.certs : subdomain => cert.arn
  }
}

output "oai_ids" {
  description = "Map of subdomain to OAI IDs"
  value = {
    for subdomain, oai in aws_cloudfront_origin_access_identity.oais : subdomain => oai.id
  }
}