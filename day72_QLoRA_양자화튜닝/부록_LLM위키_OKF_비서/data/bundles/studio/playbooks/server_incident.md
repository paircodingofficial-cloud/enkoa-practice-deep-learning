---
type: Playbook
title: 서버 장애 대응
description: 서버 장애가 났을 때의 순서, 확인과 복구 명령어, 연락처.
tags: [server, incident]
status: stable
stale_after: "2026-10-01T00:00:00+09:00"
generated: { by: "human:seoyeon", at: "2026-07-01T10:00:00+09:00" }
---
# 순서

1. 아래 명령으로 게임 서버 상태를 확인합니다. 응답이 없거나 오류가 나오면 장애입니다.

   ```bash
   curl -s https://status.starpixel.example/api/health
   ```

2. 상태 페이지에 '점검 중'을 올립니다.
3. 1차 담당 [박서연](/people/seoyeon.md)에게 전화합니다.
4. 1차 담당이 아래 명령으로 게임 서버를 다시 시작합니다.

   ```bash
   ssh game-1 "sudo systemctl restart chorong-server"
   ```

5. 30분 안에 복구되지 않으면 [윤하나](/people/yuna.md)에게 알립니다.

# 연락처

1차 담당 전화번호는 사내 연락망 7번입니다. 클라우드 업체 지원 번호는 계약서 부록에 있습니다.
