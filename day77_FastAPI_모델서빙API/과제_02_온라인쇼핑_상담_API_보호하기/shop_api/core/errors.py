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
    # TODO (1): 본문이 {"error": {"code": code, "message": message}} 인 JSON 응답을 돌려주세요
    # 1) JSONResponse 에 status_code, content, headers 를 준다
    raise NotImplementedError("core/errors.py 의 TODO (1) 부분을 완성하세요")


async def handle_http_error(request, exc):
    """HTTPException(401, 404, 429 등)을 오류 양식으로 바꾼다. Retry-After 같은 헤더는 그대로 넘긴다."""
    # TODO (2): 상태 코드에 맞는 오류 이름으로 오류 양식 응답을 만들고, 예외의 헤더를 그대로 넘기세요
    # 1) ERROR_CODES 에서 exc.status_code 의 이름을 꺼내고, 없으면 "http_error" 를 쓴다(딕셔너리의 get)
    # 2) error_response 에 상태 코드, 이름, exc.detail 을 글자로 바꾼 값, exc.headers 를 준다
    raise NotImplementedError("core/errors.py 의 TODO (2) 부분을 완성하세요")


async def handle_validation_error(request, exc):
    """요청 양식 오류(422)를 오류 양식으로 바꾼다. 첫 번째 문제의 위치와 내용을 알려 준다."""
    # TODO (3): 첫 번째 문제의 항목 이름과 내용을 "항목: 내용" 으로 이어 422 invalid_request 로 돌려주세요
    # 1) exc.errors() 의 첫 번째 딕셔너리를 꺼낸다

    # 2) loc 예: ("body", "question"). 마지막 값이 문제가 된 항목 이름이고, 내용은 msg 에 있다
    raise NotImplementedError("core/errors.py 의 TODO (3) 부분을 완성하세요")


async def handle_vllm_timeout(request, exc):
    """vLLM 이 시간 제한 안에 답하지 않으면 504."""
    # TODO (4): 상태 코드 504, 오류 이름 backend_timeout 으로 오류 양식 응답을 돌려주세요
    # 1) error_response 에 다시 시도하라는 안내 문장을 message 로 준다
    raise NotImplementedError("core/errors.py 의 TODO (4) 부분을 완성하세요")


async def handle_vllm_unreachable(request, exc):
    """vLLM 서버에 연결하지 못하면 502."""
    # TODO (5): 상태 코드 502, 오류 이름 backend_unavailable 로 오류 양식 응답을 돌려주세요
    # 1) error_response 에 다시 시도하라는 안내 문장을 message 로 준다
    raise NotImplementedError("core/errors.py 의 TODO (5) 부분을 완성하세요")


async def handle_vllm_status_error(request, exc):
    """vLLM 이 오류 상태 코드로 답하면 502. vLLM 의 상태 코드만 알리고 내부 메시지는 넘기지 않는다."""
    return error_response(502, "backend_error", f"모델 서버가 오류({exc.status_code})로 답했습니다.")


def register_error_handlers(app: FastAPI):
    """앱에 오류 처리 함수를 붙인다. 예외 종류가 겹치면 더 좁은 종류(시간 초과)의 함수가 먼저 쓰인다."""
    # TODO (6): 예외 종류마다 위의 처리 함수를 앱에 붙이세요
    # 1) app.add_exception_handler 로 StarletteHTTPException, RequestValidationError 를 붙인다

    # 2) openai.APITimeoutError 는 504, openai.APIConnectionError 는 502, openai.APIStatusError 는 handle_vllm_status_error 로 붙인다
    return None  # 아직 붙인 처리 함수가 없습니다(TODO (6)을 채우면 이 줄을 지웁니다)
