"""요청과 응답의 양식(스키마). FastAPI 는 이 양식으로 요청을 검사하고 /docs 문서를 만든다."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """상담 질문 하나. 시스템 메시지와 생성 상한은 항목에 없어 사용자가 바꿀 수 없다."""

    # 빈 질문과 지나치게 긴 질문은 vLLM 에 보내기 전에 422 로 돌려보낸다
    question: str = Field(min_length=2, max_length=500, description="사용자의 질문")
    think: bool = Field(default=False, description="True 면 모델의 생각(reasoning)을 켜고 답과 따로 돌려준다")


class Usage(BaseModel):
    """요청 하나가 쓴 토큰 수."""

    prompt_tokens: int = Field(description="입력 토큰 수(시스템 메시지 포함)")
    cached_tokens: int = Field(description="캐시 적중 토큰: 입력 토큰 가운데 캐시에서 다시 쓴 토큰 수")
    completion_tokens: int = Field(description="출력 토큰 수(생각 포함)")
    total_tokens: int = Field(description="입력과 출력의 합")


class ChatResponse(BaseModel):
    """상담 답변 하나. finish_reason, model, usage 는 vLLM 응답의 값을 그대로 옮겨 담는다."""

    # 생각이 생성 상한을 다 쓰면 답이 비어 None 이 될 수 있다(finish_reason 이 length)
    answer: str | None = Field(description="모델의 답")
    reasoning: str | None = Field(default=None, description="모델의 생각. think 가 False 면 None")
    finish_reason: str = Field(description="생성이 끝난 이유. stop 은 답을 마침, length 는 생성 상한에 닿음")
    model: str = Field(description="실제로 답한 모델 이름")
    usage: Usage = Field(description="토큰 사용량")
