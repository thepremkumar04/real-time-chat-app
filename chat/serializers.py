from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'username', 'content', 'timestamp', 'room_name', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None