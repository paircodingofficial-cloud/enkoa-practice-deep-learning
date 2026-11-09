"""서비스 키 인증과 요청 한도(과제 02). 둘 다 라우터에 의존성(Depends)으로 붙인다."""
import json
import math
import time

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from ..core.config import settings

# 키를 받을 헤더 이름. auto_error=False 면 헤더가 없을 때 None 이 들어와 401 을 직접 정할 수 있다
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# 서비스 키와 요금제별 한도. {"plans": {요금제: {"requests_per_minute": n}}, "keys": {키: {"user", "plan"}}}
with open(settings.service_keys_file, encoding="utf-8") as f:
    SERVICE_KEYS = json.load(f)

# 요청 한도를 세는 시간 창(초)
WINDOW_SECONDS = 60

# 키마다 최근 요청 시각(time.monotonic 값) 리스트. 서버 메모리에 두므로 서버를 다시 켜면 비워진다
request_log = {}


async def require_service_key(api_key: str | None = Depends(api_key_header)):
    """X-API-Key 헤더의 서비스 키를 확인하고 {"key", "user", "plan"} 을 돌려준다. 없거나 틀리면 401."""
    # 1) api_key 가 None 이거나 키 목록에 없으면 HTTPException 을 status_code 401 로 일으킨다
    if api_key is None or api_key not in SERVICE_KEYS["keys"]:
        raise HTTPException(status_code=401, detail="서비스 키가 없거나 올바르지 않습니다. X-API-Key 헤더를 확인하세요.")

    # 2) 키 목록에서 그 키의 user, plan 을 꺼내 키와 함께 딕셔너리로 돌려준다
    client = SERVICE_KEYS["keys"][api_key]
    return {"key": api_key, "user": client["user"], "plan": client["plan"]}


async def check_rate_limit(client: dict = Depends(require_service_key)):
    """키 확인을 먼저 거친 뒤, 최근 60초 요청 수가 요금제 한도 안이면 client 를 돌려준다. 넘으면 429."""
    limit = SERVICE_KEYS["plans"][client["plan"]]["requests_per_minute"]
    now = time.monotonic()

    # 1) request_log 에서 이 키의 요청 시각 가운데 now 와의 차이가 WINDOW_SECONDS 보다 작은 것만 남긴다
    #    기록에는 60초 안의 시각만 다시 저장하므로 키마다 많아야 한도만큼(free 3개, pro 30개)이다
    recent = []
    for sent_at in request_log.get(client["key"], []):
        if now - sent_at < WINDOW_SECONDS:
            recent.append(sent_at)

    # 2) 남은 수가 limit 이상이면 가장 오래된 요청이 창을 벗어날 때까지 남은 초를 math.ceil 로 올려 Retry-After 헤더에 담아 429 를 일으킨다
    if len(recent) >= limit:
        retry_after = math.ceil(WINDOW_SECONDS - (now - recent[0]))
        raise HTTPException(
            status_code=429,
            detail=f"{client['plan']} 요금제는 {WINDOW_SECONDS}초에 {limit}번까지 요청할 수 있습니다.",
            headers={"Retry-After": str(retry_after)},
        )

    # 3) 통과하면 now 를 더해 request_log 에 저장하고 client 를 돌려준다(거절한 요청은 한도에 세지 않는다)
    recent.append(now)
    request_log[client["key"]] = recent
    return client
