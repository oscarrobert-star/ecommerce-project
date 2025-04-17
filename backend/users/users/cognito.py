import boto3
from django.conf import settings
from botocore.exceptions import ClientError

client = boto3.client('cognito-idp', region_name=settings.AWS_COGNITO_REGION)

def signup_user(username, password, email):
    try:
        response = client.sign_up(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
            ]
        )
        return response
    except ClientError as e:
        return {"error": str(e)}

def confirm_signup(username, confirmation_code):
    try:
        response = client.confirm_sign_up(
            ClientId=settings.AWS_COGNITO_CLIENT_ID,
            Username=username,
            ConfirmationCode=confirmation_code,
        )
        return response
    except ClientError as e:
        return {"error": str(e)}

def login_user(username, password, new_password=None):
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
            if not new_password:
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

            return {
                "message": "Password changed & logged in",
                "id_token": challenge_response['AuthenticationResult']['IdToken'],
                "access_token": challenge_response['AuthenticationResult']['AccessToken'],
                "refresh_token": challenge_response['AuthenticationResult']['RefreshToken']
            }

        # If no challenge, return tokens as usual
        return {
            "id_token": response['AuthenticationResult']['IdToken'],
            "access_token": response['AuthenticationResult']['AccessToken'],
            "refresh_token": response['AuthenticationResult']['RefreshToken']
        }

    except client.exceptions.NotAuthorizedException:
        return {"error": "Incorrect username or password"}
    except client.exceptions.UserNotConfirmedException:
        return {"error": "User not confirmed. Check your email."}
    except client.exceptions.UserNotFoundException:
        return {"error": "User does not exist"}
    except Exception as e:
        return {"error": str(e)}

