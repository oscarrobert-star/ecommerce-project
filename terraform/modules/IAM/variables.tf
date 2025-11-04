variable "tags" {
  description = "A map of tags to assign to resources"
  type        = map(string)
  default     = {}
}

variable "aws_region" {
  description = "AWS region for the staging environment"
  type        = string
  default     = "us-east-2"
  
}