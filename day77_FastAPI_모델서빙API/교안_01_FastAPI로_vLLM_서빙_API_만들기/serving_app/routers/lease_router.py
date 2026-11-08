"""전월세 상담 창구의 주소 묶음(APIRouter). 주소는 모두 /v1/lease 로 시작한다(교안 01 함께 따라하기)."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..schemas.chat import ChatRequest, ChatResponse
from ..services.backend import ask_vllm, make_system_prompt, open_vllm_stream, to_chat_response
from ..services.streaming import relay_stream

lease_router = APIRouter(prefix="/v1/lease", tags=["전월세 상담"])

# 전월세 창구의 시스템 메시지(지침 문장 + 주택임대차보호법 참고 조문)
LEASE_SYSTEM_PROMPT = make_system_prompt(
    "너는 전월세 상담 챗봇이다. 주택임대차보호법 조문에 근거해 존댓말로 간결히 답한다.",
    "lease_reference.json",
)


@lease_router.post("/chat", response_model=ChatResponse)
async def lease_chat(request: ChatRequest):
    """전월세 질문 하나에 대한 답 전체를 한 번에 돌려준다."""
    # 🖐️ 함께 따라하기 (1): 전월세 시스템 메시지, 요청의 질문, 요청의 생각 켜기 여부로 vLLM 에 묻고, 답이 다 만들어질 때까지 기다린다
    ...

    # 🖐️ 함께 따라하기 (2): vLLM 의 응답(ChatCompletion)을 서빙 API 의 응답 양식(ChatResponse)으로 바꿔 돌려준다
    ...


@lease_router.post("/chat/stream")
async def lease_chat_stream(request: ChatRequest):
    """전월세 질문의 답을 조각이 만들어지는 대로 SSE(text/event-stream)로 보낸다."""
    # 🖐️ 함께 따라하기 (3): 일반 응답과 같은 세 값으로 vLLM 스트림을 연다. 응답을 시작하기 전에 열어야 vLLM 에 닿지 않을 때 바로 오류로 알린다
    ...

    # 🖐️ 함께 따라하기 (4): 스트림의 조각을 SSE 이벤트로 바꿔 보내는 응답(text/event-stream)을 돌려준다
    ...
