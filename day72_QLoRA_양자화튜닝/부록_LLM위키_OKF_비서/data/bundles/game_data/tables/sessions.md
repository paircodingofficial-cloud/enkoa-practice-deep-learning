---
type: Table
title: sessions
description: 접속 한 번이 한 행.
resource: bigquery://starpixel/cbt_logs/sessions
tags: [cbt, sessions]
---
# Schema

| 열 | 형식 | 설명 |
|---|---|---|
| `session_id` | INTEGER | 접속 번호 |
| `player_id` | INTEGER | [players](/tables/players.md)의 플레이어 번호 |
| `played_on` | TEXT | 접속한 날(YYYY-MM-DD) |
| `minutes` | INTEGER | 플레이한 시간(분) |
