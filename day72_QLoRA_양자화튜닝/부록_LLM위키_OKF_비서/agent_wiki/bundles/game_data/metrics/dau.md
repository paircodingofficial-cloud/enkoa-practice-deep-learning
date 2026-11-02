---
type: Metric
title: DAU
description: 하루에 한 번 이상 접속한 플레이어 수.
tags: [metric, engagement]
generated: { by: "human:seoyeon", at: "2026-10-01T10:00:00+09:00" }
---
# Definition

그날 [sessions](/tables/sessions.md)에 한 행 이상 있는 플레이어 수입니다. 사내 테스트 계정(`is_test = 1`)은 뺍니다.

# Computation

그날 `played_on`인 접속 기록의 `player_id`를 중복 없이 셉니다. [players](/tables/players.md)와 이어 `is_test = 1`인 플레이어를 뺍니다.

# 최근 값

10월 평균 DAU는 약 90명입니다(10월 31일 데이터 담당 보고).
