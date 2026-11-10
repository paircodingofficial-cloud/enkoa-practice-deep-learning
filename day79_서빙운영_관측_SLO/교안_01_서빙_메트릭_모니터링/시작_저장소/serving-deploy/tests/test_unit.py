"""단위 테스트(교안 03). 이미지나 서버 없이 서빙 API 코드의 함수와 양식만 확인한다.

CI 의 unit 작업이 이미지를 빌드하기 전에 실행한다. 몇 초면 끝나므로 코드 실수를 빌드 전에 빨리 찾는다.
"""
import pytest
from pydantic import ValidationError

from serving_app.dependencies.security import PLAN_LIMITS
from serving_app.repositories.key_store import hash_key
from serving_app.schemas.chat import ChatRequest


def test_short_question_is_rejected():
    # 질문이 2자보다 짧으면 양식 검사에서 막힌다(서버에서는 422 가 된다)
    with pytest.raises(ValidationError):
        ChatRequest(question="?")


def test_question_is_accepted():
    # 2자 이상이면 통과하고, think 는 기본값 False
    request = ChatRequest(question="주휴수당 조건")
    assert request.think is False


def test_key_is_stored_as_hash():
    # 키 원문 대신 64자리 해시를 저장한다. 같은 키는 늘 같은 해시가 된다
    key = "svc-example"
    assert hash_key(key) == hash_key(key)
    assert len(hash_key(key)) == 64
    assert hash_key(key) != key


def test_plan_limits():
    # 요금제별 60초당 요청 한도
    assert PLAN_LIMITS == {"free": 3, "pro": 30}
