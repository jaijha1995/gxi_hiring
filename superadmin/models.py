from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# -----------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role='ExternalUser', **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with all access rights."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SuperAdmin')

        return self.create_user(email, password, **extra_fields)


# -----------------------
# User Model
# -----------------------
class UserProfile(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('ExternalUser', 'External User'),
        ('HR', 'HR'),
        ('Manager', 'Manager'),
        ('SuperAdmin', 'Super Admin'),
    ]

    # Basic Info
    email = models.EmailField(unique=True, max_length=255)
    username = models.CharField(unique=True, max_length=150, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)

    # Profile Info
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Role & Permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ExternalUser')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # OTP for verification (optional)
    otp = models.CharField(max_length=6, blank=True, null=True)

    # Custom Manager
    objects = UserManager()

    # Authentication Fields
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    def __str__(self):
        return f"{self.email} ({self.role})"

    # -----------------------
    # Role-based Permission Logic
    # -----------------------
    def has_module_perms(self, app_label):
        """
        Defines if user has permissions to view app modules.
        SuperAdmin always has full access.
        """
        if self.role == 'SuperAdmin' or self.is_superuser:
            return True
        return super().has_module_perms(app_label)

    def has_perm(self, perm, obj=None):
        """
        Custom permission logic based on user role.
        """
        if self.role == 'SuperAdmin' or self.is_superuser:
            # SuperAdmin has all permissions
            return True

        elif self.role == 'Manager':
            # Manager can add or manage HR users
            if perm.startswith('add_hr') or perm.startswith('change_hr'):
                return True
            return False

        elif self.role == 'HR':
            # HR can only log in, not modify anything
            return False

        elif self.role == 'ExternalUser':
            # External users have limited access
            return False

        return super().has_perm(perm, obj)
