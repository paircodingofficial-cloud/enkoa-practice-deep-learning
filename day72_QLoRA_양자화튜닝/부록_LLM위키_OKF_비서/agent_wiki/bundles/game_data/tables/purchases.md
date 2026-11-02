---
type: Table
title: purchases
description: 결제 한 번이 한 행.
resource: bigquery://starpixel/cbt_logs/purchases
tags: [cbt, purchases]
---
# Schema

| 열 | 형식 | 설명 |
|---|---|---|
| `purchase_id` | INTEGER | 결제 번호 |
| `player_id` | INTEGER | [players](/tables/players.md)의 플레이어 번호 |
| `purchased_on` | TEXT | 결제한 날(YYYY-MM-DD) |
| `item` | TEXT | 상품 이름 |
| `amount_krw` | INTEGER | 결제 금액(원) |
