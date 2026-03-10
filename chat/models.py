from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    room_name = models.CharField(max_length=255, default='global_chat') # <-- New field for room name
    content = models.TextField()
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True) # New field for image uploads
    timestamp = models.DateTimeField(auto_now_add=True)

class Meta:
    ordering = ['timestamp'] # oldest messages first, just like whatsapp and telegram

def __str__(self):
    return f'{self.user.username}: {self.content[:20]}'
