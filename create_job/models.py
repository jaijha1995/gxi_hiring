from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


# Optional reusable timestamp mixin
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Location(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'locations'
        ordering = ["name"]


class Skills(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'skills'
        ordering = ["name"]


class Department(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    # Renamed field variable for clarity, keeps your table and relation intact
    Location_types = models.ManyToManyField(
        Location,
        related_name='departments',
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'Departments'
        ordering = ["name"]


# create_job/models.py
# create_job/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from superadmin.models import UserProfile  # just for role constants

class Teams(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    department_types = models.ForeignKey(
        'Department', on_delete=models.CASCADE, db_index=True, null=True, blank=True, related_name='teams'
    )

    # Single Manager
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='teams_managed',
        db_index=True
    )

    # Single Hiring Manager
    hiring_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='teams_as_hiring_manager',
        db_index=True
    )

    # Multiple HRs
    hr_team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teams_as_hr',
        blank=True
    )

    def clean(self):
        if self.manager and self.manager.role != UserProfile.ROLE_MANAGER:
            raise ValidationError({"manager": "Selected user is not a Manager."})

        if self.hiring_manager:
            if self.hiring_manager.role != UserProfile.Hiring_Manager:
                raise ValidationError({"hiring_manager": "Selected user is not a HiringManager."})
            if self.manager and self.hiring_manager.created_by_manager_id != self.manager_id:
                raise ValidationError({"hiring_manager": "HiringManager must be created by the selected Manager."})

        if self.pk:
            bad_roles = self.hr_team_members.exclude(role=UserProfile.ROLE_HR)
            if bad_roles.exists():
                raise ValidationError({"hr_team_members": "All selected users must have HR role."})
            if self.manager:
                wrong_mgr = self.hr_team_members.exclude(created_by_manager_id=self.manager_id)
                if wrong_mgr.exists():
                    raise ValidationError({"hr_team_members": "All HRs must be created by the selected Manager."})

    class Meta:
        db_table = 'Teams'
        ordering = ["name"]




class Job_types(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'Job_types'
        ordering = ["name"]


class add_job(TimeStampedModel):
    title = models.CharField(max_length=255, db_index=True)
    job_id = models.CharField(max_length=20, unique=True, db_index=True, editable=False) 
    Description = models.TextField()
    Salary_range = models.CharField(max_length=100, db_index=True)
    Experience_required = models.CharField(max_length=100, db_index=True)
    no_opening = models.PositiveIntegerField(validators=[MinValueValidator(1)], db_index=True)
    teams = models.ForeignKey(Teams , on_delete=models.CASCADE, null=True, blank=True, related_name='jobs', db_index=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='posted_jobs',db_index=True)
    employments_types = models.ForeignKey(Job_types , on_delete=models.CASCADE, null=True, blank=True, related_name='jobs', db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)


    def save(self, *args, **kwargs):
        # Auto-generate job_id if not set
        if not self.job_id:
            last_job = add_job.objects.all().order_by('-id').first()
            if last_job and last_job.job_id:
                try:
                    # Extract numeric part from last job_id (e.g., GXI1002 -> 1002)
                    last_number = int(last_job.job_id.replace('GXI', ''))
                except ValueError:
                    last_number = 1000  # fallback
                new_number = last_number + 1
            else:
                new_number = 1001  # Start from GXI1001

            self.job_id = f"GXI{new_number}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.job_id})"

    class Meta:
        db_table = 'add_job'
        ordering = ["-created_at"]
        indexes = [
            # Composite indexes for frequent query combinations
            models.Index(fields=['title', 'is_active']),
            models.Index(fields=['job_id', 'is_active']),
            models.Index(fields=['teams', 'is_active']),
            models.Index(fields=['employments_types', 'is_active']),
            models.Index(fields=['Salary_range', 'Experience_required']),
            models.Index(fields=['created_at', 'updated_at']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['job_id'], name='unique_job_id_constraint'),
        ]
