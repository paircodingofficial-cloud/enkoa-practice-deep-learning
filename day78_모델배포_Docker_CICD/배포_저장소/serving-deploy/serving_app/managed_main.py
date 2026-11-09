"""교안 03 서빙 API(DB 키 관리, 사용량 기록). 실행: uv run uvicorn serving_app.managed_main:app --host 0.0.0.0 --port 8080 --reload

교안 02 와 다른 점: 키를 SQLite 에 해시로 저장하고, 관리자 주소로 발급과 폐기를 하며, 요청마다 토큰 사용량을 기록한다.
"""
from contextlib import asynccontextmanager

import aiosqlite
from fastapi import Depends, FastAPI

from .core.errors import register_error_handlers
from .dependencies.security import require_admin
from .repositories.key_store import SERVICE_DB_PATH, init_db
from .routers.admin_router import admin_router
from .routers.metered_router import metered_router
from .routers.system_router import system_router
from .services.backend import vllm_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 시작할 때 DB 연결 하나를 열어 앱 전체가 함께 쓴다(FastAPI 서빙 API 단원 교안 00 5-3 과 같은 방식)
    # aiosqlite 는 이 연결의 스레드 하나에서 요청을 차례로 실행하므로, 여러 요청이 같은 연결을 써도 엉키지 않는다
    SERVICE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # output 폴더가 없으면 만든다
    connection = await aiosqlite.connect(SERVICE_DB_PATH)
    connection.row_factory = aiosqlite.Row  # 조회한 행의 값을 row["user"] 처럼 열 이름으로 꺼낸다
    await init_db(connection)  # 테이블을 만든다(이미 있으면 그대로 둔다)
    app.state.db = connection
    try:
        yield  # 준비가 끝나면 FastAPI가 요청을 처리한다.
    finally:
        await connection.close()  # 종료 때 DB 연결을 닫는다. DB 파일은 그대로 남는다.
        await vllm_client.close()  # 종료 때 요청 처리에 쓴 vLLM 연결풀을 닫는다.


app = FastAPI(
    title="노무, 전월세 상담 API(키 관리와 사용량 기록)",
    description="관리자가 발급한 서비스 키로 인증하고, 키별 토큰 사용량을 SQLite 에 기록합니다.",
    version="3.0.0",
    lifespan=lifespan,
)

register_error_handlers(app)
app.include_router(system_router)
# 반환값을 쓰지 않는 관리자 확인은 묶음을 앱에 붙일 때 지정한다(교안 02와 같은 방식).
app.include_router(admin_router, dependencies=[Depends(require_admin)])
# 상담은 키별 사용량을 기록하므로, 엔드포인트의 client=Depends(...) 로 키 정보도 받는다.
app.include_router(metered_router)
