import logging
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignupView,
    LoginView,
    ProfileView,
    ConfirmSignupView,
    LogoutView,
    health_check,
    CustomerViewSet,
    AdminUserViewSet,
    AdminInviteView,
    ForgotPasswordView,
    ConfirmForgotPasswordView,
    ResendConfirmationView,
)

logger = logging.getLogger(__name__)

from django.http import JsonResponse

def debug_cookies(request):
    """Debug endpoint to check what cookies are being received"""
    return JsonResponse({
        'cookies_received': dict(request.COOKIES),
        'headers': dict(request.headers)
    })

def debug_auth(request):
    """Debug endpoint to check authentication status"""
    return JsonResponse({
        'is_authenticated': request.user.is_authenticated,
        'username': getattr(request.user, 'username', 'None'),
        'user_attributes': dir(request.user)
    })

# Create a router to automatically generate URL patterns for ViewSets
router = DefaultRouter(trailing_slash=False)
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'admins', AdminUserViewSet, basename='admin')

urlpatterns = [
    # User authentication endpoints
    path('users/signup', SignupView.as_view(), name='signup'),
    path('users/login', LoginView.as_view(), name='login'),
    path('users/profile', ProfileView.as_view(), name='profile'),
    path('users/confirm-signup', ConfirmSignupView.as_view(), name='confirm'),
    path('users/logout', LogoutView.as_view(), name='logout'),
    path('users/health', view=health_check, name='health_check'),
    
    # New endpoints for password reset and confirmation
    path('users/forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('users/confirm-forgot-password', ConfirmForgotPasswordView.as_view(), name='confirm-forgot-password'),
    path('users/resend-confirmation-code', ResendConfirmationView.as_view(), name='resend-confirmation-code'),
    
    # New endpoint for admin invitations
    path('users/invite-admin', AdminInviteView.as_view(), name='invite-admin'),

    path('users/debug/cookies', debug_cookies, name='debug_cookies'),
    path('users/debug/auth', debug_auth, name='debug_auth'),

    # API endpoints for customers and admins, managed by the router
    path('', include(router.urls)),
]