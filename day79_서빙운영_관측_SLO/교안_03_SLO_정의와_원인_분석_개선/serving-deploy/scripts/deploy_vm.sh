#!/usr/bin/env bash
# 첫 줄(#!)은 이 파일을 bash 로 실행하라고 알린다
# GitHub Actions 의 deploy 작업이 GCP VM 에 새 이미지를 배포하고 확인하는 스크립트(교안 03)
# 필요한 환경 변수: VM_SSH_KEY(배포용 개인 키), VM_HOST(VM 외부 IP), VM_USER(VM 사용자 이름), IMAGE_TAG(배포할 이미지 태그)
# 명령 하나라도 실패하거나 없는 변수를 쓰면 멈춰, deploy 작업이 실패로 끝난다
set -euo pipefail                                 # -e: 명령이 실패하면 멈춘다, -u: 정하지 않은 변수를 쓰면 멈춘다, -o pipefail: 파이프(|)의 명령 중 하나라도 실패하면 전체를 실패로 본다

# 0) 필요한 값이 비어 있으면 무엇이 빠졌는지 알리고 멈춘다(등록하지 않은 변수는 빈 글자로 들어온다)
#    : 는 아무 일도 하지 않는 명령이고, ${이름:?문장} 이 값이 없거나 비었을 때 문장을 오류로 찍고 멈춘다
: "${VM_SSH_KEY:?비밀 변수 VM_SSH_KEY 가 비었습니다}"   # 배포용 개인 키
: "${VM_HOST:?변수 VM_HOST 가 비었습니다}"        # VM 외부 IP
: "${VM_USER:?변수 VM_USER 가 비었습니다}"        # VM 사용자 이름

# 태그는 커밋 sha(16진수 40자리)만 받는다. 태그 값이 VM 의 명령 줄에 그대로 들어가므로 다른 글자를 막는다
if [[ ! "$IMAGE_TAG" =~ ^[0-9a-f]{40}$ ]]; then   # 16진수 40자리가 아니면 아래 두 줄을 실행한다
  echo "IMAGE_TAG 는 커밋 sha 전체(16진수 40자리)여야 합니다: $IMAGE_TAG"   # 받은 값을 보여 준다
  exit 1                                          # 실패로 멈춘다
fi

# VM 안의 저장소 폴더, compose 서비스 이름, 확인할 포트
APP_DIR="serving-deploy"                          # VM 홈 폴더 안의 저장소 폴더 이름
SERVICE="serving-api"                             # compose.yaml 의 서비스 이름
PORT="8080"                                       # 배포 확인 요청을 보낼 포트

# 1) 비밀 변수의 개인 키를 러너의 파일로 저장한다(값은 로그에 찍지 않는다)
mkdir -p ~/.ssh                                   # 러너에 ~/.ssh 폴더를 만든다(있으면 그대로 둔다)
printf '%s\n' "$VM_SSH_KEY" > ~/.ssh/deploy_key   # 개인 키를 줄바꿈까지 그대로 파일에 쓴다. 화면에 찍지 않아 로그에 남지 않는다
chmod 600 ~/.ssh/deploy_key                       # 소유자만 읽고 쓰게 한다. ssh 는 다른 사용자도 읽을 수 있는 개인 키를 쓰지 않는다
# 러너는 처음 접속 때 묻는 확인(yes/no)에 답할 수 없어, VM 의 호스트 키를 known_hosts 에 미리 넣는다
if ! ssh-keyscan -H "$VM_HOST" >> ~/.ssh/known_hosts; then   # -H: 호스트 이름을 해시로 적는다. 받지 못하면 아래 두 줄을 실행한다
  echo "VM($VM_HOST) 의 22번 포트에서 호스트 키를 받지 못했습니다. VM 이 켜져 있는지, VM_HOST 가 맞는지 봅니다"   # 확인할 점을 알린다
  exit 1                                          # 실패로 멈춘다
fi
SSH="ssh -i $HOME/.ssh/deploy_key $VM_USER@$VM_HOST"   # 배포 키로 VM 에 접속하는 명령. 뒤에서 $SSH "명령" 으로 VM 에서 명령을 실행한다

# 2) VM 의 deploy 폴더에서 새 태그의 이미지를 받고(pull) 컨테이너를 바꾼다(up -d). compose.yaml 의 ${IMAGE_TAG:-latest} 가 이 sha 가 된다
$SSH "cd ~/$APP_DIR/deploy && IMAGE_TAG=$IMAGE_TAG docker compose pull $SERVICE && IMAGE_TAG=$IMAGE_TAG docker compose up -d $SERVICE"

# 3) 지금 도는 컨테이너가 방금 받은 이미지인지 확인한다(옛 컨테이너가 /healthz 에 답해 성공으로 보이는 것을 막는다)
#    VM 에서 serving-api 컨테이너(ps -q)를 만든 이미지 이름을 RUNNING 에 담는다. \$ 는 $(...) 를 러너가 아니라 VM 에서 실행하게 한다
RUNNING=$($SSH "cd ~/$APP_DIR/deploy && docker inspect --format '{{.Config.Image}}' \$(docker compose ps -q $SERVICE)")
echo "실행 중인 이미지: $RUNNING"                 # 로그에 실행 중인 이미지 이름을 찍는다
case "$RUNNING" in                                # 이미지 이름 모양에 따라 나눈다
  *":$IMAGE_TAG") ;;                              # 이름이 ":이번 커밋 sha" 로 끝나면 그대로 지나간다
  *) echo "실행 중인 컨테이너가 $IMAGE_TAG 이미지가 아닙니다"; exit 1 ;;   # 그 밖이면 새 이미지가 아니라고 알리고 실패로 멈춘다
esac

# 4) /healthz 가 200 을 돌려줄 때까지 2초마다, 최대 30번 확인한다
for attempt in $(seq 1 30); do                    # done 까지의 줄을 최대 30번 되풀이한다
  if curl -fsS --max-time 5 "http://$VM_HOST:$PORT/healthz"; then   # 러너에서 VM 의 /healthz 로 요청한다(--max-time 5: 한 번에 5초를 넘기면 끊는다). 성공하면 아래 세 줄을 실행한다
    echo                                          # 줄을 바꾼다
    echo "배포 확인: $IMAGE_TAG 이미지가 /healthz 에 응답합니다"
    exit 0                                        # 성공으로 끝낸다(deploy 작업도 성공)
  fi
  sleep 2                                         # 2초 기다린 뒤 다시 요청한다
done
echo "/healthz 가 응답하지 않습니다. VM 에서 docker compose logs $SERVICE 로 원인을 봅니다"   # 30번 모두 실패하면 원인을 볼 명령을 알린다
exit 1                                            # 실패로 끝낸다
