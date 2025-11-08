from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the connection
        await self.accept()

    async def disconnect(self, close_code):
        # Optional: clean up groups, etc.
        pass

    async def receive(self, text_data=None, bytes_data=None):
        # Echo back whatever was sent
        if text_data is not None:
            await self.send(text_data=text_data)