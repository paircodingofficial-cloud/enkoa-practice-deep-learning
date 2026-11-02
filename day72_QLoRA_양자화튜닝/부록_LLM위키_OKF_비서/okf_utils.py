"""OKF 번들을 읽는 함수. 부록 01 5절의 신뢰 단계와 만료 기준을 코드로 옮겼고, 부록 02가 가져다 씁니다."""

from datetime import datetime
from pathlib import Path

import yaml


RESERVED = ["index.md", "log.md"]  # 개념 문서로 쓸 수 없는 예약 파일 이름


def read_concept(path):
    """개념 문서를 frontmatter(딕셔너리)와 본문(문자열)으로 나눠 돌려줍니다."""
    text = Path(path).read_text(encoding="utf-8")

    # 첫 줄의 '---'부터 다음 '---' 줄까지가 frontmatter입니다
    parts = text.split("---\n", 2)
    meta = yaml.safe_load(parts[1])
    body = parts[2]
    return meta, body


def list_concepts(bundle_dir):
    """번들 안의 개념 문서 경로를 모두 돌려줍니다(예약 파일은 뺍니다)."""
    paths = []
    for path in sorted(Path(bundle_dir).rglob("*.md")):
        if path.name not in RESERVED:
            paths.append(path)
    return paths


def concept_id(bundle_dir, path):
    """번들 안 경로에서 .md를 뺀 것이 개념 ID입니다."""
    return Path(path).relative_to(bundle_dir).with_suffix("").as_posix()


def trust_tier(meta):
    """verified 기록으로 신뢰 단계를 정합니다(SPEC 5.3)."""
    verified = meta.get("verified")
    if verified is None:
        return "검증 전"

    # 검증 기록이 하나뿐이면 목록 없이 적을 수 있으므로 목록으로 바꿉니다(SPEC 5.2)
    if isinstance(verified, dict):
        verified = [verified]

    # 사람(human:)이 한 번이라도 확인했으면 사람 검토, 아니면 기계 확인
    for event in verified:
        if event["by"].startswith("human:"):
            return "사람 검토"
    return "기계 확인"


def is_stale(meta, now):
    """stale_after가 있고 지금이 그 시점 이후이면 만료입니다(SPEC 5.5)."""
    if "stale_after" not in meta:
        return False
    return now >= datetime.fromisoformat(meta["stale_after"])
