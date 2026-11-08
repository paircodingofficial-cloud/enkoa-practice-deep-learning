"""LangChain 모델 응답을 FastAPI의 텍스트 스트림으로 중계한다.

실행: uv run uvicorn step6_langchain_stream:app --host 0.0.0.0 --port 8080 --reload
실습자료/.env: OPENAI_API_KEY 필수, OPENAI_CHAT_MODEL 선택.
"""
import os
from contextlib import asynccontextmanager

import httpx
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

load_dotenv(find_dotenv(usecwd=True))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 모든 비동기 모델 요청이 같은 HTTP 연결풀을 재사용한다.
    http_client = httpx.AsyncClient(timeout=60)
    try:
        app.state.model = ChatOpenAI(
            model=os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
            http_async_client=http_client,
            temperature=0,
            max_tokens=256,
        )
        yield
    finally:
        await http_client.aclose()  # 앱 종료 시 공유 HTTP 연결도 닫는다.


app = FastAPI(title="LangChain 스트리밍 API", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500, description="모델에게 보낼 질문")


async def chat_pieces(question: str):
    """모델이 보내는 텍스트를 모으지 않고 받는 즉시 내놓는다."""
    messages = [("system", "질문에 한국어로 세 문장 이내로 답해야 한다."), ("human", question)]
    # astream 이 내놓는 AIMessageChunk 마다 텍스트(chunk.text)만 꺼내 받는 즉시 내놓는다
    async for chunk in app.state.model.astream(messages):
        if chunk.text:
            yield chunk.text


@app.post("/v1/chat/stream")
async def chat_stream(payload: ChatRequest):
    return StreamingResponse(chat_pieces(payload.question), media_type="text/plain")


# ---------------------------------------------------------------------------
# 🖐️ 함께 따라하기
# ---------------------------------------------------------------------------

# (1) BaseModel을 상속하고 요약할 text 필드를 작성하세요.
class SummaryRequest:
    pass


# (2) LangChain으로 요약을 요청하고 텍스트 조각을 그대로 내놓으세요.
async def summary_pieces():
    pass


# (3) 요약 요청을 받아 텍스트 스트림으로 반환하는 주소를 등록하세요.
async def summarize_stream():
    pass
