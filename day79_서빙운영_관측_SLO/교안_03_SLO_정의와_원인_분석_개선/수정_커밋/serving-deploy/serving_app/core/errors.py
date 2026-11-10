"""오류 응답을 한 양식으로 맞춘다(교안 02). 모든 오류는 {"error": {"code": ..., "message": ...}} 로 돌려준다."""
import openai
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# 상태 코드마다 프로그램이 읽을 짧은 오류 이름
ERROR_CODES = {
    401: "invalid_service_key",
    403: "admin_only",  # 교안 03 의 관리자 주소에서 쓴다
    404: "not_found",
    429: "rate_limited",
}


def error_response(status_code, code, message, headers=None):
    """오류 양식의 JSON 응답을 돌려준다."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


async def handle_http_error(request, exc):
    """HTTPException(401, 404, 429 등)을 오류 양식으로 바꾼다. Retry-After 같은 헤더는 그대로 넘긴다."""
    code = ERROR_CODES.get(exc.status_code, "http_error")
    return error_response(exc.status_code, code, str(exc.detail), exc.headers)


async def handle_validation_error(request, exc):
    """요청 양식 오류(422)를 오류 양식으로 바꾼다. 문제가 여럿이어도 첫 번째 문제의 위치와 내용만 알려 준다."""
    first = exc.errors()[0]
    # loc 예: ("body", "question"). 마지막 값이 문제가 된 항목 이름이다
    field = first["loc"][-1]
    return error_response(422, "invalid_request", f"{field}: {first['msg']}")


async def handle_vllm_timeout(request, exc):
    """vLLM 이 시간 제한 안에 답하지 않으면(openai.APITimeoutError) 504."""
    return error_response(504, "backend_timeout", "모델 서버가 제한 시간 안에 답하지 않았습니다. 잠시 뒤 다시 시도하세요.")


async def handle_vllm_unreachable(request, exc):
    """vLLM 서버에 연결하지 못하면(openai.APIConnectionError) 502."""
    return error_response(502, "backend_unavailable", "모델 서버에 연결할 수 없습니다. 잠시 뒤 다시 시도하세요.")


async def handle_vllm_status_error(request, exc):
    """vLLM 이 오류 상태 코드로 답하면(openai.APIStatusError) 502. vLLM 의 상태 코드만 알리고 내부 메시지는 넘기지 않는다."""
    return error_response(502, "backend_error", f"모델 서버가 오류({exc.status_code})로 답했습니다.")


def register_error_handlers(app: FastAPI):
    """앱에 오류 처리 함수를 붙인다. 예외 종류가 겹치면 더 좁은 종류(시간 초과)의 함수가 먼저 쓰인다."""
    # 없는 주소의 404 는 FastAPI 가 아니라 Starlette 가 일으킨다
    # FastAPI HTTPException 의 부모인 Starlette 쪽에 붙여 401, 429, 404 를 한 양식으로 맞춘다
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    # vLLM 쪽 실패(5절). APITimeoutError 는 APIConnectionError 의 한 종류지만 더 좁아서 먼저 쓰인다(시간 초과만 504)
    app.add_exception_handler(openai.APITimeoutError, handle_vllm_timeout)
    app.add_exception_handler(openai.APIConnectionError, handle_vllm_unreachable)
    app.add_exception_handler(openai.APIStatusError, handle_vllm_status_error)
