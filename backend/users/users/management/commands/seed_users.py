# users/management/commands/seed_users.py

from django.core.management.base import BaseCommand
import boto3
from django.conf import settings

class Command(BaseCommand):
    help = "Seed test users into AWS Cognito"

    def handle(self, *args, **kwargs):
        client = boto3.client("cognito-idp", region_name=settings.AWS_COGNITO_REGION)
        users = [
            {"username": "alice_cust", "email": "osyrobert@gmail.com", "password": "Cust@1234", "group": "customer"},
            {"username": "bob_admin", "email": "testsoscar@gmail.com", "password": "Admin@1234", "group": "admin"},
            {"username": "carol_cust", "email": "oscarokiya35@gmail.com", "password": "Cust@1234", "group": "customer"},
        ]

        for u in users:
            try:
                client.admin_create_user(
                    UserPoolId=settings.AWS_COGNITO_USER_POOL_ID,
                    Username=u["username"],
                    TemporaryPassword=u["password"],
                    UserAttributes=[{"Name": "email", "Value": u["email"]}],
                    MessageAction="SUPPRESS"  # suppress email
                )
                client.admin_add_user_to_group(
                    UserPoolId=settings.AWS_COGNITO_USER_POOL_ID,
                    Username=u["username"],
                    GroupName=u["group"]
                )
                self.stdout.write(self.style.SUCCESS(f"Created user {u['username']} in group {u['group']}"))
            except Exception as e:
                self.stderr.write(f"Error creating {u['username']}: {e}")
