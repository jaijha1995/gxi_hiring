from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.cache import cache

from .models import UserProfile
from .serializers import UserSerializer
from .utils import generate_otp, send_otp_email  # Optional utilities if needed

import logging
import secrets

logger = logging.getLogger(__name__)


class CustomerViews(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)

    def generate_token_number(self):
        return secrets.token_hex(16)

    def send_welcome_email(self, email, first_name, last_name):
        subject = 'Welcome to Gxi Hiring'
        html_message = render_to_string('welcome_email_template.html', {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
        })
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message, 'jai@skylabstech.com', [email], html_message=html_message)

    def post(self, request, org_id=None):
        data = request.data
        logger.info("Creating new customer")
        serializer = UserSerializer(data=data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            # Check email in cache to avoid duplicate
            if cache.get(email):
                return Response({
                    "status": "failure",
                    "msg": "Customer with this email already exists"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Save user
            customer = serializer.save()
            self.send_welcome_email(customer.email, customer.first_name, customer.last_name)
            cache.set(email, customer.id, timeout=3600)

            return Response({
                "status": "success",
                "data": UserSerializer(customer).data  # return fresh data without password
            }, status=status.HTTP_201_CREATED)

        logger.warning(serializer.errors)
        return Response({
            "status": "failure",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, id=None):
        if id:
            customer = UserProfile.objects.filter(id=id).first()
            if customer:
                serializer = UserSerializer(customer)
                return Response({
                    "status": "success",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                "status": "error",
                "message": "Customer not found"
            }, status=status.HTTP_404_NOT_FOUND)

        # Get all customers
        customers = UserProfile.objects.all()
        serializer = UserSerializer(customers, many=True)
        return Response({
            "status": "success",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, id=None, org_id=None):
        if not id:
            return Response({
                "status": "failure",
                "msg": "User ID is required for update."
            }, status=status.HTTP_400_BAD_REQUEST)

        customer = get_object_or_404(UserProfile, id=id)

        # Do not enforce email validation if it's not being updated
        incoming_email = request.data.get("email")
        if incoming_email and incoming_email != customer.email:
            if UserProfile.objects.exclude(id=customer.id).filter(email=incoming_email).exists():
                return Response({
                    "status": "failure",
                    "msg": "A user with this email already exists."
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(customer, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "failure",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, id=None, org_id=None):
        customer = get_object_or_404(UserProfile, id=id)
        customer.delete()
        return Response({
            "status": "success",
            "data": "Customer deleted"
        }, status=status.HTTP_200_OK)



class ListCustomerViews(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, org_id=None):
        items = UserProfile.objects.filter(org_id=org_id).only('id', 'first_name', 'last_name', 'email')
        serializer = UserSerializer(items, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)



from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password

class LoginCustomer(APIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def post(self, request, org_id=None):
        email = request.data['email']
        password = request.data['password']

        try:
            # Fetch the customer based on email
            item = UserProfile.objects.get(email=email)
            
            # Check if the password is correct
            if check_password(password, item.password):
                # Generate JWT tokens
                refresh = RefreshToken.for_user(item)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                # Serialize the customer data
                serializer = UserSerializer(item)
                data = serializer.data
                
                # Return the response with the JWT token
                return Response({
                    "status": "success",
                    "data": data,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "msg": "Login successful"
                })
            else:
                return Response({
                    "status": "failure", 
                    "msg": "Invalid credentials. Please check your email and password."
                })

        except UserProfile.DoesNotExist:
            return Response({
                "status": "failure", 
                "msg": "Email does not exist. Please check your email and try again."
            })

        
from rest_framework.permissions import AllowAny

class OTPView(APIView):
    permission_classes = [AllowAny]  # 👈 This allows unauthenticated access

    def post(self, request):
        email = request.data.get('email')
        try:
            customer = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        otp = generate_otp()
        send_otp_email(email, otp)
        customer.otp = otp
        customer.save()

        return Response({"otp": otp}, status=status.HTTP_200_OK)


class VerifyOTP(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        try:
            customer = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Invalid email.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp != customer.otp:
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        customer.is_verified = True
        customer.save()

        return Response({'message': 'OTP verified successfully.'})


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from .models import UserProfile

class ForgotPasswordAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)

        if not password or not confirm_password:
            return Response({"error": "Password and Confirm Password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        user.password = make_password(password)
        user.save(update_fields=["password"])

        return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
    
