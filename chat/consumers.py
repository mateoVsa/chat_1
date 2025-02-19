import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, ChatRoom
from django.contrib.auth.models import User
from channels.db import database_sync_to_async

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
        message = text_data_json['message']
        sender = text_data_json['sender']
        receiver = text_data_json['receiver']  # Obtener el receiver del mensaje

        # Obtener usuarios
        sender_user = await self.get_user(sender)
        receiver_user = await self.get_user(receiver)  # Obtener el objeto User del receiver

        # Verificar si los usuarios existen
        if sender_user is None or receiver_user is None:
            await self.send(text_data=json.dumps({
                'error': 'Usuario no encontrado.',
            }))
            return

        # Guardar el mensaje en la base de datos
        await self.save_message(sender_user, receiver_user, message)

        # notificaciones 
        
        #await self.channel_layer.group_send(
        #    'notifications',
        #    {
        #        'type': 'send_notification',
        #       'message': f'Nuevo mensaje de {sender} en {self.room_name}',
        #        'sender': sender
        #    }
        #)
        
        
        # Enviar el mensaje al grupo de la sala
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'receiver': receiver,
            }
        )

    # Recibir mensaje del grupo de la sala
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        receiver = event['receiver']

        # Enviar el mensaje al WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'receiver': receiver,
        }))

    @database_sync_to_async
    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def save_message(self, sender, receiver, message):
        # Guardar el mensaje en la base de datos
        Message.objects.create(sender=sender, receiver=receiver, message=message)

    @database_sync_to_async
    def is_chat_room(self, room_name):
        # Verificar si el room_name es una sala de chat grupal
        return ChatRoom.objects.filter(name=room_name).exists()
    
    
#class notificationConsumer(AsyncWebsocketConsumer):
#    async def connect(self):
#        await self.channel_layer.group_add(
#            'notifications',
#            self.channel_name
#        )
#       await self.accept()
#  
#    async def disconnect(self, close_code):
#        await self.channel_layer.group_discard(
#            'notifications',
#            self.channel_name
#        )
 #   
 #   async def send_notifications(self,event):
  #      message =  event['message']
#        sender =  event['sender']
#        
#        await self.send(text_data= json.dumps({
#            'type': 'notification',
#            'message': message,
#            'sender': sender
#        }))
        
        