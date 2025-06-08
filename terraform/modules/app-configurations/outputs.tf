output "rds_credentials_arn" {
  value = aws_secretsmanager_secret.rds_credentials.arn
}

output "database_password" {
  value     = random_password.db.result
  sensitive = true 
}

output "database_username" {
  value = jsondecode(aws_secretsmanager_secret_version.rds_credentials_version.secret_string)["username"]
  sensitive = true
}

