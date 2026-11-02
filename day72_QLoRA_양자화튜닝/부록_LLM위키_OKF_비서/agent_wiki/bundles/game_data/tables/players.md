---
type: Table
title: players
description: 플레이어 한 명이 한 행.
resource: bigquery://starpixel/cbt_logs/players
tags: [cbt, players]
---
# Schema

| 열 | 형식 | 설명 |
|---|---|---|
| `player_id` | INTEGER | 플레이어 번호 |
| `joined_on` | TEXT | 가입한 날(YYYY-MM-DD) |
| `country` | TEXT | 국가 코드(KR, JP, TW) |
| `is_test` | INTEGER | 사내 테스트 계정이면 1 |

# Joins

[sessions](/tables/sessions.md), [purchases](/tables/purchases.md)와 `player_id`로 잇습니다.
