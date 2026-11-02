---
type: Dataset
title: 게임 로그
description: 사전 출시(CBT) 기간의 플레이어, 접속, 결제 로그.
resource: bigquery://starpixel/cbt_logs
tags: [cbt, logs]
generated: { by: "process:log-export", at: "2026-11-01T03:00:00+09:00" }
verified:
  - { by: "process:log-export", at: "2026-11-01T03:00:00+09:00" }
---
# 범위

2026년 9월 1일부터 10월 31일까지의 CBT(비공개 테스트) 로그입니다. 매일 새벽 3시에 내보냅니다.

# 테이블

* [players](/tables/players.md): 플레이어 한 명이 한 행
* [sessions](/tables/sessions.md): 접속 한 번이 한 행
* [purchases](/tables/purchases.md): 결제 한 번이 한 행
