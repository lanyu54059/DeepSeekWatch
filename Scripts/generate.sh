#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! command -v xcodegen >/dev/null 2>&1; then
  brew install xcodegen
fi
xcodegen --version
python3 Scripts/icons.py
xcodegen generate --spec project.yml
xcodebuild -list -project DeepSeekWatch.xcodeproj
