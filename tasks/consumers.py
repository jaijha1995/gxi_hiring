import json
from channels.generic.websocket import AsyncWebsocketConsumer


class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            self.group_name = f"user_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        user = self.scope["user"]
        if user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_task_notification(self, event):
        message = json.loads(event["message"])
        await self.send(text_data=json.dumps({
            "type": "new_task",
            "data": message
        }))
