from openai import OpenAI
from django.conf import settings
from .models import Room, Chat


class ChatService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def get_or_create_room(self, character_id):
        """챗봇 ID로 채팅방 가져오기 또는 생성"""
        room, created = Room.objects.get_or_create(
            character_id=character_id, defaults={"title": f"{character_id} 채팅방"}
        )
        return room

    def get_recent_messages(self, room, limit=None):
        """특정 채팅방의 최근 메시지 가져오기"""
        if limit is None:
            limit = getattr(settings, "CONVERSATION_HISTORY_LIMIT", 20)

        chats = Chat.objects.filter(room=room).order_by("-created_at")[:limit]
        return list(reversed(chats))  # 시간순으로 정렬

    def create_conversation_context(self, recent_messages, character_id):
        """대화 컨텍스트 생성 - 챗봇별 시스템 프롬프트"""
        system_prompt = self.get_system_prompt(character_id)
        context = [{"role": "system", "content": system_prompt}]

        for chat in recent_messages:
            role = "user" if chat.role == "user" else "assistant"
            context.append({"role": role, "content": chat.content})

        return context

    def get_system_prompt(self, character_id):
        """챗봇별 시스템 프롬프트 설정"""

        # TODO: 캐릭터 프롬프트
        prompts = {
            "assistant": "당신은 도움이 되는 AI 어시스턴트입니다.",
            "teacher": "당신은 친절한 선생님입니다. 교육적이고 이해하기 쉽게 설명해주세요.",
            "friend": "당신은 친근한 친구입니다. 편안하고 재미있게 대화해주세요.",
        }
        return prompts.get(character_id, prompts["assistant"])

    def get_ai_response(self, room, user_message):
        """AI 응답 생성"""
        try:
            recent_messages = self.get_recent_messages(room)
            messages = self.create_conversation_context(
                recent_messages, room.character_id
            )
            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"OpenAI API 오류: {e}")
            return "죄송합니다. 현재 응답을 생성할 수 없습니다."

    def save_chat(self, room, content, role):
        """채팅 메시지 저장"""
        return Chat.objects.create(room=room, content=content, role=role)
