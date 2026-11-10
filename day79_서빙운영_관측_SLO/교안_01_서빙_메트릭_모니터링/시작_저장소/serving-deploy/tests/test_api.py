"""배포 전 테스트(교안 03). 컨테이너로 띄운 서빙 API 에 실제 HTTP 요청을 보내 확인한다.

CI 에는 vLLM 이 없어서 상담 요청은 502(backend_unavailable)가 정상이다. 가짜 모델을 쓰지 않는다.
무료 키는 60초에 3번이라, 한도를 쓰는 요청(양식 오류, 상담)은 이 파일에서 두 번만 보낸다.
"""
import os

import httpx

# 확인할 서버 주소(CI 의 image 작업은 http://localhost:8080 을 준다)
SERVING_URL = os.environ.get("SERVING_URL", "http://localhost:8080")

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
