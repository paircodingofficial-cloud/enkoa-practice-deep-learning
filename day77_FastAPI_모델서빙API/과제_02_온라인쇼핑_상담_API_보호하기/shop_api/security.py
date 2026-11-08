"""서비스 키 인증과 요청 한도(과제 02). 둘 다 라우터에 의존성(Depends)으로 붙인다."""
import json
import math
import time

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from .config import settings

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
    # TODO (1): 키가 없거나 SERVICE_KEYS["keys"] 에 없으면 401 로 거절하고, 있으면 키의 사용자와 요금제를 돌려주세요
    # 1) api_key 가 None 이거나 키 목록에 없으면 HTTPException 을 status_code 401 로 일으킨다

    # 2) 키 목록에서 그 키의 user, plan 을 꺼내 키와 함께 딕셔너리로 돌려준다
    raise NotImplementedError("security.py 의 TODO (1) 부분을 완성하세요")


async def check_rate_limit(client: dict = Depends(require_service_key)):
    """키 확인을 먼저 거친 뒤, 최근 60초 요청 수가 요금제 한도 안이면 client 를 돌려준다. 넘으면 429."""
    limit = SERVICE_KEYS["plans"][client["plan"]]["requests_per_minute"]
    now = time.monotonic()

    # TODO (2): 최근 60초 안의 요청 수가 한도에 닿았으면 429 와 Retry-After 로 거절하고, 통과한 요청만 기록하세요
    # 1) request_log 에서 이 키의 요청 시각 가운데 now 와의 차이가 WINDOW_SECONDS 보다 작은 것만 남긴다
    #    기록에는 60초 안의 시각만 다시 저장하므로 키마다 많아야 한도만큼(free 3개, pro 30개)이다

    # 2) 남은 수가 limit 이상이면 가장 오래된 요청이 창을 벗어날 때까지 남은 초를 math.ceil 로 올려 Retry-After 헤더에 담아 429 를 일으킨다

    # 3) 통과하면 now 를 더해 request_log 에 저장하고 client 를 돌려준다(거절한 요청은 한도에 세지 않는다)
    raise NotImplementedError("security.py 의 TODO (2) 부분을 완성하세요")
