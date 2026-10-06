#!/usr/bin/env bash
# 06/10/2026: o "apt-get install ffmpeg" travou 17+ min no Actions (espelho lento)
# e matou o repor_fila varios dias seguidos SEM o agendador rodar. Agora:
# 1) ffmpeg ja' instalado? usa. 2) binario estatico (teto 3 min). 3) apt com teto de 5 min.
set -u
if command -v ffmpeg >/dev/null 2>&1; then echo "ffmpeg ja' presente"; exit 0; fi
mkdir -p "$HOME/bin"
if curl -fsSL --max-time 180 -o /tmp/ff.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
   && tar -xJf /tmp/ff.tar.xz -C /tmp && cp /tmp/ffmpeg-*-static/ffmpeg /tmp/ffmpeg-*-static/ffprobe "$HOME/bin/"; then
  echo "$HOME/bin" >> "${GITHUB_PATH:-/dev/null}"; echo "ffmpeg estatico ok"; exit 0
fi
echo "::warning::ffmpeg estatico falhou; tentando apt com teto de 5 min"
timeout 300 sudo apt-get install -y -qq ffmpeg && exit 0
echo "::error::ffmpeg nao instalou (estatico e apt falharam)"; exit 1
