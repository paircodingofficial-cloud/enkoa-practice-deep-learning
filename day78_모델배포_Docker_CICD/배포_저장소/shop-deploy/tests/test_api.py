"""배포 전 테스트(과제 02, 제공). 컨테이너로 띄운 온라인 쇼핑 상담 API 에 실제 HTTP 요청을 보내 확인한다.

CI 에는 vLLM 이 없어서 상담 요청은 502(backend_unavailable)가 정상이다. 서비스 키는 이미지에 든 연습용 키를 쓴다.
"""
import os

import httpx

# 확인할 서버 주소(CI 의 image 작업은 http://localhost:8080 을 준다)
SERVING_URL = os.environ.get("SERVING_URL", "http://localhost:8080")

# shop_api/resources/service_keys.json 의 pro 요금제 연습용 키(60초에 30번)
PRO_KEY = "shop-pro-demo-0002"
QUESTION = {"question": "단순 변심으로 산 옷을 반품하려면 언제까지 신청해야 하나요?"}


def test_healthz_is_open():
    response = httpx.get(f"{SERVING_URL}/healthz", timeout=10)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_without_key_is_401():
    response = httpx.post(f"{SERVING_URL}/v1/shop/chat", json=QUESTION, timeout=10)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_service_key"


def test_short_question_is_422():
    response = httpx.post(
        f"{SERVING_URL}/v1/shop/chat", headers={"X-API-Key": PRO_KEY}, json={"question": "?"}, timeout=10
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"


def test_chat_reaches_backend():
    response = httpx.post(
        f"{SERVING_URL}/v1/shop/chat", headers={"X-API-Key": PRO_KEY}, json=QUESTION, timeout=30
    )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "backend_unavailable"
