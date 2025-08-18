import json
import os
import logging
import boto3
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

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
            region = os.getenv("AWS_REGION")
            logger.debug(f"Creating boto3 Secrets Manager client for region: {region}")
            cls._client = boto3.client("secretsmanager", region_name=region)
        return cls._client

    @classmethod
    def get_cache(cls):
        if cls._cache is None:
            logger.debug("Initializing AWS Secrets Manager cache")
            cls._cache = SecretCache(config=SecretCacheConfig(), client=cls.get_client())
        return cls._cache

    @classmethod
    def get_db_credentials(cls, secret_arn=None):
        """
        Returns: dict {username: str, password: str}
        Uses in-memory caching to avoid repeated Secrets Manager API calls.
        """
        if not secret_arn:
            logger.info("No secret ARN provided, using environment variables for DB credentials")
            return {
                "username": os.getenv("DB_USER", "default_db_user"),
                "password": os.getenv("DB_PASSWORD", "default_db_password"),
            }

        try:
            logger.info(f"Fetching DB credentials from AWS Secrets Manager for ARN: {secret_arn}")
            secret_string = cls.get_cache().get_secret_string(secret_arn)
            secret_data = json.loads(secret_string)
            logger.debug("Successfully retrieved and parsed secret from AWS Secrets Manager")
            return {
                "username": secret_data["username"],
                "password": secret_data["password"],
            }
        except Exception as e:
            logger.error(f"Failed to fetch database secret: {str(e)}")
            raise ImproperlyConfigured(f"Failed to fetch database secret: {str(e)}")

def get_database_config(db_alias="default"):
    """
    Generates Django database configuration
    """
    prefix = "" if db_alias == "default" else f"{db_alias.upper()}_"

    secret_arn = os.getenv(f"DB_{prefix}SECRET_ARN") or os.getenv("DB_SECRET_ARN")
    logger.debug(f"Using secret ARN: {secret_arn} for db_alias: {db_alias}")

    credentials = AwsSecretManager.get_db_credentials(secret_arn)

    # Allow env var overrides
    if f"DB_{prefix}USER" in os.environ:
        logger.info(f"Overriding DB username from environment variable: DB_{prefix}USER")
        credentials["username"] = os.getenv(f"DB_{prefix}USER")
    if f"DB_{prefix}PASSWORD" in os.environ:
        logger.info(f"Overriding DB password from environment variable: DB_{prefix}PASSWORD")
        credentials["password"] = os.getenv(f"DB_{prefix}PASSWORD")

    db_config = {
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
    logger.debug(f"Generated DB config for alias '{db_alias}': {db_config}")
    return db_config
