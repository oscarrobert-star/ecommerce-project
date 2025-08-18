# this module creates an ECR repository for shared use across environments
resource "aws_ecr_repository" "this" {
  for_each = toset(local.repository_names)

  name = each.value

  image_scanning_configuration {
    scan_on_push = true
  }

  image_tag_mutability = "MUTABLE"

  tags = merge(local.tags, {
    Name = each.value
  })
}