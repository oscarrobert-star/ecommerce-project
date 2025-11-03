import unittest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, force_authenticate
from unittest import mock
from django.conf import settings
from . import cognito
from .models import Customer, AdminUser
from django.db import IntegrityError
from django.contrib.auth.models import AnonymousUser
from django.test import override_settings

# Set mock Cognito settings for testing
# settings.configure(
#     AWS_COGNITO_REGION='us-east-2',
#     AWS_COGNITO_USER_POOL_ID='us-east-2_testpool',
#     AWS_COGNITO_CLIENT_ID='testclient',
#     # Configure a mock Django DB for testing to prevent replica issues
#     DATABASES={
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': ':memory:',
#         }
#     }
# )

# Mock the entire boto3 client to prevent real API calls
@mock.patch('boto3.client')
class CognitoServiceTests(unittest.TestCase):

    def setUp(self):
        self.mock_cognito_client = mock.MagicMock()
        self.mock_boto3_client = self.mock_cognito_client.return_value
        self.mock_boto3_client.exceptions.ClientError = cognito.ClientError
        self.mock_boto3_client.exceptions.NotAuthorizedException = cognito.ClientError
        self.mock_boto3_client.exceptions.UserNotConfirmedException = cognito.ClientError
        self.mock_boto3_client.exceptions.UserNotFoundException = cognito.ClientError
        
        self.test_username = "testuser@example.com"
        self.test_password = "SecurePassword1!"
        self.test_group = "customer"

    def test_signup_user_success(self, mock_client):
        # Correctly mock the return value to have a 'UserSub' key
        self.mock_boto3_client.sign_up.return_value = {"UserSub": "123"}
        response = cognito.signup_user(self.test_username, self.test_password, self.test_username)
        self.assertEqual(response['UserSub'], "123")
        self.mock_boto3_client.sign_up.assert_called_once()

    def test_signup_user_failure(self, mock_client):
        # Correctly mock the side effect to raise an exception, which the function handles and returns an error dict
        self.mock_boto3_client.sign_up.side_effect = cognito.ClientError({"Error": {"Code": "UsernameExistsException"}}, 'SignUp')
        response = cognito.signup_user(self.test_username, self.test_password, self.test_username)
        self.assertIn("error", response)
        self.mock_boto3_client.sign_up.assert_called_once()

    def test_admin_create_user_success(self, mock_client):
        # Correctly mock the return value for a successful admin creation
        self.mock_boto3_client.admin_create_user.return_value = {"User": {"Username": "admin@test.com"}}
        response = cognito.admin_create_user("admin@test.com", "Admin User", "admin")
        self.assertIn("User", response)
        self.mock_boto3_client.admin_create_user.assert_called_once()
        self.assertIn('TemporaryPassword', self.mock_boto3_client.admin_create_user.call_args[1])
        
    def test_admin_create_user_failure(self, mock_client):
        # Correctly mock the side effect to return a handled error
        self.mock_boto3_client.admin_create_user.side_effect = cognito.ClientError({"Error": {"Code": "UsernameExistsException"}}, 'AdminCreateUser')
        response = cognito.admin_create_user("admin@test.com", "Admin User", "admin")
        self.assertIn("error", response)
        self.mock_boto3_client.admin_create_user.assert_called_once()

    def test_delete_user_success(self, mock_client):
        # Correctly mock the return value with a message
        self.mock_boto3_client.admin_delete_user.return_value = {}
        response = cognito.delete_user(self.test_username)
        self.assertIn("message", response)
        self.mock_boto3_client.admin_delete_user.assert_called_once()

    def test_delete_user_failure(self, mock_client):
        # Correctly mock the side effect to raise a handled error
        self.mock_boto3_client.admin_delete_user.side_effect = cognito.ClientError({"Error": {"Code": "UserNotFoundException"}}, 'AdminDeleteUser')
        response = cognito.delete_user(self.test_username)
        self.assertIn("error", response)
        self.mock_boto3_client.admin_delete_user.assert_called_once()

