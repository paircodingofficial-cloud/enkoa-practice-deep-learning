"""서버 상태를 확인하는 주소 묶음. 인증 없이 열어 둔다(배포 뒤 상태 확인에 쓴다)."""
from fastapi import APIRouter

from ..services.backend import vllm_client

system_router = APIRouter(tags=["상태 확인"])


@system_router.get("/healthz")
async def healthz():
    """서빙 API 가 요청을 받을 수 있으면 {"status": "ok"} 를 돌려준다(vLLM 은 부르지 않는다)."""
    return {"status": "ok"}


@system_router.get("/v1/models")
async def list_models():
    """vLLM 서버가 서빙 중인 모델 이름 목록을 돌려준다."""
    models = await vllm_client.models.list()
    names = []
    for model in models.data:
        names.append(model.id)
    return {"models": names}
