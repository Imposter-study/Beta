# Beta(AI 캐릭터 챗봇 서비스)

## 소개
- Beta는 실제 존재하는 AI 캐릭터 챗봇 서비스인 **Zeta AI**의 클론 코딩 프로젝트 입니다.


    ### 팀
    - Imposter Study

    ### 프로젝트
    - 사용자가 직접 AI 캐릭터를 생성하고, 다른 사용자가 만든 캐릭터와 자유롭게 대화할 수 있는 AI 챗봇 서비스입니다.

---

## 📚주요 기능

### 사용자 관리
- `회원가입 및 인증`: 일반 회원가입 및 JWT 기반의 로그인/로그아웃 기능을 제공합니다.
- `소셜 로그인`: 카카오, 구글 계정을 이용한 간편 로그인을 지원합니다.
- `프로필 관리`: 사용자 프로필(닉네임, 프로필 사진, 소개 등)을 조회하고 수정할 수 있습니다.
- `계정 관리`: 비밀번호 변경 및 회원 탈퇴(비활성화) 기능을 제공합니다.
- `대화프로필`: 사용자가 직접 AI 캐릭터와 대화하는 프로필을 생성, 조회, 수정, 삭제할 수 있습니다.

### AI 캐릭터
- `캐릭터 생성(CRUD)`: 사용자가 직접 자신만의 AI 캐릭터를 생성하고 관리(수정/삭제)할 수 있습니다.
- `캐릭터 설정`: 캐릭터의 이름, 이미지, 소개, 성격, 상황 예시 등 다채로운 설정이 가능합니다.
- `캐릭터 검색`: 다른 사용자가 만든 공개 캐릭터를 이름이나 해시태그로 검색할 수 있습니다.
- `캐릭터 스크랩`: 마음에 드는 캐릭터를 스크랩(팔로우)하여 쉽게 다시 찾아볼 수 있습니다.

### 채팅
- `채팅방 관리`: 특정 캐릭터와 대화할 수 있는 채팅방을 생성하고 관리(목록 조회, 상단 고정, 나가기)합니다.
- `실시간 AI 채팅`: 생성된 캐릭터와 실시간으로 대화를 나눌 수 있습니다.
- `대화 관리`: AI의 답변을 수정하거나, 특정 시점부터의 대화 기록을 삭제할 수 있습니다.
- `AI 응답 재생성`: AI의 답변이 마음에 들지 않을 경우, 새로운 답변을 요청할 수 있습니다.
- `추천 답변`: 대화의 흐름에 맞춰 AI가 추천하는 다음 질문을 제안받을 수 있습니다.

---

## 📦설치 및 실행 방법

### Docker Compose를 이용한 실행 (권장)

1.  **프로젝트 클론**
    ```sh
    git clone https://github.com/Imposter-study/Beta.git
    cd Beta
    ```

2. **.env 파일 설정**
    프로젝트 루트에 `.env` 파일을 생성하고 아래 내용을 참고하여 환경 변수를 설정합니다.
    ```env
    # Django
    SECRET_KEY=your_secret_key
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1

    # Database
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    DB_HOST=localhost
    
    #pgadmin
    PGADMIN_DEFAULT_EMAIL=
    PGADMIN_DEFAULT_PASSWORD=
    PGADMIN_CONFIG_SERVER_MODE=

    #LLM
    GOOGLE_API_KEY=
    AI_MODEL=
    CONVERSATION_HISTORY_LIMIT=
    VERBOSE=
    TEMPERATURE=
    MAX_TOKENS=
    SUGGESTIONS=
    # Social
    KAKAO_CLIENT_ID=
    KAKAO_CLIENT_SECRET=

    GOOGLE_CLIENT_ID=
    GOOGLE_CLIENT_SECRET=

    #Front
    KAKAO_REDIRECT_URL=
    GOOGLE_REDIRECT_URL=

    FRONT_DOMAIN=
    CORS_ALLOW_ALL_ORIGINS=True
    CSRF_TRUSTED_ORIGINS=


    # SIMPLE_JWT
    ACCESS_TOKEN_LIFETIME_MINUTES=
    REFRESH_TOKEN_LIFETIME_DAYS=
    SIGNING_KEY=
    JWT_ALGORITHM=
    JWT_AUTH_HEADER_TYPE=
    ```

3. **Docker Compose 실행**
    ```sh
    docker-compose up --build -d
    ```
    - `-d` 옵션은 백그라운드에서 컨테이너를 실행합니다.
    - 최초 실행 시 또는 `Dockerfile` 변경 시 `--build` 옵션을 사용합니다.

4. **서버 접속**
    - 웹 서버: `http://localhost:8000`
    - PgAdmin: `http://localhost:8080`

---

## 🛠 기술 스택

- `Backend`: Python, Django, Django REST Framework

- `Database`: PostgreSQL (psycopg2-binary)

- `AI/LLM`: LangChain, Google Generative AI

- `Authentication`: dj-rest-auth, djangorestframework-simplejwt, django-allauth

- `API Documentation`: drf-spectacular

- `Deployment`: Docker, Gunicorn, Nginx

- `Others`: Black, pylint for code quality

---

## 📁폴더 구조

```
Beta (프로젝트 루트)
├── accounts/         # 사용자 관리 앱
├── characters/       # AI 캐릭터 관리 앱
├── rooms/            # 채팅방 및 메시지 관리 앱
├── beta/             # Django 프로젝트 설정
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🤝기여 방법

1. 이슈를 확인하고 작업할 항목을 선택합니다.
2. 새로운 브랜치를 생성(`git checkout -b feature/기능-이름`)하여 작업을 수행합니다.
3. Pull Request를 생성하여 변경 사항을 공유합니다.

---

## 📄라이선스

본 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.

---

## 📬문의 및 연락처

프로젝트에 대한 문의사항은 다음으로 연락주세요:
- 이메일: imposterstudy@gmail.com
- 깃허브 이슈: Open an issue