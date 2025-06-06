from rest_framework import serializers
from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "content", "sender", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, help_text="사용자 메시지")


class ChatResponseSerializer(serializers.Serializer):
    user_message = serializers.CharField()
    ai_response = serializers.CharField()
    created_at = serializers.DateTimeField()
