# # 1. ECS Task Execution Role
# resource "aws_iam_role" "ecs_task_execution_role" {
#   name = "ecs-task-execution-role"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Action = "sts:AssumeRole"
#       Principal = {
#         Service = "ecs-tasks.amazonaws.com"
#       }
#       Effect = "Allow"
#       Sid    = ""
#     }]
#   })

#   tags = var.tags
# }

# resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
#   role       = aws_iam_role.ecs_task_execution_role.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"

# }

# # Add custom inline policy for extra permissions
# resource "aws_iam_role_policy" "ecs_task_execution_custom_permissions" {
#   name = "ecs-task-execution-custom"
#   role = aws_iam_role.ecs_task_execution_role.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "ecr:GetAuthorizationToken",
#           "ecr:BatchCheckLayerAvailability",
#           "ecr:GetDownloadUrlForLayer",
#           "ecr:BatchGetImage",
#           "logs:CreateLogGroup",
#           "logs:CreateLogStream",
#           "logs:PutLogEvents",
#           "secretsmanager:GetSecretValue",
#           "secretsmanager:DescribeSecret"
#         ]
#         Resource = "*"
#       }
#     ]
#   })
# }

data "aws_caller_identity" "current" {}

# This module create ECS task role and policies for each environment. It Helps isolate environment-specific permissions.
# 2. ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Effect = "Allow"
      Sid    = ""
    }]
  })

  tags = var.tags
}

# Optional Custom Policy for the ECS Task Role
resource "aws_iam_policy" "ecs_task_policy" {
  name        = "ecs-task-policy"
  description = "Permissions for ECS tasks to access AWS services"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject"
      ]
      Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters"
        ]
        Resource = "*"
      },
      {
        "Sid" : "CognitoUserManagement",
        "Effect" : "Allow",
        "Action" : [
          /* --- Authentication & Status Retrieval --- */
          "cognito-idp:AdminInitiateAuth", /* Used by login_user */
          "cognito-idp:RespondToAuthChallenge", /* Used by login_user for NEW_PASSWORD_REQUIRED */
          "cognito-idp:GlobalSignOut", /* Used by logout_user */
          "cognito-idp:GetUser", /* Used by get_user_groups */

          /* --- Self-Service Flows (Client ID Required) --- */
          "cognito-idp:SignUp", /* Used by signup_user */
          "cognito-idp:ConfirmSignUp", /* Used by confirm_signup */
          "cognito-idp:ForgotPassword", /* Used by forgot_password */
          "cognito-idp:ConfirmForgotPassword", /* Used by confirm_forgot_password */
          "cognito-idp:ResendConfirmationCode", /* Used by resend_confirmation_code */

          /* --- Admin/Staff Actions (User Pool ID Required) --- */
          "cognito-idp:AdminCreateUser", /* Used by admin_create_user */
          "cognito-idp:AdminAddUserToGroup", /* Used by add_user_to_group */
          "cognito-idp:AdminDeleteUser" /* Used by delete_user */
        ],
        "Resource" : [
          "arn:aws:cognito-idp:${var.aws_region}:${data.aws_caller_identity.current.account_id}:userpool/*"
        ]
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_role_policy_attach" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.ecs_task_policy.arn

}
