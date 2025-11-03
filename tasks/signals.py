from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from create_job.models import Job
from .models import Task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json


@receiver(post_save, sender=Job)
def create_task_for_new_job(sender, instance, created, **kwargs):
    if created:
        # Assign job task to first staff user (you can modify this logic)
        assigned_user = User.objects.filter(is_staff=True).first()
        if not assigned_user:
            return

        task = Task.objects.create(
            user=assigned_user,
            job=instance,
            title=f"New Job: {instance.Job_Title}",
            description=f"Review the new job '{instance.Job_Title}' created at {instance.Job_Location}."
        )

        # Real-time WebSocket notification
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{assigned_user.id}",
            {
                "type": "new_task_notification",
                "message": json.dumps({
                    "task_id": task.id,
                    "title": task.title,
                    "job_title": instance.Job_Title,
                    "description": task.description,
                    "created_at": str(task.created_at),
                })
            }
        )
