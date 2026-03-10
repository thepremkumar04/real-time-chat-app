import json
import base64
from django.core.files.base import ContentFile
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope['user']

        if not user.is_authenticated:
            return

        # --- 1. HANDLE DELETIONS ---
        if data.get('action') == 'delete':
            msg_id = data.get('message_id')
            # Securely try to delete the message from the DB
            success = await self.delete_message_from_db(user, msg_id)
            if success:
                # If deleted, tell everyone in the room to remove it from their screen!
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': msg_id
                    }
                )
            return

        # --- 2. HANDLE TYPING ---
        if 'typing' in data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'user_typing', 'username': user.username, 'is_typing': data['typing']}
            )
            return 

        # --- 3. HANDLE NEW MESSAGES ---
        message = data.get('message', '')
        image_data = data.get('image', None)
        
        msg = await self.save_message(user, message, self.room_name, image_data)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': msg.id, # <-- WE NOW SEND THE ID!
                'message': message,
                'username': user.username,
                'image_url': msg.image.url if msg.image else None
            }
        )

    # --- BROADCAST HANDLERS ---
    async def user_typing(self, event):
        await self.send(text_data=json.dumps({'typing': event['is_typing'], 'username': event['username']}))

    async def message_deleted(self, event):
        # Send the delete command to the browsers
        await self.send(text_data=json.dumps({
            'action': 'delete',
            'message_id': event['message_id']
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'message': event['message'],
            'username': event['username'],
            'image_url': event.get('image_url')
        }))

    # --- DATABASE FUNCTIONS ---
    @database_sync_to_async
    def save_message(self, user, message, room_name, image_data):
        msg = Message.objects.create(user=user, content=message, room_name=room_name)
        if image_data:
            format, imgstr = image_data.split(';base64,') 
            ext = format.split('/')[-1]
            file_name = f"{user.username}_{msg.id}.{ext}"
            msg.image.save(file_name, ContentFile(base64.b64decode(imgstr)), save=True)
        return msg

    @database_sync_to_async
    def delete_message_from_db(self, user, message_id):
        try:
            # SECURITY: user=user ensures hackers can't delete someone else's message
            msg = Message.objects.get(id=message_id, user=user)
            msg.delete()
            return True
        except Message.DoesNotExist:
            return False