# 부록: LLM 위키와 OKF 비서

LLM이 원본 자료를 마크다운 위키로 정리해 두고 그 위키로 답하는 방식(LLM 위키)과, Google Cloud가 이 방식을 공통 규칙으로 정리해 누가 만든 위키든 다른 에이전트가 변환 없이 읽게 한 공개 형식 OKF(Open Knowledge Format) v0.2를 익히고, 가상 인디 게임 회사 별빛픽셀의 위키 비서를 만듭니다.

## 실행 순서

1. `부록_01_LLM위키와_OKF_설계_철학.ipynb`: OKF가 하는 일, LLM 위키, 설계 원칙, 번들 구조와 개념 문서에 넣는 것, 신뢰 표시, 적합성 조건(코드 없이 읽는 부록)
2. `부록_02_OKF_비서_묻고_답하기.ipynb`: Codex, Claude Code에 규칙 파일(`data/AGENTS.md`)을 주어 번들로 답하게 하기, 이어서 Jev가 번들을 고르고 LangChain 에이전트가 목차부터 읽어 출처를 붙여 답하는 비서 만들기
3. `부록_03_코딩에이전트_스킬로_위키_키우기.ipynb`: 스킬 구성, Claude Code와 Codex의 스킬 폴더에 등록, 작업 폴더 `agent_wiki/`에서 대화로 새 자료 넣기(새 번들 만들기 포함)와 점검(코드 없이 읽고 따라 하는 부록)

02의 2절부터는 `OPENAI_API_KEY`, `TYPESAFE_API_KEY`가 필요합니다(`.env.example`). 02의 1절과 03은 이 키 없이 Codex CLI나 Claude Code만 있으면 따라 합니다. 이 폴더에서 커널을 시작합니다.

## 폴더 구조

```
부록_LLM위키_OKF_비서/
├── okf_utils.py          번들 읽기, 신뢰 단계, 만료 판정 함수(02가 가져다 씀)
├── agent_wiki/           부록 03의 작업 폴더(미리 만들어 둠): AGENTS.md, bundles/, raw/ 사본과 등록된 스킬
│   ├── .claude/skills/   Claude Code가 찾는 스킬: okf-ingest(넣기, 새 번들 만들기), okf-lint(점검) + scripts/check.py
│   └── .agents/skills/   Codex가 찾는 스킬(같은 내용)
├── data/
│   ├── AGENTS.md         스키마: 코딩 에이전트(Codex, Claude Code)용 위키 비서 규칙. 번들 밖에 둠
│   ├── bundles/          위키: OKF 번들 두 개
│   │   ├── studio/       업무 위키, 역할별 폴더: people, projects, meetings, playbooks, decisions
│   │   └── game_data/    데이터 위키(데이터 카탈로그), 자원별 폴더: datasets, tables, metrics. 데이터 자체는 넣지 않음
│   └── raw/              원본 자료: 기존 위키의 근거인 회의 원문 메모 세 건과 비서가 새로 받은 자료 일곱 건(회의 메모, 새 팀원 메일, 지표 추가 메모, 지표 중단 메모, 광고 메일, 세계관 메모, 장비 목록 메모). 위키에 넣은 뒤에도 그대로 둠
└── images/               개념 그림
```

데이터는 `scripts/day72_build/okf/build_bundles.py`, 부록 03의 스킬은 `build_agent_skills.py`가 만듭니다. 샘플 번들의 '오늘'은 2026-11-02입니다. `__부록_03_스킬로_위키_키우기.ipynb`는 쓰지 않는 옛 판(LangChain 스킬 비서)입니다.

## 공식 문서

- OKF SPEC v0.2: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md
- Google Cloud 블로그: https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
- Karpathy LLM Wiki: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Claude Code 스킬: https://code.claude.com/docs/en/skills
- Codex 스킬: https://developers.openai.com/codex/skills
- Agent Skills: https://agentskills.io
