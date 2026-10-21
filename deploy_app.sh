#!/usr/bin/env bash
# ==============================================================================
# GTasks Flutter App - Build & Wireless/USB Deploy Script
# ==============================================================================
# Usage:
#   ./deploy_app.sh                 # Automatically finds connected device, builds/downloads, installs, and launches
#   ./deploy_app.sh <DEVICE_ID>     # Deploys to specific device (e.g. 127.0.0.1:43217)
#   ./deploy_app.sh --build-only    # Only runs tests and builds the debug APK
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}/gtasks_app"
APK_PATH="${APP_DIR}/build/app/outputs/flutter-apk/app-debug.apk"
FALLBACK_APK="/data/data/com.termux/files/home/downloads/gtasks-app-debug.apk"
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

# 1. Validation / Testing
echo "[1/4] Validating Flutter code..."
if [ -d "/data/data/com.termux" ]; then
  flutter analyze || true
else
  flutter test || true
fi

# 2. Build or Fetch Debug APK
echo "[2/4] Preparing Debug APK..."
if [ -d "/data/data/com.termux" ] && [ ! -d "/data/data/com.termux/files/home/Android/Sdk/platforms" ]; then
  echo "[i] Running in Termux without native Android SDK. Checking GitHub Actions build..."
  mkdir -p "$(dirname "${FALLBACK_APK}")"
  DOWNLOAD_URL=$(curl -s "https://api.github.com/repos/sirusdas/gtasks-terminal/releases/tags/nightly-build" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for a in data.get('assets', []):
        if a['name'] == 'app-debug.apk':
            print(a['browser_download_url'])
            sys.exit(0)
except Exception:
    pass
" 2>/dev/null || true)

  if [ -z "${DOWNLOAD_URL}" ]; then
    DOWNLOAD_URL="https://github.com/sirusdas/gtasks-terminal/releases/download/nightly-build/app-debug.apk"
  fi

  if [ -n "${DOWNLOAD_URL}" ]; then
    echo "[+] Downloading fresh APK from GitHub Actions release..."
    curl -L -o "${FALLBACK_APK}" "${DOWNLOAD_URL}"
    APK_PATH="${FALLBACK_APK}"
  elif [ -f "${FALLBACK_APK}" ]; then
    echo "[+] Using existing cached APK at ${FALLBACK_APK}"
    APK_PATH="${FALLBACK_APK}"
  else
    echo "[-] No APK available locally or remotely."
    exit 1
  fi
else
  flutter build apk --debug
  if [ ! -f "${APK_PATH}" ]; then
    if [ -f "${FALLBACK_APK}" ]; then
      APK_PATH="${FALLBACK_APK}"
    else
      echo "[-] Build failed: APK not found at ${APK_PATH}"
      exit 1
    fi
  fi
fi
echo "[+] Target APK: ${APK_PATH} ($(ls -lh "${APK_PATH}" | awk '{print $5}'))"

if [ "${DEVICE}" = "--build-only" ]; then
  echo "[+] Build-only flag specified. Skipping device installation."
  exit 0
fi

# 3. Detect ADB Device
if [ -z "${DEVICE}" ]; then
  DEVICE=$(adb devices | awk 'NR>1 && $2=="device" {print $1; exit}')
fi

# Auto-discover wireless debugging if not connected
if [ -z "${DEVICE}" ]; then
  echo "[i] No ADB device connected. Scanning for Wireless Debugging port..."
  # Clean up any offline devices first
  adb devices | awk 'NR>1 && $2=="offline" {print $1}' | while read -r offdev; do
    adb disconnect "$offdev" >/dev/null 2>&1 || true
  done

  TARGETS=$(python3 -c "
import socket
from concurrent.futures import ThreadPoolExecutor

ips = ['127.0.0.1']
try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 80))
        ips.append(s.getsockname()[0])
except:
    pass

found = []
def check_port(target):
    ip, p = target
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.04)
            if s.connect_ex((ip, p)) == 0:
                found.append(f'{ip}:{p}')
    except:
        pass

targets = [(ip, p) for ip in set(ips) for p in range(30000, 65535) if p != 48275]
with ThreadPoolExecutor(max_workers=400) as ex:
    ex.map(check_port, targets)

for f in found:
    print(f)
" 2>/dev/null || true)

  for t in ${TARGETS}; do
    adb connect "${t}" >/dev/null 2>&1 || true
    DEVICE=$(adb devices | awk -v target="${t}" '$1==target && $2=="device" {print $1; exit}')
    if [ -n "${DEVICE}" ]; then
      echo "[+] Successfully connected to Wireless Debugging on ${t}"
      break
    fi
  done
fi

if [ -z "${DEVICE}" ]; then
  echo "[-] No connected ADB devices found."
  echo "    Ensure Wireless Debugging is on (e.g., adb connect 127.0.0.1:<port>)."
  exit 1
fi

echo "[3/4] Target device: ${DEVICE}"

# Set up port reverse for direct communication with local GTasks server
echo "[+] Setting up reverse port ${REVERSE_PORT} -> ${REVERSE_PORT} on ${DEVICE}..."
adb -s "${DEVICE}" reverse "tcp:${REVERSE_PORT}" "tcp:${REVERSE_PORT}" || true

# 4. Install & Launch
echo "[4/4] Installing APK directly to device via streamed install..."
adb -s "${DEVICE}" install -r "${APK_PATH}"

echo "[+] Restarting ${PACKAGE_NAME}..."
adb -s "${DEVICE}" shell am force-stop "${PACKAGE_NAME}" || true
adb -s "${DEVICE}" shell am start -n "${PACKAGE_NAME}/${ACTIVITY_NAME}" --user 0

echo "=================================================="
echo "  Deployment Complete! App running on ${DEVICE}"
echo "=================================================="
