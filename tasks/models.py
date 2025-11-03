from django.db import models
from superadmin.models import UserProfile
from create_job.models import Job
from form_data.models import FormData

# Create your models here.

class Task(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="tasks")
    job =  models.ForeignKey('create_job.Job',on_delete=models.CASCADE,related_name="tasks",null=True,blank=True)
    form_data = models.ForeignKey(FormData, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True)  # ✅ new
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_completed"]),
            models.Index(fields=["created_at"]),
        ]


    def __str__(self):
        return f"{self.title} ({'Done' if self.is_completed else 'Pending'})"
