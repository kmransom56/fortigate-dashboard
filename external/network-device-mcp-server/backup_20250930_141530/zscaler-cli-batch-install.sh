#!/usr/bin/env bash
#
# zscaler-cli-batch-install.sh
# Batch-test multiple CLI installer URLs behind Zscaler.
# Detects block pages, vendor landing pages, runs valid installers,
# and outputs a summary table and/or JSON for CI/CD.
#
# Usage:
#   ./zscaler-cli-batch-install.sh [--no-run] [--json] [--output <file>] <url1> <url2> ...
#
# Examples:
#   ./zscaler-cli-batch-install.sh --no-run --json https://cursor.com/install
#   ./zscaler-cli-batch-install.sh --output results.json https://sh.rustup.rs

set -euo pipefail

NO_RUN=false
JSON_MODE=false
OUTPUT_FILE=""
URLS=()

# --- Parse args ---
FORMAT="table"  # default

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-run)
            NO_RUN=true
            shift
            ;;
        --json)
            JSON_MODE=true
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"  # accepts 'json' or 'csv'
            shift 2
            ;;
        *)
            URLS+=("$1")
            shift
            ;;
    esac
done


if [[ ${#URLS[@]} -lt 1 ]]; then
    echo "Usage: $0 [--no-run] [--json] [--output <file>] <install_url1> [install_url2] ..."
    exit 1
fi

ZSCALER_CRT="Zscaler Root CA.crt"
TMP_CERT=$(mktemp)
TMP_BUNDLE=$(mktemp)

declare -a SUMMARY_URLS
declare -a SUMMARY_STATUS

# --- Logging helper ---
log() {
    # In pure JSON mode (no output file), suppress logs
    if ! $JSON_MODE || [[ -n "$OUTPUT_FILE" ]]; then
        echo "$@"
    fi
}

# --- 1. Check for cert file ---
if [[ ! -f "$ZSCALER_CRT" ]]; then
    log "❌ Zscaler root certificate '$ZSCALER_CRT' not found in current directory."
    exit 1
fi

# --- 2. Convert to PEM if needed ---
if grep -q "BEGIN CERTIFICATE" "$ZSCALER_CRT"; then
    cp "$ZSCALER_CRT" "$TMP_CERT"
else
    log "🔄 Converting DER to PEM..."
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
    log "❌ Could not find system CA bundle."
    exit 1
fi

log "📄 Using system CA bundle: $SYS_CA"

# --- 4. Merge into temp bundle ---
cat "$SYS_CA" "$TMP_CERT" > "$TMP_BUNDLE"

# --- 5. Loop through URLs ---
for INSTALL_URL in "${URLS[@]}"; do
    log
    log "🔍 Processing: $INSTALL_URL"
    TMP_INSTALL=$(mktemp)

    if ! SSL_CERT_FILE="$TMP_BUNDLE" REQUESTS_CA_BUNDLE="$TMP_BUNDLE" \
         curl -fsS -A "Mozilla/5.0" "$INSTALL_URL" -o "$TMP_INSTALL"; then
        log "❌ Failed to download $INSTALL_URL"
        SUMMARY_URLS+=("$INSTALL_URL")
        SUMMARY_STATUS+=("❌ Download failed")
        continue
    fi

    # --- 6. Detect HTML/block page ---
    if grep -q "<html" "$TMP_INSTALL" || grep -q "<!DOCTYPE html" "$TMP_INSTALL"; then
        if grep -qi "zscaler" "$TMP_INSTALL"; then
            log "🔒 Likely Zscaler block page — request whitelist from your network admin."
            SUMMARY_STATUS+=("⚠️ Blocked (Zscaler)")
        else
            log "ℹ️  Likely vendor landing page or requires authentication."
            SUMMARY_STATUS+=("ℹ️ Vendor page")
        fi
        log "📂 Saved HTML to: $TMP_INSTALL"

        if ! $JSON_MODE || [[ -n "$OUTPUT_FILE" ]]; then
            if command -v xdg-open >/dev/null 2>&1; then
                xdg-open "$TMP_INSTALL" >/dev/null 2>&1 &
            elif command -v open >/dev/null 2>&1; then
                open "$TMP_INSTALL" >/dev/null 2>&1 &
            elif command -v start >/dev/null 2>&1; then
                start "$TMP_INSTALL" >/dev/null 2>&1 &
            fi
        fi

        SUMMARY_URLS+=("$INSTALL_URL")
        continue
    fi

    # --- 7. Execute installer (unless --no-run) ---
    if $NO_RUN; then
        log "🛑 Skipping execution (--no-run mode)"
        SUMMARY_STATUS+=("✅ Downloaded (not run)")
    else
        log "🚀 Running installer from $INSTALL_URL..."
        if bash "$TMP_INSTALL"; then
            log "✅ Completed: $INSTALL_URL"
            SUMMARY_STATUS+=("✅ Installed")
        else
            log "❌ Installer script failed for $INSTALL_URL"
            SUMMARY_STATUS+=("❌ Install failed")
        fi
    fi
    SUMMARY_URLS+=("$INSTALL_URL")
done

# --- 8. Output ---
generate_json() {
    echo "["
    for i in "${!SUMMARY_URLS[@]}"; do
        url="${SUMMARY_URLS[$i]}"
        status="${SUMMARY_STATUS[$i]}"
        comma=$([[ $i -lt $((${#SUMMARY_URLS[@]} - 1)) ]] && echo "," || echo "")
        printf '  { "url": "%s", "status": "%s" }%s\n' "$url" "$status" "$comma"
    done
    echo "]"
}

if [[ "$FORMAT" == "json" ]]; then
    generate_json > "${OUTPUT_FILE:-/dev/stdout}"
    if [[ -n "$OUTPUT_FILE" ]]; then
        log "💾 JSON results written to $OUTPUT_FILE"
    fi
elif [[ "$FORMAT" == "csv" ]]; then
    write_csv "${OUTPUT_FILE:-results.csv}"
    log "💾 CSV results written to ${OUTPUT_FILE:-results.csv}"
    echo
    echo "📊 Summary:"
    printf "%-50s | %s\n" "URL" "Status"
    printf "%-50s-+-%s\n" "$(printf '─%.0s' {1..50})" "$(printf '─%.0s' {1..25})"
    for i in "${!SUMMARY_URLS[@]}"; do
        printf "%-50s | %s\n" "${SUMMARY_URLS[$i]}" "${SUMMARY_STATUS[$i]}"
    done
else
    echo
    echo "📊 Summary:"
    printf "%-50s | %s\n" "URL" "Status"
    printf "%-50s-+-%s\n" "$(printf '─%.0s' {1..50})" "$(printf '─%.0s' {1..25})"
    for i in "${!SUMMARY_URLS[@]}"; do
        printf "%-50s | %s\n" "${SUMMARY_URLS[$i]}" "${SUMMARY_STATUS[$i]}"
    done
fi

write_csv() {
    local filename="$1"
    echo "URL,Status" > "$filename"
    for i in "${!SUMMARY_URLS[@]}"; do
        url="${SUMMARY_URLS[$i]}"
        status="${SUMMARY_STATUS[$i]}"
        # Escape quotes and commas if needed
        echo "\"$url\",\"$status\"" >> "$filename"
    done
}