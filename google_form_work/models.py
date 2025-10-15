from django.db import models

class GoogleSheet(models.Model):
    name = models.CharField(max_length=255)
    sheet_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GoogleFormResponse(models.Model):
    sheet = models.ForeignKey(GoogleSheet, on_delete=models.CASCADE, related_name="responses")
    response_id = models.CharField(max_length=255)
    data = models.JSONField()
    current_sattus = models.CharField(max_length=50, default='Scouting')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sheet', 'response_id')

    def __str__(self):
        return f"{self.sheet.name} - {self.response_id}"
