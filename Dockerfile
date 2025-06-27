# 멀티스테이지 빌드(Multi-stage Build) 방식 구현

# 1단계: 빌드 스테이지 (빌드 도구 포함)
FROM python:3.12-slim AS builder

WORKDIR /app

# 빌드에 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사 (collectstatic을 위해 manage.py 및 설정 필요)
COPY . /app/

# 정적 파일 수집
RUN python manage.py collectstatic --noinput

# 2단계: 런타임 스테이지 (불필요한 빌드 도구 제거, 최소화)
FROM python:3.12-slim

WORKDIR /app

# 런타임에 필요한 패키지 설치 (libpq만 남김)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# builder에서 설치된 패키지와 소스, static 파일만 복사
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# 포트 오픈
EXPOSE 8000



# 환경 변수에 따라 다른 커맨드 실행
CMD ["sh", "-c", "if [ '$DJANGO_ENV' = 'production' ]; then gunicorn beta.wsgi:application --bind 0.0.0.0:8000; else python manage.py runserver 0.0.0.0:8000; fi"]
