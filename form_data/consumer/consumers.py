import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.db.models import Q
from ..models import FormData


class FormDataRealtimeConsumer(AsyncWebsocketConsumer):
    """
    Real-time FormData consumer (event-driven, no time interval).
    Broadcasts data instantly when model changes (via signal).
    Supports:
      - Realtime total counts by status
      - Filtered data by status
    """

    async def connect(self):
        self.group_name = "formdata_realtime"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.send_json({
            "type": "connection",
            "message": "✅ Connected to real-time FormData feed"
        })

        # Send initial data
        counts = await self.get_status_counts()
        await self.send_json({
            "type": "initial_counts",
            "status_counts": counts
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Expected message examples:
        {"action": "filter_status", "status": "Ongoing"}
        {"action": "get_counts"}
        """
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "get_counts":
                counts = await self.get_status_counts()
                await self.send_json({
                    "type": "status_counts",
                    "status_counts": counts
                })

            elif action == "filter_status":
                status_value = data.get("status")
                filtered = await self.get_filtered_data(status_value)
                await self.send_json({
                    "type": "filtered_data",
                    "status": status_value,
                    "total": len(filtered),
                    "data": filtered
                })

            else:
                await self.send_json({"error": "Invalid action"})
        except Exception as e:
            await self.send_json({"error": str(e)})

    # --------------------------
    # Signal-triggered broadcast
    # --------------------------
    async def formdata_update_event(self, event):
        """
        Called when Django signal broadcasts FormData change.
        """
        await self.send_json({
            "type": "update",
            "message": event["message"],
            "status_counts": event["status_counts"]
        })

    # --------------------------
    # Helpers: Query Functions
    # --------------------------
    @sync_to_async
    def get_status_counts(self):
        """Aggregate FormData.status counts from JSONField."""
        all_forms = FormData.objects.values_list("submission_data", flat=True)
        counts = {"Scouting": 0, "Ongoing": 0, "Hired": 0, "Reject": 0}
        for data in all_forms.iterator():
            if isinstance(data, dict):
                s = data.get("status", "Scouting")
                counts[s] = counts.get(s, 0) + 1
        return counts

    @sync_to_async
    def get_filtered_data(self, status_value):
        """Filter candidates by status."""
        results = []
        forms = FormData.objects.values("id", "form_name", "submission_data", "submitted_at")
        for form in forms.iterator():
            data = form.get("submission_data", {})
            if data.get("status") == status_value:
                results.append({
                    "id": form["id"],
                    "Name": data.get("Name"),
                    "Email": data.get("Email"),
                    "Role": data.get("Role"),
                    "Status": data.get("status"),
                    "Location": data.get("Location"),
                    "Submitted_At_IST": data.get("Submitted_At_IST"),
                })
        return results

    async def send_json(self, content):
        """Send data safely as JSON"""
        await self.send(text_data=json.dumps(content))
