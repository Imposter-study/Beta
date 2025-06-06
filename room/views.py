from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import ChatMessage
from .serializers import ChatRequestSerializer, ChatResponseSerializer
from .services import ChatService


class ChatRoomView(APIView):
    def __init__(self):
        super().__init__()
        self.chat_service = ChatService()

    def post(self, request):
        # 요청 데이터 검증
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data["message"]

        # 1. 사용자 메시지를 DB에 저장
        user_msg_obj = self.chat_service.save_message(user_message, "user")

        # 2. OpenAI API 호출하여 응답 받기
        ai_response = self.chat_service.get_ai_response(user_message)

        # 3. AI 응답을 DB에 저장
        ai_msg_obj = self.chat_service.save_message(ai_response, "ai")

        # 4. 응답 반환
        response_data = {
            "user_message": user_message,
            "ai_response": ai_response,
            "created_at": ai_msg_obj.created_at,
        }

        return Response(response_data, status=status.HTTP_200_OK)
