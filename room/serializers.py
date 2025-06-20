from rest_framework import serializers
from .models import Room, Chat


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["chat_id", "content", "role", "created_at", "updated_at"]
        read_only_fields = ["chat_id", "created_at", "updated_at"]


class RoomSerializer(serializers.ModelSerializer):
    character_image = serializers.SerializerMethodField()
    character_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "room_id",
            "character_id",
            "title",
            "created_at",
            "updated_at",
            "character_image",
            "character_name",
            "last_message",
        ]
        read_only_fields = ["room_id", "created_at", "updated_at"]

    def get_character_image(self, obj):
        if obj.character_id.character_image:
            return obj.character_id.character_image.url
        return None

    def get_character_name(self, obj):
        return obj.character_id.name

    def get_last_message(self, obj):
        if hasattr(obj, "latest_chat") and obj.latest_chat:
            return obj.latest_chat[0].content

        return "대화를 시작해보세요!"


class ChatRequestSerializer(serializers.Serializer):
    character_id = serializers.CharField(max_length=50, help_text="챗봇 ID")
    message = serializers.CharField(max_length=1000, help_text="사용자 메시지")


class ChatResponseSerializer(serializers.Serializer):
    room_id = serializers.IntegerField()
    character_id = serializers.CharField()
    user_message = serializers.CharField()
    ai_response = serializers.CharField()
    created_at = serializers.DateTimeField()
