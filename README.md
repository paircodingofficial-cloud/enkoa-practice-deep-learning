# 딥러닝 실습자료

엔코아 AI캠퍼스 「데이터 분석 & AI 머신러닝 캠프」 딥러닝 과목 실습용 주피터 노트북입니다. 수업 진도에 맞춰 자료가 추가됩니다.

### 수록 자료

| 일차 | 주제 | 배우는 것 |
|---|---|---|
| **day65** | 딥러닝 학습 원리 | 모델이 학습하는 반복(예측, 손실 계산, 기울기 계산, 파라미터 갱신)을 PyTorch로 직접 돌려 봅니다. 교안 01은 직선 모델 하나로 **손실함수(MSE·MAE)·autograd·경사하강·학습률**을, 교안 02는 손글씨 숫자를 분류하는 **DNN**으로 교차 엔트로피, `DataLoader` 미니배치 학습 루프, SGD·모멘텀·Adam·AdamW, warmup + cosine 스케줄러를 다룹니다. 과제는 타이타닉 생존 예측과 날짜로 요일 맞히기입니다. 부록은 딥러닝과 지도·비지도·강화학습, 생성형 AI의 개념과 사례(알파고, 플루토, 로봇 제어)입니다 |
| **day66** | PyTorch 신경망 | 교안 01은 손글씨 숫자를 분류하는 **CNN**(합성곱, 파라미터 공유, 풀링, 수용 영역, 필터와 특징 맵)과 깊은 CNN을 위한 **배치 정규화·잔차 연결·ResNet**을, 교안 02는 데이터 누수를 막는 분할로 **과적합**을 진단하고 Dropout·가중치 감쇠·데이터 증강·조기 종료로 줄인 뒤 **PyTorch Lightning**으로 학습 코드를 정리합니다(기울기 자르기, 체크포인트로 이어 학습, 하이퍼파라미터 탐색). 과제는 낙서 10종 분류 CNN과 가위바위보 손 그림의 과적합과 규제입니다. 부록은 GAN으로 손글씨 숫자 만들기입니다 |
| **day67** | 트랜스포머 아키텍처 | 교안 01은 영화 리뷰(NSMC) 감성 분석을 따라가며 토큰화, 어휘 사전, 패딩, 토큰 임베딩에서 시작해 **어텐션**, 위치 인코딩, `nn.MultiheadAttention`과 패딩 마스크, LayerNorm을 거쳐 **트랜스포머 인코더**(`nn.TransformerEncoder`)를 쌓고 [CLS] 벡터로 분류합니다. 함께 따라하기는 숫자 20개 가운데 k번째로 큰 숫자의 위치를 찾는 순위 맞히기 게임입니다. 교안 02는 노트북이 아닌 .py 프로젝트로, 어텐션, Multi-Head Attention, LayerNorm, FFN, 인코더 블록을 **직접 구현**해 네이버 쇼핑 리뷰 감성 분석을 PyTorch Lightning으로 학습합니다. 과제는 문장 의도 7종 분류입니다. 부록은 행렬 연산과 텐서 모양(transpose, reshape, softmax, squeeze)입니다 |
| **day68** | 오픈소스 LLM 로컬 실행 | 교안 01은 오픈 웨이트 LLM 지형(개발 주체, 크기, MoE, 추론 모드)과 벤치마크·라이선스로 사내 헬프데스크에 쓸 모델(**Qwen3.5-4B**)을 고르고, **Ollama**(대화, 추론 모드)와 LangChain `ChatOllama`(구조화된 출력, 도구 호출), **Hugging Face Transformers**(chat template, 생성 설정)로 GPU에서 직접 실행합니다. 교안 02는 모델 메모리를 계산하고 FP32·BF16·INT8·4비트 **양자화**와 AWQ·GPTQ·GGUF를 비교한 뒤 Ollama 양자화 태그(Q8_0·Q4_K_M)를 크기·속도·답으로 고릅니다. 과제는 온라인 서점 상담 모델 고르고 실행하기와 택배 배송 문의 모델의 장비·양자화 형식 정하기입니다. Ollama 프로그램은 단원 폴더의 `설치_가이드.md`대로 따로 설치합니다 |
| **day69** | 파인튜닝 데이터셋 | 노무 상담 챗봇을 파인튜닝할 데이터셋을 만듭니다. 교안 01은 노동법 408문단 가운데 382문단에서 LangChain 체인으로 Q&A를 만들고, 답의 숫자를 조문과 대조해 검수합니다. 행이 적은 주제는 질문을 늘리고, 하이브리드 검색(BM25 + 의미 검색)과 Cross-Encoder 재정렬로 찾은 조문으로 답을 만들며, 범위 밖 질문에는 거절 답을 붙입니다. 교안 02는 패러프레이즈·역번역 **증강**, 품질 필터 네 단계, 평가 질문과의 **오염 검사**, 주제 상한으로 균형을 맞추고, Qwen3.5-0.8B의 **chat template 정합**과 토큰 길이를 확인한 뒤 원본 단위로 학습/검증을 나누고 데이터 카드를 씁니다. 과제는 온라인 쇼핑 상담 Q&A 만들기와 다듬기입니다. 부록은 로컬 LLM(Gemma 4)으로 같은 데이터를 만들어 API 모델과 비교합니다. 단원 폴더의 `.env.example` 을 `.env` 로 복사해 OpenAI API 키를 넣습니다(호출 비용이 듭니다) |
| **day70** | SFT 지도 파인튜닝 | 지난 시간에 만든 노무 상담 데이터로 Qwen3.5-0.8B를 **SFTTrainer**로 파인튜닝합니다. 교안 01은 prompt·completion 데이터셋, 토큰 길이와 `max_length`, 답변 토큰만 손실(labels -100)을 학습 전에 점검하고, 학습률(2e-5·5e-6)을 비교한 뒤 에폭을 늘려 **에폭별 체크포인트**를 저장합니다(학습 기록은 MLflow). 교안 02는 Jev 판사로 Base와 체크포인트의 학습 데이터 정답률·도메인 정답률·범위 밖 거절률을 채점하고, 일반 질문과 perplexity로 **일반 능력 퇴행**을 점검해 서비스에 쓸 모델을 고른 뒤 퇴행 줄이기 방법과 **가중치 보간**(α 0.5·0.75)을 실습합니다. 함께 따라하기는 전월세 상담 모델입니다. 과제는 온라인 쇼핑 상담 모델 학습과 평가입니다. GPU 메모리 24GB 이상 파드에서 실행하고, 단원 폴더의 `.env.example` 을 `.env` 로 복사해 Jev 키(`TYPESAFE_API_KEY`)를 넣습니다 |
| **day71** | PEFT·LoRA | 지난 시간과 같은 Qwen3.5-0.8B와 노무 상담 데이터로, 이번에는 베이스 가중치를 고정하고 **LoRA 어댑터**만 학습합니다. 교안 01은 $W$ 옆에 붙는 두 행렬 $B$, $A$와 `r`·`lora_alpha`·`target_modules`를 `LoraConfig`로 정하고 `get_peft_model`로 어댑터를 붙여, 같은 `SFTTrainer`로 lr 2e-4 4에폭 학습하며 에폭마다 어댑터를 저장합니다(어댑터 끄기 `disable_adapter`, 다시 불러오기 `PeftModel.from_pretrained`). 교안 02는 에폭별 어댑터 4개를 베이스 모델 하나에 얹어(`load_adapter`·`set_adapter`) 지난 시간과 같은 Jev 판사 지표로 고르고, **지난 시간 풀 파인튜닝과 비교**한 뒤 r 32·MLP만·**DoRA** 설정을 비교하고 쓸 어댑터를 `merge_and_unload`로 **병합**합니다. 함께 따라하기는 전월세 상담 어댑터와 어댑터 바꿔 끼우기입니다. 과제는 온라인 쇼핑 상담 어댑터 학습과 평가·병합입니다. 부록은 Hugging Face 허브에 어댑터와 데이터셋 올리기(Hugging Face 토큰 필요), 이미지 생성 모델 FLUX.2 [klein] 4B에 LoRA로 캐릭터 학습시키기(모델 약 16GB 내려받음)입니다. GPU 메모리 24GB 이상 파드에서 실행하고, 단원 폴더의 `.env.example` 을 `.env` 로 복사해 Jev 키(`TYPESAFE_API_KEY`)를 넣습니다 |
| **day72** | QLoRA 양자화 튜닝 | 지난 시간과 같은 Qwen3.5-0.8B, 노무 상담 데이터, LoRA 설정으로, 이번에는 베이스 모델을 **4비트(NF4)**로 불러와 어댑터를 학습합니다(**QLoRA**). 교안 01은 학습 메모리 네 가지(가중치, 기울기, 옵티마이저 상태, 활성값)와 블록별 absmax·NF4·이중 양자화를 실제 가중치로 계산하고, `BitsAndBytesConfig`로 4비트로 불러온 뒤 학습 한 번의 최대 할당 메모리를 측정해 그래디언트 체크포인팅, 배치·길이, 기울기 누적, 8비트 옵티마이저로 줄이고 24GB GPU에서 9B 모델을 학습할 설정을 고릅니다. 교안 02는 4비트 Base에 어댑터를 lr 2e-4로 4에폭 학습하고, 에폭별 어댑터를 지난 시간과 같은 Jev 판사 지표로 골라 **LoRA·풀 파인튜닝과 비교**한 뒤 원래 정밀도 베이스에 **병합**합니다. 함께 따라하기는 전월세 상담 학습 설정 고르기와 QLoRA 어댑터 학습입니다. 과제는 온라인 쇼핑 상담 모델의 4비트 불러오기와 메모리 최적화, QLoRA 학습과 평가입니다. 부록은 이미지 생성 모델 FLUX.2 [klein] 4B의 트랜스포머를 4비트로 불러와 LoRA 학습하기, Jev 1.14 이미지 입력(GPU 없이 실행)입니다. GPU 메모리 24GB 이상 파드에서 실행하고, 단원 폴더의 `.env.example` 을 `.env` 로 복사해 Jev 키(`TYPESAFE_API_KEY`)를 넣습니다 |
| **day73** | DPO 선호 정렬 | 노무 상담 SFT 모델이 범위 밖 질문에 답을 지어 내는 문제를 **DPO**로 고칩니다. 교안 01은 선호 쌍(`prompt`·`chosen`·`rejected`), 참조 모델·보상·margin·beta와 DPO 손실(chosen의 SFT 손실 포함)을 배우고, SFT 모델이 실제로 낸 답으로 범위 밖 쌍과 노무 질문 쌍을 만들어 LoRA 어댑터를 beta 0.1·0.5로 3에폭씩 학습합니다. 교안 02는 에폭별 어댑터 6개를 지난 시간의 지표에 안전 응답률을 더한 여덟 개로 채점해 미리 정한 규칙으로 정렬 모델을 고르고, 같은 질문의 정렬 전후 답, 답 길이, 경계 질문으로 퇴행(정렬 세금)을 다시 점검한 뒤 IPO·ORPO·KTO·GRPO와 비교합니다. 함께 따라하기는 전월세 상담 모델 정렬과 평가, 과제는 온라인 쇼핑 상담 모델의 DPO 학습과 정렬 평가입니다. GPU 메모리 24GB 이상 파드에서 실행하고, 교안 02·과제 02는 단원 폴더의 `.env.example` 을 `.env` 로 복사해 Jev 키(`TYPESAFE_API_KEY`)를 넣습니다 |
| **day77** | FastAPI 모델 서빙 API | 교안 00은 내 PC에서 FastAPI 기초(엔드포인트, 요청·응답 스키마, async, 스트리밍, lifespan)를 .py 파일로 띄워 봅니다. 교안 01은 같은 파드의 vLLM(Qwen3.5-4B) 앞에 **FastAPI 서빙 API**를 만들어 노무·전월세 상담 창구, 요청·응답 스키마, SSE 스트리밍 중계를, 교안 02는 **서비스 키 인증·요금제별 요청 한도·오류 응답 양식**을, 교안 03은 SQLite로 **서비스 키 발급·폐기와 키별 사용량 기록**을 다룹니다. 과제는 온라인 쇼핑 상담 API 만들기와 보호하기입니다. GPU 파드에서 vLLM 서버(터미널 1)와 FastAPI 서버(터미널 2)를 띄워 실행합니다 |
| **day78** | 모델 배포: Docker와 CI/CD | 교안 00은 내 PC에서 **Docker** 기초(가상화와 컨테이너, 이미지, Dockerfile, 레이어 캐시)를, 교안 01은 지난 시간의 서빙 API를 **이미지로 빌드**해 GitHub Actions로 **GHCR**에 올리는 과정을 다룹니다. 교안 02는 **RunPod GPU 파드**의 vLLM(Qwen3.5-4B)과 **GCP VM**의 서빙 API를 docker compose로 잇습니다(필요한 GPU 메모리 계산, 이름 있는 볼륨). 교안 03은 GitHub Actions로 **CI/CD**를 만듭니다. `ci.yml`은 단위 테스트, 이미지 빌드, 이미지 테스트를 거쳐 통과한 이미지만 올리고, `cd.yml`은 ci가 성공한 커밋만 SSH로 VM에 배포합니다. 과제는 온라인 쇼핑 상담 API의 이미지 배포와 자동 배포입니다. 부록 01대로 GCP VM(무료 e2-micro)을 먼저 만들고, `배포_저장소/`의 템플릿을 홈 폴더로 복사해 내 GitHub 저장소로 씁니다 |

