"""
URL configuration for cart project.

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
from . import views

# urlpatterns = [
#     path('cart/<str:user_id>/', views.view_cart),
#     path('cart/<str:user_id>/add/', views.add_item),
#     path('cart/<str:user_id>/remove/<str:item_id>/', views.remove_item),
#     path('cart/<str:user_id>/clear/', views.clear),
# ]
urlpatterns = [
    path('cart/', views.get_cart, name='get_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('cart/edit', views.edit_item_quantity, name='edit_item_quantity'),
]
