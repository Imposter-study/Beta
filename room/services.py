from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from django.conf import settings
from .models import Room, Chat
import logging

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL,
            temperature=0.7,
            max_tokens=1000,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    def get_or_create_room(self, character_id, user_id):
        room, created = Room.objects.get_or_create(
            character_id=character_id,
            user_id=user_id,
            defaults={"title": f"{character_id} 채팅방", "user_id": user_id},
        )
        return room

    def create_memory_from_history(self, room):
        limit = getattr(settings, "CONVERSATION_HISTORY_LIMIT")

        memory = ConversationBufferWindowMemory(
            k=limit,
            return_messages=True,
            memory_key="chat_history",
        )

        chats = Chat.objects.filter(room=room).order_by("-created_at")[:limit]
        recent_chats = list(reversed(chats))

        for chat in recent_chats:
            if chat.role == "user":
                memory.chat_memory.add_user_message(chat.content)
            elif chat.role == "ai":
                memory.chat_memory.add_ai_message(chat.content)

        return memory

    def get_system_prompt(self, character_id):
        # TODO: 캐릭터 프롬프트
        prompts = {
            "assistant": """당신은 도움이 되는 AI 어시스턴트입니다. 
            사용자의 질문에 정확하고 유용한 답변을 제공하세요.""",
            "teacher": """당신은 친절한 선생님입니다. 
            - 교육적이고 이해하기 쉽게 설명해주세요
            - 복잡한 개념은 단계별로 나누어 설명하세요
            - 예시를 들어 설명하면 더 좋습니다""",
            "friend": """당신은 친근한 친구입니다. 
            - 편안하고 재미있게 대화해주세요
            - 공감하고 격려하는 톤으로 응답하세요
            - 때로는 유머를 섞어도 좋습니다""",
        }
        return prompts.get(character_id, prompts["assistant"])

    def create_conversation_chain(self, character_id, memory):
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    self.get_system_prompt(character_id)
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        chain = ConversationChain(
            llm=self.llm, prompt=prompt, memory=memory, verbose=settings.VERBOSE
        )

        return chain

    def get_ai_response(self, room, user_message):
        try:
            memory = self.create_memory_from_history(room)

            chain = self.create_conversation_chain(room.character_id, memory)

            response = chain.predict(input=user_message)

            return response.strip()

        except Exception as e:
            logger.error(f"AI 응답 생성 오류: {e}")
            return "죄송합니다. 현재 응답을 생성할 수 없습니다."

    def save_chat(self, room, content, role):
        return Chat.objects.create(room=room, content=content, role=role)
