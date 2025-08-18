
# Define a map variable in your module to list your endpoints and their paths
# variable "api_endpoints" {
#   type = map(string)
#   default = {
#     cart  = "/cart"
#     order = "/order"
#   }
# }
variable "api_endpoints" {
  description = "Map of API endpoints to their paths"
  type        = list(string)
  default     = []
  
}

variable "tags" {
  description = "A map of tags to assign to resources"
  type        = map(string)
  default     = {}  
  
}

variable "load_balancer_arn" {
  description = "The ARN of the load balancer to integrate with the API Gateway"
  type        = string 
  
}

variable "vpc_link_id" {
  description = "The ID of the VPC link to use for the API Gateway integration"
  type        = string
  
}