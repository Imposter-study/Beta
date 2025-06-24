# 워커 수
workers = 1

# 워커 타입: 기본 sync (메모리 절약)
worker_class = "sync"

# 한 워커당 처리할 최대 요청 수 (메모리 누수 방지, 너무 작게 하면 오버헤드 발생 위험험)
max_requests = 1200
max_requests_jitter = 100

# 타임아웃
timeout = 30

# keepalive: 커넥션 재사용 시간(초)
keepalive = 2

# 로그: stdout/stderr로 출력(도커 환경)
accesslog = "-"
errorlog = "-"
