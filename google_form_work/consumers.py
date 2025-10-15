import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.cache import cache
from .models import GoogleSheet, GoogleFormResponse
from .serializers import GoogleFormResponseSerializer
from .utils import fetch_google_form_responses


class GoogleFormAllSheetsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Called when WebSocket client connects"""
        self.room_group_name = "google_forms_all"
        self.keep_running = True  # control flag for loop

        # Join group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.send(text_data=json.dumps({
            "message": "Connected to real-time updates for all Google Sheets (refresh every 4 seconds)"
        }))

        # Start periodic task (background refresh loop)
        self.bg_task = asyncio.create_task(self.refresh_data_loop())

    async def disconnect(self, close_code):
        """Stop loop when WebSocket disconnects"""
        self.keep_running = False
        if hasattr(self, 'bg_task'):
            self.bg_task.cancel()

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle client messages"""
        data = json.loads(text_data)
        action = data.get("action")

        if action == "fetch_latest":
            await self.send_all_sheets_data()
        else:
            await self.send(text_data=json.dumps({"error": "Invalid action"}))

    async def refresh_data_loop(self):
        """Fetch data every 4 seconds continuously"""
        try:
            while self.keep_running:
                await self.send_all_sheets_data()
                await asyncio.sleep(4)  # wait for 4 seconds before fetching again
        except asyncio.CancelledError:
            pass  # gracefully exit when disconnected

    @sync_to_async
    def get_all_sheets_data(self):
        """Fetch latest responses for all sheets (with 24h caching per sheet)"""
        all_data = []

        for sheet in GoogleSheet.objects.all():
            cache_key = f"sheet_{sheet.sheet_id}_responses"
            cached_data = cache.get(cache_key)

            if cached_data:
                sheet_data = {
                    "sheet_name": sheet.name,
                    "sheet_id": sheet.sheet_id,
                    "responses": cached_data
                }
            else:
                try:
                    responses = fetch_google_form_responses(sheet.sheet_id)
                    saved_responses = []
                    for r in responses:
                        response_id = r.get('Timestamp') or str(hash(frozenset(r.items())))
                        obj, _ = GoogleFormResponse.objects.get_or_create(
                            sheet=sheet,
                            response_id=response_id,
                            defaults={'data': r}
                        )
                        saved_responses.append(obj)

                    serializer = GoogleFormResponseSerializer(saved_responses, many=True)
                    serialized_data = serializer.data

                    # Cache data for 24 hours
                    cache.set(cache_key, serialized_data, timeout=86400)

                    sheet_data = {
                        "sheet_name": sheet.name,
                        "sheet_id": sheet.sheet_id,
                        "responses": serialized_data
                    }
                except Exception as e:
                    sheet_data = {
                        "sheet_name": sheet.name,
                        "sheet_id": sheet.sheet_id,
                        "error": str(e)
                    }

            all_data.append(sheet_data)
        return all_data

    async def send_all_sheets_data(self):
        """Send all sheets data to WebSocket client"""
        data = await self.get_all_sheets_data()
        await self.send(text_data=json.dumps({
            "type": "all_sheets_data",
            "data": data
        }))

    async def send_new_data(self, event):
        """Send new data to all connected clients"""
        await self.send(text_data=json.dumps({
            "type": "new_data",
            "data": event['data']
        }))
