"""온라인 쇼핑 상담 창구의 주소 묶음(APIRouter). 주소는 모두 /v1/shop 으로 시작한다."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..schemas.chat import ChatResponse, ShopChatRequest
from ..services.backend import ask_vllm, make_system_prompt, open_vllm_stream, to_chat_response
from ..services.streaming import relay_stream

# 1) APIRouter 에 prefix 와 /docs 화면의 묶음 이름 tags 를 준다
shop_router = APIRouter(prefix="/v1/shop", tags=["쇼핑 상담"])

# 시스템 메시지는 서버가 뜰 때 한 번 만든다(지침 문장 + 전자상거래법 참고 조문)
SHOP_SYSTEM_PROMPT = make_system_prompt(
    "너는 온라인 쇼핑 상담 챗봇이다. 전자상거래법 조문에 근거해 존댓말로 간결히 답한다.",
    "commerce_reference.json",
)


def make_user_message(request):
    """모델에 보낼 사용자 메시지를 돌려준다. 주문번호가 있으면 질문 앞에 붙인다."""
    # 1) request.order_id 가 None 이면 request.question 을 그대로 돌려준다
    # 2) None 이 아니면 f-string 으로 주문번호와 질문을 이어 붙인다
    if request.order_id is None:
        return request.question
    return f"[주문번호 {request.order_id}] {request.question}"


# 1) shop_router 의 post 데코레이터에 주소와 응답 양식(response_model)을 준다
# 2) async def 로 만들고 요청 본문은 ShopChatRequest 로 받는다
# 3) make_user_message 로 만든 메시지를 ask_vllm 에 넣어 await 하고, to_chat_response 로 바꿔 돌려준다
@shop_router.post("/chat", response_model=ChatResponse)
async def shop_chat(request: ShopChatRequest):
    """쇼핑 질문 하나에 대한 답 전체를 한 번에 돌려준다."""
    completion = await ask_vllm(SHOP_SYSTEM_PROMPT, make_user_message(request), request.think)
    return to_chat_response(completion)


# 1) shop_router 의 post 데코레이터에 주소를 주고, async def 로 만들어 ShopChatRequest 를 받는다
# 2) make_user_message 로 만든 메시지와 request.think 를 open_vllm_stream 에 넣어 await 하고, 스트림을 응답보다 먼저 연다
# 3) relay_stream 으로 바꾼 조각을 StreamingResponse 에 담고 media_type 을 text/event-stream 으로 준다
@shop_router.post("/chat/stream")
async def shop_chat_stream(request: ShopChatRequest):
    """쇼핑 질문의 답을 조각이 만들어지는 대로 SSE(text/event-stream)로 보낸다."""
    stream = await open_vllm_stream(SHOP_SYSTEM_PROMPT, make_user_message(request), request.think)
    return StreamingResponse(relay_stream(stream), media_type="text/event-stream")
