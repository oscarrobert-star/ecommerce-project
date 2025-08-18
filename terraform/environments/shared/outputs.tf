output "task_execution_role_arn" {
    description = "The ARN of the ECS Task Execution Role"
    value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecr_repository_urls" {
    description = "Map of ECR repository URLs"
    value       = { for repo in aws_ecr_repository.this : repo.name => repo.repository_url }
  
}