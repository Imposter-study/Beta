from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Room, Chat
from .serializers import ChatRequestSerializer, RoomSerializer
from .services import ChatService
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
)


class ChatRoomView(APIView):
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        summary="메시지 전송",
        description="""
    챗봇과 대화를 주고받을 수 있는 기능입니다.

    테스트 가능한 챗봇 종류
    - assistant
    - teacher
    - friend
    """,
        request=ChatRequestSerializer,
        responses={
            200: ChatRequestSerializer,
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="로그인 필요"),
        },
    )
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        character_id = serializer.validated_data["character_id"]
        user_message = serializer.validated_data["message"]

        chat_service = ChatService()

        room = chat_service.get_or_create_room(character_id, request.user.id)

        user_chat_obj = chat_service.save_chat(room, user_message, "user")

        ai_response = chat_service.get_ai_response(room, user_message)

        ai_chat_obj = chat_service.save_chat(room, ai_response, "ai")

        response_data = {
            "room_id": room.room_id,
            "user_id": room.user.id,
            "character_id": character_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "created_at": ai_chat_obj.created_at,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class RoomListView(APIView):
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        summary="채팅방 조회",
        description="현재 로그인 한 사용자의 채팅방의 목록을 조회합니다.",
        responses={
            200: RoomSerializer(many=True),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="로그인 필요"),
        },
    )
    def get(self, request):
        rooms = Room.objects.filter(user=request.user).order_by("-updated_at")
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RoomDetailView(APIView):
    authentication_classes = [JWTAuthentication]

    @extend_schema(
        summary="채팅방 상세 조회",
        description="로그인한 사용자가 채팅방에서 나눈 대화 내역을 출력합니다.",
        responses={
            200: OpenApiResponse(description="채팅 내역 출력"),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="로그인 필요"),
            404: OpenApiResponse(description="존재하지 않는 채팅방"),
        },
    )
    def get(self, request, room_id):
        try:
            room = Room.objects.get(room_id=room_id, user=request.user)
        except Room.DoesNotExist:
            return Response(
                {"error": "채팅방을 찾을 수 없거나 접근 권한이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        chats = Chat.objects.filter(room=room).order_by("created_at")

        response_data = {
            "room_id": room.room_id,
            "user_id": room.user.id,
            "character_id": room.character_id,
            "title": room.title,
            "created_at": room.created_at,
            "updated_at": room.updated_at,
            "chats": [
                {
                    "chat_id": chat.chat_id,
                    "content": chat.content,
                    "role": chat.role,
                    "created_at": chat.created_at,
                }
                for chat in chats
            ],
        }

        return Response(response_data, status=status.HTTP_200_OK)
