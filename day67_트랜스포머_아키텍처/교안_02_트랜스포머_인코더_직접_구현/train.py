"""직접 만든 인코더 분류기를 Lightning Trainer로 학습하고, 학습 전과 후의 테스트 결과와 리뷰 6개의 긍정 확률을 비교합니다.

사용: uv run python train.py (CPU에서 에폭마다 몇십 초, GPU에서는 몇 초). 학습 곡선은 output/learning_curve.png에 저장합니다.
"""
import logging
import platform
import warnings
from pathlib import Path

import lightning as L
import matplotlib.pyplot as plt
import pandas as pd
import torch
from lightning.pytorch.loggers import CSVLogger
from matplotlib import font_manager

import config
from data import build_vocab, load_tables, make_loader, make_tensor
from lit_model import LitReviewEncoder

# Lightning이 실행마다 띄우는 안내 문구(장치 정보, 다른 서비스 소개)를 숨깁니다
logging.getLogger("lightning.pytorch").setLevel(logging.ERROR)

# 경고는 하나만 숨깁니다: num_workers=0이라 나오는 '작업자 수가 적다'는 성능 권고
warnings.filterwarnings("ignore", message=".*does not have many workers.*")

# 데이터프레임을 줄이지 않고 출력합니다
pd.set_option("display.width", 200)
pd.set_option("display.max_colwidth", 60)

# 계산 장치: RunPod처럼 GPU(cuda)가 있으면 GPU, 없으면 CPU에서 계산합니다
if torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")
print("계산 장치:", device)

# 그래프 글꼴: 영문, 숫자, 기호는 DejaVu Sans, 한글은 운영체제의 한글 글꼴이 맡습니다
if platform.system() == "Windows":
    korean_font = "Malgun Gothic"
elif platform.system() == "Darwin":
    korean_font = "AppleGothic"
else:
    korean_font = "NanumGothic"
    # 리눅스(RunPod): 설치된 나눔고딕 파일을 matplotlib 글꼴 목록에 직접 등록합니다
    for font_path in font_manager.findSystemFonts():
        if "NanumGothic" in font_path:
            font_manager.fontManager.addfont(font_path)
plt.rcParams["font.family"] = ["DejaVu Sans", korean_font]
plt.rcParams["axes.unicode_minus"] = False  # 음수 부호가 네모로 깨지지 않게 합니다


def count_parameters(model):
    """모델의 파라미터(가중치, 절편, LayerNorm의 weight와 bias) 개수를 모두 더해 돌려줍니다."""
    total = 0
    for param in model.parameters():
        total += param.numel()
    return total


def read_metrics(trainer):
    """CSVLogger가 저장한 metrics.csv를 읽어 에폭마다 한 행으로 묶습니다.

    인자: trainer 학습을 마친 Trainer. 반환: 열이 epoch, train_loss, train_acc, val_loss, val_acc인 데이터프레임 (에폭 수, 5)
    """
    metrics = pd.read_csv(Path(trainer.logger.log_dir) / "metrics.csv")

    # 같은 에폭의 학습 행과 검증 행을 묶습니다. 빈 값(NaN)은 평균에서 빠집니다
    epoch_table = metrics.groupby("epoch")[["train_loss", "train_acc", "val_loss", "val_acc"]].mean().reset_index()
    epoch_table["epoch"] = epoch_table["epoch"] + 1  # Lightning은 에폭을 0부터 셉니다
    return epoch_table


def predict_sentiment(lit_model, texts, token_to_id):
    """리뷰 문장마다 긍정 확률(softmax의 1번 클래스 확률)을 소수 넷째 자리까지 계산합니다.

    인자: lit_model 모델, texts 리뷰 문장 목록, token_to_id 토큰 -> 토큰 ID 딕셔너리. 반환: 긍정 확률 목록 (문장 수,)
    """
    # 평가 모드: Dropout을 끕니다
    lit_model.eval()

    # 문장을 토큰 ID 텐서로 바꿔 모델과 같은 계산 장치로 옮깁니다
    tokens = make_tensor(texts, token_to_id, config.MAX_LEN).to(lit_model.device)  # (문장 수, 64)

    # 로짓을 softmax로 확률로 바꿉니다
    with torch.no_grad():
        probabilities = torch.softmax(lit_model(tokens), dim=1)  # (문장 수, 2) -> (문장 수, 2)
    return [round(p, 4) for p in probabilities[:, 1].tolist()]


