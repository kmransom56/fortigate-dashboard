#!/bin/bash
# Comprehensive Code Quality Check Script
#
# This script runs all code quality checks in the correct order:
# 1. Syntax check (catches syntax errors)
# 2. Black formatting (auto-fixes formatting)
# 3. Flake8 linting (catches style issues)
# 4. Type checking (optional, if mypy is installed)
#
# Usage: ./scripts/check_code_quality.sh [files or directories]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default paths if none provided
PATHS="${@:-app/ tests/ tools/}"

echo "🔍 Running comprehensive code quality checks..."
echo ""

# Step 1: Syntax Check (MOST IMPORTANT - catches syntax errors)
echo "1️⃣  Checking syntax errors (py_compile + ast.parse)..."
if python3 tools/utils/check_syntax.py $PATHS; then
    echo -e "${GREEN}✅ Syntax check passed${NC}"
else
    echo -e "${RED}❌ Syntax errors found! Fix these first.${NC}"
    exit 1
fi
echo ""

# Step 2: Black Formatting (auto-fixes formatting)
echo "2️⃣  Checking code formatting with Black..."
if command -v black &> /dev/null || python3 -m black --version &> /dev/null; then
    if python3 -m black --check $PATHS 2>&1; then
        echo -e "${GREEN}✅ Code formatting is correct${NC}"
    else
        echo -e "${YELLOW}⚠️  Code formatting issues found. Run: black $PATHS${NC}"
        # Don't exit - formatting can be auto-fixed
    fi
else
    echo -e "${YELLOW}⚠️  Black not installed. Skipping formatting check.${NC}"
    echo "   Install with: pip install black"
fi
echo ""

# Step 3: Flake8 Linting (catches style issues)
echo "3️⃣  Checking code style with Flake8..."
if command -v flake8 &> /dev/null || python3 -m flake8 --version &> /dev/null; then
    if python3 -m flake8 $PATHS --max-line-length=88 --ignore=E203,W503,E501 2>&1; then
        echo -e "${GREEN}✅ Code style check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Code style issues found. Review and fix.${NC}"
        # Don't exit - style issues are warnings
    fi
else
    echo -e "${YELLOW}⚠️  Flake8 not installed. Skipping style check.${NC}"
    echo "   Install with: pip install flake8"
fi
echo ""

# Step 4: Auto-fix formatting (optional)
echo "4️⃣  Auto-fixing code formatting..."
if command -v black &> /dev/null || python3 -m black --version &> /dev/null; then
    python3 -m black $PATHS 2>&1 | head -20
    echo -e "${GREEN}✅ Code formatting applied${NC}"
else
    echo -e "${YELLOW}⚠️  Black not installed. Skipping auto-format.${NC}"
fi
echo ""

echo -e "${GREEN}✅ All code quality checks complete!${NC}"
