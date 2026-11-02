---
type: Metric
title: 7일 잔존율
description: 가입 7일째 되는 날 다시 접속한 플레이어의 비율.
tags: [metric, retention]
generated: { by: "human:seoyeon", at: "2026-10-01T10:00:00+09:00" }
verified: { by: "human:seoyeon", at: "2026-10-30T15:00:00+09:00" }
---
# Definition

한 달 동안 가입한 플레이어(코호트) 가운데, 가입한 날로부터 정확히 7일 뒤에 접속 기록이 있는 플레이어의 비율입니다.

# Computation

분모는 그달 가입한 플레이어 수, 분자는 그 가운데 가입 7일 뒤 날짜에 [sessions](/tables/sessions.md) 기록이 있는 플레이어 수입니다. 사내 테스트 계정과, 데이터 마지막 날까지 가입 7일이 지나지 않은 플레이어는 뺍니다(아직 판정할 수 없으므로).

# 최근 값

* 9월 가입자: 24.0%
* 10월 가입자: 21.5%(10월 광고로 들어온 가입자가 많아 조금 낮음)
