# here we are creating the config resources like secrets, parameter store, kms keys, ssl certificates, etc.
# resource "aws_secretsmanager_secret" "rds_credentials" {
#     name        = "database-credentials"
#     description = "Credentials for the RDS database"
#     tags = merge(var.tags, {
#         Name = "rds-credentials"
#     })
# }

# resource "aws_secretsmanager_secret_version" "rds_credentials_version" {
#     secret_id     = aws_secretsmanager_secret.rds_credentials.id
#     secret_string = jsonencode({
#         username = var.db_username
#         password = random_password.db.result
#     })
# }

# resource "random_password" "db" {
#   length  = 16
#   special = true
# }

######################################################
######## PARAMETER STORE FOR CONFIGS ##########
######################################################
resource "aws_ssm_parameter" "db_username" {
  name        = "/${var.env}/database/username"
  description = "RDS master username"
  type        = "String"
  value       = var.db_username
  tags        = var.tags
}

resource "aws_ssm_parameter" "payment_callback_url" {
  name        = "/${var.env}/payment_callback_url"
  description = "RDS master password"
  type        = "SecureString"
  value       = var.payment_callback_url
  tags        = var.tags
} 

resource "aws_ssm_parameter" "paystack_secret_key" {
  name        = "/${var.env}/paystack/secret_key"
  description = "Paystack secret key"
  type        = "SecureString"
  value       = var.paystack_secret_key
  tags        = var.tags    
  
}