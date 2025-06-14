from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import StrOutputParser
from django.conf import settings


llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", google_api_key=("GOOGLE_API_KEY")
)

# 필수 입력 
title = input("챗봇 제목 (title): ")
name = input("캐릭터 이름 (name): ")
intro = input("인트로 (intro, 캐릭터 소개 한 줄): ")

# 선택 입력
description = input("상세 설명 (description): ")
character_info = input("캐릭터 성격 설명 (character_info): ")
example_situation = input("상황 예시 (example_situation): ")
presentation = input("전체 소개 문장 (presentation): ")

# 선택
optional_parts = ""
if description.strip():
    optional_parts += f"\n상세 설명: {description.strip()}"
if character_info.strip():
    optional_parts += f"\n캐릭터 설명: {character_info.strip()}"
if example_situation.strip():
    optional_parts += f"\n상황 예시: {example_situation.strip()}"
if presentation.strip():
    optional_parts += f"\n소개: {presentation.strip()}"

template = """
당신은 사용자와 대화하는 챗봇입니다. 다음의 캐릭터 설정을 기반으로 역할극을 수행하세요.

제목: {title}
캐릭터 이름: {name}
인트로: {intro}
{optional_blocks}

사용자의 질문에 캐릭터에 어울리는 말투와 성격으로 반응하세요.
질문: {input}
"""

prompt = ChatPromptTemplate.from_template(template)

# 프롬프트 → LLM → 출력 파서 체인 생성
chain = prompt | llm | StrOutputParser()

print(f"\n[{name}] 챗봇이 시작되었습니다. 'quit' 또는 'exit' 입력 시 종료됩니다.\n")

while True:
    user_input = input(" 나 : ")
    if user_input.lower() in ("quit", "exit"):
        print("챗봇을 종료합니다.")
        break

    response = chain.invoke(
        {
            "title": title,
            "name": name,
            "intro": intro,
            "optional_blocks": optional_parts,
            "input": user_input,
        }
    )

    print(f"{name}: {response}")
