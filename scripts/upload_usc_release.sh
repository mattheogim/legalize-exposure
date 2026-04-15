#!/bin/bash
# upload_usc_release.sh
# VPN 켜고 로컬에서 실행 — US Code XML을 다운받아서 GitHub Release에 캐시
#
# 사용법:
#   ./scripts/upload_usc_release.sh              # 최신 release 자동 감지
#   ./scripts/upload_usc_release.sh 119/73       # 특정 release 지정
#
# 필요:
#   - gh CLI (GitHub CLI) 로그인 상태
#   - VPN 켠 상태 (uscode.house.gov 접근 필요)

set -euo pipefail

REPO="mattheogim/legalize-us"

# 1. Release point 결정
if [ -n "${1:-}" ]; then
  RELEASE="$1"
else
  echo "Discovering latest release point..."
  RELEASE=$(curl -sfL "https://uscode.house.gov/download/releasepoints/us/pl/" \
    | grep -oP '\d+/\d+' | sort -t/ -k1,1n -k2,2n | tail -1)
  if [ -z "$RELEASE" ]; then
    echo "ERROR: Failed to discover latest release. Specify manually: $0 119/73"
    exit 1
  fi
fi

PL=$(echo "$RELEASE" | tr '/' '-')
TAG="usc-pl-${PL}"
URL="https://uscode.house.gov/download/releasepoints/us/pl/${RELEASE}/xml_uscAll@${PL}.zip"

echo "Release: pl/${RELEASE}"
echo "Tag:     ${TAG}"
echo "URL:     ${URL}"
echo ""

# 2. 이미 올라가 있는지 확인
if gh release view "$TAG" --repo "$REPO" &>/dev/null; then
  echo "Release ${TAG} already exists. Skipping."
  echo "To re-upload, first delete: gh release delete ${TAG} --repo ${REPO} --yes"
  exit 0
fi

# 3. 다운로드
TMPDIR=$(mktemp -d)
ZIPFILE="${TMPDIR}/xml_uscAll@${PL}.zip"

echo "Downloading US Code XML (this may take a few minutes)..."
curl -fL -o "$ZIPFILE" "$URL" --retry 3 --retry-delay 10

FILE_SIZE=$(stat -f%z "$ZIPFILE" 2>/dev/null || stat -c%s "$ZIPFILE")
echo "Downloaded: ${FILE_SIZE} bytes"

if [ "$FILE_SIZE" -lt 100000 ]; then
  echo "ERROR: File too small (${FILE_SIZE} bytes) — likely not a valid ZIP"
  rm -rf "$TMPDIR"
  exit 1
fi

# 4. GitHub Release 생성 + 업로드
echo "Creating GitHub Release ${TAG}..."
gh release create "$TAG" \
  --repo "$REPO" \
  --title "US Code XML — pl/${RELEASE}" \
  --notes "Auto-cached US Code XML from uscode.house.gov (pl/${RELEASE}).
Downloaded $(date -u +%Y-%m-%d). Used by GitHub Actions workflow." \
  "$ZIPFILE"

echo ""
echo "Done! Release: https://github.com/${REPO}/releases/tag/${TAG}"
echo "Actions will use this on next run."

# Cleanup
rm -rf "$TMPDIR"
