# Python Library
from datetime import timedelta

# Third-Party Package
from django.utils import timezone
from rest_framework import serializers

# Local Apps
from .models import Chat, Room
from characters.models import ConversationHistory


class RoomSerializer(serializers.ModelSerializer):
    room_id = serializers.CharField(source="uuid", read_only=True)
    character_id = serializers.SerializerMethodField()
    character_title = serializers.SerializerMethodField()
    character_name = serializers.SerializerMethodField()
    character_image = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            "room_id",
            "character_id",
            "character_title",
            "character_name",
            "character_image",
            "last_message",
            "fixation",
            "created_at",
            "updated_at",
        ]

    def get_character_id(self, obj):
        return obj.character.pk

    def get_character_title(self, obj):
        return obj.character.title

    def get_character_name(self, obj):
        return obj.character.name

    def get_character_image(self, obj):
        if obj.character.character_image:
            return obj.character.character_image.url
        return None

    def get_last_message(self, obj):
        if hasattr(obj, "latest_chat") and obj.latest_chat:
            return obj.latest_chat[0].content

        return "대화를 시작해보세요!"


class RoomCreateSerializer(serializers.Serializer):
    # TODO: uuid 적용 후 수정 예정
    character_id = serializers.IntegerField()


class RoomCreateResponseSerializer(RoomSerializer):
    class Meta(RoomSerializer.Meta):
        fields = [
            "room_id",
            "character_id",
            "character_title",
            "character_name",
            "created_at",
        ]


class RoomDetailSerializer(RoomSerializer):
    chats = serializers.SerializerMethodField()

    class Meta(RoomSerializer.Meta):
        fields = [
            "room_id",
            "character_id",
            "character_title",
            "character_name",
            "created_at",
            "updated_at",
            "chats",
        ]

    def get_chats(self, obj):
        chats = Chat.objects.filter(room=obj).order_by("created_at")
        return ChatDetailSerializer(chats, many=True).data


class RoomFixationSerializer(RoomSerializer):
    class Meta(RoomSerializer.Meta):
        fields = [
            "room_id",
            "character_id",
            "character_title",
            "character_name",
            "fixation",
        ]


class ChatDetailSerializer(serializers.ModelSerializer):
    chat_id = serializers.CharField(source="id", read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["chat_id", "name", "content", "is_main", "created_at"]

    def get_name(self, obj):
        room = obj.room
        return room.character.name if obj.role == "ai" else room.user.username


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, allow_blank=True)


class HistoryListSerializer(serializers.ModelSerializer):
    saved_date = serializers.SerializerMethodField()

    class Meta:
        model = ConversationHistory
        fields = ["history_id", "title", "last_message", "saved_date"]

    def get_saved_date(self, obj):
        now = timezone.now()
        time_diff = now - obj.saved_at

        if time_diff < timedelta(minutes=1):
            return "방금 전"
        elif time_diff < timedelta(hours=1):
            return f"{int(time_diff.total_seconds() / 60)}분 전"
        elif time_diff < timedelta(days=1):
            return f"{int(time_diff.total_seconds() / 3600)}시간 전"
        else:
            return obj.saved_at.strftime("%Y-%m-%d")


class HistoryDetailSerializer(serializers.ModelSerializer):
    character_name = serializers.CharField(source="character.name", read_only=True)
    character_id = serializers.UUIDField(
        source="character.character_id", read_only=True
    )

    class Meta:
        model = ConversationHistory
        fields = [
            "history_id",
            "title",
            "character_id",
            "character_name",
            "chat_history",
        ]


class HistoryTitleSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
