import boto3
import logging
import json
from datetime import datetime
from django.conf import settings
from botocore.exceptions import ClientError

# --- Custom JSON Formatter (Reuse from views.py or define centrally) ---
class JsonFormatter(logging.Formatter):
    """
    A custom formatter to output log records as a JSON string.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Handle extra kwargs passed to logger calls
        if hasattr(record, 'json_extra') and isinstance(record.json_extra, dict):
            log_record.update(record.json_extra)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_record)

# --- Logging Configuration ---
# 1. Create the custom formatter
json_formatter = JsonFormatter()

# 2. Create a handler (e.g., streaming to console)
json_handler = logging.StreamHandler()
json_handler.setFormatter(json_formatter)

# 3. Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Clear existing handlers (good practice in Django/multi-module setup)
if logger.hasHandlers():
    logger.handlers.clear()

# Add the JSON handler
logger.addHandler(json_handler)


# --- Placeholder/Setup ---
# Initialize the Cognito client
# NOTE: settings and boto3 are assumed to be correctly configured
try:
    client = boto3.client('cognito-idp', region_name=settings.AWS_COGNITO_REGION)
except AttributeError:
    # Placeholder client for testing outside a Django environment
    print("WARNING: Using a placeholder client as settings are not available.")
    class PlaceholderClient:
        def __init__(self, *args, **kwargs): pass
        def __getattr__(self, name): 
            # Mock the client to raise an exception for realistic log capture
            if name == 'sign_up':
                 raise ClientError({'Error': {'Code': 'MockError', 'Message': 'Mock client error'}}, 'MockAPI')
            return lambda *args, **kwargs: {}
    client = PlaceholderClient()
    class MockSettings:
        AWS_COGNITO_REGION = 'mock-region'
        AWS_COGNITO_CLIENT_ID = 'mock-client-id'
        AWS_COGNITO_USER_POOL_ID = 'mock-user-pool-id'
    settings = MockSettings()


# --- Cognito Utility Functions with Enhanced JSON Logging ---

def get_user_groups(access_token):
    """
    Gets the groups for a user from their access token.
    """
    # NOTE: Logging the raw token is often a security risk, we just log its presence.
    token_status = "Present" if access_token else "Missing"
    logger.info(
        "Attempting to retrieve user groups.",
        extra={'json_extra': {'token_status': token_status, 'action': 'get_groups_start'}}
    )
    try:
        response = client.get_user(AccessToken=access_token)
        user_groups = response.get('UserAttributes', [])
        groups = []
        for attr in user_groups:
            if attr['Name'] == 'cognito:groups':
                groups = attr['Value']
                break
        
        logger.info(
            "Successfully retrieved user groups.",
            extra={'json_extra': {'user_groups': groups, 'action': 'get_groups_success'}}
        )
        return groups
    except ClientError as e:
        logger.error(
            f"Failed to get user groups: {e}",
            extra={'json_extra': {'cognito_error': str(e), 'action': 'get_groups_fail'}}
        )
        return []

def signup_user(username, password, email):
    logger.info(
        "Cognito sign-up attempt initiated.",
        extra={'json_extra': {'username': username, 'email': email, 'action': 'signup_cognito_start'}}
    )
    try:
        response = client.sign_up(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
            ]
        )
        logger.info(
            "Cognito sign-up successful.",
            extra={'json_extra': {'username': username, 'action': 'signup_cognito_success'}}
        )
        return response
    except ClientError as e:
        logger.error(
            "Cognito sign-up failed.",
            extra={'json_extra': {'username': username, 'cognito_error': str(e), 'action': 'signup_cognito_fail'}}
        )
        return {"error": str(e)}

def admin_create_user(email, username, group_name):
    logger.info(
        "Cognito admin create user attempt initiated.",
        extra={'json_extra': {'target_email': email, 'target_username': username, 'target_group': group_name, 'action': 'admin_create_start'}}
    )
    try:
        response = client.admin_create_user(
            UserPoolId=settings.AWS_COGNITO_USER_POOL_ID,
            Username=email,
            TemporaryPassword='Temp_Password!1',
            UserAttributes=[
                {'Name': 'email', 'Value': email},
            ],
            ForceAliasCreation=True,
            MessageAction='SUPPRESS'
        )
        logger.info(
            "Cognito admin user created successfully.",
            extra={'json_extra': {'target_email': email, 'action': 'admin_create_success'}}
        )
        return response
    except ClientError as e:
        logger.error(
            "Cognito admin create user failed.",
            extra={'json_extra': {'target_email': email, 'cognito_error': str(e), 'action': 'admin_create_fail'}}
        )
        return {"error": str(e)}

def confirm_signup(username, confirmation_code):
    logger.info(
        "Cognito confirm sign-up attempt initiated.",
        extra={'json_extra': {'username': username, 'action': 'confirm_signup_start'}}
    )
    try:
        response = client.confirm_sign_up(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username,
            ConfirmationCode=confirmation_code,
        )
        logger.info(
            "Cognito confirm sign-up successful.",
            extra={'json_extra': {'username': username, 'action': 'confirm_signup_success'}}
        )
        return response
    except ClientError as e:
        logger.error(
            f"Cognito confirm sign-up failed.",
            extra={'json_extra': {'username': username, 'cognito_error': str(e), 'action': 'confirm_signup_fail'}}
        )
        return {"error": str(e)}

def login_user(username, password, new_password=None):
    logger.info(
        "Cognito login attempt initiated.",
        extra={'json_extra': {'username': username, 'action': 'login_cognito_start'}}
    )
    try:
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
            
            if not new_password:
                logger.warning(
                    "Login challenge: NEW_PASSWORD_REQUIRED, but no new password provided.",
                    extra={'json_extra': {'username': username, 'challenge': 'NEW_PASSWORD_REQUIRED', 'action': 'login_challenge_fail'}}
                )
                return {"error": "New password required", "challenge": "NEW_PASSWORD_REQUIRED"}

            logger.info(
                "Login challenge: NEW_PASSWORD_REQUIRED received, responding.",
                extra={'json_extra': {'username': username, 'challenge': 'NEW_PASSWORD_REQUIRED', 'action': 'login_challenge_respond'}}
            )
            
            challenge_response = client.respond_to_auth_challenge(
                ClientId=settings.AWS_COGNITO_CLIENT_ID,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                ChallengeResponses={
                    'USERNAME': username,
                    'NEW_PASSWORD': new_password
                },
                Session=response['Session']
            )

            logger.info(
                "Password changed and login successful via challenge response.",
                extra={'json_extra': {'username': username, 'action': 'login_challenge_success'}}
            )
            return {
                "message": "Password changed & logged in",
                "id_token": challenge_response['AuthenticationResult']['IdToken'],
                "access_token": challenge_response['AuthenticationResult']['AccessToken'],
                "refresh_token": challenge_response['AuthenticationResult']['RefreshToken']
            }

        logger.info(
            "Cognito login successful.",
            extra={'json_extra': {'username': username, 'action': 'login_cognito_success'}}
        )
        return {
            "id_token": response['AuthenticationResult']['IdToken'],
            "access_token": response['AuthenticationResult']['AccessToken'],
            "refresh_token": response['AuthenticationResult']['RefreshToken']
        }

    except client.exceptions.NotAuthorizedException:
        logger.warning(
            "Login failed: Incorrect username or password.",
            extra={'json_extra': {'username': username, 'reason': 'NotAuthorizedException', 'action': 'login_cognito_fail'}}
        )
        return {"error": "Incorrect username or password"}
    except client.exceptions.UserNotConfirmedException:
        logger.warning(
            "Login failed: User not confirmed.",
            extra={'json_extra': {'username': username, 'reason': 'UserNotConfirmedException', 'action': 'login_cognito_fail'}}
        )
        return {"error": "User not confirmed. Check your email."}
    except client.exceptions.UserNotFoundException:
        logger.warning(
            "Login failed: User not found.",
            extra={'json_extra': {'username': username, 'reason': 'UserNotFoundException', 'action': 'login_cognito_fail'}}
        )
        return {"error": "User does not exist"}
    except Exception as e:
        logger.error(
            f"Unexpected error during login: {e}",
            extra={'json_extra': {'username': username, 'error_type': type(e).__name__, 'cognito_error': str(e), 'action': 'login_cognito_fail'}}
        )
        return {"error": str(e)}

def logout_user(access_token):
    token_status = "Present" if access_token else "Missing"
    logger.info(
        "Cognito global sign-out attempt initiated.",
        extra={'json_extra': {'token_status': token_status, 'action': 'logout_cognito_start'}}
    )
    try:
        response = client.global_sign_out(
            AccessToken=access_token
        )
        logger.info(
            "Cognito global sign-out successful.",
            extra={'json_extra': {'action': 'logout_cognito_success'}}
        )
        return {"message": "Logout successful"}
    except ClientError as e:
        logger.error(
            "Cognito global sign-out failed.",
            extra={'json_extra': {'cognito_error': str(e), 'action': 'logout_cognito_fail'}}
        )
        return {"error": str(e)}
    except Exception as e:
        logger.error(
            f"Unexpected error during logout: {e}",
            extra={'json_extra': {'error_type': type(e).__name__, 'action': 'logout_cognito_fail'}}
        )
        return {"error": str(e)}

def add_user_to_group(username, group_name):
    logger.info(
        "Cognito add user to group attempt initiated.",
        extra={'json_extra': {'username': username, 'group_name': group_name, 'action': 'add_group_start'}}
    )
    try:
        response = client.admin_add_user_to_group(
            UserPoolId=settings.AWS_COGNITO_USER_POOL_ID,
            Username=username,
            GroupName=group_name
        )
        logger.info(
            "User successfully added to group.",
            extra={'json_extra': {'username': username, 'group_name': group_name, 'action': 'add_group_success'}}
        )
        return response
    except ClientError as e:
        logger.error(
            "Failed to add user to group.",
            extra={'json_extra': {'username': username, 'group_name': group_name, 'cognito_error': str(e), 'action': 'add_group_fail'}}
        )
        return {"error": str(e)}

def delete_user(username):
    logger.info(
        "Cognito delete user attempt initiated.",
        extra={'json_extra': {'username': username, 'action': 'delete_user_start'}}
    )
    try:
        response = client.admin_delete_user(
            UserPoolId=settings.AWS_COGNITO_USER_POOL_ID,
            Username=username
        )
        logger.info(
            "User successfully deleted from Cognito.",
            extra={'json_extra': {'username': username, 'action': 'delete_user_success'}}
        )
        return {"message": "User deleted successfully"}
    except ClientError as e:
        logger.error(
            "Failed to delete user from Cognito.",
            extra={'json_extra': {'username': username, 'cognito_error': str(e), 'action': 'delete_user_fail'}}
        )
        return {"error": str(e)}
        
def forgot_password(username):
    logger.info(
        "Cognito forgot password flow initiated.",
        extra={'json_extra': {'username': username, 'action': 'forgot_password_start'}}
    )
    try:
        response = client.forgot_password(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username
        )
        logger.info(
            "Forgot password flow successfully initiated.",
            extra={'json_extra': {'username': username, 'action': 'forgot_password_success'}}
        )
        return {"message": "Confirmation code sent successfully"}
    except ClientError as e:
        logger.error(
            "Forgot password flow failed.",
            extra={'json_extra': {'username': username, 'cognito_error': str(e), 'action': 'forgot_password_fail'}}
        )
        return {"error": str(e)}

def confirm_forgot_password(username, new_password, confirmation_code):
    logger.info(
        "Cognito confirm forgot password attempt initiated.",
        extra={'json_extra': {'username': username, 'action': 'confirm_forgot_start'}}
    )
    try:
        response = client.confirm_forgot_password(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username,
            Password=new_password,
            ConfirmationCode=confirmation_code
        )
        logger.info(
            "Password successfully reset via confirm forgot password.",
            extra={'json_extra': {'username': username, 'action': 'confirm_forgot_success'}}
        )
        return {"message": "Password reset successfully"}
    except ClientError as e:
        logger.error(
            "Confirm forgot password failed.",
            extra={'json_extra': {'username': username, 'cognito_error': str(e), 'action': 'confirm_forgot_fail'}}
        )
        return {"error": str(e)}

def resend_confirmation_code(username):
    logger.info(
        "Cognito resend confirmation code attempt initiated.",
        extra={'json_extra': {'username': username, 'action': 'resend_code_start'}}
    )
    try:
        response = client.resend_confirmation_code(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username
        )
        logger.info(
            "Confirmation code successfully resent.",
            extra={'json_extra': {'username': username, 'action': 'resend_code_success'}}
        )
        return {"message": "Confirmation code resent successfully"}
    except ClientError as e:
        logger.error(
            "Resend confirmation code failed.",
            extra={'json_extra': {'username': username, 'cognito_error': str(e), 'action': 'resend_code_fail'}}
        )
        return {"error": str(e)}