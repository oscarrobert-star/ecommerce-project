locals {
  repository_names = ["orders", "products", "users", "payments", "checkout", "cart", "notifications"]

  tags = {
    Environment = "Shared"
    Project     = "ecommerce"
  }

}  