---

## 실습 환경: RunPod GPU + VS Code

이 과목은 RunPod GPU 서버(파드)에 VS Code로 접속해 실습합니다. SSH 키 만들기, 파드 만들기, VS Code 연결, 정지와 종료는 [day65 부록: RunPod GPU에서 실습하기](day65_딥러닝_학습원리/부록_RunPod_GPU에서_실습하기.ipynb)에 화면과 함께 있습니다.

VS Code로 파드에 접속한 뒤 터미널에 아래 한 줄을 붙여 넣습니다. 저장소가 없으면 복제하고, 있으면 최신 자료로 맞춘 뒤 환경을 만듭니다. 파드를 새로 켤 때마다 같은 한 줄이면 됩니다. RunPod PyTorch 템플릿에는 git·curl·uv가 들어 있습니다.

```bash
cd /workspace && { [ -d enkoa-practice-deep-learning ] || git clone https://github.com/paircodingofficial-cloud/enkoa-practice-deep-learning.git; } && cd enkoa-practice-deep-learning && uv run 업데이트.py
```

`uv run 업데이트.py` 가 하는 일:

1. 최신 자료 받기: 서버의 최신 판으로 맞춥니다. 원본을 고쳐 둔 파일은 먼저 `.백업/` 에 보관합니다.
2. 패키지 설치: `uv sync` 로 `pyproject.toml`·`uv.lock` 그대로 설치합니다(PyTorch CUDA 12.8 빌드 포함).
3. 한글 글꼴: 저장소의 나눔고딕(`fonts/`)을 `~/.fonts` 에 복사하고 matplotlib 글꼴 목록 캐시를 지웁니다(apt 설치를 기다리지 않습니다).
4. Jupyter 커널: `.venv` 를 Jupyter 커널 **venv** 로 등록합니다.
5. VS Code 확장: VS Code 터미널에서 실행했다면 Python·Jupyter·Code Class Live Sharing 확장을 파드에 설치합니다.

