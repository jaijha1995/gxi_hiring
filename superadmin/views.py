# app/views.py
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password

from .models import UserProfile
from .serializers import UserSerializer, UserListSerializer
from .utils import generate_otp, send_otp_email  , send_welcome_email


class CustomerViews(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]  # we handle auth logic below

    def post(self, request):
        data = request.data

        # 1) First user -> open SuperAdmin creation
        if UserProfile.objects.count() == 0:
            serializer = UserSerializer(data=data)
            if not serializer.is_valid():
                return Response({"status": "failure", "errors": serializer.errors}, status=400)
            user = serializer.save(role=UserProfile.ROLE_SUPERADMIN)
            send_welcome_email(user.email, user.first_name or '', user.last_name or '')
            return Response({"status": "success", "msg": "SuperAdmin created", "data": UserSerializer(user).data}, status=201)

        # 2) Subsequent signups require auth
        if not request.user or not request.user.is_authenticated:
            return Response({"status": "failure", "msg": "Authentication required to create users"}, status=401)

        auth_user = request.user

        serializer = UserSerializer(data=data)
        if not serializer.is_valid():
            return Response({"status": "failure", "errors": serializer.errors}, status=400)

        email = serializer.validated_data.get('email')
        role = serializer.validated_data.get('role', UserProfile.ROLE_EXTERNAL)

        if UserProfile.objects.filter(email=email).exists():
            return Response({"status": "failure", "msg": "User already exists"}, status=400)

        # Validate creator ID presence and that authenticated user matches the provided creator
        created_by_superadmin = None
        created_by_manager = None

        if role == UserProfile.ROLE_MANAGER:
            superadmin_id = data.get('superadmin_id')
            if not superadmin_id:
                return Response({"status": "failure", "msg": "superadmin_id is required to create a Manager"}, status=400)
            superadmin = get_object_or_404(UserProfile, id=superadmin_id, role=UserProfile.ROLE_SUPERADMIN)
            # ensure authenticated user is that superadmin
            if auth_user.id != superadmin.id:
                return Response({"status": "failure", "msg": "Authenticated user must be the provided superadmin_id"}, status=403)
            created_by_superadmin = superadmin

        elif role == UserProfile.ROLE_HR:
            manager_id = data.get('manager_id')
            if not manager_id:
                return Response({"status": "failure", "msg": "manager_id is required to create HR"}, status=400)
            manager = get_object_or_404(UserProfile, id=manager_id, role=UserProfile.ROLE_MANAGER)
            if auth_user.id != manager.id:
                return Response({"status": "failure", "msg": "Authenticated user must be the provided manager_id"}, status=403)
            created_by_manager = manager

        elif role == UserProfile.ROLE_EXTERNAL:
            superadmin_id = data.get('superadmin_id')
            if not superadmin_id:
                return Response({"status": "failure", "msg": "superadmin_id is required to create ExternalUser"}, status=400)
            superadmin = get_object_or_404(UserProfile, id=superadmin_id, role=UserProfile.ROLE_SUPERADMIN)
            if auth_user.id != superadmin.id:
                return Response({"status": "failure", "msg": "Authenticated user must be the provided superadmin_id"}, status=403)
            created_by_superadmin = superadmin

        # Save user with creator fields
        user = serializer.save(
            created_by_superadmin=created_by_superadmin,
            created_by_manager=created_by_manager
        )
        send_welcome_email(user.email, user.first_name or '', user.last_name or '')
        return Response({"status": "success", "msg": f"{role} created successfully", "data": UserSerializer(user).data}, status=201)


class LoginCustomer(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({"msg": "Email and password required"}, status=400)

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"msg": "Invalid email"}, status=404)

        if not user.check_password(password):
            return Response({"msg": "Invalid password"}, status=401)

        refresh = RefreshToken.for_user(user)
        creator_info = user.get_creator_info()

        data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            **creator_info
        }

        return Response({
            "status": "success",
            "msg": f"{user.role} login successful",
            "data": data,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }, status=200)


class CustomerManageViews(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        current_user = request.user
        if id:
            user = get_object_or_404(UserProfile, id=id)
            return Response({"data": UserSerializer(user).data}, status=200)

        # SuperAdmin sees all users, others only see users they created
        if current_user.role == UserProfile.ROLE_SUPERADMIN:
            users = UserProfile.objects.all()
        else:
            users = UserProfile.objects.filter(
                models.Q(created_by_superadmin=current_user) | models.Q(created_by_manager=current_user)
            )
        return Response({"data": UserSerializer(users, many=True).data}, status=200)

    def patch(self, request, id=None):
        if not id:
            return Response({"msg": "User ID required"}, status=400)
        user = get_object_or_404(UserProfile, id=id)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=400)
        serializer.save()
        return Response({"data": serializer.data}, status=200)

    def delete(self, request, id=None):
        if not id:
            return Response({"msg": "User ID required"}, status=400)
        user = get_object_or_404(UserProfile, id=id)
        current_user = request.user
        allowed = False
        if current_user.role == UserProfile.ROLE_SUPERADMIN:
            allowed = True
        if user.created_by_superadmin == current_user or user.created_by_manager == current_user:
            allowed = True
        if not allowed:
            return Response({"msg": "You are not authorized to delete this user"}, status=403)
        user.delete()
        return Response({"msg": "User deleted successfully"}, status=200)


# OTP, VerifyOTP, ForgotPassword (kept short)
class OTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
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
        email = request.data.get('email')
        otp = request.data.get('otp')
        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"error": "Invalid email"}, status=400)
        if otp != user.otp:
            return Response({"error": "Invalid OTP"}, status=400)
        user.otp = None
        user.save()
        return Response({"message": "OTP verified successfully"}, status=200)


class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
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
