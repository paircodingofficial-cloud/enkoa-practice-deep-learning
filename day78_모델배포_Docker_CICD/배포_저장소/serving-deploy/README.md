# serving-deploy

노무, 전월세 상담 서빙 API를 Docker 이미지로 만들어 GCP VM에 배포하는 저장소입니다.

| 폴더, 파일 | 내용 |
|---|---|
| `serving_app/` | 서빙 API 코드(FastAPI) |
| `Dockerfile`, `.dockerignore` | 서빙 API 이미지를 만드는 설정 |
| `pyproject.toml`, `uv.lock` | 서버를 실행하는 라이브러리와 고정한 버전 |
| `deploy/` | VM에서 컨테이너를 띄우는 compose 설정과 환경 변수 예시 |
| `tests/` | CI가 실행하는 테스트. `test_unit.py`는 unit 작업(코드만), `test_api.py`는 image 작업(빌드한 이미지로 띄운 컨테이너) |
| `scripts/` | CD(cd.yml)의 deploy 작업이 VM에 새 이미지를 띄울 때 쓰는 스크립트 |
| `workflows/` | 교안에서 `.github/workflows/`로 복사해 켜는 워크플로(`image.yml`은 교안 01, `ci.yml`과 `cd.yml`은 교안 03). GitHub은 `.github/workflows/` 안의 워크플로만 실행하므로, `workflows/`에 둔 파일은 복사하기 전까지 실행되지 않습니다 |
| `.github/workflows/` | GitHub이 실행하는 워크플로 자리. 처음에는 비어 있고(빈 폴더를 git에 남기려는 빈 파일 `.gitkeep`만 있음), 교안에서 `workflows/`의 파일을 복사해 넣습니다 |
