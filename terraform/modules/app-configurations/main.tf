# here we are creating the config resources like secrets, parameter store, kms keys, ssl certificates, etc.
resource "aws_secretsmanager_secret" "rds_credentials" {
    name        = "database-credentials"
    description = "Credentials for the RDS database"
    tags = merge(var.tags, {
        Name = "rds-credentials"
    })
}

resource "aws_secretsmanager_secret_version" "rds_credentials_version" {
    secret_id     = aws_secretsmanager_secret.rds_credentials.id
    secret_string = jsonencode({
        username = var.db_username
        password = random_password.db.result
    })
}

resource "random_password" "db" {
  length  = 16
  special = true
}