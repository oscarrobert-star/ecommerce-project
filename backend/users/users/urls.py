"""
URL configuration for users project.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignupView, LoginView, ProfileView, ConfirmSignupView, LogoutView, health_check, CustomerViewSet


router = DefaultRouter(trailing_slash=False)
# router.register(r'customers', CustomerViewSet, basename='customer')


urlpatterns = [
    path('users/signup', SignupView.as_view(), name='signup'),
    path('users/login', LoginView.as_view(), name='login'),
    path('users/profile', ProfileView.as_view(), name='profile'),
    path('users/confirm-signup', ConfirmSignupView.as_view(), name='confirm'),
    path('users/logout', LogoutView.as_view(), name='logout'),
    path('users/health', view=health_check, name='health_check'),
    path('customers', CustomerViewSet.as_view({'get': 'list', 'post': 'create'}), name='customer-list'),
    # Add a catch-all for the router to handle customers
    path('', include(router.urls)),
]