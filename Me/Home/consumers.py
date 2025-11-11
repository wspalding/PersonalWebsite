from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .llm import getChatResponse

class ChatConsumer(AsyncWebsocketConsumer):
    gpu_active = False

    async def connect(self):
        # Accept the connection
        await self.accept()

    async def disconnect(self, close_code):
        # Optional: clean up groups, etc.
        pass

    async def receive(self, text_data=None, bytes_data=None):
        # Echo back whatever was sent
        print(text_data)
        message_response = getChatResponse(text_data)
        if text_data is not None:
            await self.send(text_data=json.dumps({
                'message': message_response
            }))