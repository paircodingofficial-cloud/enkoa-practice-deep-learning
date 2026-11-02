"""OKF 번들을 검사한다(표준 라이브러리만 씀). 문서는 고치지 않는다.

사용: 작업 폴더에서 python3 <스킬 폴더>/scripts/check.py
검사: 적합성(frontmatter, type, index.md, log.md 날짜 제목), 끊긴 링크, 만료(stale_after), 없는 원문(raw://)
"""
import re
from pathlib import Path

TODAY = "2026-11-02"  # 샘플 위키의 '오늘'
work = Path.cwd()
problems = []


def frontmatter_lines(text):
    """맨 위 --- 두 줄 사이의 줄 목록을 돌려줍니다. frontmatter가 없으면 None입니다."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return None


for bundle_dir in sorted((work / "bundles").iterdir()):
    if not (bundle_dir / "index.md").is_file():
        continue
    bundle = bundle_dir.name
    for path in sorted(bundle_dir.rglob("*.md")):
        rel = path.relative_to(bundle_dir).as_posix()
        text = path.read_text(encoding="utf-8")
        meta = frontmatter_lines(text)

        # 예약 파일: 폴더 목차에는 frontmatter 없음, 변경 기록의 날짜 제목은 YYYY-MM-DD
        if path.name == "index.md":
            if rel != "index.md" and meta is not None:
                problems.append((bundle, "적합성", rel, "폴더 목차에 frontmatter가 있음"))
            continue
        if path.name == "log.md":
            for line in text.splitlines():
                if line.startswith("## ") and not re.fullmatch(r"## \d{4}-\d{2}-\d{2}", line.strip()):
                    problems.append((bundle, "적합성", rel, "날짜 제목이 YYYY-MM-DD가 아님: " + line.strip()))
            continue

        # 개념 문서: frontmatter와 비어 있지 않은 type
        if meta is None:
            problems.append((bundle, "적합성", rel, "frontmatter 없음"))
            continue
        type_value = ""
        for line in meta:
            if line.startswith("type:"):
                type_value = line[5:].strip()
        if type_value == "":
            problems.append((bundle, "적합성", rel, "type 없음"))

        # 만료: stale_after가 오늘보다 앞
        for line in meta:
            if line.startswith("stale_after:"):
                day = line[12:].strip().strip('"').strip("'")[:10]
                if day < TODAY:
                    problems.append((bundle, "만료", rel, "stale_after " + day))

        # 없는 원문: sources의 raw:// 가 raw/ 에 있는지
        for name in re.findall(r"raw://([^\s\"',}]+)", "\n".join(meta)):
            if not (work / "raw" / name).is_file():
                problems.append((bundle, "없는 원문", rel, "raw://" + name))

        # 끊긴 링크: 번들 맨 위 기준 /폴더/파일.md
        for target in re.findall(r"\]\((/[^)#\s]+\.md)\)", text):
            if not (bundle_dir / target.lstrip("/")).is_file():
                problems.append((bundle, "끊긴 링크", rel, target))

print("번들 | 점검 | 문서 | 내용")
for row in problems:
    print(" | ".join(row))
print(f"문제 {len(problems)}개")
