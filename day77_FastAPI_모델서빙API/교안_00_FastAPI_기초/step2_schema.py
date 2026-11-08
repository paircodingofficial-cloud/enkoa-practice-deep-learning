"""도서관 안내 봇 2단계: POST 요청 본문과 응답 양식(pydantic 스키마).

실행(이 파일이 있는 폴더의 로컬 터미널, 실습자료에서 uv sync 완료 후): uv run uvicorn step2_schema:app --host 0.0.0.0 --port 8080 --reload
"""
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="도서관 안내 봇 API", version="0.2.0")


class AskRequest(BaseModel):
    """도서관 봇에게 보내는 질문 한 건."""

    # 기본값이 없는 항목은 필수, 기본값이 있는 항목은 보내지 않으면 기본값이 채워진다
    question: str = Field(min_length=2, description="이용자의 질문 문장")
    member_level: str = Field(default="basic", description="회원 등급(basic 또는 premium)")
    # ge 는 이상, le 는 이하. 10~500 밖의 값은 함수에 닿기 전에 422 로 돌아간다. 제약은 /docs 에도 그대로 표시된다
    max_length: int = Field(default=100, ge=10, le=500, description="답변 최대 길이")


class AskResponse(BaseModel):
    """도서관 봇의 답변 한 건."""

    answer: str = Field(description="안내 문장")
    member_level: str = Field(description="요청에 담겨 온 회원 등급")
    length: int = Field(description="답변 글자 수")


# 질문에 든 낱말 -> 안내문
ANSWERS = {
    "대출": "도서 대출은 1인 5권까지, 대출 기간은 14일입니다.",
    "연장": "대출 연장은 예약자가 없을 때 1회 7일 가능합니다.",
    "열람실": "열람실은 평일 9시부터 22시까지 운영합니다.",
}


def find_answer(question: str) -> str:
    """질문에 들어 있는 낱말로 안내문을 고릅니다."""
    for keyword, text in ANSWERS.items():
        if keyword in question:
            return text
    return "문의하신 내용은 안내 데스크에서 확인해 주세요."


# 매개변수의 타입이 BaseModel 이면 FastAPI 는 요청 본문(JSON)을 그 양식으로 검사해 객체로 넘긴다
@app.post("/v1/ask-simple")
def ask_simple(payload: AskRequest):
    """질문을 받아 안내문을 돌려줍니다(응답 양식은 정하지 않았습니다)."""
    # 검사를 통과한 값은 payload.question 처럼 점으로 꺼낸다
    answer = find_answer(payload.question)
    return {
        "answer": answer[: payload.max_length],
        "member_level": payload.member_level,
        "internal_note": "이 값은 밖에 나가면 안 되는 내부 메모입니다",
    }


# response_model 에 없는 항목(internal_note)은 응답에서 빠진다
@app.post("/v1/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    """질문을 받아 AskResponse 양식의 항목만 돌려줍니다."""
    answer = find_answer(payload.question)[: payload.max_length]
    return {
        "answer": answer,
        "member_level": payload.member_level,
        "length": len(answer),
        "internal_note": "이 값은 응답 양식에 없으므로 밖으로 나가지 않습니다",
    }


# ---------------------------------------------------------------------------
# 🖐️ 함께 따라하기
# ---------------------------------------------------------------------------

# (1) BaseModel을 상속하고 요청 필드 네 개를 작성하세요.
class QuietAskRequest:
    pass


# (2) BaseModel을 상속하고 응답 필드 세 개를 작성하세요.
class QuietAskResponse:
    pass


# (3) POST /v1/ask-quiet의 인자, 데코레이터, 본문을 작성하세요.
def ask_quiet():
    pass
