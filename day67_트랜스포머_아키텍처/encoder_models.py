"""교안 01(트랜스포머 인코더)에서 쓰는 위치 인코딩 함수와 모델 두 개가 든 파일입니다.

- positional_encoding: 원 논문의 sin, cos 위치 인코딩 행렬을 만듭니다(교안 7-2와 같은 코드).
- TransformerClassifier: 문장의 토큰 ID를 받아 클래스마다 로짓을 내는 트랜스포머 인코더 분류 모델입니다(영화 리뷰 감성 분석).
- RankClassifier: 순위 맞히기 게임 모델입니다. 토큰 21개를 받아 숫자 20개의 위치마다 정답일 로짓을 냅니다(함께 따라하기).
"""
import torch
import torch.nn as nn


def positional_encoding(max_len, d_model):
    """위치 0 ~ max_len - 1마다 sin, cos로 계산한 위치 벡터를 담은 위치 인코딩 행렬 (max_len, d_model)을 돌려줍니다. 학습되지 않는 고정 값입니다."""
    # 위치 인덱스 0 ~ max_len - 1을 세로 한 줄로 세웁니다
    position_ids = torch.arange(max_len).unsqueeze(1)  # (max_len, 1)

    # 짝수 차원 인덱스 2i = 0, 2, 4, ...마다 나누는 값 10000^(2i/d)
    even_index = torch.arange(0, d_model, 2)  # (d_model / 2,)
    divisor = 10000 ** (even_index / d_model)  # (d_model / 2,)

    # 짝수 차원(0::2)은 sin, 홀수 차원(1::2)은 cos. 브로드캐스팅: (max_len, 1) / (d_model / 2,) -> (max_len, d_model / 2)
    table = torch.zeros(max_len, d_model)  # (max_len, d_model)
    table[:, 0::2] = torch.sin(position_ids / divisor)  # (max_len, d_model / 2) -> 짝수 열
    table[:, 1::2] = torch.cos(position_ids / divisor)  # (max_len, d_model / 2) -> 홀수 열
    return table


class TransformerClassifier(nn.Module):
    """[CLS] + 토큰 ID를 받아, 인코더를 지난 [CLS] 위치의 벡터로 클래스마다 로짓을 냅니다.

    입력: tokens (배치, 토큰 수) 토큰 ID. 0번 위치는 [CLS], [PAD]는 0
    출력: (배치, num_classes) 로짓
    """

    def __init__(self, vocab_size, num_classes=2, d_model=64, num_heads=4, num_layers=2, max_len=64):
        super().__init__()

        # 토큰 ID -> 벡터(임베딩 행렬, 학습되는 파라미터). padding_idx=0: [PAD] 벡터는 0으로 두고 학습하지 않습니다
        self.token_embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)

        # 위치마다 더할 sin, cos 위치 인코딩 행렬 (max_len, d_model). 학습하지 않는 값이라 파라미터가 아닌 버퍼(학습되지 않는 텐서)로 등록합니다
        # 버퍼는 model.to(device)를 하면 모델과 함께 GPU로 옮겨집니다
        self.register_buffer("position_table", positional_encoding(max_len, d_model))

        # 인코더 층 하나 = Multi-Head Self-Attention + FFN, 각각 잔차 연결과 LayerNorm으로 감쌉니다
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=num_heads, dim_feedforward=4 * d_model,
                                                   dropout=0.1, batch_first=True)

        # 같은 구조의 층을 num_layers개 쌓습니다(층마다 파라미터는 따로)
        # enable_nested_tensor=False: 경고 없이 쓰려고 끕니다
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers, enable_nested_tensor=False)

        # [CLS] 위치의 벡터 하나 -> 클래스마다 로짓
        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, tokens):
        """tokens (배치, 토큰 수) -> 로짓 (배치, num_classes)"""
        # 1. 토큰 벡터 + 위치 0 ~ 토큰 수 - 1의 위치 벡터
        n_tokens = tokens.shape[1]
        h = self.token_embedding(tokens) + self.position_table[:n_tokens]  # (배치, 토큰 수) -> (배치, 토큰 수, d_model) + (토큰 수, d_model) -> (배치, 토큰 수, d_model)

        # 2. 패딩 마스크([PAD] 위치가 True, (배치, 토큰 수))와 함께 인코더에 넣습니다. shape은 그대로입니다
        h = self.encoder(h, src_key_padding_mask=(tokens == 0))  # (배치, 토큰 수, d_model) -> (배치, 토큰 수, d_model)

        # 3. 0번 위치의 [CLS] 벡터
        cls_vector = h[:, 0]  # (배치, 토큰 수, d_model) -> (배치, d_model)

        # 4. 클래스마다 로짓
        return self.classifier(cls_vector)  # (배치, d_model) -> (배치, num_classes)


class RankClassifier(nn.Module):
    """순위 맞히기 게임: 토큰 21개를 인코더에 넣고, 숫자 20개의 위치마다 그 위치가 정답일 로짓을 냅니다.

    입력: tokens (배치, 21) 토큰 ID. 맨 앞은 순위 토큰, 그 뒤 20개는 숫자
    출력: (배치, 20) 숫자 위치마다 로짓
    """

    def __init__(self, vocab_size=103, d_model=64, num_heads=4, num_layers=2, max_len=21):
        super().__init__()

        # 토큰 ID -> 벡터(어휘 크기 103: 숫자 100개 + 순위 토큰 3개)
        self.token_embedding = nn.Embedding(vocab_size, d_model)

        # 위치 21개마다 더할 sin, cos 위치 인코딩 행렬 (21, d_model). 학습하지 않는 버퍼입니다
        self.register_buffer("position_table", positional_encoding(max_len, d_model))

        # 인코더 층 하나 = Multi-Head Self-Attention + FFN. 같은 구조의 층을 num_layers개 쌓습니다
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=num_heads, dim_feedforward=4 * d_model,
                                                   dropout=0.1, batch_first=True)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers, enable_nested_tensor=False)

        # 숫자 위치의 벡터 하나 -> 그 위치가 정답일 로짓 하나
        self.score = nn.Linear(d_model, 1)

    def forward(self, tokens):
        """tokens (배치, 21) -> 로짓 (배치, 20)"""
        # 1. 토큰 벡터 + 위치 0~20의 위치 벡터
        h = self.token_embedding(tokens) + self.position_table  # (배치, 21) -> (배치, 21, d_model) + (21, d_model) -> (배치, 21, d_model)

        # 2. 게임은 시퀀스 길이가 모두 21이라 [PAD]가 없으므로 패딩 마스크 없이 인코더에 넣습니다
        h = self.encoder(h)  # (배치, 21, d_model) -> (배치, 21, d_model)

        # 3. 맨 앞 순위 토큰을 뺀 숫자 20개 위치의 벡터마다 로짓 하나
        scores = self.score(h[:, 1:])  # (배치, 20, d_model) -> (배치, 20, 1)
        logits = scores.squeeze(-1)  # (배치, 20, 1) -> (배치, 20)
        return logits
