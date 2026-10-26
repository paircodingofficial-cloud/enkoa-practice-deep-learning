# 딥러닝 실습자료

엔코아 AI캠퍼스 「데이터 분석 & AI 머신러닝 캠프」 딥러닝 과목 실습용 주피터 노트북입니다. 수업 진도에 맞춰 자료가 추가됩니다.

### 수록 자료

| 일차 | 주제 | 배우는 것 |
|---|---|---|
| **day65** | 딥러닝 학습 원리 | 모델이 학습하는 반복(예측, 손실 계산, 기울기 계산, 파라미터 갱신)을 PyTorch로 직접 돌려 봅니다. 교안 01은 직선 모델 하나로 **손실함수(MSE·MAE)·autograd·경사하강·학습률**을, 교안 02는 손글씨 숫자를 분류하는 **DNN**으로 교차 엔트로피, `DataLoader` 미니배치 학습 루프, SGD·모멘텀·Adam·AdamW, warmup + cosine 스케줄러를 다룹니다. 과제는 타이타닉 생존 예측과 날짜로 요일 맞히기입니다. 부록은 딥러닝과 지도·비지도·강화학습, 생성형 AI의 개념과 사례(알파고, 플루토, 로봇 제어)입니다 |
| **day66** | PyTorch 신경망 | 교안 01은 손글씨 숫자를 분류하는 **CNN**(합성곱, 파라미터 공유, 풀링, 수용 영역, 필터와 특징 맵)과 깊은 CNN을 위한 **배치 정규화·잔차 연결·ResNet**을, 교안 02는 데이터 누수를 막는 분할로 **과적합**을 진단하고 Dropout·가중치 감쇠·데이터 증강·조기 종료로 줄인 뒤 **PyTorch Lightning**으로 학습 코드를 정리합니다(기울기 자르기, 체크포인트로 이어 학습, 하이퍼파라미터 탐색). 과제는 낙서 10종 분류 CNN과 가위바위보 손 그림의 과적합과 규제입니다. 부록은 GAN으로 손글씨 숫자 만들기입니다 |
| **day67** | 트랜스포머 아키텍처 | 교안 01은 영화 리뷰(NSMC) 감성 분석을 따라가며 토큰화, 어휘 사전, 패딩, 토큰 임베딩에서 시작해 **어텐션**, 위치 인코딩, `nn.MultiheadAttention`과 패딩 마스크, LayerNorm을 거쳐 **트랜스포머 인코더**(`nn.TransformerEncoder`)를 쌓고 [CLS] 벡터로 분류합니다. 함께 따라하기는 숫자 20개 가운데 k번째로 큰 숫자의 위치를 찾는 순위 맞히기 게임입니다. 교안 02는 노트북이 아닌 .py 프로젝트로, 어텐션, Multi-Head Attention, LayerNorm, FFN, 인코더 블록을 **직접 구현**해 네이버 쇼핑 리뷰 감성 분석을 PyTorch Lightning으로 학습합니다. 과제는 문장 의도 7종 분류입니다. 부록은 행렬 연산과 텐서 모양(transpose, reshape, softmax, squeeze)입니다 |
| **day68** | 오픈소스 LLM 로컬 실행 | 교안 01은 오픈 웨이트 LLM 지형(개발 주체, 크기, MoE, 추론 모드)과 벤치마크·라이선스로 사내 헬프데스크에 쓸 모델(**Qwen3.5-4B**)을 고르고, **Ollama**(대화, 추론 모드)와 LangChain `ChatOllama`(구조화된 출력, 도구 호출), **Hugging Face Transformers**(chat template, 생성 설정)로 GPU에서 직접 실행합니다. 교안 02는 모델 메모리를 계산하고 FP32·BF16·INT8·4비트 **양자화**와 AWQ·GPTQ·GGUF를 비교한 뒤 Ollama 양자화 태그(Q8_0·Q4_K_M)를 크기·속도·답으로 고릅니다. 과제는 온라인 서점 상담 모델 고르고 실행하기와 택배 배송 문의 모델의 장비·양자화 형식 정하기입니다. Ollama 프로그램은 단원 폴더의 `설치_가이드.md`대로 따로 설치합니다 |

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

이 도우미는 RunPod(리눅스) 전용입니다. 내 PC(Windows·macOS)에서 실행하면 아무것도 하지 않고 끝나니, 내 PC에서는 `git pull` 과 `uv sync` 를 직접 실행합니다.

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
- 새 자료가 올라오면 RunPod 의 저장소 폴더에서 `uv run 업데이트.py` 를 다시 실행합니다(맥·윈도우에서는 실행되지 않습니다). `git pull` 이 충돌로 막혔을 때도 이 명령으로 풀립니다(바뀐 내용은 `.백업/` 에 보관됩니다).
- 실습은 원본 대신 `내작업/` 폴더에 복사해서 합니다. `내작업/` 안의 파일은 깃이 무시합니다.
