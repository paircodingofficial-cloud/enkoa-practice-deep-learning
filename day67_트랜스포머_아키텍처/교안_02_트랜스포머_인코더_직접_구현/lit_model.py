"""직접 만든 ReviewEncoder를 Lightning의 LightningModule로 감싼 파일입니다. PyTorch 신경망 단원 교안 02의 LitCNN과 같은 구조입니다."""
import lightning as L
import torch
import torch.nn as nn

import config
from encoder import ReviewEncoder


class LitReviewEncoder(L.LightningModule):  # LightningModule의 기능을 물려받는 새 클래스
    """ReviewEncoder로 리뷰의 감성(0 부정, 1 긍정)을 분류하고, 손실과 정확도를 기록합니다."""

    def __init__(self, vocab_size, lr):
        """분류 모델과 손실 함수를 만듭니다. vocab_size: 어휘 크기, lr: 학습률."""
        super().__init__()

        # 인자(vocab_size, lr)를 체크포인트 파일에 함께 저장합니다
        self.save_hyperparameters()

        # 직접 만든 분류 모델. 크기는 config.py의 값입니다
        self.model = ReviewEncoder(vocab_size=vocab_size, num_classes=config.NUM_CLASSES, d_model=config.D_MODEL,
                                   num_heads=config.NUM_HEADS, num_layers=config.NUM_LAYERS, d_ff=config.D_FF,
                                   dropout=config.DROPOUT, max_len=config.MAX_LEN)

        # 교차 엔트로피 = 평균(-log(정답 클래스의 확률))
        self.loss_fn = nn.CrossEntropyLoss()

        # configure_optimizers에서 쓸 학습률
        self.lr = lr

    def forward(self, X_batch):
        """lit_model(X_batch)처럼 부릅니다. 인자: 토큰 ID (배치, 64). 반환: 로짓 (배치, 2)."""
        return self.model(X_batch)

    def training_step(self, batch, batch_idx):
        """학습 미니배치 하나의 손실과 정확도를 기록하고 손실을 돌려줍니다. Trainer가 이 손실로 zero_grad, backward, step을 합니다.

        인자: batch (토큰 ID (배치, 64), 정답 (배치,)), batch_idx 미니배치 번호. 반환: 손실 스칼라 ()
        """
        # 1) 미니배치를 토큰 ID와 정답으로 나눕니다
        X_batch, y_batch = batch  # (배치, 64), (배치,)

        # 2) 로짓과 손실
        logits = self(X_batch)  # (배치, 64) -> (배치, 2)
        loss = self.loss_fn(logits, y_batch)  # (배치, 2), (배치,) -> ()

        # 3) 정확도: 가장 큰 로짓의 클래스가 정답과 같은 비율
        accuracy = (logits.argmax(dim=1) == y_batch).float().mean()  # (배치, 2) -> (배치,) -> ()

        # 4) 에폭 평균으로 기록하고(on_epoch=True), 진행 막대에도 보입니다(prog_bar=True)
        self.log("train_loss", loss, on_step=False, on_epoch=True, prog_bar=True)
        self.log("train_acc", accuracy, on_step=False, on_epoch=True, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        """검증 미니배치 하나의 손실과 정확도를 기록합니다. Trainer가 평가 모드, 기울기 없이 부릅니다."""
        X_batch, y_batch = batch
        logits = self(X_batch)  # (배치, 64) -> (배치, 2)

        # 검증 값은 기본으로 에폭 평균이 기록됩니다
        self.log("val_loss", self.loss_fn(logits, y_batch), prog_bar=True)
        self.log("val_acc", (logits.argmax(dim=1) == y_batch).float().mean(), prog_bar=True)

    def test_step(self, batch, batch_idx):
        """테스트 미니배치 하나의 손실과 정확도를 기록합니다. trainer.test가 부릅니다."""
        X_batch, y_batch = batch
        logits = self(X_batch)  # (배치, 64) -> (배치, 2)
        self.log("test_loss", self.loss_fn(logits, y_batch))
        self.log("test_acc", (logits.argmax(dim=1) == y_batch).float().mean())

    def configure_optimizers(self):
        """학습을 시작할 때 Trainer가 한 번 부릅니다. 반환: 교안 01과 같은 AdamW 옵티마이저."""
        return torch.optim.AdamW(self.parameters(), lr=self.lr, weight_decay=config.WEIGHT_DECAY)
