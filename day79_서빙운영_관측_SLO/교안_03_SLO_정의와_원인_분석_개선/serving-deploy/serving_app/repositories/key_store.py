"""서비스 키와 사용량을 SQLite 파일 하나에 저장한다(교안 03).

키 원문은 저장하지 않고 SHA-256 해시만 저장한다. DB 파일을 누가 읽어도 키 원문은 알 수 없다.
DB 를 읽고 쓰는 함수는 모두 async def 이고, 앱의 lifespan 이 연 aiosqlite 연결(connection)을 받아 await 한다.
aiosqlite 는 연결마다 스레드 하나에서 sqlite3 를 실행해, DB 를 쓰는 동안에도 이벤트 루프가 다른 요청을 받는다.
SQLite 는 파일 하나에 한 번에 한 곳만 쓰므로 동시에 온 쓰기는 차례로 처리된다.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from ..core.config import settings

# 서비스 키와 사용량을 저장할 SQLite 파일. 설정의 service_db_path(환경 변수 SERVICE_DB_PATH, 기본 output/service.db)
SERVICE_DB_PATH = settings.service_db_path


async def init_db(connection):
    """키 테이블(api_keys)과 사용량 테이블(usage)을 만든다. 이미 있으면 그대로 둔다."""
    # IF NOT EXISTS: 테이블이 이미 있으면 그대로 둬, 서버를 다시 켜도 발급한 키와 사용량 기록이 남는다
    await connection.executescript("""
        -- 서비스 키 테이블: 발급한 키 하나가 한 행
        CREATE TABLE IF NOT EXISTS api_keys (
            key_id     INTEGER PRIMARY KEY AUTOINCREMENT,  -- 키 번호. 발급할 때마다 1씩 저절로 늘어난다
            key_hash   TEXT NOT NULL UNIQUE,  -- 키 원문의 SHA-256 해시(원문은 저장하지 않는다)
            user       TEXT NOT NULL,         -- 키를 받은 사용자(앱, 고객사) 이름
            plan       TEXT NOT NULL,         -- 요금제(free, pro)
            created_at TEXT NOT NULL,         -- 발급 시각(UTC)
            revoked_at TEXT                   -- 폐기 시각. 폐기 전에는 비어 있다(NULL)
        );
        -- 사용량 테이블: 처리한 상담 요청 하나가 한 행
        CREATE TABLE IF NOT EXISTS usage (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,  -- 행 번호(1부터 저절로 늘어난다)
            key_id            INTEGER NOT NULL,  -- 요청에 쓴 키(api_keys 의 key_id)
            path              TEXT NOT NULL,     -- 요청한 주소(/v1/labor/chat 등)
            prompt_tokens     INTEGER NOT NULL,  -- 입력 토큰 수(서버가 붙인 시스템 메시지 포함)
            cached_tokens     INTEGER NOT NULL,  -- 캐시 적중 토큰: 입력 토큰 가운데 캐시에서 다시 쓴 토큰 수
            completion_tokens INTEGER NOT NULL,  -- 출력 토큰 수(생각 포함)
            created_at        TEXT NOT NULL      -- 기록 시각(UTC)
        );
    """)


def hash_key(api_key):
    """키 원문의 SHA-256 해시(64자리 16진수 문자열)를 돌려준다."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def now_text():
    """지금 시각(UTC)을 '2026-01-01T00:00:00+00:00' 모양 문자열로 돌려준다."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def issue_key(connection, user, plan):
    """새 서비스 키를 만들어 해시만 저장하고, 키 원문이 든 딕셔너리를 돌려준다(원문은 이때 한 번만 보인다)."""
    # 1) 추측할 수 없는 무작위 키를 만든다
    api_key = "svc-" + secrets.token_urlsafe(24)  # 추측할 수 없는 긴 무작위 문자열

    # 2) 키 원문 대신 해시를 저장한다. key_id 는 DB 가 1, 2, 3 처럼 차례로 매긴다
    cursor = await connection.execute(
        "INSERT INTO api_keys (key_hash, user, plan, created_at) VALUES (?, ?, ?, ?)",
        (hash_key(api_key), user, plan, now_text()),
    )
    await connection.commit()
    key_id = cursor.lastrowid  # 방금 넣은 행의 번호. 비밀이 아니라 차례로 늘어나도 된다(비밀은 api_key)

    # 원문은 이 딕셔너리에만 담겨 발급 응답에서 한 번만 보인다(잃어버리면 새로 발급하고 옛 키는 폐기한다)
    return {"key_id": key_id, "api_key": api_key, "user": user, "plan": plan}


async def find_active_key(connection, api_key):
    """키 원문의 해시로 폐기되지 않은 키를 찾아 {"key_id", "user", "plan"} 을 돌려준다. 없으면 None."""
    # 해시가 같고 폐기되지 않은(revoked_at IS NULL) 행만 찾는다. 폐기한 키는 없는 키와 같아진다
    cursor = await connection.execute(
        "SELECT key_id, user, plan FROM api_keys WHERE key_hash = ? AND revoked_at IS NULL",
        (hash_key(api_key),),
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return {"key_id": row["key_id"], "user": row["user"], "plan": row["plan"]}


async def list_keys(connection):
    """발급한 키 목록을 발급 순서대로 돌려준다(키 원문과 해시는 담지 않는다)."""
    cursor = await connection.execute(
        "SELECT key_id, user, plan, created_at, revoked_at FROM api_keys ORDER BY key_id"
    )
    rows = await cursor.fetchall()
    keys = []
    for row in rows:
        keys.append(dict(row))
    return keys


async def revoke_key(connection, key_id):
    """키를 폐기한다(행을 지우지 않고 revoked_at 을 채운다). 폐기했으면 True, 없거나 이미 폐기된 키면 False."""
    cursor = await connection.execute(
        "UPDATE api_keys SET revoked_at = ? WHERE key_id = ? AND revoked_at IS NULL",
        (now_text(), key_id),
    )
    await connection.commit()
    # 바뀐 행이 하나면 이번에 폐기한 것이다
    return cursor.rowcount == 1


async def record_usage(connection, key_id, path, prompt_tokens, cached_tokens, completion_tokens):
    """요청 하나의 토큰 사용량을 usage 테이블에 한 행으로 남긴다."""
    await connection.execute(
        "INSERT INTO usage (key_id, path, prompt_tokens, cached_tokens, completion_tokens, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (key_id, path, prompt_tokens, cached_tokens, completion_tokens, now_text()),
    )
    await connection.commit()


async def usage_summary(connection, key_id, start=None, end=None):
    """키 하나의 요청 수와 토큰 합계를 딕셔너리로 돌려준다. start, end(날짜, 둘 다 포함)를 주면 그 기간만 더한다."""
    # 1) 조건을 모은다. created_at 은 '2026-11-08T03:00:00+00:00' 모양 UTC 문자열이라 날짜 문자열과 크기 비교가 된다
    conditions = ["key_id = ?"]
    values = [key_id]
    if start is not None:
        conditions.append("created_at >= ?")
        values.append(start.isoformat())
    if end is not None:
        conditions.append("created_at < ?")  # 끝 날짜를 포함하려고 다음 날 0시 전까지 더한다
        values.append((end + timedelta(days=1)).isoformat())

    # 2) 기록이 없으면 SUM 이 NULL 이므로 COALESCE 로 0 으로 바꾼다
    cursor = await connection.execute(
        "SELECT COUNT(*) AS requests, "
        "COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens, "
        "COALESCE(SUM(cached_tokens), 0) AS cached_tokens, "
        "COALESCE(SUM(completion_tokens), 0) AS completion_tokens "
        "FROM usage WHERE " + " AND ".join(conditions),
        values,
    )
    row = await cursor.fetchone()
    return {
        "key_id": key_id,
        "start": start,
        "end": end,
        "requests": row["requests"],
        "prompt_tokens": row["prompt_tokens"],
        "cached_tokens": row["cached_tokens"],
        "completion_tokens": row["completion_tokens"],
        "total_tokens": row["prompt_tokens"] + row["completion_tokens"],
    }
