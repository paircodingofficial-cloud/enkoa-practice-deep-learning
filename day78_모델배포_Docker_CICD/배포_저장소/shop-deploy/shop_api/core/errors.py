"""오류 응답을 한 양식으로 맞춘다(과제 02). 모든 오류는 {"error": {"code": ..., "message": ...}} 로 돌려준다."""
import openai
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# 상태 코드마다 프로그램이 읽을 짧은 오류 이름
ERROR_CODES = {
    401: "invalid_service_key",
    404: "not_found",
    429: "rate_limited",
}


def error_response(status_code, code, message, headers=None):
    """오류 양식의 JSON 응답을 돌려준다."""
    # 1) JSONResponse 에 status_code, content, headers 를 준다
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
        headers=headers,
    )


async def handle_http_error(request, exc):
    """HTTPException(401, 404, 429 등)을 오류 양식으로 바꾼다. Retry-After 같은 헤더는 그대로 넘긴다."""
    # 1) ERROR_CODES 에서 exc.status_code 의 이름을 꺼내고, 없으면 "http_error" 를 쓴다(딕셔너리의 get)
    # 2) error_response 에 상태 코드, 이름, exc.detail 을 글자로 바꾼 값, exc.headers 를 준다
    code = ERROR_CODES.get(exc.status_code, "http_error")
    return error_response(exc.status_code, code, str(exc.detail), exc.headers)


async def handle_validation_error(request, exc):
    """요청 양식 오류(422)를 오류 양식으로 바꾼다. 첫 번째 문제의 위치와 내용을 알려 준다."""
    # 1) exc.errors() 의 첫 번째 딕셔너리를 꺼낸다
    first = exc.errors()[0]

    # 2) loc 예: ("body", "question"). 마지막 값이 문제가 된 항목 이름이고, 내용은 msg 에 있다
    field = first["loc"][-1]
    return error_response(422, "invalid_request", f"{field}: {first['msg']}")


async def handle_vllm_timeout(request, exc):
    """vLLM 이 시간 제한 안에 답하지 않으면 504."""
    # 1) error_response 에 다시 시도하라는 안내 문장을 message 로 준다
    return error_response(504, "backend_timeout", "모델 서버가 제한 시간 안에 답하지 않았습니다. 잠시 뒤 다시 시도하세요.")


async def handle_vllm_unreachable(request, exc):
    """vLLM 서버에 연결하지 못하면 502."""
    # 1) error_response 에 다시 시도하라는 안내 문장을 message 로 준다
    return error_response(502, "backend_unavailable", "모델 서버에 연결할 수 없습니다. 잠시 뒤 다시 시도하세요.")


async def handle_vllm_status_error(request, exc):
    """vLLM 이 오류 상태 코드로 답하면 502. vLLM 의 상태 코드만 알리고 내부 메시지는 넘기지 않는다."""
    return error_response(502, "backend_error", f"모델 서버가 오류({exc.status_code})로 답했습니다.")


def register_error_handlers(app: FastAPI):
    """앱에 오류 처리 함수를 붙인다. 예외 종류가 겹치면 더 좁은 종류(시간 초과)의 함수가 먼저 쓰인다."""
    # 1) app.add_exception_handler 로 StarletteHTTPException, RequestValidationError 를 붙인다
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)

    # 2) openai.APITimeoutError 는 504, openai.APIConnectionError 는 502, openai.APIStatusError 는 handle_vllm_status_error 로 붙인다
    app.add_exception_handler(openai.APITimeoutError, handle_vllm_timeout)
    app.add_exception_handler(openai.APIConnectionError, handle_vllm_unreachable)
    app.add_exception_handler(openai.APIStatusError, handle_vllm_status_error)
