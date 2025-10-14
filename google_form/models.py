from django.db import models

class google_form(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    identifier = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["identifier"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.name or self.identifier}"
