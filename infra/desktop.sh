#!/usr/bin/env bash
set -euo pipefail
mkdir -p /workspace/artifacts/logs
cp /workspace/infra/preview.html /workspace/artifacts/index.html
Xvfb :99 -screen 0 1600x1000x24 -s 0 -ac -nolisten tcp > /workspace/artifacts/logs/xvfb.log 2>&1 &
for i in {1..50}; do xdpyinfo >/dev/null 2>&1 && break; sleep .2; done
python3 /workspace/infra/disable_screen_saver.py
fluxbox > /workspace/artifacts/logs/fluxbox.log 2>&1 &
x11vnc -display :99 -localhost -rfbport 5900 -forever -shared -nopw -noxdamage > /workspace/artifacts/logs/vnc.log 2>&1 &
websockify --web=/usr/share/novnc 6080 localhost:5900 > /workspace/artifacts/logs/novnc.log 2>&1 &
python3 -m http.server 8080 --directory /workspace/artifacts > /workspace/artifacts/logs/http.log 2>&1 &
wait -n
