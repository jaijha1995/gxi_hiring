from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role='ExternalUser', **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "SuperAdmin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class UserProfile(AbstractBaseUser, PermissionsMixin):
    ROLE_SUPERADMIN = 'SuperAdmin'
    ROLE_MANAGER = 'Manager'
    ROLE_HR = 'HR'
    ROLE_EXTERNAL = 'ExternalUser'

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, 'SuperAdmin'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_HR, 'HR'),
        (ROLE_EXTERNAL, 'ExternalUser'),
    ]

    email = models.EmailField(unique=True, max_length=255, db_index=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True, db_index=True)
    first_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    last_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_EXTERNAL, db_index=True)

    created_by_superadmin = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='superadmin_created', db_index=True
    )
    created_by_manager = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='manager_created', db_index=True
    )

    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    otp = models.CharField(max_length=10, null=True, blank=True, db_index=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"

    def clean(self):
        """
        Enforce hierarchical consistency:
         - Manager must have created_by_superadmin set (can't be null when role is Manager).
         - HR must have created_by_manager set.
         - ExternalUser must have created_by_superadmin set.
         - Prevent circular created_by references (self or child role).
        """
        if self.role == self.ROLE_MANAGER and not self.created_by_superadmin:
            raise ValidationError("Manager must be created by a SuperAdmin.")
        if self.role == self.ROLE_HR and not self.created_by_manager:
            raise ValidationError("HR must be created by a Manager.")
        if self.role == self.ROLE_EXTERNAL and not self.created_by_superadmin:
            raise ValidationError("ExternalUser must be created by a SuperAdmin.")

        # prevent circular refs
        if self.created_by_superadmin and self.created_by_superadmin_id == self.id:
            raise ValidationError("created_by_superadmin cannot be the user itself.")
        if self.created_by_manager and self.created_by_manager_id == self.id:
            raise ValidationError("created_by_manager cannot be the user itself.")

    def save(self, *args, **kwargs):
        self.full_clean()
        # set staff flags implicitly (keeps serializer code simpler)
        if self.role == self.ROLE_SUPERADMIN:
            self.is_staff = True
            self.is_superuser = True
        elif self.role in (self.ROLE_MANAGER, self.ROLE_HR):
            self.is_staff = True
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    def get_creator_info(self):
        if self.role == self.ROLE_MANAGER and self.created_by_superadmin:
            return {"superadmin_id": self.created_by_superadmin.id, "superadmin_email": self.created_by_superadmin.email}
        if self.role == self.ROLE_HR and self.created_by_manager:
            return {"manager_id": self.created_by_manager.id, "manager_email": self.created_by_manager.email}
        if self.role == self.ROLE_EXTERNAL and self.created_by_superadmin:
            return {"superadmin_id": self.created_by_superadmin.id, "superadmin_email": self.created_by_superadmin.email}
        return {}

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['first_name']),
            models.Index(fields=['last_name']),
            models.Index(fields=['full_name']),
            models.Index(fields=['role']),
            models.Index(fields=['created_by_superadmin']),
            models.Index(fields=['created_by_manager']),
            models.Index(fields=['is_active']),
            models.Index(fields=['otp']),
        ]
        ordering = ['id']


# Proxy / Virtual Models remain unchanged
class SuperAdminManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=UserProfile.ROLE_SUPERADMIN)


class ManagerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=UserProfile.ROLE_MANAGER)


class HRManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=UserProfile.ROLE_HR)


class ExternalUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=UserProfile.ROLE_EXTERNAL)


class SuperAdmin(UserProfile):
    objects = SuperAdminManager()

    class Meta:
        proxy = True
        verbose_name = 'SuperAdmin'
        verbose_name_plural = 'SuperAdmins'

    def save(self, *args, **kwargs):
        self.role = UserProfile.ROLE_SUPERADMIN
        super().save(*args, **kwargs)


class Manager(UserProfile):
    objects = ManagerManager()

    class Meta:
        proxy = True
        verbose_name = 'Manager'
        verbose_name_plural = 'Managers'

    def save(self, *args, **kwargs):
        self.role = UserProfile.ROLE_MANAGER
        super().save(*args, **kwargs)


class HR(UserProfile):
    objects = HRManager()

    class Meta:
        proxy = True
        verbose_name = 'HR'
        verbose_name_plural = 'HRs'

    def save(self, *args, **kwargs):
        self.role = UserProfile.ROLE_HR
        super().save(*args, **kwargs)


class ExternalUser(UserProfile):
    objects = ExternalUserManager()

    class Meta:
        proxy = True
        verbose_name = 'ExternalUser'
        verbose_name_plural = 'ExternalUsers'

    def save(self, *args, **kwargs):
        self.role = UserProfile.ROLE_EXTERNAL
        super().save(*args, **kwargs)
