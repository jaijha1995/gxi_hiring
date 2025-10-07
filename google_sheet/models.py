from django.db import models

class Hiring_process(models.Model):
    INTEGRATION_CHOICES = [
        ("google_sheet", "Google Sheet"),
        ("typeform", "Typeform"),
        ("surveymonkey", "SurveyMonkey"),
    ]

    integration_type = models.CharField(max_length=50, choices=INTEGRATION_CHOICES, db_index=True)
    name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    identifier = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["integration_type"]),
            models.Index(fields=["name"]),
            models.Index(fields=["identifier"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.integration_type}: {self.name or self.identifier}"
