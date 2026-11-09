"""요청과 응답의 양식(스키마). FastAPI 는 이 양식으로 요청을 검사하고 /docs 문서를 만든다."""
from pydantic import BaseModel, Field


class ShopChatRequest(BaseModel):
    """쇼핑 상담 질문 하나(질문, 생각 켜기, 주문번호)."""

    # 1) 자료형은 str, 기본값은 두지 않는다(빠지면 422)
    # 2) Field 의 min_length, max_length 로 글자 수를 제한한다
    question: str = Field(min_length=2, max_length=300, description="고객의 질문(상담 창의 입력 한도 300자)")

    # 1) 자료형은 bool, Field 의 default 로 기본값을 준다
    think: bool = Field(default=False, description="True 면 모델의 생각(reasoning)을 켜고 답과 따로 돌려준다")

    # 1) 자료형은 str | None, 기본값은 None 이다
    # 2) Field 의 pattern 에 정규식 ^ORD-\d{6}$ 를 준다(형식이 틀리면 vLLM 에 보내기 전에 422)
    order_id: str | None = Field(default=None, pattern=r"^ORD-\d{6}$", description="질문과 관련된 주문번호(예: ORD-123456)")


class Usage(BaseModel):
    """요청 하나가 쓴 토큰 수."""

    prompt_tokens: int = Field(description="입력 토큰 수(시스템 메시지 포함)")
    cached_tokens: int = Field(description="캐시 적중 토큰: 입력 토큰 가운데 캐시에서 다시 쓴 토큰 수")
    completion_tokens: int = Field(description="출력 토큰 수(생각 포함)")
    total_tokens: int = Field(description="입력과 출력의 합")


class ChatResponse(BaseModel):
    """상담 답변 하나."""

    # 생각이 생성 상한을 다 쓰면 답이 비어 None 이 될 수 있다(finish_reason 이 length)
    answer: str | None = Field(description="모델의 답")
    reasoning: str | None = Field(default=None, description="모델의 생각. think 가 False 면 None")
    finish_reason: str = Field(description="생성이 끝난 이유. stop 은 답을 마침, length 는 생성 상한에 닿음")
    model: str = Field(description="실제로 답한 모델 이름")
    usage: Usage = Field(description="토큰 사용량")
