from rest_framework import permissions
import jwt
from django.conf import settings
from . import cognito

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admins to access a view.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Get the access token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return False
        
        access_token = auth_header.split(' ')[1]
        
        # Use a placeholder method to get user groups from the token
        # This logic should be handled by a proper JWT library or middleware
        # For a full implementation, you would need to parse the ID token, which contains
        # the user groups. The `cognito.get_user_groups` is a simplified placeholder
        # and not a production-ready solution for this.
        user_groups = cognito.get_user_groups(access_token)
        
        return "admin" in user_groups