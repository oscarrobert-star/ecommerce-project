import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from . import cognito
from .models import Customer, AdminUser
from django.http import JsonResponse
from .serializers import CustomerSerializer 
from rest_framework import viewsets

logger = logging.getLogger(__name__)

from django.db import IntegrityError

class SignupView(APIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        email = request.data['email']
        user_type = request.data.get('type', 'customer')  # 'admin' or 'customer'

        logger.info(f"Signup attempt for username: {username}, type: {user_type}")

        result = cognito.signup_user(username, password, email)

        if 'error' in result:
            logger.error(f"Signup failed for username: {username}, error: {result['error']}")
            return Response(result, status=400)

        logger.info(f"Signup successful for username: {username}")

        try:
            if user_type == 'customer':
                Customer.objects.create(
                    cognito_username=username,
                    full_name="",  # Empty for now
                    email=email,
                    shipping_address=""  # Empty for now
                )
                logger.info(f"Customer record created for username: {username}")
            elif user_type == 'admin':
                AdminUser.objects.create(
                    cognito_username=username,
                    username=username,
                    role="manager"  # Default role
                )
                logger.info(f"AdminUser record created for username: {username}")
        except IntegrityError:
            logger.warning(f"Duplicate signup attempt detected for username: {username}")
            return Response({"error": "User already exists."}, status=400)

        return Response({"message": "Signup successful. Confirm via email."})

    
class ConfirmSignupView(APIView):
    def post(self, request):
        logger.info("Confirm signup request received")
        username = request.data['username']
        code = request.data['code']
        logger.debug(f"Confirm signup details - Username: {username}")

        result = cognito.confirm_signup(username, code)
        if 'error' in result:
            logger.error(f"Confirm signup failed for {username}: {result['error']}")
            return Response(result, status=400)

        logger.info(f"Account confirmed successfully for {username}")
        return Response({"message": "Account confirmed successfully"})    

class LoginView(APIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        new_password = request.data.get('new_password')  # optional

        result = cognito.login_user(username, password, new_password)

        if 'error' in result:
            return Response(result, status=400)

        response = Response({"message": "Login successful"})

        # Set cookies
        response.set_cookie(
            key="access_token",
            value=result['access_token'],
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="Lax"
        )
        response.set_cookie(
            key="id_token",
            value=result['id_token'],
            httponly=True,
            secure=False,
            samesite="Lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=result['refresh_token'],
            httponly=True,
            secure=False,
            samesite="Lax"
        )

        return response

class ProfileView(APIView):
    def get(self, request):
        logger.info("Profile fetch request received")
        username = request.headers.get("X-Username")  # Example header
        logger.debug(f"Fetching profile for {username}")

        try:
            customer = Customer.objects.get(cognito_username=username)
            logger.info(f"Customer profile fetched for {username}")
            return Response({"type": "customer", "data": {
                "name": customer.full_name,
                "email": customer.email,
                "shipping_address": customer.shipping_address
            }})
        except Customer.DoesNotExist:
            logger.debug(f"No customer record found for {username}")
            try:
                admin = AdminUser.objects.get(cognito_username=username)
                logger.info(f"Admin profile fetched for {username}")
                return Response({"type": "admin", "data": {
                    "username": admin.username,
                    "role": admin.role
                }})
            except AdminUser.DoesNotExist:
                logger.error(f"User not found for username {username}")
                return Response({"error": "User not found"}, status=404)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Skip CSRF check
        return
   

@method_decorator(csrf_exempt, name='dispatch')   
class LogoutView(APIView):
    authentication_classes = (CsrfExemptSessionAuthentication,)
    permission_classes = (AllowAny,)  # optional, but good for logout

    def post(self, request):
        access_token = request.headers.get('Authorization')

        if not access_token:
            return Response({"error": "Access token missing in Authorization header."}, status=status.HTTP_400_BAD_REQUEST)

        # In case token is in the format "Bearer <token>", split it
        if access_token.startswith('Bearer '):
            access_token = access_token.split(' ')[1]

        result = cognito.logout_user(access_token)

        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)

def health_check(request):
    """
    Health check endpoint to verify if the service is running.
    """
    logger.info("Health check request received")
    return JsonResponse({"status": "ok"}, status=status.HTTP_200_OK)        

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("full_name")
    serializer_class = CustomerSerializer
