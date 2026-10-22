#!/usr/bin/env python3
"""실습자료 업데이트와 실습 환경 준비 도우미.

저장소 폴더에서 아래 한 줄을 실행하면 다음을 차례로 합니다.

    uv run 업데이트.py

1. 최신 자료 받기: 배포된 원본 파일을 서버의 최신 판으로 맞춥니다.
   `git pull` 이 충돌로 막혔을 때도 이 파일로 풀립니다.
   '내작업/' 폴더와 여러분이 만든 파일은 건드리지 않고,
   되돌리기 전에 바뀐 내용은 '.백업/날짜_시각/' 에 그대로 보관합니다.
2. 파이썬 환경 맞추기: `uv sync` 로 pyproject.toml, uv.lock 에 적힌 패키지를 설치합니다.
3. 리눅스(RunPod)에서만: 그래프 한글 글꼴(나눔고딕)을 설치하고, matplotlib 글꼴 목록을 새로 만들게 하고,
   Jupyter Lab 에서 쓸 수 있게 .venv 를 커널(venv)로 등록합니다.
"""
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BACKUP_ROOT = Path(".백업")


def git(*args: str) -> subprocess.CompletedProcess:
    """git 명령을 실행하고 결과를 돌려준다."""
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


def fail(message: str, hint: str = "") -> None:
    print(f"\n❌ {message}")
    if hint:
        print(f"   {hint}")
    print("\n해결되지 않으면 이 화면을 그대로 강사님께 보여주세요.")
    sys.exit(1)


def run(command: list) -> bool:
    """명령을 실행하고 화면에 출력을 그대로 보여 준다. 성공하면 True."""
    print("   $ " + " ".join(command))
    return subprocess.run(command).returncode == 0


def nanum_installed() -> bool:
    """나눔고딕 글꼴 파일이 시스템 글꼴 폴더에 있는지 본다."""
    for folder in ["/usr/share/fonts", "/usr/local/share/fonts", str(Path.home() / ".fonts")]:
        if list(Path(folder).glob("**/NanumGothic*.ttf")):
            return True
    return False


def setup_linux_fonts() -> None:
    """리눅스(RunPod)에서 나눔고딕을 설치하고 matplotlib 글꼴 목록 캐시를 지운다."""
    print("\n그래프 한글 글꼴(나눔고딕)을 확인하는 중...")
    if nanum_installed():
        print("   이미 설치되어 있습니다.")
    else:
        # RunPod 파드는 root 로 접속하므로 apt-get 을 바로 쓰고, root 가 아니면 sudo 를 붙인다
        prefix = []
        if os.geteuid() != 0:
            if shutil.which("sudo") is None:
                print("   관리자 권한이 없어 글꼴을 설치하지 못했습니다. 관리자에게 아래 명령을 부탁하세요.")
                print("   apt-get update && apt-get install -y fonts-nanum")
                return
            prefix = ["sudo"]
        ok = run(prefix + ["apt-get", "update"]) and run(prefix + ["apt-get", "install", "-y", "fonts-nanum"])
        if not ok or not nanum_installed():
            print("   글꼴을 설치하지 못했습니다. 위 메시지를 강사님께 보여 주세요.")
            return
        print("   설치했습니다.")

    # matplotlib 은 처음 쓸 때 만든 글꼴 목록을 캐시 파일로 저장해 두고 계속 쓴다.
    # 글꼴을 설치하기 전에 만든 목록에는 나눔고딕이 없으므로 지워서 다시 만들게 한다
    if os.environ.get("MPLCONFIGDIR"):
        cache_dir = Path(os.environ["MPLCONFIGDIR"])
    else:
        cache_dir = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "matplotlib"
    removed = 0
    for cache_file in cache_dir.glob("fontlist-*.json"):
        cache_file.unlink()
        removed += 1
    print(f"   matplotlib 글꼴 목록 캐시 {removed}개를 지웠습니다(다음 실행 때 새로 만듭니다).")


