from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.sender} to {self.receiver}: {self.message}'

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Nombre de la sala
    allowed_users = models.ManyToManyField(User, related_name='allowed_chat_rooms')  # Usuarios permitidos

    def __str__(self):
        return self.name