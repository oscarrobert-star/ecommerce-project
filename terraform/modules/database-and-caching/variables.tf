variable "db_name" {
    description = "The name of the database to create"
    type        = string
}

variable "db_username" {
    description = "Username for the database"
    type        = string
    sensitive = true
}

# variable "db_username_param_name" {
#     description = "SSM parameter name for the database username"
#     type        = string    
# }

# variable "db_password" {
#     description = "Password for the database"
#     type        = string
#     sensitive   = true
# }

variable "db_subnet_group" {
    description = "Subnet group for the RDS instance"
    type        = string
}

variable "db_security_group_ids" {
    description = "List of security group IDs to associate with the RDS instance"
    type        = list(string)
}

variable "tags" {
    description = "A map of tags to assign to resources"
    type        = map(string)
    default     = {}
}

variable "instance_class" {
    description = "Instance class for the RDS instance"
    type        = string
    default     = "db.t3.micro"
}

variable "node_type" {
    description = "Node type for the ElastiCache Redis cluster"
    type        = string
    default     = "cache.t3.micro"
  
}

variable "subnet_ids" {
    description = "List of subnet IDs for the ElastiCache Redis cluster"
    type        = list(string)
}

variable "redis_subnet_group_name" {
    description = "Subnet group name for the ElastiCache Redis cluster"
    type        = string
}