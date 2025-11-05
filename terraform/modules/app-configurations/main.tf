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
# resource "aws_ssm_parameter" "db_username" {
#   name        = "/${var.env}/database/username"
#   description = "RDS master username"
#   type        = "String"
#   value       = var.db_username
#   tags        = var.tags
# }

resource "aws_ssm_parameter" "payment_callback_url" {
  name        = "/${var.env}/payment_callback_url"
  description = "RDS master password"
  type        = "String"
  value       = var.payment_callback_url
  tags        = var.tags
} 

resource "aws_ssm_parameter" "paystack_secret_key" {
  name        = "/${var.env}/paystack/secret_key"
  description = "Paystack secret key"
  type        = "String"
  value       = var.paystack_secret_key
  tags        = var.tags    
  
}

#################################################
######## CART SERVICE REDIS CLEANUP ##########
#################################################

# Define the Python code for the Lambda function
locals {
  lambda_cleanup_code = <<-EOF
    import http.client
    import os
    import logging
    import json
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Environment variables set in Terraform
    CART_SERVICE_HOST = os.environ.get("CART_SERVICE_HOST")
    CART_SERVICE_PORT = os.environ.get("CART_SERVICE_PORT", "8000")
    CLEANUP_PATH = "/cart/cleanup-reservations"

    def handler(event, context):
        logger.info("Starting scheduled cart cleanup...")
        
        try:
            # 1. Establish connection (using HTTP for internal service communication)
            conn = http.client.HTTPConnection(CART_SERVICE_HOST, int(CART_SERVICE_PORT), timeout=10)
            
            # 2. Prepare request
            headers = {"Content-type": "application/json"}
            
            # 3. Send POST request
            conn.request("POST", CLEANUP_PATH, body="{}", headers=headers)
            
            # 4. Get and process response
            response = conn.getresponse()
            response_data = response.read().decode()
            
            if response.status not in (200, 201):
                logger.error(f"Cleanup call failed. Status: {response.status}. Response: {response_data}")
                # Raise an exception to trigger the scheduler's retry policy
                raise Exception(f"HTTP call failed with status {response.status}")
            
            logger.info(f"Cleanup call succeeded. Status: {response.status}. Response: {response_data}")
            return {
                "statusCode": response.status,
                "body": response_data
            }
        except Exception as e:
            logger.error(f"An error occurred during cleanup: {e}")
            raise # Re-raise to signal failure to EventBridge Scheduler
        finally:
            if 'conn' in locals():
                conn.close()

  EOF
}

data "archive_file" "lambda_cleanup" {
  type        = "zip"
  output_path = "${path.module}/lambda_cleanup.zip" # Create the zip file inside the current module directory
  
  # Specify the content for the zip file (index.py will contain the Python code)
  source {
    content  = local.lambda_cleanup_code 
    filename = "index.py"
  }
}

# --- Lambda IAM Role (Allows execution and logging) ---
resource "aws_iam_role" "cleanup_lambda_role" {
  name = "cart-cleanup-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs_attach" {
  role       = aws_iam_role.cleanup_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Lambda Function Resource ---
resource "aws_lambda_function" "cart_cleanup_caller" {
  function_name    = "CartServiceCleanupCaller"
  role             = aws_iam_role.cleanup_lambda_role.arn
  handler          = "index.handler"
  runtime          = "python3.11"
  timeout          = 30 
  
  # IMPORTANT: The source_code_hash must reflect the hash of the packaged code.
  # If using a deployment pipeline, the source_code_hash and filename are updated dynamically.
  # For manual deployment, ensure the index.py file is zipped.
  filename         = data.archive_file.lambda_cleanup.output_path
  source_code_hash = data.archive_file.lambda_cleanup.output_base64sha256
  
  environment {
    variables = {
      # CRITICAL: Change this host/port to the internal DNS/IP and port of your Cart Service
      CART_SERVICE_HOST = "your-cart-service-internal-dns" 
      CART_SERVICE_PORT = "8000"
    }
  }

  # NOTE: If your Django service is in a private VPC (recommended), configure the Lambda VPC settings:
  # vpc_config {
  #   subnet_ids         = ["subnet-xxxxxxxxxxxx"]
  #   security_group_ids = ["sg-xxxxxxxxxxxx"]
  # }
}

# --- Scheduler IAM Role (Allows EventBridge to invoke Lambda) ---
resource "aws_iam_role" "scheduler_invoke_role" {
  name = "scheduler-invoke-lambda-cleanup-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = { Service = "scheduler.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_policy" "scheduler_lambda_policy" {
  name = "scheduler-lambda-invoke-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = "lambda:InvokeFunction",
        Effect   = "Allow",
        Resource = aws_lambda_function.cart_cleanup_caller.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "scheduler_lambda_attach" {
  role       = aws_iam_role.scheduler_invoke_role.name
  policy_arn = aws_iam_policy.scheduler_lambda_policy.arn
}

# --- The EventBridge Schedule Resource ---
resource "aws_scheduler_schedule" "cart_cleanup_cron" {
  name        = "cart-service-cleanup-cron"
  description = "Invokes the Lambda caller to run the stock cleanup job."

  flexible_time_window {
    mode = "OFF" # Ensures the schedule runs exactly at the cron time
  }

  # Runs every 5 minutes (at 0, 5, 10, 15, ..., 55 minutes past the hour)
  schedule_expression          = "cron(0/5 * * * ? *)" 
  schedule_expression_timezone = "Etc/UTC"

  target {
    arn      = aws_lambda_function.cart_cleanup_caller.arn
    role_arn = aws_iam_role.scheduler_invoke_role.arn
    
    retry_policy {
      maximum_retry_attempts = 3
      # max_event_age_in_seconds = 300 # 5 minutes
    }
  }

  state = "ENABLED"
}