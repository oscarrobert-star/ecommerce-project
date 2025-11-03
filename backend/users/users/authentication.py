import jwt
import requests
import json
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

logger = logging.getLogger(__name__)

class CognitoCookieAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Get access token from cookie
        access_token = request.COOKIES.get("access_token")
        logger.debug(f"Access token from cookie: {'Present' if access_token else 'Missing'}")

        if not access_token:
            logger.warning("No access token found in cookies")
            return None

        try:
            # Get JWKS keys
            jwks_url = f"https://cognito-idp.{settings.AWS_COGNITO_REGION}.amazonaws.com/{settings.AWS_COGNITO_USER_POOL_ID}/.well-known/jwks.json"
            jwks_response = requests.get(jwks_url)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

            # Get the key ID from the token header
            header = jwt.get_unverified_header(access_token)
            kid = header.get('kid')
            
            if not kid:
                raise AuthenticationFailed("Token missing key ID")

            # Find the matching key
            public_key = None
            for key in jwks['keys']:
                if key['kid'] == kid:
                    public_key = self.jwk_to_pem(key)
                    break

            if not public_key:
                raise AuthenticationFailed("No matching public key found")

            # Verify and decode the token
            payload = jwt.decode(
                access_token,
                public_key,
                algorithms=["RS256"],
                audience=settings.AWS_COGNITO_CLIENT_ID,
                issuer=f"https://cognito-idp.{settings.AWS_COGNITO_REGION}.amazonaws.com/{settings.AWS_COGNITO_USER_POOL_ID}"
            )

            logger.debug(f"Token validated for user: {payload.get('username')}")

            # Create a simple user object
            from django.contrib.auth.models import AnonymousUser
            user = AnonymousUser()
            user.is_authenticated = True
            user.username = payload.get('username') or payload.get('cognito:username')
            user.payload = payload  # Store the full payload for later use

            return (user, None)

        except jwt.ExpiredSignatureError:
            logger.warning("Access token has expired")
            raise AuthenticationFailed("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise AuthenticationFailed(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationFailed(f"Authentication failed: {str(e)}")

    def jwk_to_pem(self, jwk):
        """Convert JWK to PEM format"""
        # Extract the modulus and exponent from the JWK
        n = int.from_bytes(base64.urlsafe_b64decode(jwk['n'] + '=='), 'big')
        e = int.from_bytes(base64.urlsafe_b64decode(jwk['e'] + '=='), 'big')
        
        # Create RSA public key
        from cryptography.hazmat.primitives.asymmetric import rsa
        public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
        
        # Convert to PEM format
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return pem.decode('utf-8')