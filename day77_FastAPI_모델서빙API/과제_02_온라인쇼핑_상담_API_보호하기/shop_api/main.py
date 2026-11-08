"""과제 01 에서 완성한 앱. 과제 02 는 이 파일 대신 secure_main.py 의 app 을 띄운다."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers.shop_router import shop_router
from .routers.system_router import system_router
from .services.backend import vllm_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # vllm_client 는 backend.py 가 이미 만들었다(만들 때는 연결을 열지 않는다)
    try:
        yield  # 준비가 끝나면 FastAPI가 요청을 처리한다.
    finally:
        await vllm_client.close()  # 종료 때 요청 처리에 쓴 vLLM 연결풀을 닫는다.


# 1) FastAPI 에 title, description, version 을 준다(title 은 "온라인 쇼핑 상담 API", lifespan=lifespan 은 그대로 둔다)
app = FastAPI(
    title="온라인 쇼핑 상담 API",
    description="같은 파드의 vLLM(qwen3.5-4b)에 쇼핑 질문을 보내 전자상거래법에 근거한 상담 답을 돌려줍니다.",
    version="1.0.0",
    lifespan=lifespan,
)

# 1) include_router 로 system_router 를 붙인다(/healthz, /v1/models)
# 2) include_router 로 shop_router 를 붙인다(/v1/shop/...)
app.include_router(system_router)
app.include_router(shop_router)
