#!/bin/bash
# Simple code fixing script using uv run

set -e

FILE="${1:-.}"

echo "🔧 Fixing code: $FILE"
echo ""

# Sort imports
echo "1. Sorting imports..."
uv run isort --profile=black --line-length=100 "$FILE"

# Format with black
echo "2. Formatting with black..."
uv run black --line-length=100 --quiet "$FILE"

# Check with flake8
echo "3. Checking with flake8..."
uv run flake8 --max-line-length=100 --extend-ignore=E203,W503 --exclude=venv,.venv,__pycache__,.git "$FILE" || true

echo ""
echo "✅ Done!"
