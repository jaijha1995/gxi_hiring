from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q  # ✅ use Q from here

from .models import UserProfile
from .serializers import UserSerializer, UserListSerializer
from .utils import send_otp, verify_otp, EmailService


# -------------------------
# Signup / Create User
# -------------------------
class CustomerViews(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]  # explicit auth checks are done below

    def post(self, request):
        data = request.data.copy()

        # --- Normalize input ---
        if 'email' in data and data['email']:
            data['email'] = data['email'].lower().strip()

        # --- Bootstrap: create the first SuperAdmin (no auth required) ---
        if UserProfile.objects.count() == 0:
            serializer = UserSerializer(data=data, context={"request": request})
            if not serializer.is_valid():
                return Response({"status": "failure", "errors": serializer.errors}, status=400)

            with transaction.atomic():
                user = serializer.save(role=UserProfile.ROLE_SUPERADMIN)

            try:
                EmailService.send_html(
                    [user.email], "Welcome", "welcome_email_template.html",
                    {'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name}
                )
            except Exception:
                pass

            return Response(
                {"status": "success", "msg": "SuperAdmin created", "data": UserSerializer(user).data},
                status=201
            )

        # --- Subsequent creations require authentication ---
        if not request.user or not request.user.is_authenticated:
            return Response({"status": "failure", "msg": "Authentication required to create users"}, status=401)

        auth_user = request.user

        serializer = UserSerializer(data=data, context={"request": request})
        if not serializer.is_valid():
            return Response({"status": "failure", "errors": serializer.errors}, status=400)

        email = serializer.validated_data.get('email')
        role = serializer.validated_data.get('role', UserProfile.ROLE_EXTERNAL)

        # prevent duplicates
        if UserProfile.objects.filter(email=email.lower()).exists():
            return Response({"status": "failure", "msg": "User already exists"}, status=400)

        # --- Decide creator + enforce permissions ---
        created_by_superadmin = None
        created_by_manager = None

        if auth_user.role == UserProfile.ROLE_SUPERADMIN:
            # SuperAdmin can create: SuperAdmin (optional), Manager, ExternalUser
            if role in (UserProfile.ROLE_MANAGER, UserProfile.ROLE_EXTERNAL):
                created_by_superadmin = auth_user
            elif role == UserProfile.ROLE_SUPERADMIN:
                # allow SA to create SA (no creator link needed)
                pass
            else:
                # HR / HiringManager must be created by a Manager
                return Response(
                    {"status": "failure", "msg": "HiringManager/HR must be created by a Manager"},
                    status=403
                )

        elif auth_user.role == UserProfile.ROLE_MANAGER:
            # Manager can create: HR, HiringManager
            if role in (UserProfile.ROLE_HR, UserProfile.Hiring_Manager):
                created_by_manager = auth_user
            else:
                return Response(
                    {"status": "failure", "msg": "Managers can only create HR or HiringManager users"},
                    status=403
                )
        else:
            # HR / External / HiringManager cannot create users
            return Response(
                {"status": "failure", "msg": "You don't have permission to create users"},
                status=403
            )

        # --- Create user with explicit creator fields ---
        with transaction.atomic():
            user = serializer.save(
                role=role,  # ensure role from validated payload is used
                created_by_superadmin=created_by_superadmin,
                created_by_manager=created_by_manager
            )

        # --- Best-effort welcome email ---
        try:
            EmailService.send_html(
                [user.email], "Welcome", "welcome_email_template.html",
                {'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name}
            )
        except Exception:
            pass

        return Response(
            {"status": "success", "msg": f"{user.role} created successfully", "data": UserSerializer(user).data},
            status=201
        )

# -------------------------
# Login
# -------------------------
class LoginCustomer(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({"msg": "Email and password required"}, status=400)

        try:
            user = UserProfile.objects.get(email=email.lower())
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


# -------------------------
# User Management (list/detail/update/delete)
# -------------------------
class CustomerManageViews(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):
        current_user = request.user

        if id:
            user = get_object_or_404(UserProfile, id=id)
            return Response({"data": UserSerializer(user).data}, status=200)

        if current_user.role == UserProfile.ROLE_SUPERADMIN:
            users = UserProfile.objects.all()
        else:
            users = UserProfile.objects.filter(
                Q(created_by_superadmin=current_user) | Q(created_by_manager=current_user)
            )

        return Response({"data": UserListSerializer(users, many=True).data}, status=200)

    def patch(self, request, id=None):
        if not id:
            return Response({"msg": "User ID required"}, status=400)

        user = get_object_or_404(UserProfile, id=id)
        current_user = request.user

        # Only SuperAdmin or the creator can edit
        if not (
            current_user.role == UserProfile.ROLE_SUPERADMIN or
            user.created_by_superadmin == current_user or
            user.created_by_manager == current_user
        ):
            return Response({"msg": "You are not authorized to edit this user"}, status=403)

        serializer = UserSerializer(user, data=request.data, partial=True, context={"request": request})
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


# -------------------------
# OTP endpoints
# -------------------------
class OTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=400)
        ok, msg = send_otp(email)
        if not ok:
            return Response({"error": msg}, status=429)
        return Response({"message": msg}, status=200)


class VerifyOTP(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        if not email or not otp:
            return Response({"error": "Email and OTP required"}, status=400)
        ok, msg = verify_otp(email, otp)
        if not ok:
            return Response({"error": msg}, status=400)
        return Response({"message": msg}, status=200)


# -------------------------
# Forgot password (via OTP)
# -------------------------
class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        otp = request.data.get('otp')

        if not all([email, password, confirm_password, otp]):
            return Response({"error": "All fields are required: email, password, confirm_password, otp"}, status=400)

        if password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        ok, msg = verify_otp(email, otp)
        if not ok:
            return Response({"error": msg}, status=400)

        try:
            user = UserProfile.objects.get(email=email.lower())
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.password = make_password(password)
        user.save(update_fields=["password"])
        return Response({"message": "Password reset successful"}, status=200)
    


class ManagerTeamListAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, manager_id=None):
        """
        Fetch HR and HiringManager users created by a specific Manager (manager_id).
        Supports either path param /managers/<manager_id>/team/ or ?manager_id=<id>
        """
        # Accept manager_id from path or query param
        manager_id = manager_id or request.query_params.get("manager_id")
        if not manager_id:
            return Response(
                {"status": "error", "message": "manager_id is required (path param or ?manager_id=)."},
                status=400,
            )

        # Validate manager existence
        try:
            manager = UserProfile.objects.get(pk=manager_id)
        except UserProfile.DoesNotExist:
            return Response({"status": "error", "message": "Manager not found."}, status=404)

        # Ensure the user is actually a Manager
        if manager.role != UserProfile.ROLE_MANAGER:
            return Response({"status": "error", "message": "The provided user is not a Manager."}, status=400)

        # Resolve HiringManager role constant (supports both your old/new names)
        hiring_role = getattr(UserProfile, "ROLE_HIRING_MANAGER", getattr(UserProfile, "Hiring_Manager", "HiringManager"))

        # Query users created_by_manager = manager_id and role in [HR, HiringManager]
        base_qs = UserProfile.objects.filter(
            created_by_manager=manager_id,
            role__in=[UserProfile.ROLE_HR, hiring_role],
        ).order_by("id")

        hr_qs = base_qs.filter(role=UserProfile.ROLE_HR)
        hm_qs = base_qs.filter(role=hiring_role)

        hr_data = UserListSerializer(hr_qs, many=True).data
        hm_data = UserListSerializer(hm_qs, many=True).data

        return Response(
            {
                "status": "success",
                "manager": {"id": manager.id, "email": manager.email, "full_name": manager.full_name},
                "counts": {
                    "hr": hr_qs.count(),
                    "hiring_manager": hm_qs.count(),
                    "total": base_qs.count(),
                },
                "hr_list": hr_data,
                "hiring_manager_list": hm_data,
            },
            status=200,
        )
