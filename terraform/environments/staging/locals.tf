locals {
  service_names = ["orders", "products", "users", "payments", "checkout", "cart"]

  service_paths = {
    for name in local.service_names :
    name => "/${name}"
  }

  db_env = [
    { name = "DB_HOST",     value = module.datastore.db_instance_endpoint },
    { name = "DB_PORT",     value = "5432" },
    { name = "DB_NAME",     value = "ecommerce" },
    { name = "DB_USER",     value = module.app-configurations.database_username },
    { name = "DB_PASSWORD", value = module.app-configurations.database_password }
  ]

  payments_extra_env = [
    { name = "PAYSTACK_SECRET_KEY", value = "sk_test_3d3a69512e465c85fb29b3bedc14ab77d6b943ae" },
    { name = "PAYMENT_CALLBACK",    value = "https://api.ecommerce.com/payments/callback" }
  ]

  checkout_extra_env = [
    { name = "ORDERS_SERVICE_URL",  value = module.vpc.alb_dns_name },
    { name = "PAYMENT_SERVICE_URL", value = module.vpc.alb_dns_name }
  ]

  cart_env = [
    { name = "REDIS_HOST",         value = module.datastore.redis_endpoint },
    { name = "REDIS_PORT",         value = "6379" },
    { name = "CART_TTL_SECONDS",   value = "180" },
    { name = "CART_MAX_ITEMS",     value = "100" }
  ]

  task_environment = {
    orders   = local.db_env,
    products = local.db_env,
    users    = local.db_env,
    payments = concat(local.db_env, local.payments_extra_env),
    checkout = concat(local.db_env, local.checkout_extra_env),
    cart     = local.cart_env
  }

  api_endpoints = {
    orders   = "/orders",
    products = "/products",
    users    = "/users",
    payments = "/payments",
    checkout = "/checkout",
    cart     = "/cart"
  }  
}
