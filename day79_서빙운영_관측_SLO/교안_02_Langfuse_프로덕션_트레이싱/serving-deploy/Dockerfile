# 노무, 전월세 상담 서빙 API 이미지(교안 01)

# (1) 베이스 이미지: 파이썬 3.12 의 slim 버전(서버 실행에 필요한 것만 든 작은 버전). 태그를 꼭 적는다
FROM python:3.12-slim

# (2) uv 실행 파일만 공식 uv 이미지에서 복사한다. 버전을 적어 두면 언제 빌드해도 같은 uv 를 쓴다
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

# (3) 이후 명령이 실행될 작업 폴더
WORKDIR /app

# (4) 라이브러리 목록과 잠금 파일만 먼저 복사해 설치한다. 코드만 고치면 이 두 층은 캐시를 그대로 쓴다
#     --locked: uv.lock 에 적힌 버전 그대로, --no-dev: 테스트 도구 제외, --no-cache: 내려받은 파일을 이미지에 남기지 않음
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-cache

# (5) 자주 바뀌는 서버 코드는 마지막에 복사한다
COPY serving_app ./serving_app

# (6) 설치한 가상환경의 실행 파일을 먼저 찾게 하고, 키 DB 위치를 정한다(배포 때 이 폴더에 볼륨을 붙인다)
ENV PATH="/app/.venv/bin:$PATH" \
    SERVICE_DB_PATH=/app/data/service.db

# (7) 이 이미지가 쓰는 포트를 적어 둔다(표시일 뿐이고, 실제로 여는 것은 docker run -p 와 compose 의 ports)
EXPOSE 8080

# (8) 컨테이너를 켜면 실행할 명령(exec 형식). 컨테이너 밖에서 들어오려면 0.0.0.0 에 묶는다
CMD ["uvicorn", "serving_app.managed_main:app", "--host", "0.0.0.0", "--port", "8080"]
