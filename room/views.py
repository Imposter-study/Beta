from django.db.models import Prefetch
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)
from .models import Room, Chat
from .serializers import ChatRequestSerializer, RoomSerializer, RoomDetailSerializer
from .services import ChatService


class ChatRoomView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="메시지 전송",
        description="""
    챗봇과 대화를 주고받을 수 있는 기능입니다.
    character에서 캐릭터를 생성하고 캐릭터 id를 입력하여 대화합니다.
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

        user_chat_obj = chat_service.save_chat(room, user_message, "user")

        ai_response = chat_service.get_ai_response(room, user_message)

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


class RoomListView(APIView):
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


class RoomDetailView(APIView):
    permission_classes = [IsAuthenticated]

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

        serializer = RoomDetailSerializer(room)

        return Response(serializer.data, status=status.HTTP_200_OK)
