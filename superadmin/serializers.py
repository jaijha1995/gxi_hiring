from rest_framework import serializers
from django.core.validators import validate_email
from rest_framework.exceptions import ValidationError
from .models import UserProfile


# ------------------------------------------
# Base User Serializer (Create / Update)
# ------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'address', 'profile_picture',
            'password', 'confirm_password', 'role',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    # ------------------------------
    # Field Validations
    # ------------------------------
    def validate_email(self, value):
        """Ensure unique email except for self during update."""
        user_id = self.instance.id if self.instance else None
        if UserProfile.objects.exclude(id=user_id).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # Password validation logic
        if password or confirm_password:
            if not password or not confirm_password:
                raise serializers.ValidationError({"password": "Password and Confirm Password are required"})
            if password != confirm_password:
                raise serializers.ValidationError({"password": "Passwords do not match"})

        # Clean full_name if provided
        if 'full_name' in data and data['full_name']:
            data['full_name'] = data['full_name'].strip()

        return data

    # ------------------------------
    # Create User
    # ------------------------------
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        role = validated_data.get('role', 'ExternalUser')

        # Assign is_staff / is_superuser based on role
        if role == 'SuperAdmin':
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = True
        elif role == 'Manager':
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = False
        elif role == 'HR':
            validated_data['is_staff'] = True
            validated_data['is_superuser'] = False
        else:  # ExternalUser
            validated_data['is_staff'] = False
            validated_data['is_superuser'] = False

        user = UserProfile(**validated_data)

        if password:
            user.set_password(password)
        user.save()
        return user

    # ------------------------------
    # Update User
    # ------------------------------
    def update(self, instance, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        # Update flags when role changes
        if 'role' in validated_data:
            role = validated_data['role']
            if role == 'SuperAdmin':
                instance.is_staff = True
                instance.is_superuser = True
            elif role in ['Manager', 'HR']:
                instance.is_staff = True
                instance.is_superuser = False
            else:
                instance.is_staff = False
                instance.is_superuser = False

        instance.save()
        return instance


# ------------------------------------------
# Limited Fields Serializer (for updates)
# ------------------------------------------
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'profile_picture', 'phone_number', 'address',
            'is_active', 'is_staff', 'role'
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        try:
            validate_email(value)
        except Exception:
            raise ValidationError("Enter a valid email address.")
        return value

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ------------------------------------------
# Simple List Serializer (for listing users)
# ------------------------------------------
class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'email', 'full_name', 'phone_number', 'address', 'role']


# ------------------------------------------
# OTP Verification Serializer
# ------------------------------------------
class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data
