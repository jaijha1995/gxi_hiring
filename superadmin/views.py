from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile
from .serializers import UserSerializer
from .utils import generate_otp, send_otp_email
import secrets, logging

logger = logging.getLogger(__name__)


# -------------------------- Helper --------------------------
def send_welcome_email(email, first_name, last_name):
    subject = 'Welcome to Gxi Hiring'
    html_message = render_to_string('welcome_email_template.html', {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
    })
    plain_message = strip_tags(html_message)
    send_mail(subject, plain_message, 'jaijhavats32@gmail.com', [email], html_message=html_message)


# -------------------------- SIGNUP --------------------------
class CustomerViews(APIView):
    authentication_classes = ()  # Open for first signup
    permission_classes = (AllowAny,)

    def post(self, request, org_id=None):
        """
        Create user (SuperAdmin, Manager, HR, or External_user)
        First user can sign up without authentication.
        """
        data = request.data
        serializer = UserSerializer(data=data)

        if not serializer.is_valid():
            return Response({"status": "failure", "errors": serializer.errors}, status=400)

        email = serializer.validated_data.get("email")
        if UserProfile.objects.filter(email=email).exists():
            return Response({"status": "failure", "msg": "User already exists"}, status=400)

        # First user (SuperAdmin) can register freely
        if UserProfile.objects.count() == 0:
            user = serializer.save()
            send_welcome_email(user.email, user.first_name, user.last_name)
            return Response({"status": "success", "msg": "SuperAdmin created", "data": UserSerializer(user).data}, status=201)

        # For next users, no restriction on who can create (anyone can)
        user = serializer.save()
        send_welcome_email(user.email, user.first_name, user.last_name)
        return Response({"status": "success", "msg": "User created", "data": UserSerializer(user).data}, status=201)


# -------------------------- LOGIN --------------------------
class LoginCustomer(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"msg": "Email and password required"}, status=400)

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"msg": "Invalid email"}, status=404)

        if not check_password(password, user.password):
            return Response({"msg": "Invalid password"}, status=401)

        # ✅ All roles can log in now
        refresh = RefreshToken.for_user(user)
        return Response({
            "status": "success",
            "msg": f"{user.role} login successful",
            "data": UserSerializer(user).data,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }, status=200)


# -------------------------- MANAGE USERS --------------------------
class CustomerManageViews(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, id=None):
        """Get user(s)"""
        if id:
            user = get_object_or_404(UserProfile, id=id)
            return Response({"data": UserSerializer(user).data}, status=200)

        users = UserProfile.objects.all()
        return Response({"data": UserSerializer(users, many=True).data}, status=200)

    def patch(self, request, id=None):
        """Update user"""
        if not id:
            return Response({"msg": "User ID required"}, status=400)
        user = get_object_or_404(UserProfile, id=id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data}, status=200)
        return Response({"errors": serializer.errors}, status=400)

    def delete(self, request, id=None):
        """Delete user"""
        user = get_object_or_404(UserProfile, id=id)
        user.delete()
        return Response({"msg": "User deleted successfully"}, status=200)


# -------------------------- LIST USERS BY ORG --------------------------
class ListCustomerViews(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, org_id=None):
        users = UserProfile.objects.filter(org_id=org_id).only('id', 'first_name', 'last_name', 'email')
        serializer = UserSerializer(users, many=True)
        return Response({"data": serializer.data}, status=200)


# -------------------------- OTP --------------------------
class OTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        otp = generate_otp()
        send_otp_email(email, otp)
        user.otp = otp
        user.save()
        return Response({"message": "OTP sent successfully"}, status=200)


class VerifyOTP(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"error": "Invalid email"}, status=400)

        if otp != user.otp:
            return Response({"error": "Invalid OTP"}, status=400)

        user.is_verified = True
        user.save()
        return Response({"message": "OTP verified successfully"}, status=200)


# -------------------------- FORGOT PASSWORD --------------------------
class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        confirm_password = request.data.get("confirm_password")

        if not all([email, password, confirm_password]):
            return Response({"error": "All fields are required"}, status=400)

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        user.password = make_password(password)
        user.save(update_fields=["password"])
        return Response({"message": "Password reset successful"}, status=200)
