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

resource "aws_ecr_lifecycle_policy" "this" {
  for_each = toset(local.repository_names)

  repository = aws_ecr_repository.this[each.value].name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description   = "Expire untagged images older than 30 days"
        selection     = {
          tagStatus = "untagged"
          countType = "sinceImagePushed"
          countUnit = "days"
          countNumber = 1
        }
        action       = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description   = "Keep only 2 most recent tagged images"
        selection     = {
          tagStatus   = "tagged"
          countType   = "imageCountMoreThan"
          countNumber = 2
        }
        action       = {
          type = "expire"
        }
      }
    ]
  })
}