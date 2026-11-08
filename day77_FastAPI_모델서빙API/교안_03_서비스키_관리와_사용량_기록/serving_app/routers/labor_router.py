"""노무 상담 창구의 주소 묶음(APIRouter). 주소는 모두 /v1/labor 로 시작한다."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..core.config import settings
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.backend import ask_vllm, make_system_prompt, open_vllm_stream, to_chat_response
from ..services.streaming import relay_stream

# prefix 는 묶음 안 모든 주소 앞에 붙고(/chat 은 /v1/labor/chat), tags 는 /docs 화면에서 묶어 보여 줄 이름이다
labor_router = APIRouter(prefix="/v1/labor", tags=["노무 상담"])

# 시스템 메시지는 서버가 뜰 때 한 번 만든다. 사용자는 질문만 보내고 시스템 메시지는 바꿀 수 없다
LABOR_SYSTEM_PROMPT = make_system_prompt(
    "너는 노무 상담 챗봇이다. 노동법 조문에 근거해 존댓말로 간결히 답한다.",
    "labor_reference.json",
)


# 교안 00 의 @app.post 와 같은 데코레이터지만, 함수를 앱이 아니라 묶음에 등록한다
@labor_router.post("/chat", response_model=ChatResponse)
async def labor_chat(request: ChatRequest):
    """노무 질문 하나에 대한 답 전체를 한 번에 돌려준다."""
    # vLLM 의 답을 기다리는 동안(await) 서버는 다른 요청을 받는다
    # 시스템 메시지가 길어 생각 상한은 노무 창구 값(settings.max_tokens_think_labor)을 넘긴다
    # 입력 토큰 수와 생성 상한의 합이 vLLM 의 --max-model-len(8192)을 넘으면 vLLM 이 거절한다
    completion = await ask_vllm(LABOR_SYSTEM_PROMPT, request.question, request.think, max_tokens_think=settings.max_tokens_think_labor)
    return to_chat_response(completion)


@labor_router.post("/chat/stream")
async def labor_chat_stream(request: ChatRequest):
    """노무 질문의 답을 조각이 만들어지는 대로 SSE(text/event-stream)로 보낸다."""
    # 스트림을 응답보다 먼저 연다. 첫 조각을 보낸 뒤에는 상태 코드를 바꿀 수 없으므로, vLLM 에 닿지 않으면 응답을 시작하기 전에 여기서 오류를 낸다
    stream = await open_vllm_stream(LABOR_SYSTEM_PROMPT, request.question, request.think, max_tokens_think=settings.max_tokens_think_labor)
    # relay_stream 이 yield 한 줄을 바로 보내고, media_type 으로 SSE 응답임을 알린다
    return StreamingResponse(relay_stream(stream), media_type="text/event-stream")
