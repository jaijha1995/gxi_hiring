# tasks/signals_update_formdata.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from tasks.models import Task
from django.utils import timezone

@receiver(post_save, sender=Task)
def update_formdata_on_task_complete(sender, instance, **kwargs):
    """
    Whenever a Task is marked as completed by HR,
    update the related FormData.status automatically.
    """
    # only if HR completed the task
    if instance.is_completed and instance.form_data:
        form = instance.form_data
        submission_data = form.submission_data or {}
        old_status = submission_data.get("status", "Scouting")

        # set new status
        new_status = "Reviewed by HR"

        # append to history
        submission_data.setdefault("status_history", []).append({
            "from": old_status,
            "to": new_status,
            "updated_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_by": getattr(instance.user, "email", "HR")
        })

        submission_data["status"] = new_status

        form.submission_data = submission_data
        form.save(update_fields=["submission_data"])
