"""교안 02 서빙 API(인증, 요청 한도, 오류 양식). 실행(교안 02 폴더): uv run uvicorn serving_app.secure_main:app --host 0.0.0.0 --port 8080 --reload

교안 01 의 라우터를 그대로 가져와, 붙일 때 의존성만 더한다. 교안 01 코드는 고치지 않는다.
"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from .core.errors import register_error_handlers
from .dependencies.security import check_rate_limit
from .routers.labor_router import labor_router
from .routers.lease_router import lease_router
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
    title="노무, 전월세 상담 API(서비스 키 필요)",
    description="X-API-Key 헤더의 서비스 키를 확인하고, 요금제별 요청 한도를 지킨 요청만 vLLM 에 보냅니다.",
    version="2.0.0",
    lifespan=lifespan,
)

# 오류 응답 양식을 먼저 붙인다
register_error_handlers(app)

# 상태 확인 주소는 키 없이 열어 둔다(배포 뒤 자동 확인용)
app.include_router(system_router)

# 상담 주소에는 요청 한도 의존성을 붙인다. check_rate_limit 은 키 확인(require_service_key)을 먼저 거친다
protected = [Depends(check_rate_limit)]
app.include_router(labor_router, dependencies=protected)
app.include_router(lease_router, dependencies=protected)
