"""스트리밍 중계. vLLM 이 보내는 조각을 받아 서빙 API 의 SSE 이벤트로 바꿔 사용자에게 보낸다.

서빙 API 가 보내는 이벤트(한 줄에 하나, 빈 줄로 구분):
    data: {"type": "reasoning", "text": "..."}   생각 조각(think 가 True 일 때만)
    data: {"type": "answer", "text": "..."}      답 조각
    data: {"type": "usage", "prompt_tokens": ..., "cached_tokens": ..., "completion_tokens": ..., "total_tokens": ...}
    data: [DONE]                                 끝
"""
import json


def sse_line(event):
    """이벤트 딕셔너리 하나를 SSE 한 줄("data: ..." + 빈 줄)로 바꿔 돌려준다."""
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


async def relay_stream(stream):
    """vLLM 스트림의 조각을 받는 대로 SSE 이벤트로 바꿔 하나씩 내보낸다(비동기 제너레이터)."""
    async for chunk in stream:
        # 1) 생각 조각과 답 조각: 조각마다 choices 가 하나 들어 있다
        for choice in chunk.choices:
            # 생각은 vLLM 전용 항목이라 model_extra 에 들어 있다
            reasoning = choice.delta.model_extra.get("reasoning")
            if reasoning:
                yield sse_line({"type": "reasoning", "text": reasoning})
            if choice.delta.content:
                yield sse_line({"type": "answer", "text": choice.delta.content})

        # 2) 마지막 조각: choices 가 비어 있고 토큰 사용량만 들어 있다
        if chunk.usage is not None:
            yield sse_line({
                "type": "usage",
                "prompt_tokens": chunk.usage.prompt_tokens,
                "cached_tokens": chunk.usage.prompt_tokens_details.cached_tokens,  # 캐시 적중 토큰
                "completion_tokens": chunk.usage.completion_tokens,
                "total_tokens": chunk.usage.total_tokens,
            })

    # 3) 끝을 알리는 줄(OpenAI, vLLM 과 같은 약속)
    yield "data: [DONE]\n\n"
