"""단위 테스트(과제 02, 제공). 이미지나 서버 없이 코드의 함수와 양식만 확인한다. CI 의 unit 작업이 이미지를 빌드하기 전에 실행한다.

설정(shop_api/core/config.py)은 불러올 때 VLLM_API_KEY 를 꼭 읽으므로, unit 작업이 테스트 전용 값을 env 로 준다.
"""
import pydantic
import pytest

from shop_api.dependencies.security import SERVICE_KEYS
from shop_api.routers.shop_router import make_user_message
from shop_api.schemas.chat import ShopChatRequest

QUESTION = "배송은 주문하고 며칠 뒤에 오나요?"


def test_short_question_is_rejected():
    with pytest.raises(pydantic.ValidationError):
        ShopChatRequest(question="?")


def test_order_id_must_match_pattern():
    with pytest.raises(pydantic.ValidationError):
        ShopChatRequest(question=QUESTION, order_id="123456")
    request = ShopChatRequest(question=QUESTION, order_id="ORD-123456")
    assert request.order_id == "ORD-123456"


def test_user_message_puts_order_id_first():
    with_order = ShopChatRequest(question=QUESTION, order_id="ORD-123456")
    without_order = ShopChatRequest(question=QUESTION)
    assert make_user_message(with_order) == f"[주문번호 ORD-123456] {QUESTION}"
    assert make_user_message(without_order) == QUESTION


def test_plan_limits():
    assert SERVICE_KEYS["plans"]["free"]["requests_per_minute"] == 3
    assert SERVICE_KEYS["plans"]["pro"]["requests_per_minute"] == 30
    assert SERVICE_KEYS["keys"]["shop-pro-demo-0002"]["plan"] == "pro"
