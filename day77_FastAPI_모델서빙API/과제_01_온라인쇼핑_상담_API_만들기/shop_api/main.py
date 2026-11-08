"""과제 01 서빙 API. 실행(과제 01 폴더): uv run uvicorn shop_api.main:app --host 0.0.0.0 --port 8080 --reload"""
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


# TODO (1): /docs 화면 맨 위에 보일 제목과 설명을 붙여 FastAPI 앱 app 을 만드세요
# 1) FastAPI 에 title, description, version 을 준다(title 은 "온라인 쇼핑 상담 API", lifespan=lifespan 은 그대로 둔다)
app = FastAPI(lifespan=lifespan)  # 제목 없는 앱(TODO (1)에서 제목을 붙입니다)

# TODO (2): 상태 확인 주소 묶음과 쇼핑 상담 주소 묶음을 앱에 붙이세요
# 1) include_router 로 system_router 를 붙인다(/healthz, /v1/models)
# 2) include_router 로 shop_router 를 붙인다(/v1/shop/...)