# 1. 데이터: 데이터를 나누고, 학습 리뷰로 어휘 사전을 만들고, DataLoader 세 개를 만듭니다
train_table, valid_table, test_table = load_tables()
vocab, token_to_id = build_vocab(train_table)
train_loader = make_loader(train_table, token_to_id, shuffle=True)
valid_loader = make_loader(valid_table, token_to_id, shuffle=False)
test_loader = make_loader(test_table, token_to_id, shuffle=False)
print("어휘 크기:", len(vocab), "| 학습:", len(train_table), "| 검증:", len(valid_table), "| 테스트:", len(test_table))

# 2. 모델: 시드를 고정하고, 어휘 크기로 모델을 만듭니다
L.seed_everything(config.SEED, verbose=False)
lit_model = LitReviewEncoder(vocab_size=len(vocab), lr=config.LEARNING_RATE)
print("파라미터 수:", count_parameters(lit_model))

# 3. Trainer: self.log로 남긴 값은 output/lesson02_encoder/version_N/metrics.csv에 적힙니다
logger = CSVLogger(save_dir=config.OUTPUT_DIR, name="lesson02_encoder")
trainer = L.Trainer(max_epochs=config.EPOCHS, logger=logger, accelerator=device.type, enable_model_summary=False,
                    deterministic="warn")

# 4. 학습 전: 테스트 손실과 정확도
test_before = trainer.test(lit_model, test_loader, verbose=False)[0]

# 학습 전: 테스트 리뷰 6개의 긍정 확률. 긍정 3개, 부정 3개이고 '빼고는', '하지만'처럼 좋고 나쁨이 섞인 리뷰도 골랐습니다
review_index = [0, 24, 26, 18, 36, 11]
compare_table = test_table.loc[review_index, ["리뷰", "감성"]].copy()
compare_table["학습 전 긍정 확률"] = predict_sentiment(lit_model, compare_table["리뷰"].tolist(), token_to_id)

# 5. 학습: predict_sentiment가 eval()로 바꿨고 Trainer는 fit 시작에 train()을 부르지 않아, 학습 모드로 되돌립니다
lit_model.train()

# 미니배치 섞는 순서와 Dropout을 고정하려고 시드를 다시 고정하고, 에폭 반복과 검증은 Trainer가 합니다
L.seed_everything(config.SEED, verbose=False)
trainer.fit(lit_model, train_loader, valid_loader)

# 6. 에폭별 기록: 열 이름을 한국어로 바꿔 출력합니다
history = read_metrics(trainer)
history_table = history.rename(columns={"epoch": "에폭", "train_loss": "학습 손실", "train_acc": "학습 정확도",
                                        "val_loss": "검증 손실", "val_acc": "검증 정확도"}).set_index("에폭")
print()
print("에폭별 학습, 검증 손실과 정확도")
print(history_table.round(4))

# 7. 학습 곡선: 왼쪽은 손실, 오른쪽은 정확도. 학습과 검증을 같은 그래프에 그립니다
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(history["epoch"], history["train_loss"], marker="o", label="학습")
axes[0].plot(history["epoch"], history["val_loss"], marker="o", label="검증")
axes[0].set_title("손실")
axes[1].plot(history["epoch"], history["train_acc"], marker="o", label="학습")
axes[1].plot(history["epoch"], history["val_acc"], marker="o", label="검증")
axes[1].set_title("정확도")
for ax in axes:
    ax.set_xlabel("에폭")
    ax.legend()
fig.tight_layout()

# output/learning_curve.png로 저장합니다(다시 실행하면 덮어씁니다)
curve_path = config.OUTPUT_DIR / "learning_curve.png"
fig.savefig(curve_path, dpi=120)
plt.close(fig)
print("학습 곡선 저장:", curve_path)

# 8. 학습 후: 같은 테스트 데이터와 같은 리뷰 6개
test_after = trainer.test(lit_model, test_loader, verbose=False)[0]
compare_table["학습 후 긍정 확률"] = predict_sentiment(lit_model, compare_table["리뷰"].tolist(), token_to_id)

# 학습 전과 후의 테스트 손실과 정확도
summary_table = pd.DataFrame({
    "테스트 손실": [test_before["test_loss"], test_after["test_loss"]],
    "테스트 정확도": [test_before["test_acc"], test_after["test_acc"]],
}, index=["학습 전", "학습 후"])
print()
print("학습 전, 후 테스트 손실과 정확도")
print(summary_table.round(4))
print()
print("쇼핑 리뷰 6개의 긍정 확률(감성 0 부정, 1 긍정)")
print(compare_table)
