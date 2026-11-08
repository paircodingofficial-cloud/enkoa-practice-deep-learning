"""도서관 안내 봇 1단계: GET 엔드포인트와 경로 매개변수, 쿼리 매개변수.

실행(이 파일이 있는 폴더의 로컬 터미널, 실습자료에서 uv sync 완료 후): uv run uvicorn step1_endpoint:app --host 0.0.0.0 --port 8080 --reload
"""
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware

# title, description, version 은 /docs 문서 화면 맨 위에 보인다
app = FastAPI(
    title="도서관 안내 봇 API",
    description="도서관 이용 문의에 답하는 서비스입니다.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
)

# 책 번호 -> 제목, 서가 위치, 대출 가능 여부
BOOKS = {
    12: {"title": "파이썬으로 배우는 데이터 분석", "shelf": "A-3", "available": True},
    45: {"title": "도서관 이용 안내서", "shelf": "B-1", "available": False},
}

# 주제 -> 안내문
NOTICES = {
    "대출": "도서 대출은 1인 5권까지, 대출 기간은 14일입니다.",
    "열람실": "열람실은 평일 9시부터 22시까지, 주말은 9시부터 18시까지 운영합니다.",
}


# GET /healthz 요청을 이 함수가 처리한다. 주소를 정하는 것은 함수 이름이 아니라 데코레이터의 "/healthz" 다
@app.get("/healthz")
def health_check():
    """서버가 요청을 받을 수 있으면 상태 ok 를 돌려줍니다."""
    # 딕셔너리를 돌려주면 FastAPI 가 JSON 으로 바꿔 보낸다
    return {"status": "ok", "service": "library-bot"}


# 주소의 {book_id} 자리 값이 같은 이름의 매개변수로 들어온다(경로 매개변수)
@app.get("/books/{book_id}")
def get_book(book_id: int = Path(ge=1)):  # 글자 "12" 를 정수 12 로 바꿔 넘긴다. Path(ge=1) 은 1 이상만 받는다
    """책 번호로 책 한 권의 정보를 돌려줍니다. 없는 번호면 404 입니다."""
    book = BOOKS.get(book_id)

    # 없는 책이면 함수를 여기서 끝내고 404(Not Found, 요청한 대상 없음)와 {"detail": 메시지} 본문을 돌려준다
    if book is None:
        raise HTTPException(status_code=404, detail=f"{book_id}번 책이 없습니다.")

    # 책 번호와 책 정보(title, shelf, available)를 한 딕셔너리로 합친다
    return {"book_id": book_id, **book}


# 주소의 {} 에 없는 매개변수는 쿼리 매개변수(?topic=...&max_length=...)가 된다. 기본값이 있으면 보내지 않아도 된다
# Query(default=100, ge=1, le=500): 보내지 않으면 100, 1 이상 500 이하만 받는다
@app.get("/notice")
def get_notice(topic: str, max_length: int = Query(default=100, ge=1, le=500)):
    """주제별 안내문을 돌려줍니다. max_length 로 안내문 길이를 자를 수 있습니다."""
    text = NOTICES.get(topic, "해당 주제의 안내문이 없습니다.")
    return {"topic": topic, "notice": text[:max_length], "truncated": len(text) > max_length}


# ---------------------------------------------------------------------------
# 🖐️ 함께 따라하기
# ---------------------------------------------------------------------------

# (1) 77번 책의 정보를 BOOKS에 추가하세요.
BOOKS[77] = ...


# (2) GET /v2/notice의 인자, 데코레이터, 본문을 작성하세요.
def get_notice_v2():
    pass
