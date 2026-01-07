#!/bin/bash

set -euo pipefail

# ─────────────────────────────────────────────
# 🧠 Defaults and Globals
# ─────────────────────────────────────────────
FORMAT="table"
OUTPUT_FILE=""
NO_RUN=false
JSON_MODE=false
URLS=()
SUMMARY_URLS=()
SUMMARY_STATUS=()

# ─────────────────────────────────────────────
# 🧩 Argument Parser
# ─────────────────────────────────────────────
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
            FORMAT="$2"
            shift 2
            ;;
        *)
            URLS+=("$1")
            shift
            ;;
    esac
done

# ─────────────────────────────────────────────
# 🧪 Diagnostics Stub (replace with real logic)
# ─────────────────────────────────────────────
for url in "${URLS[@]}"; do
    # Simulate status check
    status="OK"
    if [[ "$url" == *"rustup"* ]]; then
        status="Blocked"
    fi
    SUMMARY_URLS+=("$url")
    SUMMARY_STATUS+=("$status")
done

# ─────────────────────────────────────────────
# 📄 CSV Writer
# ─────────────────────────────────────────────
write_csv() {
    local filename="$1"
    echo "URL,Status" > "$filename"
    for i in "${!SUMMARY_URLS[@]}"; do
        url="${SUMMARY_URLS[$i]}"
        status="${SUMMARY_STATUS[$i]}"
        echo "\"$url\",\"$status\"" >> "$filename"
    done
}

# ─────────────────────────────────────────────
# 📊 Output Logic
# ─────────────────────────────────────────────
if [[ "$FORMAT" == "json" ]]; then
    echo "[" > "${OUTPUT_FILE:-/dev/stdout}"
    for i in "${!SUMMARY_URLS[@]}"; do
        url="${SUMMARY_URLS[$i]}"
        status="${SUMMARY_STATUS[$i]}"
        echo "  {\"url\": \"$url\", \"status\": \"$status\"}," >> "${OUTPUT_FILE:-/dev/stdout}"
    done
    echo "]" >> "${OUTPUT_FILE:-/dev/stdout}"
elif [[ "$FORMAT" == "csv" ]]; then
    write_csv "${OUTPUT_FILE:-results.csv}"
    echo "💾 CSV results written to ${OUTPUT_FILE:-results.csv}"
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
