# In this module we create the database and caching resources - AWS RDS, AWS ElastiCache Redis
resource "aws_db_instance" "postgres" {
    allocated_storage    = 20
    storage_type         = "gp2"
    engine               = "postgres"
    engine_version       = "17.5"
    instance_class       = var.instance_class
    db_name = var.db_name
    identifier           = "ecommerce-postgres"
    username             = var.db_username
    password             = var.db_password
    parameter_group_name = "default.postgres17"
    db_subnet_group_name = var.db_subnet_group
    vpc_security_group_ids = var.db_security_group_ids
    skip_final_snapshot  = true
    publicly_accessible  = false
    multi_az             = false
    backup_retention_period = 0
    tags = var.tags
}

resource "aws_elasticache_cluster" "redis" {
    cluster_id           = "ecommerce-redis"
    engine               = "redis"
    node_type            = var.node_type
    num_cache_nodes      = 1
    parameter_group_name = "default.redis7"
    subnet_group_name    = var.redis_subnet_group_name
    security_group_ids   = var.db_security_group_ids
    tags                 = var.tags
}

# Very expensive to run, so commented out for now
# Uncomment if you want to use ElastiCache Serverless Redis
# resource "aws_elasticache_serverless_cache" "ecommerce" {
#   engine = "redis"
#   name = "ecommerce-redis"
#   cache_usage_limits {
#     data_storage {
#       maximum = 1
#       unit    = "GB"
#     }
#     ecpu_per_second {
#       maximum = 5000
#     }
#   }
#   security_group_ids = var.db_security_group_ids
#   subnet_ids = var.subnet_ids
#   major_engine_version     = "7"
# }