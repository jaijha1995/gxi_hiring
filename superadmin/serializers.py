from rest_framework import serializers
from .models import UserProfile
from rest_framework.exceptions import ValidationError
from django.core.validators import validate_email
# from .utils import CustomLogger, send_email

# logger = CustomLogger('restserver', filename='auth.log')



class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone_number', 'address', 'profile_picture',
            'password', 'confirm_password', 'full_name'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
        }

    def validate_email(self, value):
        """
        Skip unique validation if email belongs to the current instance.
        """
        user_id = self.instance.id if self.instance else None
        if UserProfile.objects.exclude(id=user_id).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # Only validate passwords if one of them is provided (i.e., during creation or password change)
        if password or confirm_password:
            if not password or not confirm_password:
                raise serializers.ValidationError({"password": "Password and Confirm Password are required"})

            if password != confirm_password:
                raise serializers.ValidationError({"password": "Passwords do not match"})

        # Clean full_name if provided
        if 'full_name' in data and data['full_name']:
            data['full_name'] = data['full_name'].strip()

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)

        user = UserProfile(**validated_data)

        if password:
            user.set_password(password)

        user.save()
        return user

    def update(self, instance, validated_data):
        # Remove confirm_password if present
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)

        # Update instance fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update password if provided
        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'email', 'username', 'first_name','last_name', 'profile_picture', 'phone_number', 'address', 'is_active', 'is_staff']
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


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id','email', 'full_name', 'phone_number', 'address']



class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Password do not match")
        return data