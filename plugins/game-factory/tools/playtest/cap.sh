#!/usr/bin/env bash
# Capture the device screen and a downscaled copy.
# usage: ./cap.sh NNN   -> $SESSION_DIR/NNN.png and $SESSION_DIR/small/NNN.jpg
# env:   SESSION_DIR  output folder (default: current directory)
#        ADB          path to adb (default: adb from PATH, else ~/Library/Android/sdk/platform-tools/adb)
#        ADB_SERIAL   device serial (default: emulator-5554)
#        SCALE_DIV    downscale divisor for the small copy (default: 2)
set -u
NAME="${1:?usage: cap.sh NNN}"
DIR="${SESSION_DIR:-$PWD}"
SERIAL="${ADB_SERIAL:-emulator-5554}"
ADB="${ADB:-$(command -v adb || echo "$HOME/Library/Android/sdk/platform-tools/adb")}"
DIV="${SCALE_DIV:-2}"
mkdir -p "$DIR/small"

# macOS has no `timeout`: perl alarm is the portable version. Retry once, adb is flaky.
shot() { perl -e 'alarm 60; exec @ARGV' "$ADB" -s "$SERIAL" exec-out screencap -p > "$DIR/$NAME.png"; }
shot || shot
ffmpeg -loglevel error -y -i "$DIR/$NAME.png" -vf "scale=iw/$DIV:-1" "$DIR/small/$NAME.jpg"
date +%H:%M
