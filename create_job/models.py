from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings
from django.core.exceptions import ValidationError
from superadmin.models import UserProfile  # just for role constants


# Optional reusable timestamp mixin (left as-is per your code)
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


class Teams(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    department_types = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
        related_name='teams'
    )

    def __str__(self):
        return self.name

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
    title = models.CharField(max_length=255,  unique=True,db_index=True)
    job_id = models.CharField(max_length=20, unique=True, db_index=True, editable=False)
    Description = models.TextField()
    Salary_range = models.CharField(max_length=100, db_index=True)
    Experience_required = models.CharField(max_length=100, db_index=True)
    no_opening = models.PositiveIntegerField(validators=[MinValueValidator(1)], db_index=True)
    skills_required = models.ManyToManyField(Skills, related_name='jobs', blank=True)
    last_hiring_date = models.DateField(null=True, blank=True, db_index=True)
    teams = models.ForeignKey(Teams,on_delete=models.CASCADE,null=True,blank=True,related_name='jobs',db_index=True)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='posted_jobs',db_index=True)
    employments_types = models.ForeignKey(Job_types,on_delete=models.CASCADE,null=True,blank=True,related_name='jobs',db_index=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='jobs_managed',db_index=True)
    hiring_manager = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='jobs_as_hiring_manager',db_index=True)
    hr_team_members = models.ManyToManyField(settings.AUTH_USER_MODEL,related_name='jobs_as_hr')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    # def clean(self):
    #     errors = {}
    #     if self.manager and getattr(self.manager, 'role', None) != UserProfile.ROLE_MANAGER:
    #         errors["manager"] = "Selected user is not a Manager."

    #     if self.hiring_manager:
    #         if getattr(self.hiring_manager, 'role', None) != UserProfile.Hiring_Manager:
    #             errors["hiring_manager"] = "Selected user is not a HiringManager."
    #         if self.manager and getattr(self.hiring_manager, 'created_by_manager_id', None) != self.manager_id:
    #             errors["hiring_manager"] = "HiringManager must be created by the selected Manager."

    #     # ⬇️ Only check M2M after the instance has a PK
    #     if self.pk:
    #         if self.hr_team_members.exists():
    #             bad_roles = self.hr_team_members.exclude(role=UserProfile.ROLE_HR)
    #             if bad_roles.exists():
    #                 errors["hr_team_members"] = "All selected users must have HR role."
    #             if self.manager:
    #                 wrong_mgr = self.hr_team_members.exclude(created_by_manager_id=self.manager_id)
    #                 if wrong_mgr.exists():
    #                     errors["hr_team_members"] = "All HRs must be created by the selected Manager."

    #     if errors:
    #         raise ValidationError(errors)


    def save(self, *args, **kwargs):
        if not self.job_id:
            last_job = add_job.objects.all().order_by('-id').first()
            if last_job and last_job.job_id:
                try:
                    last_number = int(last_job.job_id.replace('GXI', ''))
                except ValueError:
                    last_number = 1000
                new_number = last_number + 1
            else:
                new_number = 1001

            self.job_id = f"GXI{new_number}"

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.job_id})"

    class Meta:
        db_table = 'add_job'
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['title', 'is_active']),
            models.Index(fields=['job_id', 'is_active']),
            models.Index(fields=['teams', 'is_active']),
            models.Index(fields=['employments_types', 'is_active']),
            models.Index(fields=['Salary_range', 'Experience_required']),
            models.Index(fields=['created_at', 'updated_at']),
            models.Index(fields=['manager', 'is_active']),
            models.Index(fields=['hiring_manager', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['job_id'], name='unique_job_id_constraint'),
        ]
