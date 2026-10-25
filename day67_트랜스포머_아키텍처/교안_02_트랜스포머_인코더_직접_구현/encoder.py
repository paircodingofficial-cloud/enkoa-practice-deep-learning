"""인코더 블록과 리뷰 분류 모델을 직접 구현한 파일입니다. LayerNorm, FeedForward -> EncoderBlock -> ReviewEncoder 순서로 쌓습니다.

positional_encoding은 교안 01 7-2와 같은 코드입니다. shape 표기: d_model = 64, d_ff = 256, 클래스 수 = 2.
"""
import torch
import torch.nn as nn

from attention import MultiHeadAttention


def positional_encoding(max_len, d_model):
    """sin, cos로 계산한 위치 인코딩 행렬을 돌려줍니다. 학습되지 않는 고정 값입니다.

    인자: max_len 위치 수(64), d_model 토큰 벡터 차원 수(64). 반환: 위치 인코딩 행렬 (max_len, d_model)
    """
    # 위치 인덱스 0 ~ max_len - 1을 세로 한 줄로 세웁니다
    position_ids = torch.arange(max_len).unsqueeze(1)  # (max_len, 1)

    # 짝수 차원 인덱스 2i = 0, 2, 4, ...마다 나누는 값 10000^(2i/d)
    even_index = torch.arange(0, d_model, 2)  # (d_model / 2,)
    divisor = 10000 ** (even_index / d_model)  # (d_model / 2,)

    # 짝수 차원(0::2)은 sin, 홀수 차원(1::2)은 cos
    table = torch.zeros(max_len, d_model)  # (max_len, d_model)
    table[:, 0::2] = torch.sin(position_ids / divisor)  # (max_len, 1) / (d_model / 2,) -> (max_len, d_model / 2)
    table[:, 1::2] = torch.cos(position_ids / divisor)  # (max_len, 1) / (d_model / 2,) -> (max_len, d_model / 2)
    return table


class LayerNorm(nn.Module):
    """토큰 벡터마다 평균 0, 분산 1로 맞춘 뒤 weight를 곱하고 bias를 더합니다. nn.LayerNorm(d_model)과 같은 계산입니다."""

    def __init__(self, d_model, eps=1e-5):
        """학습되는 파라미터 weight, bias (d_model,)를 만듭니다. eps: 0으로 나누지 않게 분산에 더하는 작은 수."""
        super().__init__()

        # 학습되는 파라미터: weight(gamma)는 1, bias(beta)는 0에서 시작합니다
        self.weight = nn.Parameter(torch.ones(d_model))  # (d_model,)
        self.bias = nn.Parameter(torch.zeros(d_model))  # (d_model,)

        # 분산이 0일 때 0으로 나누지 않게 더하는 작은 수
        self.eps = eps

    def forward(self, x):
        """토큰 벡터마다 정규화합니다. 인자: x (배치, 토큰 수, d_model). 반환: (배치, 토큰 수, d_model)"""
        # 1) 마지막 축(d_model개 차원)의 평균. keepdim=True가 크기 1인 축을 남깁니다
        mean = x.mean(dim=-1, keepdim=True)  # (배치, 토큰 수, d_model) -> (배치, 토큰 수, 1)

        # 2) 같은 축의 분산. nn.LayerNorm과 같게 n으로 나눕니다(unbiased=False)
        var = x.var(dim=-1, unbiased=False, keepdim=True)  # (배치, 토큰 수, d_model) -> (배치, 토큰 수, 1)

        # 3) 평균을 빼고 표준편차로 나눈 뒤 weight를 곱하고 bias를 더합니다. 크기 1인 축과 (d_model,)은 브로드캐스팅으로 퍼집니다
        return self.weight * (x - mean) / ((var + self.eps) ** 0.5) + self.bias  # (배치, 토큰 수, d_model)


class FeedForward(nn.Module):
    """토큰 벡터를 d_ff차원으로 넓혔다가 d_model차원으로 줄이는 2층 신경망입니다. 토큰마다 따로 계산합니다."""

    def __init__(self, d_model, d_ff, dropout):
        """Linear 두 개(d_model -> d_ff -> d_model)와 Dropout을 만듭니다. dropout: 0으로 끌 비율(0.1)."""
        super().__init__()

        # 64차원 -> 256차원 -> 64차원
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        """넓히기 -> ReLU -> Dropout -> 줄이기. 인자: x (배치, 토큰 수, d_model). 반환: (배치, 토큰 수, d_model)"""
        # 1) linear1로 넓히고 ReLU로 음수를 0으로 바꿉니다
        hidden = torch.relu(self.linear1(x))  # (배치, 토큰 수, d_model) -> (배치, 토큰 수, d_ff)

        # 2) Dropout: 학습 중에만 일부 값을 0으로 끕니다
        hidden = self.dropout(hidden)  # (배치, 토큰 수, d_ff)

        # 3) linear2로 다시 줄입니다
        return self.linear2(hidden)  # (배치, 토큰 수, d_ff) -> (배치, 토큰 수, d_model)


