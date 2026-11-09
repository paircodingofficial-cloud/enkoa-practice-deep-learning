# 웹 페이지 한 장을 보내는 이미지(Docker 기초 교안)

# (1) 베이스 이미지: 파이썬 3.12 slim 버전
FROM python:3.12-slim

# (2) 작업 폴더
WORKDIR /app

# (3) 웹 페이지 파일을 이미지 안으로 복사합니다
COPY index.html .

# (4) 컨테이너가 쓰는 포트 표시
EXPOSE 8080

# (5) 실행 명령: 파이썬 내장 웹 서버로 /app 의 파일을 8080 포트에서 보냅니다
CMD ["python", "-m", "http.server", "8080"]
