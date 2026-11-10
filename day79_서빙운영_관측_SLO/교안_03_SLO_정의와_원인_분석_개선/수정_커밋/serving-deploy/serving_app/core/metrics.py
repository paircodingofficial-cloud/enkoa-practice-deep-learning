"""서빙 API 의 메트릭(관측 단원 교안 01). 상담 요청 수, 걸린 시간, 출력 토큰 수를 세어 /metrics 로 내보낸다.

prometheus_client 가 숫자를 메모리에 세어 두고, /metrics 를 부르면 그 숫자를 Prometheus 텍스트 형식으로 돌려준다.
vLLM 의 /metrics 와 같은 형식이라 같은 방법으로 읽는다.
"""
import time

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, disable_created_metrics, generate_latest

from ..dependencies.security import require_admin

# 걸린 시간을 측정하는 상담 주소. 아무 주소나 세면 없는 주소로 보낸 요청마다 줄이 늘어나므로, 정해 둔 주소만 센다
# 스트리밍 주소는 첫 조각이 나갈 때 응답이 시작되어 전체 시간을 측정할 수 없으므로 넣지 않는다
CHAT_PATHS = ["/v1/labor/chat", "/v1/lease/chat"]

# Counter, Histogram, Summary 는 _created 보조 메트릭도 내보낼 수 있습니다.
# _created 의 숫자는 메트릭을 만든 Unix 시각이며 요청 수가 아닙니다. 이 실습에서는 쓰지 않아 내보내지 않습니다.
disable_created_metrics()

# 카운터: 늘어나기만 하는 수. /metrics 에는 이름 뒤에 _total 이 붙어 나간다
REQUESTS = Counter("serving_requests", "상담 주소가 돌려준 응답 수", ["path", "status"])

# Histogram 은 요청 시간을 정한 경계별 누적 건수로 기록합니다.
# buckets 는 초 단위 상한 목록이며, 15를 넣으면 15초 이하 요청 수를 셀 수 있습니다.
REQUEST_SECONDS = Histogram(
    "serving_request_seconds",
    "상담 요청 하나를 받아 응답하기까지 걸린 시간(초)",
    ["path"],
    buckets=[0.5, 1, 2.5, 5, 10, 15, 20, 30, 60, 90],
)

# 창구별 출력 토큰 수(GPU 가 만든 토큰). 상담 엔드포인트가 답을 받은 뒤 더한다
OUTPUT_TOKENS = Counter("serving_output_tokens", "창구별 출력 토큰 수", ["desk"])

metrics_router = APIRouter(tags=["관측"])


# GET /metrics 주소를 등록하고, Depends(require_admin) 이 관리자 키를 확인합니다.
@metrics_router.get("/metrics", dependencies=[Depends(require_admin)])
def metrics():
    """관리자 키를 확인한 뒤, 현재 등록된 메트릭을 Prometheus 텍스트로 돌려줍니다."""
    # generate_latest() 는 등록된 메트릭을 모아 Prometheus 텍스트 본문으로 만듭니다.
    metrics_text = generate_latest()
    # Response 는 HTTP 응답을 만듭니다. content 는 본문, media_type 은 본문 형식을 알리는 Content-Type 헤더입니다.
    return Response(content=metrics_text, media_type=CONTENT_TYPE_LATEST)


async def record_chat_request(request, call_next):
    """모든 HTTP 요청을 다음 처리 단계로 넘기고, 상담 주소면 처리 시간과 응답 상태를 기록합니다."""
    # request.url.path 는 호스트와 쿼리를 뺀 경로입니다. 측정 대상이 아니면 다음 처리 단계로 넘깁니다.
    path = request.url.path
    if path not in CHAT_PATHS:
        # call_next(request) 가 요청을 나머지 앱으로 보내고, 그 앱의 응답을 돌려줍니다.
        return await call_next(request)

    # time.perf_counter() 값을 응답 전후로 빼 요청 처리에 걸린 초를 구합니다.
    started = time.perf_counter()
    # call_next(request) 가 요청을 인증·제한·상담 처리기로 보내고, 만들어진 응답을 돌려줍니다.
    response = await call_next(request)
    elapsed_seconds = time.perf_counter() - started
    # labels(path=...) 는 이 주소의 히스토그램을 고르고, observe(...) 는 걸린 초를 기록합니다.
    REQUEST_SECONDS.labels(path=path).observe(elapsed_seconds)
    # labels(path, status) 는 주소와 상태 코드별 카운터를 고르고, inc() 는 완료 요청 하나를 더합니다.
    REQUESTS.labels(path=path, status=str(response.status_code)).inc()
    return response
