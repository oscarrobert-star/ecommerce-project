import requests
import json
from django.conf import settings

def get_jwks():
    jwks_url = f"https://cognito-idp.{settings.AWS_COGNITO_REGION}.amazonaws.com/{settings.AWS_COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    response.raise_for_status()
    return json.loads(response.text)