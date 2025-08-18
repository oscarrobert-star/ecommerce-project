import json
import os
import boto3
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from django.core.exceptions import ImproperlyConfigured

class AwsSecretManager:
    """
    Handles retrieval of database credentials from AWS Secrets Manager
    with local caching to minimize API calls.
    """
    _client = None
    _cache = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION"))
        return cls._client

    @classmethod
    def get_cache(cls):
        if cls._cache is None:
            cls._cache = SecretCache(config=SecretCacheConfig(), client=cls.get_client())
        return cls._cache

    @classmethod
    def get_db_credentials(cls, secret_arn=None):
        """
        Returns: dict {username: str, password: str}
        Uses in-memory caching to avoid repeated Secrets Manager API calls.
        """
        if not secret_arn:
            return {
                "username": os.getenv("DB_USER", "default_db_user"),
                "password": os.getenv("DB_PASSWORD", "default_db_password"),
            }

        try:
            secret_string = cls.get_cache().get_secret_string(secret_arn)
            secret_data = json.loads(secret_string)
            return {
                "username": secret_data["username"],
                "password": secret_data["password"],
            }
        except Exception as e:
            raise ImproperlyConfigured(f"Failed to fetch database secret: {str(e)}")

def get_database_config(db_alias="default"):
    """
    Generates Django database configuration
    """
    prefix = "" if db_alias == "default" else f"{db_alias.upper()}_"

    secret_arn = os.getenv(f"DB_{prefix}SECRET_ARN") or os.getenv("DB_SECRET_ARN")
    credentials = AwsSecretManager.get_db_credentials(secret_arn)

    # Allow env var overrides
    if f"DB_{prefix}USER" in os.environ:
        credentials["username"] = os.getenv(f"DB_{prefix}USER")
    if f"DB_{prefix}PASSWORD" in os.environ:
        credentials["password"] = os.getenv(f"DB_{prefix}PASSWORD")

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv(f"DB_{prefix}NAME", os.getenv("DB_NAME", "default_db_name")),
        "USER": credentials["username"],
        "PASSWORD": credentials["password"],
        "HOST": os.getenv(f"DB_{prefix}HOST", os.getenv("DB_HOST", "localhost")),
        "PORT": os.getenv(f"DB_{prefix}PORT", os.getenv("DB_PORT", "5432")),
        "OPTIONS": {
            "connect_timeout": 5,
            "application_name": os.getenv("APP_NAME", f"django_{db_alias}"),
        },
    }
