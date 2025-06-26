from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
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
from .serializers import (
    ChatRequestSerializer,
    RoomSerializer,
    RoomDetailSerializer,
    ChatDeleteSerializer,
)
from .services import ChatService


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

    @extend_schema(
        summary="메시지 수정",
        description="가장 최근 대화를 수정하는 기능입니다.",
        request=ChatRequestSerializer,
        responses={
            200: ChatRequestSerializer,
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            403: OpenApiResponse(description="사용자의 메시지"),
            404: OpenApiResponse(description="존재하지 않는 채팅방"),
        },
    )
    def put(self, request):
        serializer = ChatRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        character_id = serializer.validated_data["character_id"]
        update_message = serializer.validated_data["message"]

        room = get_object_or_404(
            Room.objects.select_related("character_id").prefetch_related("chats"),
            character_id=character_id,
            user=request.user,
        )

        last_chat = room.chats.order_by("-created_at").first()

        if not last_chat:
            return Response(
                {"error": "존재하지 않는 채팅방입니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if last_chat.role == "User":
            return Response(
                {"error": "사용자 메시지는 수정할 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        last_chat.content = update_message
        last_chat.save()

        return Response(
            {"message": "메시지가 수정되었습니다."}, status=status.HTTP_200_OK
        )


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
                    {"error": "해당 채팅방에 존재하지 않는 chat_id입니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            chats_to_delete = Chat.objects.filter(room=room, chat_id__gte=chat_id)
        else:
            chats_to_delete = Chat.objects.filter(room=room)

        deleted_count = chats_to_delete.count()
        chats_to_delete.delete()

        return Response(
            {"message": "대화 내역이 삭제되었습니다.", "deleted_count": deleted_count},
            status=status.HTTP_200_OK,
        )
