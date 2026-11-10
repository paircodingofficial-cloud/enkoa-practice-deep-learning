"""서빙 API 설정. 배포(로컬, RunPod, Docker)마다 달라질 수 있는 값을 Settings 클래스 하나에 모은다.

주소 앞부분이나 SSE 이벤트 이름처럼 어디서 띄워도 같은 앱 동작은 각 파일의 코드에 두고, 띄우는 곳이나 쓰는 모델에 따라
바뀔 수 있는 값(vLLM 주소와 키, 모델 이름, 생성 상한과 샘플링 값, 파일 위치)은 모두 여기에 둔다.

설정은 pydantic-settings 의 BaseSettings 로 읽는다. FastAPI 공식 문서(Settings and Environment Variables)도 이 방법을 권한다.
코드에 값을 적지 않고 환경 변수로 받으면, 배포할 때 코드는 그대로 두고 값만 바꿀 수 있다. BaseSettings 를 쓰면 다음이 편해진다.
- 어떤 설정이 있고 기본값이 무엇인지 클래스 하나에 모여 한눈에 보인다.
- 적어 둔 타입대로 값을 바꾸고 검사한다. 값이 틀리거나(VLLM_TIMEOUT_SECONDS=abc) 꼭 필요한 값이 없으면,
  요청을 받기 전에 서버가 뜨면서 어떤 이름이 문제인지 알려 준다.
- 셸이나 Docker 에서 준 환경 변수가 .env 의 값보다 먼저 쓰인다.
"""
from pathlib import Path

from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 시스템 메시지에 붙일 참고 조문이 든 폴더(이 패키지 안의 resources)
RESOURCE_DIR = Path(__file__).resolve().parent.parent / "resources"


class Settings(BaseSettings):
    """환경 변수에서 읽는 설정. 필드 이름을 대문자로 쓴 것이 환경 변수 이름이다(vllm_base_url -> VLLM_BASE_URL)."""

    # 이 클래스는 이름, 타입, 기본값을 적어 둔 설계도다. 클래스를 정의할 때는 아무 값도 읽지 않는다.
    # 맨 아래 settings = Settings() 가 실행될 때 필드마다 환경 변수 -> .env -> 기본값 순서로 찾아 처음 찾은 값을 넣는다.
    # 그래서 "= 값" 은 다른 곳에 값이 없을 때만 쓰는 기본값이고, 줄의 순서와 상관없이 환경 변수가 먼저 쓰인다.
    # 환경 변수 이름은 대소문자를 구분하지 않는다(case_sensitive 의 기본값이 False). 소문자 필드 vllm_base_url 을 VLLM_BASE_URL 이 채운다.

    # 서버를 실행한 폴더에서 위로 올라가며 찾은 .env(실습자료/.env)도 읽는다. .env 의 다른 키는 무시한다(extra="ignore").
    # 값이 틀려 서버가 멈출 때 오류 메시지에 입력값을 찍지 않는다(hide_input_in_errors). 키가 로그에 남지 않게 한다
    model_config = SettingsConfigDict(
        env_file=find_dotenv(usecwd=True) or None,
        extra="ignore",
        hide_input_in_errors=True,
    )

    # vLLM 서버 주소. 같은 파드에서는 127.0.0.1:8000, 배포 단원에서는 다른 파드의 주소로 바꾼다
    vllm_base_url: str = "http://127.0.0.1:8000/v1"

    # vLLM 서버를 --api-key 로 띄울 때 쓴 키. 기본값이 없으므로 반드시 정해야 한다(사용자에게는 알려 주지 않는다)
    vllm_api_key: str

    # vLLM 의 --served-model-name
    served_name: str = "qwen3.5-4b"

    # vLLM 응답을 기다리는 최대 시간(초). 넘기면 시간 초과 오류가 난다
    vllm_timeout_seconds: float = 120

    # 생각을 끈 요청의 생성 상한(서빙 벤치마킹 단원과 같은 값). Field(gt=0) 는 0 이하의 값을 서버가 뜰 때 막는다
    max_tokens: int = Field(256, gt=0)

    # 생각을 켠 요청의 생성 상한. 생각도 출력 토큰을 쓰고, 생각이 상한을 다 쓰면 답이 비므로 더 크게 둔다
    # 입력 토큰 수와 이 상한의 합이 vLLM 의 --max-model-len(8192)을 넘으면 vLLM 이 요청을 거절(400)하므로,
    # 전월세 500자 질문의 가장 긴 입력 3,716토큰(글자마다 최대 4토큰)이 들어가도록 8192 - 3716 = 4476 보다 작게 둔다.
    # --max-model-len 이나 모델을 바꾸면 이 값도 함께 다시 계산한다
    max_tokens_think: int = Field(4400, gt=0)

    # 시스템 메시지가 긴 노무 창구(입력 약 5,000토큰)의 생각 상한. max_tokens_think 를 주면 합이 8192 를 넘으므로 줄여 둔다
    max_tokens_think_labor: int = Field(2048, gt=0)

    # 생각을 켠 요청의 샘플링 값(Qwen3.5 모델 카드의 생각 모드 권장값). 모델을 바꾸면 그 모델의 권장값으로 바꾼다
    # temperature=0 이면 이 모델은 생각을 되풀이하다 상한에 닿는다
    think_temperature: float = Field(1.0, ge=0)
    think_top_p: float = Field(0.95, gt=0, le=1)
    think_top_k: int = Field(20, gt=0)
    think_presence_penalty: float = Field(1.5, ge=-2, le=2)

    # 서비스 키와 사용량을 저장할 SQLite 파일. 서버를 실행한 폴더 기준 상대 경로이고, 배포할 때는 환경 변수로 바꾼다
    service_db_path: Path = Path("output/service.db")

    # 관리자 키. 관리자 주소를 여는 앱만 쓰므로 기본값은 None 이고, 그 앱이 없으면 멈춘다
    admin_api_key: str | None = None

    # 예비 모델(OpenAI)의 키. 예비 모델을 쓰는 앱만 쓰므로 기본값은 None 이고, 그 앱이 없으면 멈춘다
    openai_api_key: str | None = None


# 여기서 값을 읽는다. 서버가 뜰 때 한 번만 읽으므로, 값을 바꾸려면 서버를 다시 띄운다. 모든 모듈이 이 settings 를 같이 쓴다
settings = Settings()
