"""DB 에 저장한 서비스 키로 인증하고 요청 한도를 지킨다(교안 03).

교안 02 의 security.py 와 같은 흐름이다. 다른 점은 키를 JSON 파일 대신 SQLite 에서 해시로 찾는 것과,
폐기된 키도 401 로 돌려보내는 것이다.
"""
import math
import secrets
import time

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

from ..core.config import settings
from ..repositories.key_store import find_active_key

# 헤더 확인과 요청 기록은 이 앱이 직접 만든다. JSON 키 파일은 읽지 않는다.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
WINDOW_SECONDS = 60
request_log = {}

ADMIN_API_KEY = settings.admin_api_key
admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin(admin_key: str | None = Depends(admin_key_header)):
    """X-Admin-Key 가 서버의 관리자 키와 같은지 확인한다. 다르면 403."""
    # compare_digest 는 비교 시간으로 키를 추측하기 어렵게 한다.
    if ADMIN_API_KEY is None or admin_key is None or not secrets.compare_digest(admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="관리자 키가 필요합니다. X-Admin-Key 헤더를 확인하세요.")


# 요금제별 60초당 요청 한도
PLAN_LIMITS = {"free": 3, "pro": 30}


def get_db(request: Request):
    """요청이 들어온 앱의 lifespan 이 연 DB 연결을 꺼낸다(app.state.db).

    엔드포인트와 의존성은 connection=Depends(get_db) 로 받아 key_store 함수에 넘긴다.
    """
    return request.app.state.db


async def require_service_key(api_key: str | None = Depends(api_key_header), connection=Depends(get_db)):
    """X-API-Key 의 키를 DB 에서 찾아 {"key_id", "user", "plan"} 을 돌려준다. 없거나 폐기된 키면 401."""
    if api_key is None:
        raise HTTPException(status_code=401, detail="서비스 키가 없습니다. X-API-Key 헤더를 확인하세요.")

    client = await find_active_key(connection, api_key)  # 폐기한 키도 찾지 못해 없는 키와 같이 401 이 된다
    if client is None:
        raise HTTPException(status_code=401, detail="발급되지 않았거나 폐기된 서비스 키입니다.")
    return client


async def check_rate_limit(client: dict = Depends(require_service_key)):
    """DB 키 확인을 먼저 거친 뒤, key_id 의 최근 60초 요청 수가 요금제 한도 안이면 client 를 돌려준다. 넘으면 429."""
    # 메모리의 기록만 고치는 함수라 async def 로 둔다(한 이벤트 루프에서 차례로 실행되어 기록이 엉키지 않는다)
    limit = PLAN_LIMITS[client["plan"]]
    now = time.monotonic()

    # 1) 60초 창 안의 요청 시각만 남긴다(교안 02 의 check_rate_limit 과 같은 계산)
    # 교안 02 는 키 원문별로 기록했다. 원문을 메모리에도 두지 않으려고 key_id 별로 기록한다
    recent = []
    for sent_at in request_log.get(client["key_id"], []):
        if now - sent_at < WINDOW_SECONDS:
            recent.append(sent_at)

    # 2) 한도를 다 썼으면 가장 오래된 요청이 창을 벗어날 때까지 남은 초를 Retry-After 로 알린다
    if len(recent) >= limit:
        retry_after = math.ceil(WINDOW_SECONDS - (now - recent[0]))
        raise HTTPException(
            status_code=429,
            detail=f"{client['plan']} 요금제는 {WINDOW_SECONDS}초에 {limit}번까지 요청할 수 있습니다.",
            headers={"Retry-After": str(retry_after)},
        )

    # 3) 통과한 요청만 기록한다
    recent.append(now)
    request_log[client["key_id"]] = recent
    return client
