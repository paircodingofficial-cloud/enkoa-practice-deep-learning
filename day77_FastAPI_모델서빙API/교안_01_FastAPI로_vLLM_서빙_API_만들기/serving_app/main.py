"""교안 01 서빙 API. 실행(교안 01 폴더): uv run uvicorn serving_app.main:app --host 0.0.0.0 --port 8080 --reload"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers.labor_router import labor_router
from .routers.lease_router import lease_router
from .routers.system_router import system_router
from .services.backend import vllm_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # vllm_client 는 여러 라우터 파일이 함께 쓰므로 app.state 대신 backend.py 에서 만든다(만들 때는 연결을 열지 않는다)
    try:
        yield  # 준비가 끝나면 FastAPI가 요청을 처리한다.
    finally:
        await vllm_client.close()  # 종료 때 요청 처리에 쓴 vLLM 연결풀을 닫는다.


# title, description 은 /docs 문서 화면 맨 위에 보인다
app = FastAPI(
    title="노무, 전월세 상담 API",
    description="같은 파드의 vLLM(qwen3.5-4b)에 질문을 보내 상담 답을 돌려줍니다.",
    version="1.0.0",
    lifespan=lifespan,
)

# 기능별 주소 묶음을 앱에 붙인다. 묶음의 prefix 가 주소 앞부분이 되고, 붙이지 않은 묶음의 주소는 404 다
app.include_router(system_router)
app.include_router(labor_router)
app.include_router(lease_router)
