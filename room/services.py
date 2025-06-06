import openai
from django.conf import settings
from .models import ChatMessage


class ChatService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def get_recent_messages(self, limit=None):
        """최근 대화 내역을 가져오기"""
        if limit is None:
            limit = settings.CONVERSATION_HISTORY_LIMIT

        messages = ChatMessage.objects.all()[:limit]
        return list(reversed(messages))  # 시간순으로 정렬

    def create_conversation_context(self, recent_messages):
        """OpenAI API 형식으로 대화 내역 변환"""
        context = [{"role": "system", "content": settings.SYSTEM_PROMPT}]

        for message in recent_messages:
            role = "user" if message.sender == "user" else "assistant"
            context.append({"role": role, "content": message.content})

        return context

    def get_ai_response(self, user_message):
        """OpenAI API 호출하여 응답 받기"""
        try:
            # 최근 대화 내역 가져오기
            recent_messages = self.get_recent_messages()

            # 대화 컨텍스트 생성
            messages = self.create_conversation_context(recent_messages)

            # 현재 사용자 메시지 추가
            messages.append({"role": "user", "content": user_message})

            # OpenAI API 호출
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            return "죄송합니다. 현재 응답을 생성할 수 없습니다."

    def save_message(self, content, sender):
        """메시지를 DB에 저장"""
        return ChatMessage.objects.create(content=content, sender=sender)
