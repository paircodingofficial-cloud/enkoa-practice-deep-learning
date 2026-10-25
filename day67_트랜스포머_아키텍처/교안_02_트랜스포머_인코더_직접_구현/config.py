"""경로, 모델 크기, 학습 설정을 한곳에 모은 파일입니다. 다른 파일은 여기 값을 불러 씁니다."""
from pathlib import Path

# 이 파일이 있는 폴더(교안_02_트랜스포머_인코더_직접_구현)
PROJECT_DIR = Path(__file__).resolve().parent

# 단원 폴더의 data/교안02: 네이버 쇼핑 리뷰(학습용 50,000개, 테스트용 5,000개)
DATA_DIR = PROJECT_DIR.parent / "data" / "교안02"
TRAIN_CSV = DATA_DIR / "shopping_train.csv"
TEST_CSV = DATA_DIR / "shopping_test.csv"

# 학습 기록(metrics.csv), 체크포인트, 학습 곡선 그림을 저장할 폴더
OUTPUT_DIR = PROJECT_DIR / "output"

# 어휘 사전과 시퀀스 길이: 교안 01과 같은 규칙입니다
MIN_COUNT = 3  # 학습 리뷰에서 3번 이상 나온 문자만 어휘 사전에 넣습니다
MAX_LEN = 64  # [CLS] 포함 토큰 수 상한. 더 긴 리뷰는 뒤를 자릅니다

# 모델 크기: 교안 01의 TransformerClassifier와 같습니다
D_MODEL = 64  # 토큰 벡터의 차원 수
NUM_HEADS = 4  # 헤드 수. 헤드 하나는 16차원(64 / 4)을 맡습니다
NUM_LAYERS = 2  # 인코더 블록 수
D_FF = 4 * D_MODEL  # FFN이 넓힌 벡터의 차원 수(256)
DROPOUT = 0.1
NUM_CLASSES = 2  # 클래스 수: 부정(0), 긍정(1)

# 학습 설정: 교안 01과 같습니다
BATCH_SIZE = 128
LEARNING_RATE = 0.0005
WEIGHT_DECAY = 0.01
EPOCHS = 8
SEED = 0
