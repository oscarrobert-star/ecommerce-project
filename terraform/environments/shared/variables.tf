variable "repository_names" {
  type        = list(string)
  description = "List of ECR repository names to create"
}

variable "tags" {
  type        = map(string)
  description = "A map of tags to assign to resources"
  default     = {}  
  
}

variable "aws_region" {
  description = "AWS region for the staging environment"
  type        = string
  default     = "us-east-2"
  
}