def register_kernel() -> None:
    """Jupyter Lab 에서 고를 수 있게 .venv 를 'venv' 커널로 등록한다."""
    print("\nJupyter Lab 커널(venv)을 등록하는 중...")
    # uv run 으로 실행됐으므로 sys.executable 이 저장소의 .venv 파이썬이다
    if run([sys.executable, "-m", "ipykernel", "install", "--user", "--name", "venv"]):
        print("   등록했습니다. Jupyter Lab 에서는 커널 'venv' 를 고릅니다. VS Code 에서는 .venv 를 고릅니다.")
    else:
        print("   등록하지 못했습니다. VS Code 로 실습한다면 이 단계는 없어도 됩니다.")


def setup_environment() -> None:
    """uv sync 로 패키지를 맞추고, 리눅스라면 글꼴과 커널까지 준비한다."""
    print("\n파이썬 환경을 맞추는 중(uv sync)...")
    if not run(["uv", "sync"]):
        fail("uv sync 가 실패했습니다.", "위 메시지를 확인하고, 인터넷 연결을 확인해 주세요.")

    if platform.system() == "Linux":
        setup_linux_fonts()
        register_kernel()
    else:
        print(f"\n{platform.system()} 이라 글꼴 설치와 커널 등록은 건너뜁니다(리눅스 RunPod 에서만 합니다).")


def main() -> None:
    # 안내 문구와 uv, apt-get 출력이 화면에 순서대로 나오게 한 줄씩 바로 내보낸다
    sys.stdout.reconfigure(line_buffering=True)
    print("실습자료 업데이트와 실습 환경 준비 도우미")
    print("─" * 46)

    # 저장소 폴더 안에서 실행됐는지 확인 (더블클릭 실행 대비)
    here = Path(__file__).resolve().parent
    os.chdir(here)

    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        fail(
            "여기는 git 저장소가 아닙니다.",
            "git clone 으로 내려받은 'enkoa-practice' 폴더 안에서 실행하세요.",
        )

    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"

    print("최신 정보를 확인하는 중...")
    fetched = git("fetch", "origin")
    if fetched.returncode != 0:
        fail("서버에서 자료를 가져오지 못했습니다.", "인터넷 연결을 확인해 주세요.")

    remote = f"origin/{branch}"
    if git("rev-parse", "--verify", remote).returncode != 0:
        fail(f"서버에 '{branch}' 브랜치가 없습니다.")

    # 원격과 다른 배포 파일을 모두 찾는다 (수정·staged·직접 커밋한 것까지 포함)
    # -z 로 받아야 한글 파일명이 "\353\263\200" 처럼 escape 되지 않는다
    diff = git("diff", "--name-only", "-z", remote)
    changed = [name for name in diff.stdout.split("\0") if name.strip()]

    if changed:
        stamp = datetime.now().strftime("%m%d_%H%M")
        dest = BACKUP_ROOT / stamp
        print(f"\n배포 원본이 바뀐 파일 {len(changed)}개를 '{dest}' 에 보관합니다:")
        saved, missing = 0, []
        for rel in changed:
            src = Path(rel)
            if not src.is_file():
                # 서버에서 지워진 파일 등: 되돌려도 잃을 내용이 없다
                missing.append(rel)
                continue
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            saved += 1
            print(f"   - {rel}")

        if saved:
            print("   (여기서 필요한 내용을 꺼내 '내작업/' 으로 옮기세요)")
        if missing:
            print(f"   ※ 보관할 실물이 없는 항목 {len(missing)}개는 건너뛰었습니다.")
        if saved == 0 and not missing:
            fail(
                "바뀐 파일을 보관하지 못했습니다.",
                "되돌리면 작업 내용이 사라질 수 있어 중단합니다.",
            )
    else:
        print("되돌릴 파일이 없습니다.")

    print("\n배포 원본을 되돌리고 새 자료를 받는 중...")
    reset = git("reset", "--hard", remote)
    if reset.returncode != 0:
        fail("자료를 되돌리지 못했습니다.", reset.stderr.strip())

    print("   최신 자료를 받았습니다.")

    setup_environment()

    print("─" * 46)
    print("✅ 업데이트 완료!")
    print("   '내작업/' 폴더와 직접 만든 파일은 그대로 있습니다.")
    if changed:
        print("   앞으로는 자료를 '내작업/' 에 복사한 뒤 실습해 주세요.")
    print("   열려 있던 노트북이 있으면 커널을 다시 시작(Restart)한 뒤 실행하세요.")


if __name__ == "__main__":
    main()
