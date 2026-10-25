"""어텐션을 직접 구현한 파일입니다. scaled_dot_product_attention은 헤드 하나의 계산, MultiHeadAttention은 헤드 4개로 나눠 쓰는 층입니다.

shape 표기: d_model = 64, 헤드 수 = 4, d_k = 16. Q 쪽 축은 Query 토큰 수, K와 V 쪽 축은 Key 토큰 수입니다(Self-Attention이라 같은 수).
"""
import torch
import torch.nn as nn


def scaled_dot_product_attention(Q, K, V, padding_mask):
    """어텐션 점수를 계산하고 [PAD] 열을 막은 뒤, 어텐션 가중치로 Value를 가중합합니다.

    인자: Q (배치, 헤드 수, Query 토큰 수, d_k), K와 V (배치, 헤드 수, Key 토큰 수, d_k), padding_mask (배치, Key 토큰 수)는 [PAD] 위치가 True
    반환: 출력 (배치, 헤드 수, Query 토큰 수, d_k), 어텐션 가중치 (배치, 헤드 수, Query 토큰 수, Key 토큰 수)
    """
    # shape에서 배치 크기, Key 토큰 수, d_k를 꺼냅니다
    batch = K.shape[0]
    n = K.shape[2]
    d_k = K.shape[-1]

    # 1) 어텐션 점수: Q와 K의 마지막 두 축을 바꾼 것을 행렬 곱하고 d_k ** 0.5로 나눕니다
    scores = Q @ K.transpose(-2, -1) / (d_k ** 0.5)  # (배치, 헤드 수, Query 토큰 수, d_k) @ (배치, 헤드 수, d_k, Key 토큰 수) -> (배치, 헤드 수, Query 토큰 수, Key 토큰 수)

    # 2) 패딩 마스크: [PAD] 열의 어텐션 점수를 -inf로 바꿉니다. 크기 1인 축은 브로드캐스팅으로 모든 헤드와 Query 행에 퍼집니다
    scores = scores.masked_fill(padding_mask.reshape(batch, 1, 1, n), float("-inf"))  # 마스크 (배치, Key 토큰 수) -> (배치, 1, 1, Key 토큰 수)

    # 3) softmax: Key 토큰 축으로 정규화해 행마다 합이 1인 어텐션 가중치를 만듭니다
    weights = torch.softmax(scores, dim=-1)  # (배치, 헤드 수, Query 토큰 수, Key 토큰 수)

    # 4) 가중합: 어텐션 가중치로 Value를 가중합한 출력과 어텐션 가중치를 함께 돌려줍니다
    return weights @ V, weights  # (배치, 헤드 수, Query 토큰 수, Key 토큰 수) @ (배치, 헤드 수, Key 토큰 수, d_k) -> (배치, 헤드 수, Query 토큰 수, d_k)


class MultiHeadAttention(nn.Module):
    """Self-Attention을 헤드 num_heads개로 나눠 계산하는 층입니다. 평가 모드에서 nn.MultiheadAttention(batch_first=True)과 같은 계산입니다."""

    def __init__(self, d_model, num_heads):
        """Q, K, V 투영 행렬과 출력 투영을 만듭니다. d_model: 토큰 벡터 차원 수(64), num_heads: 헤드 수(4)."""
        super().__init__()
        self.num_heads = num_heads

        # 헤드 하나가 맡는 차원 수 d_k = 64 / 4 = 16
        self.d_k = d_model // num_heads

        # Query, Key, Value를 만드는 투영 행렬. 역할마다 따로 학습합니다
        self.W_Q = nn.Linear(d_model, d_model)
        self.W_K = nn.Linear(d_model, d_model)
        self.W_V = nn.Linear(d_model, d_model)

        # 이어 붙인 헤드 출력을 선형 변환하는 출력 투영(nn.MultiheadAttention과 같은 이름)
        self.out_proj = nn.Linear(d_model, d_model)

    def forward(self, x, padding_mask):
        """x로 Q, K, V를 만들어 헤드로 나누고, 헤드별 어텐션 출력을 이어 붙여 out_proj에 통과시킵니다.

        인자: x (배치, 토큰 수, d_model), padding_mask (배치, Key 토큰 수)
        반환: 출력 (배치, Query 토큰 수, d_model), 헤드별 어텐션 가중치 (배치, 헤드 수, Query 토큰 수, Key 토큰 수)
        """
        # x에서 배치 크기, 토큰 수, d_model을 꺼냅니다
        batch = x.shape[0]
        n = x.shape[1]
        d_model = x.shape[2]

        # 1) 같은 x를 W_Q, W_K, W_V에 넣어 Q, K, V를 만듭니다
        Q = self.W_Q(x)  # (배치, 토큰 수, d_model) -> (배치, Query 토큰 수, d_model)
        K = self.W_K(x)  # (배치, 토큰 수, d_model) -> (배치, Key 토큰 수, d_model)
        V = self.W_V(x)  # (배치, 토큰 수, d_model) -> (배치, Key 토큰 수, d_model)

        # 2) 헤드로 나누기: reshape으로 마지막 축을 (헤드 수, d_k)로 자르고, transpose(1, 2)로 헤드 축을 앞으로 보냅니다
        Qh = Q.reshape(batch, n, self.num_heads, self.d_k).transpose(1, 2)  # (배치, Query 토큰 수, d_model) -> (배치, 헤드 수, Query 토큰 수, d_k)
        Kh = K.reshape(batch, n, self.num_heads, self.d_k).transpose(1, 2)  # (배치, Key 토큰 수, d_model) -> (배치, 헤드 수, Key 토큰 수, d_k)
        Vh = V.reshape(batch, n, self.num_heads, self.d_k).transpose(1, 2)  # (배치, Key 토큰 수, d_model) -> (배치, 헤드 수, Key 토큰 수, d_k)

        # 3) 헤드별 어텐션: 헤드 4개를 한 번에 계산합니다
        head_out, head_weights = scaled_dot_product_attention(Qh, Kh, Vh, padding_mask)  # (배치, 헤드 수, Query 토큰 수, d_k), (배치, 헤드 수, Query 토큰 수, Key 토큰 수)

        # 4) 이어 붙이기: transpose(1, 2)로 헤드 축을 되돌리고 reshape으로 헤드 4개의 d_k를 이어 d_model로 만듭니다
        concat = head_out.transpose(1, 2).reshape(batch, n, d_model)  # (배치, 헤드 수, Query 토큰 수, d_k) -> (배치, Query 토큰 수, d_model)

        # 5) 출력 투영: 이어 붙인 헤드 출력을 선형 변환해 헤드 사이의 정보를 합칩니다
        return self.out_proj(concat), head_weights  # (배치, Query 토큰 수, d_model)
