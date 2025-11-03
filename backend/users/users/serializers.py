from rest_framework import serializers
from .models import Customer, AdminUser

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "full_name", "email", "shipping_address", "cognito_username"]
        read_only_fields = ["id", "cognito_username"]

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = ["id", "username", "role", "cognito_username"]
        read_only_fields = ["id", "cognito_username"]
