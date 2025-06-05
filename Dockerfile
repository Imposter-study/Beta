# 베이스 이미지
FROM python:3.12-slim

# 작업 디렉토리
WORKDIR /app

# requirements.txt를 컨테이너로 복사 후, 의존성 패키지 설치
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일을 컨테이너의 /app으로 복사
COPY . /app/

# Django 서버 실행 포트 설정
EXPOSE 8000

# 환경 변수에 따라 다른 커맨드 실행
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