# Use override_settings to ensure the test suite uses the correct database
@override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
@mock.patch('users.views.cognito')
class AuthViewsTests(APITestCase):

    def setUp(self):
        self.mock_cognito = mock.MagicMock()

        self.customer_user = Customer.objects.create(
            cognito_username="customer@test.com",
            full_name="Test Customer",
            email="customer@test.com",
        )
        self.admin_user = AdminUser.objects.create(
            cognito_username="admin@test.com",
            username="test_admin",
            role="manager",
        )
        # Mocking the `is_authenticated` property on the request
        self.mock_request_user = mock.MagicMock()
        self.mock_request_user.is_authenticated = True

    def test_signup_customer_success(self, mock_cognito):
        mock_cognito.signup_user.return_value = {}
        mock_cognito.add_user_to_group.return_value = {}
        
        response = self.client.post(
            reverse('signup'),
            {"email": "newuser@test.com", "password": "SecurePassword1!"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_cognito.signup_user.assert_called_once()
        mock_cognito.add_user_to_group.assert_called_once_with("newuser@test.com", "customer")
        self.assertTrue(Customer.objects.filter(cognito_username="newuser@test.com").exists())

    def test_admin_invite_success(self, mock_cognito):
        # Force authentication and set user groups
        self.client.force_authenticate(user=self.mock_request_user)
        mock_cognito.get_user_groups.return_value = ["admin"]
        mock_cognito.admin_create_user.return_value = {}
        mock_cognito.add_user_to_group.return_value = {}

        response = self.client.post(
            reverse('invite-admin'),
            {"email": "newadmin@test.com", "username": "new_admin_user"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("invited successfully", response.data['message'])
        mock_cognito.admin_create_user.assert_called_once()
        mock_cognito.add_user_to_group.assert_called_once_with("newadmin@test.com", "admin")
        self.assertTrue(AdminUser.objects.filter(cognito_username="newadmin@test.com").exists())

    def test_admin_invite_permission_denied(self, mock_cognito):
        # Force authentication as a customer, which lacks admin permissions
        self.client.force_authenticate(user=self.mock_request_user)
        mock_cognito.get_user_groups.return_value = ["customer"]

        response = self.client.post(
            reverse('invite-admin'),
            {"email": "unauthorized@test.com"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_cognito.admin_create_user.assert_not_called()

    def test_login_success(self, mock_cognito):
        mock_cognito.login_user.return_value = {
            "access_token": "mock_access_token", "id_token": "mock_id_token", "refresh_token": "mock_refresh_token"
        }
        
        response = self.client.post(
            reverse('login'),
            {"username": "testuser", "password": "password"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("access_token", response.data)
        self.assertIn("id_token", response.data)

    def test_customer_profile(self, mock_cognito):
        self.client.force_authenticate(user=self.mock_request_user)
        
        response = self.client.get(
            reverse('profile'),
            HTTP_X_USERNAME=self.customer_user.cognito_username
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'customer')

    def test_admin_profile(self, mock_cognito):
        self.client.force_authenticate(user=self.mock_request_user)
        
        response = self.client.get(
            reverse('profile'),
            HTTP_X_USERNAME=self.admin_user.cognito_username
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type'], 'admin')

@override_settings(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}})
@mock.patch('users.views.cognito')
class CrudViewSetTests(APITestCase):

    def setUp(self):
        # Create a mock admin user with authentication
        self.admin_user = AdminUser.objects.create(
            cognito_username="admin@test.com",
            username="test_admin",
            role="manager"
        )
        self.client.force_authenticate(user=self.admin_user)
        self.mock_cognito = mock.MagicMock()
        self.mock_cognito.get_user_groups.return_value = ["admin"]

    def test_customer_delete_cascades_to_cognito(self, mock_cognito):
        # Create a customer to be deleted
        customer_to_delete = Customer.objects.create(
            cognito_username="delete_me@test.com",
            full_name="Delete Me",
            email="delete_me@test.com",
        )
        
        # Mock the Cognito delete_user call
        mock_cognito.delete_user.return_value = {}
        
        delete_url = reverse('customer-detail', kwargs={'pk': customer_to_delete.id})
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Customer.objects.filter(id=customer_to_delete.id).exists())
        mock_cognito.delete_user.assert_called_once_with("delete_me@test.com")

    def test_admin_delete_cascades_to_cognito(self, mock_cognito):
        # Create an admin to be deleted
        admin_to_delete = AdminUser.objects.create(
            cognito_username="delete_me_admin@test.com",
            username="delete_me",
        )
        
        # Mock the Cognito delete_user call
        mock_cognito.delete_user.return_value = {}
        
        delete_url = reverse('admin-detail', kwargs={'pk': admin_to_delete.id})
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AdminUser.objects.filter(id=admin_to_delete.id).exists())
        mock_cognito.delete_user.assert_called_once_with("delete_me_admin@test.com")
