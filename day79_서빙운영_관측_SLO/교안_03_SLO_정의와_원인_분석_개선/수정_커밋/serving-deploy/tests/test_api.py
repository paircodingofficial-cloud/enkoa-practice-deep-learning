"""배포 전 테스트(교안 03). 컨테이너로 띄운 서빙 API 에 실제 HTTP 요청을 보내 확인한다.

CI 에는 vLLM 이 없어서 상담 요청은 502(backend_unavailable)가 정상이다. 가짜 모델을 쓰지 않는다.
무료 키는 60초에 3번이라, 한도를 쓰는 요청(양식 오류, 상담)은 이 파일에서 두 번만 보낸다.
"""
import os

import httpx

# 확인할 서버 주소(CI 의 image 작업은 http://localhost:8080 을 준다)
SERVING_URL = os.environ.get("SERVING_URL", "http://localhost:8080")
ADMIN_API_KEY = os.environ["ADMIN_API_KEY"]                       # 관측 단원: /metrics 를 여는 관리자 키(CI 의 image 작업이 준다)

QUESTION = {"question": "주휴수당은 어떤 조건에서 받을 수 있나요?"}


def test_healthz_is_open():
    # 상태 확인 주소는 키 없이 200 과 {"status": "ok"}
    response = httpx.get(f"{SERVING_URL}/healthz", timeout=10)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_without_key_is_401():
    # 서비스 키가 없으면 vLLM 에 가기 전에 401
    response = httpx.post(f"{SERVING_URL}/v1/labor/chat", json=QUESTION, timeout=10)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_service_key"


def test_short_question_is_422(service_key):
    # 질문이 2자보다 짧으면 양식 오류 422
    response = httpx.post(
        f"{SERVING_URL}/v1/labor/chat", headers={"X-API-Key": service_key}, json={"question": "?"}, timeout=10
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_chat_reaches_backend(service_key):
    # 키와 양식이 맞으면 vLLM 을 부른다. CI 에서는 vLLM 이 없으므로 502 로 돌아와야 한다
    response = httpx.post(
        f"{SERVING_URL}/v1/labor/chat", headers={"X-API-Key": service_key}, json=QUESTION, timeout=30
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "backend_unavailable"


# 관측 단원 교안 01: 메트릭 주소 테스트 두 개
def test_metrics_needs_admin_key():
    # 관리자 키 없이 /metrics 를 부르면 403
    response = httpx.get(f"{SERVING_URL}/metrics", timeout=10)
    assert response.status_code == 403


def test_chat_is_counted():
    # 키 없는 상담 요청(401)도 미들웨어가 세므로, /metrics 에 그 상태 코드로 센 줄과 15초 경계 칸이 있어야 한다
    httpx.post(f"{SERVING_URL}/v1/labor/chat", json=QUESTION, timeout=10)
    response = httpx.get(f"{SERVING_URL}/metrics", headers={"X-Admin-Key": ADMIN_API_KEY}, timeout=10)
    assert response.status_code == 200
    assert 'serving_requests_total{path="/v1/labor/chat",status="401"}' in response.text
    assert 'serving_request_seconds_bucket{le="15.0",path="/v1/labor/chat"}' in response.text
