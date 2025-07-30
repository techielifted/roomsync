import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from asgiref.sync import sync_to_async

# DO NOT import get_user_model() or other Django models here globally
# Import them inside methods or @sync_to_async wrapped functions,
# where the Django app registry is guaranteed to be ready.

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # The user object is available in self.scope['user'] due to AuthMiddlewareStack
        self.user = self.scope['user']

        # Ensure the user is authenticated and has an apartment_id
        if not self.user.is_authenticated or not self.user.apartment_id:
            await self.close() # Close connection if user is not authenticated or lacks apartment_id
            return

        self.apartment_id = self.user.apartment_id
        self.apartment_group_name = f'chat_{self.apartment_id}' # Group name for apartment's chat

        # Join apartment group
        await self.channel_layer.group_add(
            self.apartment_group_name,
            self.channel_name
        )
        await self.accept() # Accept the WebSocket connection

    async def disconnect(self, close_code):
        # Leave apartment group on disconnect
        await self.channel_layer.group_discard(
            self.apartment_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Receives messages from the WebSocket.
        """
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '').strip()

        if not message:
            return # Don't process empty messages

        # Save message to database using a synchronous function (sync_to_async)
        # Import models inside this sync_to_async context to avoid AppRegistryNotReady
        await self.save_chat_message(self.user, self.apartment_id, message)

        # Send message to the apartment's group (all connected clients in that group)
        await self.channel_layer.group_send(
            self.apartment_group_name,
            {
                'type': 'chat_message',  # Corresponds to the chat_message method below
                'message': message,
                'user_email': self.user.email,
                'timestamp': timezone.now().isoformat(), # Send ISO format for JavaScript parsing
            }
        )

    async def chat_message(self, event):
        """
        Receives messages from the apartment group and sends them to the WebSocket.
        This method is called by the channel layer when a message is sent to the group.
        """
        message = event['message']
        user_email = event['user_email']
        timestamp = event['timestamp']

        # Send message data back to the WebSocket client
        await self.send(text_data=json.dumps({
            'message': message,
            'user_email': user_email,
            'timestamp': timestamp,
        }))

    @sync_to_async
    def save_chat_message(self, user, apartment_id, message_content):
        """
        Synchronous function to save the chat message to the database.
        It's run in a separate thread pool by Channels' sync_to_async.
        """
        # Import models here to ensure the Django app registry is ready
        from .models import Apartment, ChatMessage

        try:
            apartment_obj = Apartment.objects.get(apartment_id=apartment_id)
            ChatMessage.objects.create(user=user, apartment=apartment_obj, message=message_content)
        except Apartment.DoesNotExist:
            print(f"Error: Apartment with ID {apartment_id} not found for chat message.")
        except Exception as e:
            print(f"Error saving chat message: {e}")