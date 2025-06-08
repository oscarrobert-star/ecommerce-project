variable "repository_names" {
  type        = list(string)
  description = "List of ECR repository names to create"
}

variable "cluster_name" {
  type        = string
  description = "Name of the ECS cluster to create"
}

variable "service_names" {
  type        = list(string)
  description = "List of ECS service names to create"
}

variable "tags" {
  type        = map(string)
  description = "A map of tags to assign to resources"
  default     = {}  
  
}

variable "task_environment" {
  description = "Map of service name to environment variables"
  type = map(list(object({
    name  = string
    value = string
  })))
  default = {}
}

variable "alb_listener_arn" {
  description = "ARN of the ALB listener for path-based routing"
  type        = string
}

variable "service_paths" {
  description = "Map of service name to path to route"
  type        = map(string)
}

variable "vpc_id" {
  description = "VPC ID where the ECS services will be deployed"
  type        = string       
}

variable "subnet_ids" {
  description = "List of subnet IDs for the ECS services"
  type        = list(string)
  
}

variable "security_group_ids" {
  description = "List of security group IDs for the ECS services"
  type        = list(string)    
  
}

variable "task_execution_role_arn" {
  description = "ARN of the IAM role for ECS task execution"
  type        = string
}
variable "task_role_arn" {
  description = "ARN of the IAM role for ECS tasks"
  type        = string
}

variable "region" {
  description = "AWS region where the resources will be created"
  type        = string
  
}