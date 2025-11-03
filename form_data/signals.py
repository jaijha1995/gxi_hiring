from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import FormData


def get_status_counts():
    """Helper for computing counts in sync context (for signal)"""
    all_forms = FormData.objects.values_list("submission_data", flat=True)
    counts = {"Scouting": 0, "Ongoing": 0, "Hired": 0, "Reject": 0}
    for data in all_forms.iterator():
        if isinstance(data, dict):
            status = data.get("status", "Scouting")
            counts[status] = counts.get(status, 0) + 1
    return counts


@receiver([post_save, post_delete], sender=FormData)
def broadcast_formdata_update(sender, instance, **kwargs):
    """Broadcast update to WebSocket group when any FormData changes."""
    channel_layer = get_channel_layer()
    counts = get_status_counts()
    async_to_sync(channel_layer.group_send)(
        "formdata_realtime",
        {
            "type": "formdata_update_event",
            "message": f"FormData record updated: {instance.id}",
            "status_counts": counts,
        }
    )
