"""
URL configuration for users project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from .views import SignupView, LoginView, ProfileView, ConfirmSignupView, LogoutView, health_check

urlpatterns = [
    path('users/signup/', SignupView.as_view(), name='signup'),
    path('users/login/', LoginView.as_view(), name='login'),
    path('users/profile/', ProfileView.as_view(), name='profile'),
    path('users/confirm-signup/', ConfirmSignupView.as_view(), name='confirm'),
    path('users/logout/', LogoutView.as_view, name='logout'),
    path('users/health/', view=health_check, name='health_check'),
]


