"""도서관 안내 봇 3단계: def 와 async def, async def 안의 time.sleep 이 다른 요청까지 멈추는 것.

실행(이 파일이 있는 폴더의 로컬 터미널, 실습자료에서 uv sync 완료 후): uv run uvicorn step3_async:app --host 0.0.0.0 --port 8080 --reload
"""
import asyncio
import time

from fastapi import FastAPI

app = FastAPI(title="도서관 안내 봇 API", version="0.3.0")

# 모델 서버의 답을 기다리는 시간 대신 쓰는 대기 시간(초)
BACKEND_DELAY = 0.5


# def 엔드포인트: FastAPI 가 스레드 풀(미리 띄워 둔 작업 스레드 묶음)의 스레드 하나에서 실행한다
@app.get("/wait/def")
def wait_def():
    """일반 함수 엔드포인트. time.sleep 으로 BACKEND_DELAY 초 동안 이 스레드만 멈춥니다."""
    time.sleep(BACKEND_DELAY)
    return {"endpoint": "def + time.sleep"}


# async def 엔드포인트: 이벤트 루프에서 실행하고, await 에서 기다리는 동안 다른 요청을 처리한다
@app.get("/wait/async")
async def wait_async():
    """코루틴 엔드포인트. await asyncio.sleep 으로 기다리는 동안 이벤트 루프를 비워 둡니다."""
    await asyncio.sleep(BACKEND_DELAY)
    return {"endpoint": "async def + await asyncio.sleep"}


# 잘못 쓴 예: async def 안의 time.sleep 은 이벤트 루프 자체를 멈춰, 그동안 다른 요청을 하나도 처리하지 못한다
@app.get("/wait/blocking")
async def wait_blocking():
    """코루틴 엔드포인트 안에서 time.sleep 을 부른 예. 이벤트 루프가 BACKEND_DELAY 초 동안 멈춥니다."""
    time.sleep(BACKEND_DELAY)
    return {"endpoint": "async def + time.sleep"}

