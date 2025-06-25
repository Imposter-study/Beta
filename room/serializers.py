from rest_framework import serializers
from .models import Room, Chat


class ChatRequestSerializer(serializers.Serializer):
    character_id = serializers.CharField(max_length=50)
    message = serializers.CharField(max_length=1000, allow_blank=True)


class RoomSerializer(serializers.ModelSerializer):
    character_title = serializers.SerializerMethodField()
    character_name = serializers.SerializerMethodField()
    character_image = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "room_id",
            "character_title",
            "character_name",
            "character_image",
            "last_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["room_id", "created_at", "updated_at"]

    def get_character_title(self, obj):
        return obj.character_id.title

    def get_character_name(self, obj):
        return obj.character_id.name

    def get_character_image(self, obj):
        if obj.character_id.character_image:
            return obj.character_id.character_image.url
        return None

    def get_last_message(self, obj):
        if hasattr(obj, "latest_chat") and obj.latest_chat:
            return obj.latest_chat[0].content

        return "대화를 시작해보세요!"


class ChatDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["content", "name", "created_at"]

    def get_name(self, obj):
        room = obj.room
        return room.character_id.name if obj.role == "ai" else room.user.username


class RoomDetailSerializer(serializers.ModelSerializer):
    character_title = serializers.CharField(source="character_id.title", read_only=True)
    chats = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ["room_id", "character_title", "created_at", "updated_at", "chats"]

    def get_chats(self, obj):
        chats = Chat.objects.filter(room=obj).order_by("created_at")
        return ChatDetailSerializer(chats, many=True).data
