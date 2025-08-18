locals {
  repository_names = ["orders", "products", "users", "payments", "checkout", "cart"]

  tags = {
    Environment = "Shared"
    Project     = "ecommerce"
  }

}  