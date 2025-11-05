from rest_framework import serializers
from django.core.validators import validate_email
from django.db import transaction
from .models import UserProfile, SuperAdmin, Manager, HR, ExternalUser , hiring_managerUser

class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=False)

    class Meta:
        model = UserProfile
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'address', 'profile_picture',
            'password', 'confirm_password', 'role',
            'created_by_superadmin', 'created_by_manager'
        ]
        read_only_fields = ('created_by_superadmin', 'created_by_manager')
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def validate_email(self, value):
        user_id = self.instance.id if self.instance else None
        if UserProfile.objects.exclude(id=user_id).filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        try:
            validate_email(value)
        except Exception:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.lower()

    def validate(self, data):
        password = data.get('password')
        confirm = data.get('confirm_password')
        if password or confirm:
            if not password or not confirm:
                raise serializers.ValidationError({"password": "Both password and confirm_password are required."})
            if password != confirm:
                raise serializers.ValidationError({"password": "Passwords do not match."})
        if 'full_name' in data and data['full_name']:
            data['full_name'] = data['full_name'].strip()
        return data

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        role = validated_data.get('role', UserProfile.ROLE_EXTERNAL)
        user = UserProfile(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.role = role
        user.save()
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        # role-driven staff flags handled in model.save()
        instance.save()
        return instance

# role-specific serializers (keep for convenience)
class SuperAdminSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = SuperAdmin

class ManagerSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = Manager

class HRSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = HR

class ExternalUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = ExternalUser

class Hiring_managerSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = hiring_managerUser 

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'email', 'full_name', 'phone_number', 'address', 'role', 'created_by_superadmin', 'created_by_manager']
