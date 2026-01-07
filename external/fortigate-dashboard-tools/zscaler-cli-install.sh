#!/usr/bin/env bash
#
# zscaler-cli-install.sh
# General-purpose CLI installer wrapper for environments behind Zscaler.
# Merges Zscaler Root CA into system CA bundle, sets trust env vars, and runs the installer.
#
# Usage:
#   ./zscaler-cli-install.sh <install_url>
#
# Example:
#   ./zscaler-cli-install.sh https://cursor.com/install
#   ./zscaler-cli-install.sh https://sh.rustup.rs

set -euo pipefail

# --- 0. Validate input ---
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <install_url>"
    exit 1
fi
INSTALL_URL="$1"

ZSCALER_CRT="Zscaler Root CA.crt"
TMP_CERT=$(mktemp)
TMP_BUNDLE=$(mktemp)

# --- 1. Check for cert file ---
if [[ ! -f "$ZSCALER_CRT" ]]; then
    echo "❌ Zscaler root certificate '$ZSCALER_CRT' not found in current directory."
    exit 1
fi

# --- 2. Convert to PEM if needed ---
if grep -q "BEGIN CERTIFICATE" "$ZSCALER_CRT"; then
    cp "$ZSCALER_CRT" "$TMP_CERT"
else
    echo "🔄 Converting DER to PEM..."
    openssl x509 -inform der -in "$ZSCALER_CRT" -out "$TMP_CERT"
fi

# --- 3. Detect system CA bundle ---
if command -v python3 >/dev/null 2>&1 && python3 -m certifi >/dev/null 2>&1; then
    SYS_CA=$(python3 -m certifi)
elif [[ -f /etc/ssl/certs/ca-certificates.crt ]]; then
    SYS_CA="/etc/ssl/certs/ca-certificates.crt"
elif [[ -f /etc/pki/tls/certs/ca-bundle.crt ]]; then
    SYS_CA="/etc/pki/tls/certs/ca-bundle.crt"
else
    echo "❌ Could not find system CA bundle."
    exit 1
fi

echo "📄 Using system CA bundle: $SYS_CA"

# --- 4. Merge into temp bundle ---
cat "$SYS_CA" "$TMP_CERT" > "$TMP_BUNDLE"

# --- 5. Run installer with env vars ---
echo "🚀 Running installer from $INSTALL_URL with Zscaler CA trust..."
SSL_CERT_FILE="$TMP_BUNDLE" REQUESTS_CA_BUNDLE="$TMP_BUNDLE" \
    curl "$INSTALL_URL" -fsS | bash

echo "✅ Installation complete."

# --- 6. Cleanup ---
rm -f "$TMP_CERT"
# Keep TMP_BUNDLE for debugging if needed
