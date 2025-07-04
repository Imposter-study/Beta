# Python Library
import uuid

# Third-Party Package
from django.conf import settings
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema

# Local Apps
from characters.models import Character, ConversationHistory
from .models import Chat, Room
from .serializers import (
    RoomSerializer,
    RoomCreateSerializer,
    RoomCreateResponseSerializer,
    RoomDetailSerializer,
    RoomFixationSerializer,
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatUpdateResponseSerializer,
    ChatDetailSerializer,
    HistoryListSerializer,
    HistoryDetailSerializer,
    HistoryTitleSerializer,
    HistoryTitleResponseSerializer,
)
from .services import ChatService


class RoomAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="채팅방 리스트 조회",
        description="현재 로그인 한 사용자의 채팅방의 목록을 조회합니다.",
        responses={
            200: RoomSerializer(many=True),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
        },
        tags=["rooms/room"],
    )
    def get(self, request):
        rooms = (
            Room.objects.filter(user=request.user)
            .select_related("character")
            .prefetch_related(
                Prefetch(
                    "chats",
                    queryset=Chat.objects.order_by("-created_at")[:1],
                    to_attr="latest_chat",
                )
            )
            .order_by("-fixation", "-updated_at")
        )

        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="채팅방 생성",
        description="character_id를 입력하여 새로운 채팅방을 생성합니다.",
        request=RoomCreateSerializer,
        responses={
            200: OpenApiResponse(description="이미 채팅방이 존재하는 캐릭터"),
            201: OpenApiResponse(description="채팅방 생성"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
        },
        tags=["rooms/room"],
    )
    def post(self, request):
        serializer = RoomCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        character_id = serializer.validated_data["character_id"]
        character = get_object_or_404(Character, character_id=character_id)
        user = request.user

        room, created = Room.objects.get_or_create(
            user=user,
            character=character,
        )

        response_serializer = RoomCreateResponseSerializer(room)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(response_serializer.data, status=status_code)


class RoomDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_room(self, room_uuid, user):
        room = get_object_or_404(Room, uuid=room_uuid)

        if room.user != user:
            raise PermissionDenied("해당 채팅방에 대한 접근 권한이 없습니다.")

        return room

    @extend_schema(
        summary="채팅방 상세 조회",
        description="로그인한 사용자가 채팅방에서 나눈 대화 내역을 출력합니다.",
        responses={
            200: OpenApiResponse(description="채팅 내역 조회 성공"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방"),
        },
        tags=["rooms/room"],
    )
    def get(self, request, room_uuid):
        room = self.get_room(room_uuid, request.user)

        serializer = RoomDetailSerializer(room)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="채팅방 고정 상태 변경",
        description="채팅방의 고정 상태를 토글합니다. (True ↔ False)",
        responses={
            200: OpenApiResponse(description="고정 상태 변경 성공"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방"),
        },
        tags=["rooms/room"],
    )
    def patch(self, request, room_uuid):
        room = self.get_room(room_uuid, request.user)

        room.fixation = not room.fixation
        room.save()

        serializer = RoomFixationSerializer(room)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="채팅방 나가기",
        description="채팅방을 삭제합니다.",
        responses={
            204: OpenApiResponse(description="채팅방 삭제 성공"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방"),
        },
        tags=["rooms/room"],
    )
    def delete(self, request, room_uuid):
        room = self.get_room(room_uuid, request.user)

        room.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="채팅 메시지 전송",
        description="""
        채팅방에서 챗봇과 메시지를 주고받는 API입니다.
        user_message를 생략하면 이어서 AI가 응답만 생성합니다.
        """,
        request=ChatRequestSerializer,
        responses={
            200: ChatRequestSerializer,
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="채팅방을 찾을 수 없음"),
        },
        tags=["rooms/message"],
    )
    def post(self, request, room_uuid):
        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data["message"]

        room = get_object_or_404(Room, uuid=room_uuid, user=request.user)

        chat_service = ChatService()

        if user_message:
            user_chat_obj = chat_service.save_chat(room, user_message, "user")
            ai_response = chat_service.get_ai_response(room, user_message)
        else:
            ai_response = chat_service.get_ai_response(room)

        ai_chat_obj = chat_service.save_chat(room, ai_response, "ai")

        response_serializer = ChatResponseSerializer(
            ai_chat_obj, context={"input_user_message": user_message}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ChatMessageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="메시지 수정",
        description="응답 메시지를 수정합니다.",
        request=ChatRequestSerializer,
        responses={
            200: OpenApiResponse(description="메시지 수정 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="사용자의 메시지 수정 불가"),
            404: OpenApiResponse(description="존재하지 않는 채팅 또는 채팅방"),
        },
        tags=["rooms/message"],
    )
    def put(self, request, room_uuid, chat_id):
        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        room = get_object_or_404(Room, uuid=room_uuid, user=request.user)
        chat = get_object_or_404(Chat, id=chat_id)

        if chat.room != room:
            return Response(
                {"detail": "해당 채팅이 이 채팅방에 속하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if chat.role != "ai":
            return Response(
                {"detail": "사용자 메시지는 수정할 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        chat.content = serializer.validated_data["message"]
        chat.save()

        response_serializer = ChatUpdateResponseSerializer(chat)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="regeneration_group 내 main 메시지 지정",
        description=(
            "지정한 chat을 regeneration_group 내 main 메시지로 설정합니다. "
            "대화를 재생성했을 때 사용자에게 보여줄 메시지를 선택할 수 있는 기능입니다."
        ),
        responses={
            200: OpenApiResponse(description="main 설정 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            404: OpenApiResponse(description="채팅 또는 채팅방이 존재하지 않음"),
        },
        tags=["rooms/message"],
    )
    def patch(self, request, room_uuid, chat_id):
        room = get_object_or_404(Room, uuid=room_uuid, user=request.user)
        chat = get_object_or_404(Chat, id=chat_id)

        if chat.room != room:
            return Response(
                {"detail": "해당 채팅이 이 채팅방에 속하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if chat.regeneration_group is None:
            return Response(
                {"detail": "재생성 하지 않은 메시지는 is_main을 변경할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Chat.objects.filter(
            room=room, regeneration_group=chat.regeneration_group
        ).exclude(id=chat.id).update(is_main=False)

        chat.is_main = True
        chat.save()

        serializer = ChatDetailSerializer(chat)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="메시지 삭제",
        description="chat_id부터 해당 채팅방의 최신 메시지까지 삭제합니다.",
        responses={
            200: OpenApiResponse(description="대화 내역 삭제 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅 또는 채팅방"),
        },
        tags=["rooms/message"],
    )
    def delete(self, request, room_uuid, chat_id):
        room = get_object_or_404(Room, uuid=room_uuid, user=request.user)
        target_chat = Chat.objects.filter(id=chat_id, room=room).first()

        if not target_chat:
            return Response(
                {"error": "존재하지 않는 chat_id입니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        base_queryset = Chat.objects.filter(room=room, id__gte=chat_id)
        chat_ids = list(base_queryset.values_list("id", flat=True))

        if target_chat.regeneration_group is not None:
            regeneration_queryset = Chat.objects.filter(
                room=room, regeneration_group=target_chat.regeneration_group
            )
            regeneration_ids = list(regeneration_queryset.values_list("id", flat=True))
            chat_ids += regeneration_ids

        chat_ids = list(set(chat_ids))

        deleted_count, _ = Chat.objects.filter(id__in=chat_ids).delete()

        return Response(
            {"message": f"{deleted_count}개의 채팅이 삭제되었습니다."},
            status=status.HTTP_200_OK,
        )


class ChatSuggestionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="추천 답변 생성",
        description="이전 대화 내역을 기준으로 사용자가 할 수 있는 추천 답변 3가지를 생성합니다.",
        request=None,
        responses={
            200: OpenApiResponse(description="추천 답변 생성 성공"),
            400: OpenApiResponse(description="잘못된 요청 또는 대화 내역 없음"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방"),
        },
        tags=["rooms/message"],
    )
    def post(self, request, room_uuid):
        room = get_object_or_404(Room, uuid=room_uuid)

        if room.user != request.user:
            return Response(
                {"error": "해당 채팅방에 대한 접근 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        chat_service = ChatService()

        try:
            memory = chat_service.create_memory_from_history(room)
            if not memory.chat_memory.messages:
                return Response(
                    {"error": "추천 답변을 생성할 대화 내역이 없습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            suggestions = []
            for _ in range(settings.SUGGESTIONS):
                suggestion = chat_service.get_chat_suggestion(room)
                suggestions.append(suggestion)

            response_data = {"suggestions": suggestions}

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"error": "추천 답변 생성 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChatRegenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="메시지 재생성",
        description="마지막 사용자 메시지를 기준으로 AI 응답을 재생성합니다.",
        request=None,
        responses={
            200: OpenApiResponse(description="AI 응답 재생성 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방 또는 메시지가 없음"),
        },
        tags=["rooms/message"],
    )
    def post(self, request, room_uuid):
        room = get_object_or_404(Room, uuid=room_uuid)

        if room.user != request.user:
            return Response(
                {"error": "해당 채팅방에 대한 접근 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        last_message = Chat.objects.filter(room=room).order_by("-created_at").first()

        if not last_message:
            return Response(
                {"error": "재생성할 메시지가 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if last_message.role == "user":
            return Response(
                {"error": "사용자 메시지는 재생성할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        last_user_message = (
            Chat.objects.filter(room=room, role="user").order_by("-created_at").first()
        )

        if not last_user_message:
            return Response(
                {"error": "재생성할 사용자 메시지가 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        chat_service = ChatService()

        ai_response = chat_service.get_ai_response(
            room, last_user_message.content, last_user_message
        )

        if last_message.regeneration_group:
            regeneration_group_id = last_message.regeneration_group
        else:
            regeneration_group_id = uuid.uuid4()
            last_message.regeneration_group = regeneration_group_id
            last_message.save()

        Chat.objects.filter(regeneration_group=regeneration_group_id).update(
            is_main=False
        )

        ai_chat_obj = chat_service.save_chat(room, ai_response, "ai")
        ai_chat_obj.regeneration_group = regeneration_group_id
        ai_chat_obj.save()

        response_data = {
            "room_id": room.uuid,
            "character_name": room.character.name,
            "regenerated_response": ai_response,
            "regeneration_group": str(regeneration_group_id),
            "created_at": ai_chat_obj.created_at,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class HistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_room(self, room_uuid, user):
        room = get_object_or_404(Room, uuid=room_uuid)

        if room.user != user:
            raise PermissionDenied("해당 채팅방에 대한 접근 권한이 없습니다.")

        return room

    @extend_schema(
        summary="대화 내역 목록 조회",
        description="저장한 대화 내역 목록을 조회합니다.",
        responses={
            200: HistoryListSerializer(many=True),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방"),
        },
        tags=["rooms/history"],
    )
    def get(self, request, room_uuid):
        room = self.get_room(room_uuid, request.user)

        conversation_histories = ConversationHistory.objects.filter(
            character=room.character, user=request.user
        ).order_by("-saved_at")

        serializer = HistoryListSerializer(conversation_histories, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="대화 내역 저장",
        description="현재 채팅방의 대화 내역을 캐릭터에 저장합니다.",
        request=HistoryTitleSerializer,
        responses={
            200: OpenApiResponse(description="대화 내역 저장"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방"),
        },
        tags=["rooms/history"],
    )
    def post(self, request, room_uuid):
        serializer = HistoryTitleSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        title = serializer.validated_data["title"]
        room = self.get_room(room_uuid, request.user)
        chats = Chat.objects.filter(room=room).order_by("created_at")

        if not chats.exists():
            return Response(
                {"message": "저장할 대화 내역이 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chat_history = []
        for chat in chats:
            chat_history.append(
                {
                    "content": chat.content,
                    "role": chat.role,
                    "is_main": chat.is_main,
                    "regeneration_group": (
                        str(chat.regeneration_group)
                        if chat.regeneration_group
                        else None
                    ),
                    "timestamp": chat.created_at.isoformat(),
                }
            )

        last_message = chats.last().content[:50] if chats.exists() else ""

        conversation_history = ConversationHistory.objects.create(
            character=room.character,
            user=request.user,
            title=title,
            chat_history=chat_history,
            last_message=last_message,
        )

        return Response(
            {
                "message": "대화 내역이 저장되었습니다.",
                "history_id": conversation_history.history_id,
                "title": conversation_history.title,
                "saved_chats": len(chat_history),
            },
            status=status.HTTP_200_OK,
        )


class HistoryDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_conversation_history(self, history_id, user):
        try:
            conversation_history = ConversationHistory.objects.get(
                history_id=history_id, user=user
            )
            return conversation_history
        except ConversationHistory.DoesNotExist:
            raise Http404("존재하지 않는 대화 내역이거나 접근 권한이 없습니다.")

    @extend_schema(
        summary="저장된 대화 내역 상세 조회",
        description="저장된 대화 내역의 상세 정보를 조회합니다.",
        responses={
            200: OpenApiResponse(
                description="대화 내역 상세 조회 성공",
                response=HistoryDetailSerializer,
            ),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="존재하지 않는 대화 내역"),
        },
        tags=["rooms/history"],
    )
    def get(self, request, room_uuid, history_id):
        conversation_history = self.get_conversation_history(history_id, request.user)
        serializer = HistoryDetailSerializer(conversation_history)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="저장된 대화 내역 제목 수정",
        description="저장된 대화 내역의 제목을 수정합니다.",
        request=HistoryTitleSerializer,
        responses={
            200: OpenApiResponse(description="대화 내역 제목 수정 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="존재하지 않는 대화 내역"),
        },
        tags=["rooms/history"],
    )
    def put(self, request, room_uuid, history_id):
        serializer = HistoryTitleSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        conversation_history = self.get_conversation_history(history_id, request.user)
        conversation_history.title = serializer.validated_data["title"]
        conversation_history.save()

        response_serializer = HistoryTitleResponseSerializer(conversation_history)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="저장된 대화 내역 삭제",
        description="저장된 대화 내역을 삭제합니다.",
        responses={
            204: OpenApiResponse(description="대화 내역 삭제 성공"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="존재하지 않는 대화 내역"),
        },
        tags=["rooms/history"],
    )
    def delete(self, request, room_uuid, history_id):
        conversation_history = self.get_conversation_history(history_id, request.user)
        conversation_history.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="대화 내역 불러오기",
        description=(
            "특정 대화 내역(history_id)을 해당 채팅방(room_uuid)에 불러옵니다. "
            "불러오기 전에 기존 대화 내역은 모두 삭제됩니다."
        ),
        responses={
            200: OpenApiResponse(description="대화 내역 불러오기 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방 또는 대화 내역"),
            409: OpenApiResponse(
                description="채팅방과 대화 내역의 캐릭터가 일치하지 않음"
            ),
        },
        tags=["rooms/history"],
    )
    def patch(self, request, room_uuid, history_id):
        room = get_object_or_404(Room, uuid=room_uuid, user=request.user)
        conversation_history = get_object_or_404(
            ConversationHistory, history_id=history_id, user=request.user
        )

        if room.character != conversation_history.character:
            return Response(
                {
                    "error": "채팅방과 대화 내역의 캐릭터가 일치하지 않습니다.",
                    "room_character": room.character.name,
                    "history_character": conversation_history.character.name,
                },
                status=status.HTTP_409_CONFLICT,
            )

        deleted_count = Chat.objects.filter(room=room).count()
        Chat.objects.filter(room=room).delete()

        loaded_chats = []
        for chat_data in conversation_history.chat_history:
            chat = Chat.objects.create(
                room=room,
                content=chat_data["content"],
                role=chat_data["role"],
                is_main=chat_data.get("is_main", True),
                regeneration_group=chat_data.get("regeneration_group", None),
                created_at=chat_data["timestamp"],
            )
            loaded_chats.append(chat)

        return Response(
            {
                "message": "대화 내역 불러오기 완료.",
                "deleted_count": deleted_count,
                "loaded_count": len(loaded_chats),
                "history_title": conversation_history.title,
            },
            status=status.HTTP_200_OK,
        )
