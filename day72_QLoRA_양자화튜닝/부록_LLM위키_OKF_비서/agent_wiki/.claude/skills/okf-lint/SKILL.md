---
name: okf-lint
description: OKF 위키(bundles/)를 점검해 문제를 표로 보고한다. 사람이 위키를 점검하라고 할 때 쓴다. 문서는 고치지 않는다.
allowed-tools: Read, Glob, Grep, Bash(python3 *)
---
# OKF 위키 점검

점검은 문제를 찾아 알리기만 하고 문서를 고치지 않는다. 고칠지와 무엇을 바꿀지는 사람이 정한다. 오늘 날짜는 2026-11-02다. 스크립트는 이 SKILL.md 옆 `scripts/check.py`다. 작업 폴더에서 Claude Code는 `python3 .claude/skills/okf-lint/scripts/check.py`, Codex는 `python3 .agents/skills/okf-lint/scripts/check.py`로 실행한다.

## 순서

1. check.py를 실행한다. 적합성, 끊긴 링크, 만료, 없는 원문을 찾는다.
2. 번들마다 `log.md`의 `## 2026-11-02` 아래에서 오늘 바뀐 문서를 찾는다.
3. 오늘 바뀐 문서(문서 A)와, 그 문서가 링크하거나 그 문서를 링크하는 문서(문서 B)를 읽고, 같은 대상(날짜, 금액, 담당자, 상태)을 서로 다르게 말하는 줄을 찾는다. 회의 정리 문서는 그날의 기록이라 문서 B로 보지 않는다.
4. 한국어 표 두 개로 보고한다: check.py 결과(번들, 점검, 문서, 내용), 모순(문서 A의 줄, 문서 B의 줄). 문서는 고치지 않는다.
