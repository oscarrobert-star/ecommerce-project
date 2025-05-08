import boto3
import logging
from django.conf import settings
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

client = boto3.client('cognito-idp', region_name=settings.AWS_COGNITO_REGION)

def signup_user(username, password, email):
    logger.info(f"Signup attempt - Username: {username}, Email: {email}")
    try:
        response = client.sign_up(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
            ]
        )
        logger.info(f"Signup successful for Username: {username}")
        return response
    except ClientError as e:
        logger.error(f"Signup failed for Username: {username} - Error: {e}")
        return {"error": str(e)}

def confirm_signup(username, confirmation_code):
    logger.info(f"Confirm signup attempt - Username: {username}")
    try:
        response = client.confirm_sign_up(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username,
            ConfirmationCode=confirmation_code,
        )
        logger.info(f"Confirm signup successful for Username: {username}")
        return response
    except ClientError as e:
        logger.error(f"Confirm signup failed for Username: {username} - Error: {e}")
        return {"error": str(e)}

def login_user(username, password, new_password=None):
    logger.info(f"Login attempt - Username: {username}")
    try:
        client = boto3.client('cognito-idp', region_name=settings.AWS_COGNITO_REGION)

        response = client.admin_initiate_auth(
            UserPoolId=settings.AWS_COGNITO_USER_POOL_ID,
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            AuthFlow='ADMIN_NO_SRP_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

        if response.get("ChallengeName") == "NEW_PASSWORD_REQUIRED":
            logger.info(f"New password challenge for Username: {username}")
            if not new_password:
                logger.warning(f"New password required but not provided for Username: {username}")
                return {"error": "New password required", "challenge": "NEW_PASSWORD_REQUIRED"}

            challenge_response = client.respond_to_auth_challenge(
                ClientId=settings.AWS_COGNITO_CLIENT_ID,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                ChallengeResponses={
                    'USERNAME': username,
                    'NEW_PASSWORD': new_password
                },
                Session=response['Session']
            )

            logger.info(f"Password changed and login successful for Username: {username}")
            return {
                "message": "Password changed & logged in",
                "id_token": challenge_response['AuthenticationResult']['IdToken'],
                "access_token": challenge_response['AuthenticationResult']['AccessToken'],
                "refresh_token": challenge_response['AuthenticationResult']['RefreshToken']
            }

        logger.info(f"Login successful for Username: {username}")
        return {
            "id_token": response['AuthenticationResult']['IdToken'],
            "access_token": response['AuthenticationResult']['AccessToken'],
            "refresh_token": response['AuthenticationResult']['RefreshToken']
        }

    except client.exceptions.NotAuthorizedException:
        logger.warning(f"Login failed - Incorrect username or password for Username: {username}")
        return {"error": "Incorrect username or password"}
    except client.exceptions.UserNotConfirmedException:
        logger.warning(f"Login failed - User not confirmed for Username: {username}")
        return {"error": "User not confirmed. Check your email."}
    except client.exceptions.UserNotFoundException:
        logger.warning(f"Login failed - User not found: {username}")
        return {"error": "User does not exist"}
    except Exception as e:
        logger.error(f"Unexpected error during login for Username: {username} - Error: {e}")
        return {"error": str(e)}

def logout_user(access_token):
    logger.info(f"Logout attempt with Access Token: {access_token}")
    try:
        response = client.global_sign_out(
            AccessToken=access_token
        )
        logger.info(f"Logout successful for Access Token: {access_token}")
        return {"message": "Logout successful"}
    except ClientError as e:
        logger.error(f"Logout failed - Error: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error during logout - Error: {e}")
        return {"error": str(e)}