내 PC(Windows·macOS)에서도 저장소 폴더에서 `uv run 업데이트.py` 를 실행하면 1·2단계(최신 자료 받기, 패키지 설치)를 합니다. 3~5단계는 RunPod 에서만 하고 내 PC에서는 건너뜁니다. Windows 에서 `uv sync` 가 실패하면 열려 있는 노트북과 VS Code 를 닫고 다시 실행합니다.

예전에 받은 저장소에서 "이 도우미는 RunPod(리눅스)에서만 실행합니다"가 나오면, 저장소 폴더에서 아래 두 줄로 새 도우미를 한 번 받은 뒤 `uv run 업데이트.py` 를 다시 실행합니다.

```bash
git fetch origin
git checkout origin/main -- 업데이트.py
```

`git`·`uv` 가 없다는 오류가 나면 먼저 설치합니다.

```bash
apt-get update && apt-get install -y git curl
curl -LsSf https://astral.sh/uv/install.sh | sh && source $HOME/.local/bin/env
```

노트북 커널은 저장소의 **.venv (Python 3.12)** 를 고릅니다. 내 PC(CPU)에서 열어 볼 때도 저장소 폴더에서 `uv sync` 한 뒤 같은 `.venv` 를 고르면 됩니다.

브라우저의 Jupyter Lab으로 열려면 저장소 폴더에서 `uv run jupyter lab` 을 실행하고 커널로 **venv** 를 고릅니다(Jupyter는 `uv sync` 때 함께 설치됩니다).

---

## ⚠️ 꼭 기억하세요

> ### 볼륨 없이 만든 파드는 **정지하면 파일이 모두 지워집니다.**
> ### 실습 결과는 끝내기 전에 **내려받으세요.**

- 파드를 새로 켜면 위의 한 줄 명령을 다시 실행합니다.
- 새 자료가 올라오면 저장소 폴더에서 `uv run 업데이트.py` 를 다시 실행합니다(내 PC에서도 같습니다). `git pull` 이 충돌로 막혔을 때도 이 명령으로 풀립니다(바뀐 내용은 `.백업/` 에 보관됩니다).
- 실습은 원본 대신 `내작업/` 폴더에 복사해서 합니다. `내작업/` 안의 파일은 깃이 무시합니다.
