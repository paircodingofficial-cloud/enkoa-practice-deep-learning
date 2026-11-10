"""vLLM 백엔드 연결. 같은 파드(또는 배포된 다른 파드)의 vLLM 에 OpenAI 호환 방식으로 요청한다."""
import json

from openai import AsyncOpenAI

from ..core.config import RESOURCE_DIR, settings
from ..schemas.chat import ChatResponse, Usage

# 비동기 클라이언트는 이 파일을 불러올 때 하나만 만들어 모든 요청이 함께 쓴다(요청마다 만들면 연결 준비를 반복한다)
# 만들 때는 연결을 열지 않는다. 첫 요청 때 연 연결을 연결풀에 두고 재사용하다가, 앱 조립 파일의 lifespan 이 종료 때 닫는다
# max_retries=0: 실패를 숨기지 않고 바로 오류로 받는다(다시 시도할지는 서빙 API 가 정한다)
vllm_client = AsyncOpenAI(
    base_url=settings.vllm_base_url,
    api_key=settings.vllm_api_key,
    timeout=settings.vllm_timeout_seconds,  # vLLM 응답을 기다리는 최대 시간(VLLM_TIMEOUT_SECONDS, 기본 120초)
    max_retries=0,
)


def make_system_prompt(instruction, reference_file):
    """지침 문장 뒤에 참고 조문을 붙인 시스템 메시지를 돌려준다(서빙 벤치마킹 단원과 같은 구성)."""
    with open(RESOURCE_DIR / reference_file, encoding="utf-8") as f:
        reference = json.load(f)

    # 시스템 메시지 = 지침 문장 + 빈 줄 + [참고 조문] + 조문들(한 줄에 조문 하나)
    articles = []
    for article in reference["articles"]:
        articles.append(article["text"])
    return instruction + "\n\n[참고 조문]\n" + "\n".join(articles)


def build_request(system_prompt, question, think, max_tokens_think=settings.max_tokens_think):
    """vLLM chat completions 요청에 넣을 인자를 딕셔너리로 돌려준다."""
    # 생각을 끈 요청: 생성 상한 settings.max_tokens, temperature=0(같은 질문에 같은 답)
    request = {
        "model": settings.served_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "max_tokens": settings.max_tokens,
        "temperature": 0,
        # vLLM 전용 인자: 이 요청에서 Qwen3.5 의 생각을 켜거나 끈다. 서버 기본값과 상관없이 요청마다 정한다
        "extra_body": {"chat_template_kwargs": {"enable_thinking": think}},
    }

    # 생각을 켠 요청: 생각도 출력 토큰을 쓰므로 생성 상한을 키우고(시스템 메시지가 긴 창구는 더 작은 값을 넘긴다),
    # 샘플링은 모델 카드 권장값으로 바꾼다(temperature=0 이면 같은 생각을 되풀이하다 상한에 닿는다. 대신 답이 실행마다 달라진다)
    if think:
        request["max_tokens"] = max_tokens_think
        request["temperature"] = settings.think_temperature
        request["top_p"] = settings.think_top_p
        request["presence_penalty"] = settings.think_presence_penalty
        # top_k 는 OpenAI 표준 인자가 아니라 vLLM 전용이므로 extra_body 에 넣는다
        request["extra_body"]["top_k"] = settings.think_top_k
    return request


async def ask_vllm(system_prompt, question, think, max_tokens_think=settings.max_tokens_think):
    """vLLM 에 질문 하나를 보내고 완성된 응답(ChatCompletion)을 돌려준다."""
    return await vllm_client.chat.completions.create(**build_request(system_prompt, question, think, max_tokens_think))


async def open_vllm_stream(system_prompt, question, think, max_tokens_think=settings.max_tokens_think):
    """vLLM 에 스트리밍 요청을 보내고, 조각을 하나씩 꺼낼 수 있는 스트림을 돌려준다."""
    return await vllm_client.chat.completions.create(
        **build_request(system_prompt, question, think, max_tokens_think),
        stream=True,  # vLLM 이 조각을 만들어지는 대로 하나씩 보낸다
        # 마지막에 토큰 사용량만 담은 조각을 하나 더 받는다
        stream_options={"include_usage": True},
    )


def to_chat_response(completion):
    """vLLM 응답(ChatCompletion)을 서빙 API 의 응답 양식(ChatResponse)으로 바꿔 돌려준다."""
    choice = completion.choices[0]

    # 생각은 OpenAI 표준에 없는 vLLM 전용 항목이라 model_extra 에 들어 있다(생각을 끄면 None)
    reasoning = choice.message.model_extra.get("reasoning")

    return ChatResponse(
        answer=choice.message.content,
        reasoning=reasoning,
        finish_reason=choice.finish_reason,
        model=completion.model,
        usage=Usage(
            prompt_tokens=completion.usage.prompt_tokens,
            # 서버 명령의 --enable-prompt-tokens-details 가 prompt_tokens_details 를 응답에 넣는다
            cached_tokens=completion.usage.prompt_tokens_details.cached_tokens,
            completion_tokens=completion.usage.completion_tokens,
            total_tokens=completion.usage.total_tokens,
        ),
    )
