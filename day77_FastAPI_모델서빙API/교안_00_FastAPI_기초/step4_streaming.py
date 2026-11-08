"""도서관 안내 봇 4단계: 비동기 제너레이터와 StreamingResponse 로 답변을 조각으로 보내기.

실행(이 파일이 있는 폴더의 로컬 터미널, 실습자료에서 uv sync 완료 후): uv run uvicorn step4_streaming:app --host 0.0.0.0 --port 8080 --reload
"""
import asyncio

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="도서관 안내 봇 API", version="0.4.0")

# 모델이 다음 조각을 만드는 데 걸리는 시간 대신 쓰는 대기 시간(초)
PIECE_DELAY = 0.3



# 질문에 든 낱말 -> 안내문
ANSWERS = {'대출': '도서 대출은 1인 5권까지, 대출 기간은 14일입니다.', '연장': '대출 연장은 예약자가 없을 때 1회 7일 가능합니다.', '열람실': '열람실은 평일 9시부터 22시까지 운영합니다.'}


class StreamRequest(BaseModel):
    """스트리밍으로 답변을 받을 질문 한 건."""

    question: str = Field(min_length=2, description="이용자의 질문 문장")


def find_answer(question: str) -> str:
    """질문에 들어 있는 낱말로 안내문을 고릅니다."""
    for keyword, text in ANSWERS.items():
        if keyword in question:
            return text
    return "문의하신 내용은 안내 데스크에서 확인해 주세요."


async def answer_pieces(question: str):
    """안내문을 낱말 하나씩 조각으로 내놓는 비동기 제너레이터입니다."""
    text = find_answer(question)
    for word in text.split(" "):
        # 다음 조각이 만들어지기를 기다린다. 기다리는 동안 이벤트 루프는 다른 요청을 처리한다
        await asyncio.sleep(PIECE_DELAY)
        # 낱말 뒤에 띄어쓰기를 붙여 내놓는다. 받는 쪽은 조각을 이어 붙이면 원래 문장이 된다
        yield f"{word} "


# StreamingResponse 는 제너레이터가 조각을 내놓을 때마다 그 조각을 바로 보낸다
# 응답이 딕셔너리 하나가 아니라 이어 보내는 글자 조각이라 response_model 은 쓰지 않는다(요청 양식 검사는 그대로 한다)
@app.post("/v1/ask-stream")
async def ask_stream(payload: StreamRequest):
    """답변을 조각으로 이어 보냅니다(text/plain)."""
    # media_type="text/plain" 은 일반 글자를 보낸다는 표시다
    return StreamingResponse(answer_pieces(payload.question), media_type="text/plain")


# 비교용: 같은 조각을 끝까지 모은 뒤 한 번에 돌려준다
@app.post("/v1/ask-once")
async def ask_once(payload: StreamRequest):
    """답변을 끝까지 만든 뒤 JSON 하나로 돌려줍니다."""
    text = ""
    async for piece in answer_pieces(payload.question):
        text += piece
    # 마지막 조각 뒤의 띄어쓰기는 뺀다
    return {"answer": text.strip()}
