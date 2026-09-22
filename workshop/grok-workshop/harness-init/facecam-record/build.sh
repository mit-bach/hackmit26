#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
SRC="$ROOT/Sources"
RES="$ROOT/Resources"
DIST="$ROOT/dist"
APPNAME="FaceCam Record"
EXEC="FaceCamRecord"
APP="$DIST/$APPNAME.app"
BIN="$APP/Contents/MacOS/$EXEC"

rm -rf "$DIST"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

echo "Compiling…"
xcrun swiftc -O \
  -target arm64-apple-macosx13.0 \
  -sdk "$(xcrun --show-sdk-path)" \
  -framework AppKit \
  -framework AVFoundation \
  -framework CoreGraphics \
  -framework QuartzCore \
  -framework UserNotifications \
  -o "$BIN" \
  "$SRC/main.swift" \
  "$SRC/OverlayPanel.swift" \
  "$SRC/Recorder.swift" \
  "$SRC/AppDelegate.swift"

printf 'APPL????' > "$APP/Contents/PkgInfo"
cp "$ROOT/Info.plist" "$APP/Contents/Info.plist"

if [[ -f "$RES/AppIcon.icns" ]]; then
  cp "$RES/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
fi

codesign --force --deep --sign - "$APP" >/dev/null
echo "Built $APP"
