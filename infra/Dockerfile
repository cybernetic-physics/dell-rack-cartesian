FROM nvcr.io/nvidia/isaac-sim@sha256:783444c706538aa76cf5126e911ddc5e618779e6105305ad4af4260362a30aa9
USER root
ENV DEBIAN_FRONTEND=noninteractive DISPLAY=:99 ACCEPT_EULA=Y PRIVACY_CONSENT=N
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb fluxbox x11vnc novnc websockify x11-utils xdotool ffmpeg \
    python3-pil python3-websocket git curl fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD curl -fsS http://127.0.0.1:6080/vnc.html >/dev/null && curl -fsS http://127.0.0.1:8080/ >/dev/null && xdpyinfo >/dev/null
ENTRYPOINT ["bash", "/workspace/infra/desktop.sh"]