class EncoderBlock(nn.Module):
    """인코더 블록 하나(Post-LN). 평가 모드에서 nn.TransformerEncoderLayer(batch_first=True)와 같은 계산이고, 층 이름도 같습니다."""

    def __init__(self, d_model, num_heads, d_ff, dropout):
        """서브층 두 개(어텐션, FFN)와 서브층마다 LayerNorm, Dropout을 만듭니다."""
        super().__init__()

        # 서브층 두 개: 어텐션과 FFN
        self.self_attn = MultiHeadAttention(d_model, num_heads)
        self.ffn = FeedForward(d_model, d_ff, dropout)

        # 서브층마다 LayerNorm 하나
        self.norm1 = LayerNorm(d_model)
        self.norm2 = LayerNorm(d_model)

        # 서브층 출력에 거는 Dropout. 잔차 연결로 더하기 전에 씁니다
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, padding_mask):
        """어텐션 서브층과 FFN 서브층을 Post-LN 순서(더한 뒤 LayerNorm)로 잇습니다.

        인자: x (배치, 토큰 수, d_model), padding_mask (배치, Key 토큰 수)
        반환: 블록 출력 (배치, 토큰 수, d_model), 헤드별 어텐션 가중치 (배치, 헤드 수, Query 토큰 수, Key 토큰 수)
        """
        # 1) 어텐션
        attn_out, head_weights = self.self_attn(x, padding_mask)  # (배치, 토큰 수, d_model)

        # 2) 어텐션 서브층: 잔차 연결로 x에 더한 뒤 norm1
        x = self.norm1(x + self.dropout1(attn_out))  # (배치, 토큰 수, d_model)

        # 3) FFN 서브층: FFN 출력을 잔차 연결로 더한 뒤 norm2
        x = self.norm2(x + self.dropout2(self.ffn(x)))  # (배치, 토큰 수, d_model)

        # 4) 입력과 출력의 shape가 같아 블록을 쌓을 수 있습니다
        return x, head_weights


class ReviewEncoder(nn.Module):
    """토큰 임베딩 + 위치 인코딩 -> 인코더 블록 num_layers개 -> [CLS] 벡터 분류 층으로 리뷰를 분류하는 모델입니다."""

    def __init__(self, vocab_size, num_classes, d_model, num_heads, num_layers, d_ff, dropout, max_len):
        """임베딩 행렬, 위치 인코딩 행렬, 인코더 블록, 분류 층을 만듭니다. 크기는 config.py의 값을 받습니다."""
        super().__init__()

        # 임베딩 행렬: 토큰 ID -> 토큰 벡터. [PAD](토큰 ID 0) 벡터는 0으로 두고 학습하지 않습니다
        self.token_embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)  # (어휘 크기, d_model)

        # 위치 인코딩 행렬. 학습되지 않아 버퍼로 등록합니다(모델과 함께 GPU로 옮겨집니다)
        self.register_buffer("position_table", positional_encoding(max_len, d_model))  # (max_len, d_model)

        # 같은 구조의 블록 num_layers개. 블록마다 파라미터는 따로입니다
        self.blocks = nn.ModuleList()
        for _ in range(num_layers):
            self.blocks.append(EncoderBlock(d_model, num_heads, d_ff, dropout))

        # [CLS] 벡터 하나 -> 클래스마다 로짓
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, tokens):
        """토큰 ID로 클래스마다 로짓을 계산합니다.

        인자: tokens [CLS] + 토큰 ID (배치, 토큰 수), [PAD]는 0. 반환: 로짓 (배치, 클래스 수)
        """
        # 1) 토큰 임베딩에 위치 인코딩 행렬의 앞 (토큰 수)개 행을 더합니다. 브로드캐스팅으로 모든 리뷰에 같은 위치 인코딩을 더합니다
        h = self.token_embedding(tokens) + self.position_table[:tokens.shape[1]]  # (배치, 토큰 수) -> (배치, 토큰 수, d_model)

        # 2) 패딩 마스크: [PAD](토큰 ID 0) 위치가 True입니다
        padding_mask = tokens == 0  # (배치, 토큰 수)

        # 3) 블록을 차례로 지납니다. 블록은 (출력, 어텐션 가중치)를 돌려줍니다
        for block in self.blocks:
            h, _ = block(h, padding_mask)  # (배치, 토큰 수, d_model)

        # 4) 0번 위치의 [CLS] 벡터를 분류 층에 넣어 로짓을 계산합니다
        return self.classifier(h[:, 0])  # (배치, 토큰 수, d_model) -> (배치, d_model) -> (배치, 클래스 수)
