from django.conf import settings
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)
from .models import Room, Chat
from characters.models import ConversationHistory
from .serializers import (
    ChatRequestSerializer,
    ChatUpdateSerializer,
    ChatRegenerateSerializer,
    RoomSerializer,
    RoomDetailSerializer,
    ChatDeleteSerializer,
    HistoryTitleSerializer,
    HistoryListSerializer,
    HistoryLoadSerializer,
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
    )
    def get(self, request):
        rooms = (
            Room.objects.filter(user=request.user)
            .select_related("character_id")
            .prefetch_related(
                Prefetch(
                    "chats",
                    queryset=Chat.objects.order_by("-created_at")[:1],
                    to_attr="latest_chat",
                )
            )
            .order_by("-updated_at")
        )

        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="메시지 전송",
        description="""
    챗봇과 대화를 주고받을 수 있는 기능입니다.
    character에서 캐릭터를 생성하고 캐릭터 id를 입력하여 대화합니다.
    user_message를 작성하지 않고 요청을 보낼 경우 대화를 이어서 생성합니다.
    """,
        request=ChatRequestSerializer,
        responses={
            200: ChatRequestSerializer,
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
        },
    )
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        character_id = serializer.validated_data["character_id"]
        user_message = serializer.validated_data["message"]

        chat_service = ChatService()

        room, character = chat_service.get_or_create_room(character_id, request.user.id)

        if user_message != "":
            user_chat_obj = chat_service.save_chat(room, user_message, "user")
            ai_response = chat_service.get_ai_response(room, user_message)
        else:
            ai_response = chat_service.get_ai_response(room)

        ai_chat_obj = chat_service.save_chat(room, ai_response, "ai")

        response_data = {
            "room_id": room.room_id,
            "user_id": room.user.id,
            "character_id": character.name,
            "user_message": user_message,
            "ai_response": ai_response,
            "created_at": ai_chat_obj.created_at,
        }

        return Response(response_data, status=status.HTTP_200_OK)


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
    )
    def post(self, request, room_id):
        try:
            room = Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            return Response(
                {"error": "존재하지 않는 채팅방입니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

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
        request=ChatRegenerateSerializer,
        responses={
            200: OpenApiResponse(description="AI 응답 재생성 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(
                description="존재하지 않는 채팅방 또는 사용자 메시지가 없음"
            ),
        },
    )
    def post(self, request):
        serializer = ChatRegenerateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        room_id = serializer.validated_data["room_id"]

        try:
            room = Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            return Response(
                {"error": "존재하지 않는 채팅방입니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if room.user != request.user:
            return Response(
                {"error": "해당 채팅방에 대한 접근 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
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

        ai_chat_obj = chat_service.save_chat(room, ai_response, "ai")

        response_data = {
            "room_id": room.room_id,
            "character_name": room.character_id.name,
            "regenerated_response": ai_response,
            "created_at": ai_chat_obj.created_at,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class RoomDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_room(self, room_id, user):
        room = get_object_or_404(Room, room_id=room_id)

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
    )
    def get(self, request, room_id):
        room = self.get_room(room_id, request.user)

        serializer = RoomDetailSerializer(room)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="메시지 수정",
        description="chat_id를 입력받아 해당 메시지를 수정합니다.",
        request=ChatUpdateSerializer,
        responses={
            200: ChatUpdateSerializer,
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="사용자의 메시지, 접근 권한 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅"),
        },
    )
    def put(self, request, room_id):
        serializer = ChatUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        chat_id = serializer.validated_data["chat_id"]
        update_message = serializer.validated_data["message"]

        room = self.get_room(room_id, request.user)
        chat = get_object_or_404(Chat, chat_id=chat_id)

        if chat.room != room:
            return Response(
                {"error": "해당 채팅이 이 채팅방에 속하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if chat.role == "user":
            return Response(
                {"error": "사용자 메시지는 수정할 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        chat.content = update_message
        chat.save()

        return Response(
            {"message": "메시지가 수정되었습니다."}, status=status.HTTP_200_OK
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
    )
    def delete(self, request, room_id):
        room = self.get_room(room_id, request.user)

        room.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="대화 내역 삭제",
        description="채팅방의 대화 내역을 삭제합니다. chat_id를 입력하면 해당 chat_id부터 최신까지 삭제, 입력하지 않으면 모든 대화 삭제",
        request=ChatDeleteSerializer,
        responses={
            200: OpenApiResponse(description="대화 내역 삭제 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방 또는 채팅"),
        },
    )
    def patch(self, request, room_id):
        room = self.get_room(room_id, request.user)

        serializer = ChatDeleteSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        chat_id = serializer.validated_data.get("chat_id")

        if chat_id:
            if not Chat.objects.filter(chat_id=chat_id, room=room).exists():
                return Response(
                    {"error": "존재하지 않는 chat_id입니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            chats_to_delete = Chat.objects.filter(room=room, chat_id__gte=chat_id)

        else:
            chats_to_delete = Chat.objects.filter(room=room)

        deleted_count = chats_to_delete.count()
        chats_to_delete.delete()

        return Response(
            {"message": "대화 내역 삭제", "deleted_count": deleted_count},
            status=status.HTTP_200_OK,
        )


class HistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_room(self, room_id, user):
        room = get_object_or_404(Room, room_id=room_id)

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
    )
    def get(self, request, room_id):
        room = self.get_room(room_id, request.user)

        conversation_histories = ConversationHistory.objects.filter(
            character=room.character_id, user=request.user
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
    )
    def post(self, request, room_id):
        serializer = HistoryTitleSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        title = serializer.validated_data["title"]
        room = self.get_room(room_id, request.user)
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
                    "timestamp": chat.created_at.isoformat(),
                }
            )

        last_message = chats.last().content[:50] if chats.exists() else ""

        conversation_history = ConversationHistory.objects.create(
            character=room.character_id,
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

    @extend_schema(
        summary="대화 내역 불러오기",
        description="저장된 대화 내역을 현재 채팅방에 불러옵니다. 기존 대화 내역은 모두 삭제됩니다.",
        request=HistoryLoadSerializer,
        responses={
            200: OpenApiResponse(description="대화 내역 불러오기 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="접근 권한이 없음"),
            404: OpenApiResponse(description="존재하지 않는 채팅방 또는 대화 내역"),
        },
    )
    def patch(self, request, room_id):
        history_id = request.data.get("history_id")

        if not history_id:
            return Response(
                {"error": "history_id가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        room = self.get_room(room_id, request.user)

        try:
            conversation_history = ConversationHistory.objects.get(
                history_id=history_id, user=request.user
            )
        except ConversationHistory.DoesNotExist:
            return Response(
                {"error": "존재하지 않는 대화 내역이거나 접근 권한이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted_count = Chat.objects.filter(room=room).count()
        Chat.objects.filter(room=room).delete()

        loaded_chats = []
        for chat_data in conversation_history.chat_history:
            chat = Chat.objects.create(
                room=room,
                content=chat_data["content"],
                role=chat_data["role"],
                created_at=chat_data["timestamp"],
            )
            loaded_chats.append(chat)

        return Response(
            {
                "message": "대화 내역이 불러오기 완료.",
                "deleted_count": deleted_count,
                "loaded_count": len(loaded_chats),
                "history_title": conversation_history.title,
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
        summary="저장된 대화 내역 제목 수정",
        description="저장된 대화 내역의 제목을 수정합니다.",
        request=HistoryTitleSerializer,
        responses={
            200: OpenApiResponse(description="대화 내역 제목 수정 성공"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="존재하지 않는 대화 내역"),
        },
    )
    def put(self, request, room_id, history_id):
        serializer = HistoryTitleSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        conversation_history = self.get_conversation_history(history_id, request.user)
        conversation_history.title = serializer.validated_data["title"]
        conversation_history.save()

        return Response(
            {
                "message": "대화 내역 제목이 수정되었습니다.",
                "history_id": conversation_history.history_id,
                "title": conversation_history.title,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="저장된 대화 내역 삭제",
        description="저장된 대화 내역을 삭제합니다.",
        responses={
            204: OpenApiResponse(description="대화 내역 삭제 성공"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="존재하지 않는 대화 내역"),
        },
    )
    def delete(self, request, room_id, history_id):
        conversation_history = self.get_conversation_history(history_id, request.user)
        conversation_history.delete()

        return Response(
            {"message": "삭제되었습니다."},
            status=status.HTTP_204_NO_CONTENT,
        )
