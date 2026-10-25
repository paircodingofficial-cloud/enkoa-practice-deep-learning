"""쇼핑 리뷰를 읽어 어휘 사전을 만들고, 학습, 검증, 테스트 DataLoader를 만드는 파일입니다.

encode, make_tensor와 어휘 사전 규칙은 교안 01과 같고, 어휘 사전은 쇼핑 리뷰 학습 데이터로 새로 만듭니다.
"""
from collections import Counter

import pandas as pd
import torch
from torch.utils.data import DataLoader, TensorDataset

import config


def load_tables():
    """쇼핑 리뷰 CSV를 읽어 학습, 검증, 테스트로 나눕니다. 감성은 0 부정(평점 1, 2), 1 긍정(평점 4, 5)입니다.

    반환: (학습 45,000행, 검증 5,000행, 테스트 5,000행) 데이터프레임. 열은 리뷰, 평점, 감성
    """
    shopping_train = pd.read_csv(config.TRAIN_CSV)
    test_table = pd.read_csv(config.TEST_CSV)

    # 학습용 50,000개를 섞어(순서 고정) 45,000개는 학습, 5,000개는 검증에 씁니다
    shuffled = shopping_train.sample(frac=1, random_state=0)
    train_table = shuffled.iloc[:45000]
    valid_table = shuffled.iloc[45000:]
    return train_table, valid_table, test_table


def build_vocab(train_table):
    """학습 리뷰로 어휘 사전을 만듭니다. 토큰 ID 0, 1, 2는 [PAD], [UNK], [CLS]입니다.

    인자: train_table 학습 데이터프레임. 반환: (어휘 사전 목록, 토큰 -> 토큰 ID 딕셔너리)
    """
    # 학습 리뷰에서 문자마다 나온 횟수를 셉니다
    char_counts = Counter()
    for review in train_table["리뷰"]:
        char_counts.update(list(review))

    # 특수 토큰 세 개 다음에, MIN_COUNT번 이상 나온 문자를 많이 나온 순서로 붙입니다
    vocab = ["[PAD]", "[UNK]", "[CLS]"]
    for token, count in char_counts.most_common():
        if count >= config.MIN_COUNT:
            vocab.append(token)

    # 토큰 -> 토큰 ID를 찾는 딕셔너리
    token_to_id = {}
    for token_id, token in enumerate(vocab):
        token_to_id[token] = token_id
    return vocab, token_to_id


def encode(text, token_to_id):
    """문장을 문자 단위로 자르고 문자마다 토큰 ID를 찾습니다. 어휘 사전에 없는 문자는 [UNK]의 토큰 ID입니다.

    인자: text 문장, token_to_id 토큰 -> 토큰 ID 딕셔너리. 반환: 토큰 ID 목록 (문자 수,)
    """
    ids = []
    for token in list(text):
        if token in token_to_id:
            ids.append(token_to_id[token])
        else:
            ids.append(token_to_id["[UNK]"])
    return ids


def make_tensor(texts, token_to_id, max_len):
    """문장마다 [CLS] + 문자 토큰 ID를 만들고, max_len에 맞춰 자르거나 [PAD](0)로 채웁니다.

    인자: texts 문장 목록, token_to_id 토큰 -> 토큰 ID 딕셔너리, max_len 시퀀스 길이(64). 반환: 토큰 ID 텐서 (문장 수, max_len)
    """
    rows = []
    for text in texts:
        ids = [token_to_id["[CLS]"]] + encode(text, token_to_id)
        ids = ids[:max_len]  # 길면 뒤를 자릅니다
        ids = ids + [token_to_id["[PAD]"]] * (max_len - len(ids))  # 짧으면 뒤를 [PAD](0)로 채웁니다
        rows.append(ids)
    return torch.tensor(rows)


def make_loader(table, token_to_id, shuffle):
    """리뷰 토큰 ID와 감성을 미니배치로 자르는 DataLoader를 만듭니다. shuffle: 에폭마다 섞을지 여부.

    반환: DataLoader. 미니배치 하나는 (토큰 ID (배치, 64), 감성 (배치,))
    """
    X = make_tensor(table["리뷰"].tolist(), token_to_id, config.MAX_LEN)  # (리뷰 수, 64)
    y = torch.tensor(table["감성"].values)  # (리뷰 수,)

    # 학습용만 shuffle=True로 에폭마다 섞습니다
    return DataLoader(TensorDataset(X, y), batch_size=config.BATCH_SIZE, shuffle=shuffle)
