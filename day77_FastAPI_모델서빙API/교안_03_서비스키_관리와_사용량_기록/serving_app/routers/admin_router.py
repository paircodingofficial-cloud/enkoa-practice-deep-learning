"""관리자용 키 관리 주소 묶음(교안 03). 주소는 모두 /v1/admin/keys 로 시작하고 X-Admin-Key 가 맞아야 한다."""
import secrets
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from ..core.config import settings
from ..dependencies.db_security import get_db
from ..repositories.key_store import issue_key, list_keys, revoke_key, usage_summary

# 관리자 키는 서버 쪽 .env 에만 둔다(설정의 admin_api_key, 환경 변수 ADMIN_API_KEY)
ADMIN_API_KEY = settings.admin_api_key

# 관리자 주소를 여는 앱이므로, 관리자 키가 없으면 서버가 뜰 때 바로 멈춘다
if ADMIN_API_KEY is None:
    raise RuntimeError("ADMIN_API_KEY 가 없습니다. 환경 변수나 .env 에 관리자 키를 넣으세요.")

admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def require_admin(admin_key: str | None = Depends(admin_key_header)):
    """X-Admin-Key 가 서버의 관리자 키와 같은지 확인한다. 다르면 403."""
    # compare_digest: 글자를 앞에서부터 비교하다 멈추지 않아, 걸린 시간으로 키를 추측할 수 없다
    if admin_key is None or not secrets.compare_digest(admin_key, ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="관리자 키가 필요합니다. X-Admin-Key 헤더를 확인하세요.")


class IssueKeyRequest(BaseModel):
    """키 발급 요청."""

    user: str = Field(min_length=1, max_length=50, description="키를 받을 사용자(앱, 고객사) 이름")
    # 요금제는 두 값만 받는다. 그 밖의 값은 교안 02 의 오류 양식과 같은 422(invalid_request)
    plan: Literal["free", "pro"] = Field(description="요금제. free 는 60초에 3번, pro 는 30번")


class IssuedKey(BaseModel):
    """발급한 키. api_key 원문은 이 응답에서 한 번만 보인다."""

    key_id: int
    api_key: str
    user: str
    plan: str


class KeyInfo(BaseModel):
    """키 목록의 한 행(원문과 해시는 담지 않는다)."""

    key_id: int
    user: str
    plan: str
    created_at: str
    revoked_at: str | None


class UsageSummary(BaseModel):
    """키 하나의 사용량 합계."""

    key_id: int
    start: date | None  # 조회 기간의 첫날(주지 않으면 None, 처음부터)
    end: date | None  # 조회 기간의 끝날(주지 않으면 None, 지금까지)
    requests: int
    prompt_tokens: int
    cached_tokens: int
    completion_tokens: int
    total_tokens: int


# 라우터에 붙인 의존성은 이 묶음의 모든 주소에 적용된다
# 교안 02 는 앱에 붙일 때(include_router) 지정했다. 라우터를 만들 때 지정하면 어느 앱에 넣어도 확인이 빠지지 않는다
admin_router = APIRouter(prefix="/v1/admin/keys", tags=["키 관리(관리자)"], dependencies=[Depends(require_admin)])


# 새 키를 만드는 주소라 200 대신 201 Created(새 것을 만들었다)로 답한다
@admin_router.post("", status_code=201, response_model=IssuedKey)
async def create_key(request: IssueKeyRequest, connection=Depends(get_db)):
    """새 서비스 키를 발급한다(201 Created)."""
    return await issue_key(connection, request.user, request.plan)


# 관리자 키 확인은 admin_router 에 붙인 require_admin 이 이 함수보다 먼저 한다(키가 없거나 틀리면 403)
@admin_router.get("", response_model=list[KeyInfo])
async def read_keys(connection=Depends(get_db)):
    """발급한 키 목록을 돌려준다."""
    return await list_keys(connection)


# 관리자 키 확인은 admin_router 에 붙인 require_admin 이 이 함수보다 먼저 한다(키가 없거나 틀리면 403)
@admin_router.delete("/{key_id}")
async def delete_key(key_id: int, connection=Depends(get_db)):  # key_id: 경로의 키 번호. 숫자가 아니면 422
    """키를 폐기한다. 없거나 이미 폐기된 키면 404."""
    if not await revoke_key(connection, key_id):  # 바뀐 행이 없으면 없는 key_id 이거나 이미 폐기한 키다
        raise HTTPException(status_code=404, detail=f"폐기할 키가 없습니다: {key_id}")
    return {"key_id": key_id, "revoked": True}


# 관리자 키 확인은 admin_router 에 붙인 require_admin 이 이 함수보다 먼저 한다(키가 없거나 틀리면 403)
@admin_router.get("/{key_id}/usage", response_model=UsageSummary)
async def read_key_usage(
    key_id: int,
    start: date | None = None,  # 쿼리 매개변수 ?start=2026-11-01. 날짜 모양이 아니면 422
    end: date | None = None,  # 날짜는 UTC 기준(한국 시간 오전 9시 전 요청은 전날로 잡힌다)
    connection=Depends(get_db),
):
    """키 하나의 요청 수와 토큰 합계를 돌려준다. start, end 를 주면 그 기간만 더한다."""
    return await usage_summary(connection, key_id, start, end)  # 관리자는 아무 키나 본다. /v1/usage 와 같은 함수로 계산한다
