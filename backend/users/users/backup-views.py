import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from . import cognito
from .models import Customer, AdminUser
from django.http import JsonResponse
from .serializers import CustomerSerializer, AdminUserSerializer
from rest_framework import viewsets
from django.db import IntegrityError
from .permissions import IsAdminUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

class SignupView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        display_name = request.data.get("username", "")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=400)

        logger.info(f"Customer signup attempt for email: {email}")

        # Cognito signup
        result = cognito.signup_user(email, password, email)
        if "error" in result:
            logger.error(f"Signup failed for email: {email}, error: {result['error']}")
            return Response(result, status=400)

        # Add to Cognito customer group
        group_result = cognito.add_user_to_group(email, "customer")
        if "error" in group_result:
            return Response(group_result, status=400)

        # Local DB record
        try:
            Customer.objects.create(
                cognito_username=email,
                full_name=display_name,
                email=email,
                shipping_address=""
            )
            logger.info(f"Customer record created for email: {email}")
        except IntegrityError:
            logger.warning(f"Duplicate signup attempt detected for email: {email}")
            return Response({"error": "User already exists."}, status=400)

        return Response({"message": "Signup successful. Confirm via email."})

class AdminInviteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def post(self, request):
        email = request.data.get("email")
        display_name = request.data.get("username", "")

        if not email:
            return Response({"error": "Email is required."}, status=400)
        
        logger.info(f"Admin invite attempt for email: {email}")

        # Cognito admin_create_user call
        result = cognito.admin_create_user(email, display_name, "admin")
        if "error" in result:
            logger.error(f"Admin invite failed for email: {email}, error: {result['error']}")
            return Response(result, status=400)
        
        # Add to Cognito admin group
        group_result = cognito.add_user_to_group(email, "admin")
        if "error" in group_result:
            return Response(group_result, status=400)

        # Local DB record
        try:
            AdminUser.objects.create(
                cognito_username=email,
                username=display_name if display_name else email,
                role="staff"
            )
            logger.info(f"AdminUser record created for email: {email}")
        except IntegrityError:
            logger.warning(f"Duplicate admin invite detected for email: {email}")
            return Response({"error": "User already exists."}, status=400)
        
        # Email with temporary password would be sent here
        # Note: You would need to implement a separate email service for this
        
        return Response({"message": "Admin user invited successfully. They will receive an email to set their password."})

class ConfirmSignupView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        logger.info("Confirm signup request received")
        username = request.data['email']
        code = request.data['code']
        logger.debug(f"Confirm signup details - Username: {username}")

        result = cognito.confirm_signup(username, code)
        if 'error' in result:
            logger.error(f"Confirm signup failed for {username}: {result['error']}")
            return Response(result, status=400)

        logger.info(f"Account confirmed successfully for {username}")
        return Response({"message": "Account confirmed successfully"})    

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({"error": "Username is required."}, status=400)

        result = cognito.forgot_password(username)
        if 'error' in result:
            return Response(result, status=400)
        
        return Response({"message": "Password reset code sent successfully."})

class ConfirmForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        new_password = request.data.get('new_password')
        confirmation_code = request.data.get('code')

        if not username or not new_password or not confirmation_code:
            return Response({"error": "All fields are required."}, status=400)

        result = cognito.confirm_forgot_password(username, new_password, confirmation_code)
        if 'error' in result:
            return Response(result, status=400)

        return Response({"message": "Password reset successfully."})

class ResendConfirmationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({"error": "Username is required."}, status=400)

        result = cognito.resend_confirmation_code(username)
        if 'error' in result:
            return Response(result, status=400)

        return Response({"message": "Confirmation code resent successfully."})

