"""과제 02 서빙 API(인증, 요청 한도, 오류 양식). 실행(과제 02 폴더): uv run uvicorn shop_api.secure_main:app --host 0.0.0.0 --port 8080 --reload

과제 01 의 라우터를 그대로 가져와, 붙일 때 의존성만 더한다. 과제 01 코드는 고치지 않는다.
"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from .core.errors import register_error_handlers
from .dependencies.security import check_rate_limit
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


app = FastAPI(
    title="온라인 쇼핑 상담 API(서비스 키 필요)",
    description="X-API-Key 헤더의 서비스 키를 확인하고, 요금제별 요청 한도를 지킨 요청만 vLLM 에 보냅니다.",
    version="2.0.0",
    lifespan=lifespan,
)

# 오류 응답 양식을 붙인다
register_error_handlers(app)

# 1) include_router 로 system_router 를 의존성 없이 붙인다
app.include_router(system_router)

# 1) include_router 의 dependencies 에 Depends(check_rate_limit) 하나를 담은 리스트를 준다
# 2) check_rate_limit 이 서비스 키 확인(require_service_key)을 먼저 거치므로 키 확인을 따로 붙이지 않는다
app.include_router(shop_router, dependencies=[Depends(check_rate_limit)])
