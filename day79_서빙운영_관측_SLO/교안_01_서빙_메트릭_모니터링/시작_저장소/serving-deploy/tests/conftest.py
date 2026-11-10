"""테스트들이 함께 쓰는 설정과 준비물(교안 03).

SERVING_URL 은 확인할 서버 주소, ADMIN_API_KEY 는 그 서버의 관리자 키다.
CI 의 image 작업이 두 값을 환경 변수로 준다.
"""
import os

import httpx
import pytest

# 확인할 서버 주소와 그 서버의 관리자 키
SERVING_URL = os.environ.get("SERVING_URL", "http://localhost:8080")
ADMIN_API_KEY = os.environ["ADMIN_API_KEY"]


@pytest.fixture(scope="module")
def service_key():
    """관리자 주소로 무료 요금제 서비스 키를 하나 발급받아 돌려준다. 테스트 파일마다 새 키를 받는다."""
    response = httpx.post(
        f"{SERVING_URL}/v1/admin/keys",
        headers={"X-Admin-Key": ADMIN_API_KEY},
        json={"user": "배포 전 테스트", "plan": "free"},
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return response.json()["api_key"]
