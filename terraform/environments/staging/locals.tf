locals {
  service_names = ["orders", "products", "users", "payments", "checkout", "cart"]

  service_paths = {
    for name in local.service_names :
    name => "/${name}"
  }

  db_env = [
    { name = "DB_HOST", value = module.datastore.db_instance_endpoint },
    { name = "DB_PORT", value = "5432" },
    { name = "DB_NAME", value = "ecommerce" },
    { name = "DB_SECRET_ARN", value = module.datastore.db_password_secret_arn },
    { name = "AWS_REGION", value = var.aws_region }
    # { name = "DB_PASSWORD", valueFrom = module.datastore.db_password_secret_arn }
  ]
 
  cors_origins = [
    { name = "CORS_ADDITIONAL_HOSTS", value = "shop.${local.domain_name},admin.${local.domain_name},api.${var.env}.${local.domain_name},api.${local.domain_name}"  }
  ]

  redis_env = [
    { name = "REDIS_HOST", value = module.datastore.redis_endpoint },
    { name = "REDIS_PORT", value = "6379" }
  ]


  db_secrets = [
    # { name = "DB_PASSWORD", valueFrom = module.datastore.db_password_secret_arn },
    # { name = "DB_USERNAME", valueFrom = module.app-configurations.db_username_param_arn }
  ]

  payments_secrets =  [
    { name = "PAYSTACK_SECRET_KEY", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.env}/paystack/secret_key" },
    { name = "PAYMENT_CALLBACK", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/${var.env}/payment_callback_url" }
  ]

  payments_env = concat(local.db_env, local.cors_origins, [
    { name = "ORDERS_SERVICE_URL", value = "http://${module.vpc.alb_dns_name}" }
  ])

  checkout_env = concat(local.cors_origins, [
    { name = "ORDERS_SERVICE_URL", value = "http://${module.vpc.alb_dns_name}" },
    { name = "PAYMENT_SERVICE_URL", value = "http://${module.vpc.alb_dns_name}" }
  ])

  cart_env = concat(local.redis_env, local.cors_origins, [
    { name = "CART_TTL_SECONDS", value = "1800" },
    { name = "CART_MAX_ITEMS", value = "100" }
  ])

  order_env = concat(local.db_env, local.cors_origins, [
    { name = "PRODUCT_SERVICE_URL", value = "http://${module.vpc.alb_dns_name}/products" }
  ])

  products_env = concat(local.db_env, local.cors_origins, local.redis_env, [
    { name = "IMAGE_BUCKET_NAME", value = var.image_bucket_name != "" ? var.image_bucket_name : "okiyalabs-shop-src-images" },
  ])

  users_env = concat(local.db_env, local.cors_origins, local.redis_env, [
    { name = "AWS_COGNITO_USER_POOL_ID", value = module.cognito.user_pool_id },
    { name = "AWS_COGNITO_CLIENT_ID", value = module.cognito.client_id },
  ])

  task_environment = {
    orders   = local.order_env,
    products = local.products_env,
    users    = local.users_env,
    payments = local.payments_env,
    checkout = local.checkout_env,
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
    "GET /cart",
    "POST /cart/remove",
    "POST /cart/clear",
    "PATCH /cart/edit",
    "GET /cart/ttl",
    "GET /cart/health",
    # checkout service endpoints
    "POST /checkout",
    "GET /checkout/health",
    # orders service endpoints
    "POST /orders",
    "GET /orders",
    "GET /orders/{pk}",
    "GET /orders/health-check",
    "PATCH /orders/{pk}/payment_status",
    "PATCH /orders/{pk}/shipping_status",
    "GET /orders/status/{reference}",
    # payments service endpoints
    "POST /payments/pay",
    "POST /payments/webhook",
    "GET /payments/health",
    # products service endpoints
    "GET /products",
    "POST /products",
    "GET /products/{pk}",
    "PUT /products/{pk}",
    "PATCH /products/{pk}",
    "DELETE /products/{pk}",
    "GET /products/categories",
    "GET /products/random",
    "POST /products/bulk",
    "POST /products/s3-url",
    "PATCH /products/update_stock",
    "POST /products/current-stock",
    "GET /health-check",
    # users service endpoints
    "POST /users/signup",
    "POST /users/login",
    "POST /users/logout",
    "GET /users/profile",
    "POST /users/confirm-signup",
    "POST /users/resend-confirmation",
    "POST /users/forgot-password",
    "POST /users/confirm-forgot-password",
    "POST /users/admin/invite",
    "GET /users/health-check",
    "GET /users/customers",
    "POST /users/customers",
    "GET /users/customers/{pk}",
    "PUT /users/customers/{pk}",
    "PATCH /users/customers/{pk}",
    "DELETE /users/customers/{pk}",
    "GET /users/admins",
    "PUT /users/admins/{pk}",
    "PATCH /users/admins/{pk}",
    "DELETE /users/admins/{pk}"
  ]

  # UI/WebApp configurations
  domain_name      = "okiyalabs.click"
  subdomains       = ["shop", "admin"]
  hosted_zone_name = "okiyalabs.click"
  hosted_zone_id   = "Z03305803JZFXK21BF0DI"
}
