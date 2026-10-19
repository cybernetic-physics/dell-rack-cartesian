#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/remote.sh 'mkdir -p /mnt/stateful_partition/home/hadjiyiannis_3_gmail_com/dell-rack'
COPYFILE_DISABLE=1 tar --no-xattrs --exclude='./vendor' --exclude='./.venv' --exclude='./.git' --exclude='./artifacts' --exclude='./research/*.pdf' --exclude='__pycache__' -czf - . | \
  gcloud compute ssh --zone us-central1-b isaac-g4-rtxpro6000x2-flex \
  --project project-512201fe-6308-4879-83c --quiet \
  --command='sudo tar -xzf - -C /mnt/stateful_partition/home/hadjiyiannis_3_gmail_com/dell-rack'
