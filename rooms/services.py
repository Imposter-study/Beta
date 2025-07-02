# Python Library
import logging

# Third-Party Packages
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)

# Local Apps
from .models import Chat

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS,
            google_api_key=settings.GOOGLE_API_KEY,
        )

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
            example_texts = []
            for inner_list in character.example_situation:
                if isinstance(inner_list, list):
                    for item_dict in inner_list:
                        if isinstance(item_dict, dict):
                            role = item_dict.get("role", "")
                            message = item_dict.get("message", "")
                            if role and message:
                                example_texts.append(f"{role}: {message}")

            if example_texts:
                example_text = "\n".join(example_texts)
                prompt += f"예시 상황:\n{example_text}\n\n"

        if character.presentation:
            prompt += f"말투/스타일: {character.presentation}\n\n"

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
            character = room.character

            if last_user_message:
                memory = self.recreate_memory_from_history(room, last_user_message)
            else:
                memory = self.create_memory_from_history(room)

            chain = self.create_conversation_chain(character, memory)

            if user_message == None:
                # TODO: 메시지 이어서 생성 프롬프트
                user_message = ""

            response = chain.predict(input=user_message)

            return response.strip()

        except Exception as e:
            logger.error(f"AI 응답 생성 오류: {e}")
            return "죄송합니다. 현재 응답을 생성할 수 없습니다."

    def get_chat_suggestion(self, room):
        character = room.character
        memory = self.create_memory_from_history(room)

        suggestion_system_prompt = f"""당신은 '{character.name}' 캐릭터와 대화하는 사용자를 위한 추천 답변 생성기입니다.

    캐릭터 정보:
    - 이름: {character.name}
    - 제목: {character.title}"""

        if character.description:
            suggestion_system_prompt += f"\n- 설명: {character.description}"

        if character.character_info:
            suggestion_system_prompt += f"\n- 캐릭터 정보: {character.character_info}"

        suggestion_system_prompt += """

    지침:
    1. 이전 대화 맥락을 고려하여 자연스럽게 이어질 수 있는 사용자 답변을 제안하세요
    2. 질문, 공감, 또는 새로운 주제 제안 등 다양한 형태로 구성하세요
    3. 한 문장으로 간결하게 작성하세요

    이전 대화를 참고하여 사용자가 다음에 할 수 있는 자연스러운 답변 하나를 생성해주세요."""

        suggestion_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(suggestion_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template(
                    "위 대화를 바탕으로 사용자가 할 수 있는 자연스러운 답변을 하나 생성해주세요:"
                ),
            ]
        )

        suggestion_chain = LLMChain(
            llm=self.llm,
            prompt=suggestion_prompt,
            memory=memory,
            verbose=settings.VERBOSE,
        )

        suggestion = suggestion_chain.predict(input="")

        return suggestion.strip()
