from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import Room, Chat
from accounts.models import User
from characters.models import Character
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
import logging

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            google_api_key=settings.GOOGLE_API_KEY,
        )

    def get_or_create_room(self, character_id, user_id):
        character = get_object_or_404(Character, character=character_id)
        user = User.objects.get(id=user_id)

        room, created = Room.objects.get_or_create(
            user=user,
            character_id=character,
        )
        return room, character

    def create_memory_from_history(self, room, before_datetime=None):
        limit = getattr(settings, "CONVERSATION_HISTORY_LIMIT")

        memory = ConversationBufferWindowMemory(
            k=limit,
            return_messages=True,
            memory_key="chat_history",
        )

        queryset = Chat.objects.filter(room=room)
        if before_datetime:
            queryset = queryset.filter(created_at__lt=before_datetime)

        chats = queryset.order_by("-created_at")[:limit]
        recent_chats = list(reversed(chats))

        for chat in recent_chats:
            if chat.role == "user":
                memory.chat_memory.add_user_message(chat.content)
            elif chat.role == "ai":
                memory.chat_memory.add_ai_message(chat.content)

        return memory

    def recreate_memory_from_history(self, room, last_user_message):
        return self.create_memory_from_history(room, last_user_message.created_at)

    def get_system_prompt(self, character):
        prompt = f"당신은 '{character.name}'입니다.\n"
        prompt += f"제목: {character.title}\n"

        if character.intro:
            intro_messages = [item.get("message", "") for item in character.intro]
            intro_text = " ".join(intro_messages)
            prompt += f"소개: {intro_text}\n\n"

        if character.description:
            prompt += f"상세 설명: {character.description}\n\n"

        if character.character_info:
            prompt += f"캐릭터 정보: {character.character_info}\n\n"

        if character.example_situation:
            prompt += f"예시 상황: {character.example_situation}\n\n"

        if character.presentation:
            prompt += f"말투/스타일: {character.presentation}\n\n"

        # 기본 지침 추가
        prompt += """대화 지침:
        - 위에 명시된 캐릭터의 성격과 특징을 일관되게 유지하세요
        - 자연스럽고 몰입감 있는 대화를 이어가세요
        - 사용자와 친근하게 소통하되, 캐릭터의 고유한 톤을 잃지 마세요
        - **로 감싸진 문자는 상황 설명으로 인지하세요"""

        return prompt

    def create_conversation_chain(self, character, memory):
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    self.get_system_prompt(character)
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        chain = LLMChain(
            llm=self.llm, prompt=prompt, memory=memory, verbose=settings.VERBOSE
        )

        return chain

    def save_chat(self, room, content, role):
        return Chat.objects.create(room=room, content=content, role=role)

    def get_ai_response(self, room, user_message=None, last_user_message=None):
        try:
            character = room.character_id

            if last_user_message:
                memory = self.recreate_memory_from_history(room, last_user_message)
            else:
                memory = self.create_memory_from_history(room)

            chain = self.create_conversation_chain(character, memory)

            if user_message == None:
                user_message = ""

            response = chain.predict(input=user_message)

            return response.strip()

        except Exception as e:
            logger.error(f"AI 응답 생성 오류: {e}")
            return "죄송합니다. 현재 응답을 생성할 수 없습니다."
