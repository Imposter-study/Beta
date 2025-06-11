from openai import OpenAI
from django.conf import settings
from .models import ChatMessage


class ChatService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def get_recent_messages(self, limit=None):
        if limit is None:
            limit = settings.CONVERSATION_HISTORY_LIMIT

        messages = ChatMessage.objects.all()[:limit]
        return list(reversed(messages))

    def create_conversation_context(self, recent_messages):
        context = [{"role": "system", "content": settings.SYSTEM_PROMPT}]

        for message in recent_messages:
            role = "user" if message.sender == "user" else "assistant"
            context.append({"role": role, "content": message.content})

        return context

    def get_ai_response(self, user_message):
        try:
            recent_messages = self.get_recent_messages()
            messages = self.create_conversation_context(recent_messages)
            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            return "죄송합니다. 현재 응답을 생성할 수 없습니다."

    def save_message(self, content, sender):
        return ChatMessage.objects.create(content=content, sender=sender)
