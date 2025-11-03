from django.db import models
from superadmin.models import UserProfile
from create_job.models import Job

# Create your models here.

class Task(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="tasks")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({'Done' if self.is_completed else 'Pending'})"
