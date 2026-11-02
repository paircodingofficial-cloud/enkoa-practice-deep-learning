# OKF 위키 비서 규칙

이 폴더는 LLM 위키의 세 층으로 나뉜다. bundles/ 아래의 폴더 하나가 OKF 번들(위키) 하나이고, studio는 업무 위키, game_data는 데이터 위키다. raw/는 원본 자료다. 위키 문서의 근거가 된 원문(회의 메모 등)과 비서가 새로 받은 자료가 들어 있고, 위키에 넣은 뒤에도 원문은 그대로 둔다. 이 파일은 위키를 읽고 쓰는 규칙이다.

## 위키 형식(OKF)

- 번들 안의 .md 파일 하나가 개념 문서 하나다. 번들 안 경로에서 .md를 뺀 것이 개념 ID다(예: playbooks/server_incident).
- index.md는 목차다. 번들 맨 위 index.md에는 폴더가, 폴더 안 index.md에는 그 폴더의 문서가 한 줄씩 적혀 있다. log.md는 번들의 변경 기록이다. 둘은 개념 문서가 아니다.
- 개념 문서는 맨 위 --- 두 줄 사이의 frontmatter와 그 아래 본문으로 나뉜다. frontmatter 키의 뜻: type은 문서 종류, description은 한 줄 설명, status는 draft(초안), stable(기본값), deprecated(기록용), stale_after는 이 시각이 지나면 내용이 낡았을 수 있다는 표시, sources는 근거 자료, generated는 누가 썼는지, verified는 누가 내용을 확인했는지다.
- 본문의 링크 [이름](/폴더/파일.md)는 번들 맨 위 기준 경로다.

## 질문에 답할 때

1. 질문에 맞는 번들의 맨 위 index.md(bundles/<번들>/index.md)부터 읽고, 필요한 폴더의 index.md를 읽은 뒤 필요한 개념 문서만 연다. ls, find, rg로 폴더 전체를 먼저 훑지 않는다.
2. 답에 쓰는 사실은 bundles/에서 읽은 개념 문서에서만 가져온다. raw/의 원본 자료는 답할 때 읽지 않는다. 문서에 없는 값이나 계산식은 만들지 말고 모른다고 답한다.
3. 읽은 문서의 frontmatter에서 status가 draft나 deprecated이거나 stale_after가 오늘보다 앞이면, 답의 첫 줄을 '주의: '로 시작해 그 사실을 적는다(stale_after가 지났으면 내용이 낡았을 수 있다고 적는다).
4. 답은 한국어로 짧게 쓰고, 마지막 줄에 출처를 적는다.
   - 형식: `출처: 번들 이름/개념 ID(신뢰 단계)`. 쓴 문서가 여럿이면 쉼표로 잇는다.
   - 번들 이름과 개념 ID의 하위 폴더를 모두 적는다. 앞에 bundles/를 붙이지 않고, 끝에 .md를 붙이지 않는다.
   - 맞는 예: `출처: studio/playbooks/server_incident(검증 전), game_data/metrics/dau(검증 전)`
   - 틀린 예: `playbooks/server_incident`(번들 이름 빠짐), `game_data/dau`(하위 폴더 빠짐), `bundles/studio/playbooks/server_incident`(bundles/ 붙음), `studio/playbooks/server_incident.md`(.md 붙음)
   - 답에 쓴 문서가 없으면 `출처: 없음`이라고 적는다.
   - 신뢰 단계는 verified 키만 보고 정한다. verified가 없으면 검증 전, verified에 human: 기록이 있으면 사람 검토, 그 밖의 기록만 있으면 기계 확인이다. generated(누가 썼는지)는 신뢰 단계와 상관없다.

## 문서를 고칠 때

- 사람이 고치라고 지시할 때만 고친다. 질문에 답하다가 문서를 고치지 않는다.
- 고칠 수 있는 것은 bundles/ 안의 파일(개념 문서, index.md, log.md)뿐이다.
- raw/의 원본 자료는 읽기만 하고 고치거나 지우거나 옮기지 않는다. 원문을 위키 문서에 그대로 붙이지 않고, 정리한 사실만 적은 뒤 sources로 원문을 가리킨다.
- 규칙 파일(AGENTS.md)은 사람만 고친다.
- 문서를 고치면 그 번들 log.md의 오늘 날짜 제목 아래에 무엇을 고쳤는지 한 줄 적는다.
