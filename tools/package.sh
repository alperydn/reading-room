#!/usr/bin/env sh
# claude.ai'ye yüklenecek skill zip'ini üretir: dist/reading-room-skill.zip
set -e
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist
find plugins -name __pycache__ -type d -exec rm -rf {} +
(cd plugins/reading-room/skills && zip -rq ../../../dist/reading-room-skill.zip reading-room -x '*.DS_Store')
echo "dist/reading-room-skill.zip"
