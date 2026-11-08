"""SQLite DB 연결의 앱 수명 주기. 실행: uv run uvicorn step5_lifespan:app --host 0.0.0.0 --port 8080 --reload"""
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

# 이 파일과 같은 폴더의 SQLite 파일. books 테이블에 책 번호, 제목, 서가, 대출 가능 여부가 들어 있다.
DB_PATH = Path(__file__).resolve().parent / "library.db"


# @asynccontextmanager 를 붙이면 yield 앞은 시작 때 준비 코드, 뒤(finally)는 종료 때 정리 코드로 쓰인다
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 프로세스 시작 때 DB 파일에 한 번 연결해 앱 전체가 함께 쓴다.
    # def 엔드포인트는 스레드 풀의 다른 스레드에서 실행되므로 check_same_thread=False 로 허용한다(이 예시는 읽기만 한다).
    connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row  # 조회 결과의 행을 열 이름으로 읽는다(row["title"]).
    app.state.db = connection  # app.state 는 앱 전체가 함께 쓸 값을 두는 공간이다
    print("DB 연결 준비 완료")
    try:
        yield  # 준비가 끝나면 FastAPI가 요청을 처리한다.
    finally:
        connection.close()  # 이 앱의 연결을 닫는다. DB 파일은 그대로 남는다.
        print("DB 연결 종료 완료")


app = FastAPI(title="SQLite 연결 수명 주기", lifespan=lifespan)


# sqlite3 는 동기 라이브러리라 def 로 작성한다(스레드 풀에서 실행된다)
@app.get("/db/books/{book_id}")
def db_book(book_id: int):
    """앱이 시작할 때 연 연결로 books 테이블에서 책 한 권을 찾는다."""
    # ? 자리에 값을 따로 넘겨, 사용자 입력을 SQL 문자열에 직접 붙이지 않는다.
    row = app.state.db.execute(
        "SELECT book_id, title, shelf, available FROM books WHERE book_id = ?", (book_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{book_id}번 책이 없습니다.")
    return {"book_id": row["book_id"], "title": row["title"], "shelf": row["shelf"], "available": bool(row["available"])}
