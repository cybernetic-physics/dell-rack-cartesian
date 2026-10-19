#!/usr/bin/env bash
set -euo pipefail
printf 'Desktop: http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale\nArtifacts: http://127.0.0.1:18080/\n'

# Reuse a working connection; never kill an existing listener automatically.
listeners=$(lsof -nP -iTCP:16080 -iTCP:18080 -sTCP:LISTEN 2>/dev/null || true)
if [[ -n "$listeners" ]]; then
  desktop=$(curl --noproxy '*' -fsS --max-time 4 http://127.0.0.1:16080/vnc.html 2>/dev/null || true)
  artifacts=$(curl --noproxy '*' -fsS --max-time 4 http://127.0.0.1:18080/ 2>/dev/null || true)
  if [[ "$desktop" == *noVNC* && "$artifacts" == *'Dell rack'* ]]; then
    printf '\nAlready connected: both demo services are responding. Open the desktop link above.\nNo new tunnel was started; leave the existing tunnel running.\n'
    exit 0
  fi
  printf '\nPorts 16080/18080 are occupied, but both demo services could not be verified.\nNo processes were stopped. Inspect these listeners before retrying:\n%s\n' "$listeners" >&2
  exit 1
fi

printf 'Starting SSH tunnel. Keep this terminal open.\n'
exec gcloud compute ssh --zone us-central1-b isaac-g4-rtxpro6000x2-flex \
  --project project-512201fe-6308-4879-83c --quiet -- \
  -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 127.0.0.1:16080:127.0.0.1:6080 -L 127.0.0.1:18080:127.0.0.1:8080
