import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from form_data.models import FormData
from form_data.serializers import FormDataSerializer


class FormDataModelRealtimeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "formdata_model_realtime"

        # Add this connection to the group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send initial dataset when connected
        await self.send_json({
            "type": "connection",
            "message": "✅ Connected to live FormData model stream"
        })

        initial_data = await self.get_all_formdata()
        await self.send_json({
            "type": "initial_data",
            "total": len(initial_data),
            "data": initial_data
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "refresh":
                refreshed = await self.get_all_formdata()
                await self.send_json({
                    "type": "refresh_data",
                    "total": len(refreshed),
                    "data": refreshed
                })

            elif action == "filter":
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

    async def formdata_model_event(self, event):
        """
        Triggered when a FormData object is added/updated/deleted.
        """
        await self.send_json({
            "type": "update",
            "message": event["message"],
            "action": event.get("action"),
            "record": event.get("record"),
            "total": event.get("total", 0)
        })

    @sync_to_async
    def get_all_formdata(self):
        """Return all FormData records serialized"""
        queryset = FormData.objects.all().order_by("-submitted_at")[:100]  # latest 100 records
        serializer = FormDataSerializer(queryset, many=True)
        return serializer.data

    @sync_to_async
    def get_filtered_data(self, status_value):
        """Filter FormData by status (inside submission_data)"""
        results = []
        queryset = FormData.objects.values("id", "form_name", "submission_data", "submitted_at")

        for form in queryset.iterator():
            data = form.get("submission_data", {})
            if data.get("status") == status_value:
                results.append({
                    "id": form["id"],
                    "Name": data.get("Name"),
                    "Email": data.get("Email"),
                    "Role": data.get("Role"),
                    "Status": data.get("status"),
                    "Submitted_At_IST": data.get("Submitted_At_IST"),
                })
        return results
    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))
