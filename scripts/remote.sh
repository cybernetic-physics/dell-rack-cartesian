#!/usr/bin/env bash
set -euo pipefail
exec gcloud compute ssh --zone us-central1-b isaac-g4-rtxpro6000x2-flex \
  --project project-512201fe-6308-4879-83c --quiet --command="$*"
