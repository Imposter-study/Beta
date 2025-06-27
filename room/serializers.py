from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import Room, Chat
from characters.models import ConversationHistory


class ChatRequestSerializer(serializers.Serializer):
    character_id = serializers.CharField(max_length=50)
    message = serializers.CharField(max_length=1000, allow_blank=True)


class ChatUpdateSerializer(serializers.Serializer):
    chat_id = serializers.IntegerField()
    message = serializers.CharField(max_length=1000)


class ChatRegenerateSerializer(serializers.Serializer):
    room_id = serializers.UUIDField()


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
        fields = ["chat_id", "content", "name", "created_at"]

    def get_name(self, obj):
        room = obj.room
        return room.character_id.name if obj.role == "ai" else room.user.username


class ChatDeleteSerializer(serializers.Serializer):
    chat_id = serializers.IntegerField(required=False)


class RoomDetailSerializer(serializers.ModelSerializer):
    character_title = serializers.CharField(source="character_id.title", read_only=True)
    chats = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ["room_id", "character_title", "created_at", "updated_at", "chats"]

    def get_chats(self, obj):
        chats = Chat.objects.filter(room=obj).order_by("created_at")
        return ChatDetailSerializer(chats, many=True).data


class ChatHistorySaveSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)


class ConversationHistoryListSerializer(serializers.ModelSerializer):
    saved_date = serializers.SerializerMethodField()

    class Meta:
        model = ConversationHistory
        fields = ["history_id", "title", "last_message", "saved_date"]

    def get_saved_date(self, obj):
        now = timezone.now()
        saved_at = obj.saved_at
        time_diff = now - saved_at

        if time_diff < timedelta(minutes=1):
            return "방금 전"

        elif time_diff < timedelta(hours=1):
            minutes = int(time_diff.total_seconds() / 60)
            return f"{minutes}분 전"

        elif time_diff < timedelta(days=1):
            hours = int(time_diff.total_seconds() / 3600)
            return f"{hours}시간 전"

        else:
            return saved_at.strftime("%Y-%m-%d")
