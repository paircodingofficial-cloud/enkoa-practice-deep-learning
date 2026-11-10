"""사용량을 기록하는 상담 주소 묶음(교안 03).

토큰 사용량은 vLLM 의 답이 나온 뒤에야 알 수 있다. 그래서 교안 02 처럼 라우터를 붙일 때 의존성만 더하는 방식으로는
기록할 수 없고, 엔드포인트 안에서 답을 받은 뒤 기록한다. 노무와 전월세 창구는 경로 매개변수 desk 하나로 함께 처리한다.
"""
import json
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..core.config import settings
from ..core.metrics import OUTPUT_TOKENS
from ..dependencies.security import check_rate_limit, get_db, require_service_key
from ..repositories.key_store import record_usage, usage_summary
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.backend import ask_vllm, make_system_prompt, open_vllm_stream, to_chat_response
from ..services.streaming import relay_stream

metered_router = APIRouter(prefix="/v1", tags=["상담(사용량 기록)"])

# 창구 이름 -> 시스템 메시지. 이전 교안의 라우터를 불러오지 않고 참고 조문으로 직접 만든다.
SYSTEM_PROMPTS = {
    "labor": make_system_prompt(
        "너는 노무 상담 챗봇이다. 노동법 조문에 근거해 존댓말로 간결히 답한다.",
        "labor_reference.json",
    ),
    "lease": make_system_prompt(
        "너는 전월세 상담 챗봇이다. 주택임대차보호법 조문에 근거해 존댓말로 간결히 답한다.",
        "lease_reference.json",
    ),
}

# 창구 이름 -> 생각 상한. 노무 창구는 시스템 메시지가 길어 더 작은 값을 쓴다(설정 max_tokens_think_labor)
THINK_LIMITS = {"labor": settings.max_tokens_think_labor, "lease": settings.max_tokens_think}


# 경로 매개변수 desk 에 Literal 을 붙여 노무, 전월세 창구를 엔드포인트 하나로 처리한다
@metered_router.post("/{desk}/chat", response_model=ChatResponse)
async def metered_chat(
    desk: Literal["labor", "lease"],
    request: ChatRequest,
    client: dict = Depends(check_rate_limit),
    connection=Depends(get_db),  # lifespan 이 연 DB 연결
):
    """상담 답을 돌려주고, 키별 사용량과 창구별 출력 토큰 수를 기록합니다."""
    # 1) desk 에 맞는 시스템 메시지로 vLLM 에 묻는다(desk 가 labor, lease 가 아니면 422)
    completion = await ask_vllm(SYSTEM_PROMPTS[desk], request.question, request.think, max_tokens_think=THINK_LIMITS[desk])

    # 2) 그 요청의 토큰 사용량을 기록한다. client 는 check_rate_limit 을 통과한 키다
    usage = completion.usage
    await record_usage(
        connection, client["key_id"], f"/v1/{desk}/chat",
        usage.prompt_tokens, usage.prompt_tokens_details.cached_tokens, usage.completion_tokens,
    )

    # labels(desk=desk) 는 이 창구의 카운터를 고릅니다. inc(...) 는 이 답의 출력 토큰 수를 더합니다.
    OUTPUT_TOKENS.labels(desk=desk).inc(completion.usage.completion_tokens)
    return to_chat_response(completion)


async def relay_and_record(stream, connection, key_id, path):
    """relay_stream 이 만든 SSE 줄을 그대로 보내면서, usage 이벤트를 만나면 사용량을 기록한다."""
    # usage 이벤트 전에 스트림이 끊기면 기록하지 않는다
    async for line in relay_stream(stream):
        # usage 이벤트 줄: data: {"type": "usage", ...}
        if line.startswith('data: {"type": "usage"'):
            usage = json.loads(line[len("data: "):])
            await record_usage(connection, key_id, path, usage["prompt_tokens"], usage["cached_tokens"], usage["completion_tokens"])
            # labels(...) 는 URL의 창구별 카운터를 고르고, inc(...) 는 마지막 usage 이벤트의 출력 토큰 수를 더합니다.
            OUTPUT_TOKENS.labels(desk=path.split("/")[2]).inc(usage["completion_tokens"])
        yield line


@metered_router.post("/{desk}/chat/stream")
async def metered_chat_stream(
    desk: Literal["labor", "lease"],
    request: ChatRequest,
    client: dict = Depends(check_rate_limit),
    connection=Depends(get_db),
):
    """상담 답을 SSE 로 중계하고, 마지막 usage 이벤트의 토큰 수를 키별로 기록한다."""
    stream = await open_vllm_stream(SYSTEM_PROMPTS[desk], request.question, request.think, max_tokens_think=THINK_LIMITS[desk])
    return StreamingResponse(
        relay_and_record(stream, connection, client["key_id"], f"/v1/{desk}/chat/stream"),
        media_type="text/event-stream",
    )


# 서비스 키 확인만 붙여 요청 한도에 세지 않는다
@metered_router.get("/usage")
async def my_usage(
    start: date | None = None,  # 쿼리 매개변수 ?start=2026-11-01. 날짜 모양이 아니면 422
    end: date | None = None,  # 날짜는 UTC 기준(한국 시간 오전 9시 전 요청은 전날로 잡힌다)
    client: dict = Depends(require_service_key),
    connection=Depends(get_db),
):
    """X-API-Key 주인의 사용량 합계를 돌려준다(자기 키의 것만 볼 수 있다). start, end 를 주면 그 기간만 더한다."""
    return await usage_summary(connection, client["key_id"], start, end)
