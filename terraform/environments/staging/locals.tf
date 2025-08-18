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
    { name = "DB_SECRET_ARN", value = module.datastore.db_password_secret_arn },
    { name = "AWS_REGION", value = var.aws_region }
    # { name = "DB_PASSWORD", valueFrom = module.datastore.db_password_secret_arn }
  ]


  db_secrets = [
    { name = "DB_PASSWORD", valueFrom = module.datastore.db_password_secret_arn },
    # { name = "DB_USERNAME", valueFrom = module.app-configurations.db_username_param_arn }
  ]

  payments_secrets = [
    { name = "PAYSTACK_SECRET_KEY", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/paystack_secret_key" },
    { name = "PAYMENT_CALLBACK", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/payment_callback_url" }
  ]

#   payments_extra_env = [
#     { name = "PAYSTACK_SECRET_KEY", value = "sk_test_3d3a69512e465c85fb29b3bedc14ab77d6b943ae" },
#     { name = "PAYMENT_CALLBACK",    value = "https://api.ecommerce.com/payments/callback" }
#   ]

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
    payments = local.db_env,
    checkout = local.checkout_extra_env,
    cart     = local.cart_env
  }

  secrets = {
    orders   = local.db_secrets,
    products = local.db_secrets,
    users    = local.db_secrets,
    payments = local.payments_secrets
  }

  api_endpoint = [
    # cart service endpoints
    "POST /cart/add",
    "POST /cart/remove",
    "GET /cart",
    "GET /cart/health",
    "POST /cart/clear",
    "PATCH /cart/edit",
    # checkout service endpoints
    "POST /checkout",
    "GET /checkout/health",
    # orders service endpoints
    "POST /orders",
    "GET /orders",
    "GET /orders/{id}",
    "GET /orders/health",
    "PATCH /orders/{id}/payment_status",
    "PATCH /orders/{id}/shipping_status",
    "GET /orders/status/{payment_id}",
    # payments service endpoints
    "POST /payments/pay",
    "POST /payments/webhook",
    "GET /payments/health",
    # products service endpoints
    "POST /products",
    "GET /products",
    "GET /products/{id}",
    "PATCH /products/{id}",
    "DELETE /products/{id}",
    "GET /products/health",
    "POST /products/bulk",
    # users service endpoints
    "POST /users/signup",
    "POST /users/login",
    "POST /users/logout",
    "GET /users/profile",
    "POST /users/confirm-signup",
    "GET /users/health"
  ]
}