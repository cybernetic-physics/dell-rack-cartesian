#!/usr/bin/env bash
# Run on the existing COS VM after scripts/sync.sh.
set -euo pipefail
cd /mnt/stateful_partition/home/hadjiyiannis_3_gmail_com/dell-rack
mkdir -p artifacts/logs cache vendor
if [ ! -d vendor/IsaacAutomator/.git ]; then
  git clone --branch devcontainer --single-branch https://github.com/boredengineering/IsaacAutomator.git vendor/IsaacAutomator
fi
git -C vendor/IsaacAutomator rev-parse HEAD
sudo docker build -t dell-rack-sim:6.0.1 -f infra/Dockerfile .
if [ "${1:-}" = '--recreate' ] && sudo docker container inspect dell-rack-sim >/dev/null 2>&1; then
  # Preserve the old application container for recovery; bind-mounted data stays in place.
  sudo docker stop dell-rack-sim
  sudo docker rename dell-rack-sim "dell-rack-sim-backup-$(date -u +%Y%m%dT%H%M%S)"
fi
if sudo docker container inspect dell-rack-sim >/dev/null 2>&1; then
  if [ "$(sudo docker inspect -f '{{.Image}}' dell-rack-sim)" != "$(sudo docker image inspect -f '{{.Id}}' dell-rack-sim:6.0.1)" ]; then
    echo 'Image changed. Close the simulation, then run infra/start.sh --recreate to preserve and replace only this application container.' >&2
    exit 1
  fi
  sudo docker start dell-rack-sim
else
  sudo docker run -d --name dell-rack-sim --restart unless-stopped \
    --gpus all --shm-size=4g -e NVIDIA_DRIVER_CAPABILITIES=all \
    -p 127.0.0.1:6080:6080 -p 127.0.0.1:8080:8080 \
    -v "$PWD:/workspace" -v "$PWD/cache:/root/.cache" dell-rack-sim:6.0.1
fi