class LoginView(APIView):
    authentication_classes = []  # Disable authentication for login
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("=== Login Request ===")
        logger.info(f"Cookies received: {dict(request.COOKIES)}")
        
        username = request.data.get('username')
        password = request.data.get('password')
        new_password = request.data.get('new_password')

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=400)

        logger.info(f"Login attempt for username: {username}")

        result = cognito.login_user(username, password, new_password)

        if 'error' in result:
            logger.error(f"Login failed for {username}: {result['error']}")
            return Response(result, status=400)

        logger.info(f"Login successful for {username}")

        response = Response({
            "message": "Login successful", 
            "access_token": result.get('access_token'),
            "id_token": result.get('id_token'),
            "refresh_token": result.get('refresh_token')
        })

        # Set new cookies with the fresh tokens
        if 'access_token' in result:
            response.set_cookie(
                key="access_token",
                value=result['access_token'],
                httponly=True,
                secure=True,    
                samesite="None",
                max_age=3600  # 1 hour
            )
        
        if 'id_token' in result:
            response.set_cookie(
                key="id_token",
                value=result['id_token'],
                httponly=True,
                secure=True,    
                samesite="None",
                max_age=3600
            )
        
        if 'refresh_token' in result:
            response.set_cookie(
                key="refresh_token",
                value=result['refresh_token'],
                httponly=True,
                secure=True,     # CHANGED TO TRUE
                samesite="None",
                max_age=30*24*3600  # 30 days
            )
        return response
    
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info("=== Profile View Debug ===")
        logger.info(f"User authenticated: {request.user.is_authenticated}")
        logger.info(f"User username: {getattr(request.user, 'username', 'No username')}")
        
        # Log all cookies
        logger.info("Cookies received:")
        for cookie_name, cookie_value in request.COOKIES.items():
            logger.info(f"  {cookie_name}: {'Present' if cookie_value else 'Empty/Missing'}")

        # Check if user has the expected attributes
        if not hasattr(request.user, 'username') or not request.user.username:
            logger.error("User object missing username attribute")
            return Response({"error": "User authentication incomplete"}, status=401)

        username = request.user.username
        logger.info(f"Looking up profile for username: {username}")

        try:
            # Try to find customer first
            customer = Customer.objects.get(cognito_username=username)
            logger.info(f"Found customer profile for {username}")
            return Response({
                "type": "customer", 
                "data": {
                    "full_name": customer.full_name,
                    "email": customer.email,
                    "shipping_address": customer.shipping_address
                }
            })
        except Customer.DoesNotExist:
            logger.debug(f"No customer found for {username}, checking admin users")
            try:
                admin = AdminUser.objects.get(cognito_username=username)
                logger.info(f"Found admin profile for {username}")
                return Response({
                    "type": "admin", 
                    "data": {
                        "username": admin.username,
                        "role": admin.role
                    }
                })
            except AdminUser.DoesNotExist:
                logger.error(f"No user record found in database for {username}")
                return Response({
                    "error": "User not found in database",
                    "cognito_username": username
                }, status=404)

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        # Skip CSRF check
        return
   
@method_decorator(csrf_exempt, name='dispatch')   
class LogoutView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        response = Response({"message": "Logged out successfully"})
        response.delete_cookie("access_token")
        response.delete_cookie("id_token")
        response.delete_cookie("refresh_token")
        return response

def health_check(request):
    """
    Health check endpoint to verify if the service is running.
    """
    logger.info("Health check request received")
    return JsonResponse({"status": "ok"}, status=status.HTTP_200_OK)        

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("full_name")
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        """
        Deletes a customer and also cascades the deletion to Cognito.
        """
        instance = self.get_object()
        cognito_username = instance.cognito_username
        
        # Delete user from Cognito first
        cognito_result = cognito.delete_user(cognito_username)
        if "error" in cognito_result:
            return Response(cognito_result, status=status.HTTP_400_BAD_REQUEST)
        
        # Then, proceed with local database deletion
        return super().destroy(request, *args, **kwargs)

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = AdminUser.objects.all().order_by("username")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def destroy(self, request, *args, **kwargs):
        """
        Deletes an admin user and also cascades the deletion to Cognito.
        """
        instance = self.get_object()
        cognito_username = instance.cognito_username
        
        # Delete user from Cognito first
        cognito_result = cognito.delete_user(cognito_username)
        if "error" in cognito_result:
            return Response(cognito_result, status=status.HTTP_400_BAD_REQUEST)
        
        # Then, proceed with local database deletion
        return super().destroy(request, *args, **kwargs)

# class CognitoCookieAuthentication(BaseAuthentication):
#     def authenticate(self, request):
#         access_token = request.COOKIES.get("access_token")
#         if not access_token:
#             return None

#         try:
#             # Verify JWT against Cognito public keys
#             payload = jwt.decode(
#                 access_token,
#                 options={"verify_signature": False}  # ⚠️ for testing only, replace with real JWKS verification
#             )
#             username = payload.get("username") or payload.get("cognito:username")
#             if not username:
#                 raise AuthenticationFailed("Invalid token: no username")

#             # Attach Django user-like object
#             from django.contrib.auth.models import AnonymousUser
#             user = AnonymousUser()
#             user.is_authenticated = True
#             user.username = username
#             return (user, None)
#         except jwt.ExpiredSignatureError:
#             raise AuthenticationFailed("Token expired")
#         except Exception as e:
#             raise AuthenticationFailed(str(e))
