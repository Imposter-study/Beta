from rest_framework import serializers
from .models import Room, Chat


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["chat_id", "content", "role", "created_at", "updated_at"]
        read_only_fields = ["chat_id", "created_at", "updated_at"]


class RoomSerializer(serializers.ModelSerializer):
    recent_chats = ChatSerializer(many=True, read_only=True, source="chats")

    class Meta:
        model = Room
        fields = [
            "room_id",
            "character_id",
            "title",
            "created_at",
            "updated_at",
            "recent_chats",
        ]
        read_only_fields = ["room_id", "created_at", "updated_at"]


class ChatRequestSerializer(serializers.Serializer):
    character_id = serializers.CharField(max_length=50, help_text="챗봇 ID")
    message = serializers.CharField(max_length=1000, help_text="사용자 메시지")


class ChatResponseSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    character_id = serializers.CharField()
    user_message = serializers.CharField()
    ai_response = serializers.CharField()
    created_at = serializers.DateTimeField()
