from django.db import models
from django.core.validators import MinValueValidator


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


class Teams(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    department_types = models.ForeignKey(
        Department,
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


class Job(TimeStampedModel):
    Job_Title = models.CharField(max_length=255, db_index=True)
    Experience_In_Years = models.IntegerField(
        db_index=True,
        validators=[MinValueValidator(0)]
    )
    Description = models.TextField()
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
        related_name='jobs'
    )
    Job_Type = models.ForeignKey(
        Job_types,
        on_delete=models.CASCADE,
        db_index=True,
        null=True,
        blank=True,
        related_name='jobs'
    )
    Job_Location = models.CharField(max_length=255, db_index=True)
    no_of_opening = models.IntegerField(
        db_index=True,
        validators=[MinValueValidator(0)]
    )
    # Keeping your original column name (typo) but adding a clearer Python name alias is risky for existing code.
    # To avoid breaking code, we keep your original field name and add help_text.
    Targerted_Hiring_Date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="(typo kept for backward compatibility) Targeted hiring date."
    )
    Skills_Required = models.ManyToManyField(
        Skills,
        related_name='jobs',
        blank=True
    )

    def __str__(self):
        return self.Job_Title

    class Meta:
        db_table = 'job_listings'
        indexes = [
            models.Index(fields=["Job_Title"]),
            models.Index(fields=["Experience_In_Years"]),
            models.Index(fields=["Job_Location"]),
            models.Index(fields=["Targerted_Hiring_Date"]),
        ]
        ordering = ["-created_at", "-id"]
