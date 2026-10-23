#!/usr/bin/env bash
# Send input to the device. Wraps `adb shell input` with a timeout.
# usage: ./in.sh tap X Y
#        ./in.sh swipe X1 Y1 X2 Y2 MS
#        ./in.sh keyevent KEYCODE
# For bursts, pass a whole shell snippet:
#        ./in.sh burst 'input tap 2250 980; sleep 0.3; input tap 2010 980'
# env:   ADB, ADB_SERIAL as in cap.sh
set -u
SERIAL="${ADB_SERIAL:-emulator-5554}"
ADB="${ADB:-$(command -v adb || echo "$HOME/Library/Android/sdk/platform-tools/adb")}"
if [ "${1:-}" = "burst" ]; then
  shift
  perl -e 'alarm 60; exec @ARGV' "$ADB" -s "$SERIAL" shell "$1"
else
  perl -e 'alarm 60; exec @ARGV' "$ADB" -s "$SERIAL" shell input "$@"
fi
