import json
import base64
import os
import uuid
from django.core.files.base import ContentFile
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, ChatRoom
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from datetime import datetime

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.sender = self.scope['user'].username  # Usuario actual

        # Verificar si es un chat grupal o individual
        if await self.is_chat_room(self.room_name):
            # Chat grupal: usar el nombre de la sala como grupo
            self.room_group_name = f'chat_{self.room_name}'
        else:
            # Chat individual: crear un nombre de grupo único
            if self.sender < self.room_name:
                self.room_group_name = f'chat_{self.sender}_{self.room_name}'
            else:
                self.room_group_name = f'chat_{self.room_name}_{self.sender}'

        # Unirse al grupo de la sala
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Salir del grupo de la sala
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Recibir mensaje del WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message','') 
        image_data = text_data_json.get('image','')
        sender = self.scope['user'].username
        receiver = text_data_json.get('receiver')
        timestamp = datetime.now().strftime('%H:%M')

        sender_user = await self.get_user(sender)
        receiver_user = await self.get_user(receiver)

        if sender_user is None or receiver_user is None:
            await self.send(text_data=json.dumps({'error': 'Usuario no encontrado.'}))
            return
        
        
        image_url = None
        if image_data:
            try:
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]  # Obtener la extensión del archivo
                file_name = f"{uuid.uuid4()}.{ext}"
                file_path = os.path.join(settings.MEDIA_ROOT, "chat_images", file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(imgstr))

                image_url = settings.MEDIA_URL + f"chat_images/{file_name}"

            except Exception as e:
                await self.send(text_data=json.dumps({'error': f'Error al procesar la imagen: {str(e)}'}))
                return
                
        # Guardar el mensaje en la BD
        await self.save_message(sender_user, receiver_user, message, image_url)

        # Enviar el mensaje al grupo de chat
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'image':image_url,
                'sender': sender,
                'receiver': receiver,
                'timestamp': timestamp,
            }
        )

        # Enviar una notificación al destinatario si está en línea
        await self.channel_layer.group_send(
            f"notifications_{receiver}",
            {
                'type': 'send_notification',
                'sender': sender,
                'receiver': receiver,
                'message': message if message else "Foto",
            }
        )

    # Recibir mensaje del grupo de la sala
    async def chat_message(self, event):
        message = event.get('message','')
        image_url = event.get('image','')
        sender = event['sender']
        receiver = event['receiver']
        timestamp = event['timestamp']

        # Enviar el mensaje al WebSocket
        await self.send(text_data=json.dumps({
            'message': message if message else "",
            'image':image_url if image_url else "",
            'sender': sender,
            'receiver': receiver,
            'timestamp':timestamp,
        }))

    @database_sync_to_async
    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, sender, receiver, message, image_url=None):
        # Guardar el mensaje en la base de datos
     return  Message.objects.create(
         sender=sender, 
         receiver=receiver, 
         message=message if message else "",
         image=image_url if image_url else None,
         ) 
      

    @database_sync_to_async
    def is_chat_room(self, room_name):
        # Verificar si el room_name es una sala de chat grupall
        return ChatRoom.objects.filter(name=room_name).exists()
    
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group_name = f"notifications_{self.user.username}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        """ Enviar notificación a un usuario específico. """
        await self.send(text_data=json.dumps({
            'type': 'send_notification',
            'sender': event['sender'],
            'receiver': event['receiver'],
            'message': event['message']
        }))
    