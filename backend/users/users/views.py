from rest_framework.views import APIView
from rest_framework.response import Response
from . import cognito
from .models import Customer, AdminUser

class SignupView(APIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        email = request.data['email']
        user_type = request.data.get('type', 'customer')  # 'admin' or 'customer'

        result = cognito.signup_user(username, password, email)
        if 'error' in result:
            return Response(result, status=400)

        if user_type == 'customer':
            Customer.objects.create(cognito_username=username, full_name="", email=email)
        elif user_type == 'admin':
            AdminUser.objects.create(cognito_username=username, username=username, role="manager")

        return Response({"message": "Signup successful. Confirm via email."})
    
class ConfirmSignupView(APIView):
    def post(self, request):
        username = request.data['username']
        code = request.data['code']

        result = cognito.confirm_signup(username, code)
        if 'error' in result:
            return Response(result, status=400)

        return Response({"message": "Account confirmed successfully"})    

class LoginView(APIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        new_password = request.data.get('new_password')  # optional

        result = cognito.login_user(username, password, new_password)

        if 'error' in result:
            return Response(result, status=400)
        return Response(result)


class ProfileView(APIView):
    def get(self, request):
        # Assume token validation done already
        username = request.headers.get("X-Username")  # Example header
        try:
            customer = Customer.objects.get(cognito_username=username)
            return Response({"type": "customer", "data": {
                "name": customer.full_name,
                "email": customer.email,
                "shipping_address": customer.shipping_address
            }})
        except Customer.DoesNotExist:
            try:
                admin = AdminUser.objects.get(cognito_username=username)
                return Response({"type": "admin", "data": {
                    "username": admin.username,
                    "role": admin.role
                }})
            except AdminUser.DoesNotExist:
                return Response({"error": "User not found"}, status=404)
