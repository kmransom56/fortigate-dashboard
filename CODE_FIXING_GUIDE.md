# Code Fixing and Linting Guide

## Quick Start

### Install Linting Tools

```bash
uv pip install black flake8 isort autopep8 mypy
```

Or install from requirements.txt:
```bash
uv pip install -r requirements.txt
```

### Fix All Code

```bash
# Fix all Python files in the project
python fix_code.py

# Fix a specific file
python fix_code.py app/main.py

# Check only (don't modify files)
python fix_code.py --check
```

### Individual Tools

```bash
# Format with black only
python fix_code.py --black-only

# Sort imports only
python fix_code.py --isort-only

# Check with flake8 only
python fix_code.py --flake8-only
```

## Docker Container Reset

### Quick Reset (Stop and Delete)

```bash
./scripts/stop_and_delete_container.sh
```

### Full Reset (Interactive)

```bash
./scripts/reset_docker.sh
```

### Manual Reset

```bash
# Stop and remove container
docker stop fortigate-dashboard
docker rm fortigate-dashboard

# Rebuild and start
docker compose up --build -d
```

## Linting Tools

### Black (Code Formatter)
- Formats code to a consistent style
- Line length: 100 characters
- Run: `black --line-length=100 .`

### isort (Import Sorter)
- Sorts and organizes imports
- Compatible with black
- Run: `isort --profile=black .`

### autopep8 (PEP 8 Fixer)
- Automatically fixes PEP 8 issues
- Run: `autopep8 --in-place --aggressive --aggressive .`

### flake8 (Linter)
- Checks for code quality issues
- Run: `flake8 --max-line-length=100 .`

## Integration with AutoGen Agent

The AutoGen agent can also fix code:

```bash
python autogen_agent.py --task "Fix all code quality issues in app/main.py"
```

## Pre-commit Hook (Optional)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
python fix_code.py --check
if [ $? -ne 0 ]; then
    echo "Code quality checks failed. Run: python fix_code.py"
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```
