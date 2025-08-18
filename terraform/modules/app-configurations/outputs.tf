# output "rds_credentials_arn" {
#   value = aws_secretsmanager_secret.rds_credentials.arn
# }

# output "database_password" {
#   value     = random_password.db.result
#   sensitive = true 
# }

# output "database_username" {
#   value = jsondecode(aws_secretsmanager_secret_version.rds_credentials_version.secret_string)["username"]
#   sensitive = true
# }

######################################################
######## SSM PARAMETERS FOR CONFIGS ##########
######################################################
output "db_username_param_name" {
  value = aws_ssm_parameter.db_username.name
}

output "db_username_param_arn" {
  value = aws_ssm_parameter.db_username.arn
}