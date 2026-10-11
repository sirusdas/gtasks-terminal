#!/usr/bin/env bash
# ==============================================================================
# GTasks Flutter App - Build & Wireless/USB Deploy Script
# ==============================================================================
# Usage:
#   ./deploy_app.sh                 # Automatically finds connected device, builds, installs, and launches
#   ./deploy_app.sh <DEVICE_ID>     # Deploys to specific device (e.g. 192.168.1.3:39379)
#   ./deploy_app.sh --build-only    # Only runs tests and builds the debug APK
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/gtasks_app"
APK_PATH="${APP_DIR}/build/app/outputs/flutter-apk/app-debug.apk"
PACKAGE_NAME="com.gtasks.gtasks_app"
ACTIVITY_NAME=".MainActivity"
REVERSE_PORT="48275"

DEVICE="${1:-}"

echo "=================================================="
echo "  GTasks App Build & Deploy Automation"
echo "=================================================="

# Check directory
if [ ! -d "${APP_DIR}" ]; then
  echo "[-] Error: ${APP_DIR} does not exist."
  exit 1
fi

cd "${APP_DIR}"

# 1. Run Flutter Tests
echo "[1/4] Running Flutter unit & widget tests..."
flutter test

# 2. Build Debug APK
echo "[2/4] Compiling Debug APK..."
flutter build apk --debug

if [ ! -f "${APK_PATH}" ]; then
  echo "[-] Build failed: APK not found at ${APK_PATH}"
  exit 1
fi
echo "[+] Build completed successfully: ${APK_PATH}"

if [ "${DEVICE}" = "--build-only" ]; then
  echo "[+] Build-only flag specified. Skipping device installation."
  exit 0
fi

# 3. Detect ADB Device
if [ -z "${DEVICE}" ]; then
  # Grab first online device from adb devices
  DEVICE=$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')
fi

if [ -z "${DEVICE}" ]; then
  echo "[-] No connected ADB devices found."
  echo "    Ensure USB debugging or Wireless ADB is connected (e.g., adb connect <ip>:<port>)."
  exit 1
fi

echo "[3/4] Target device: ${DEVICE}"

# Set up port reverse for direct communication with local GTasks server
echo "[+] Setting up reverse port ${REVERSE_PORT} -> ${REVERSE_PORT} on ${DEVICE}..."
adb -s "${DEVICE}" reverse "tcp:${REVERSE_PORT}" "tcp:${REVERSE_PORT}" || true

# 4. Install & Launch
echo "[4/4] Pushing APK to device and installing..."
adb -s "${DEVICE}" push "${APK_PATH}" /data/local/tmp/gtasks-debug.apk
adb -s "${DEVICE}" shell pm install -r --user 0 /data/local/tmp/gtasks-debug.apk
adb -s "${DEVICE}" shell rm -f /data/local/tmp/gtasks-debug.apk

echo "[+] Restarting ${PACKAGE_NAME}..."
adb -s "${DEVICE}" shell am force-stop "${PACKAGE_NAME}" || true
adb -s "${DEVICE}" shell am start -n "${PACKAGE_NAME}/${ACTIVITY_NAME}" --user 0

echo "=================================================="
echo "  Deployment Complete! App running on ${DEVICE}"
echo "=================================================="
