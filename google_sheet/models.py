from django.db import models

class GoogleSheet(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    spreadsheet_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.spreadsheet_id
