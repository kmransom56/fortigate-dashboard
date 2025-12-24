# Quick Fix Guide

## Fix Code Issues

```bash
# Using Python modules (works even with permission issues)
python -m isort --profile=black app/main.py
python -m black --line-length=100 app/main.py
python -m flake8 --max-line-length=100 app/main.py

# Or use the Python script
python fix_code.py app/main.py
```

## Stop and Delete Docker Container

```bash
# Quick method
docker stop fortigate-dashboard && docker rm fortigate-dashboard

# Or use bash
bash scripts/stop_and_delete_container.sh

# Then rebuild
docker compose up --build -d
```

## Common Issues

### Permission Denied on Scripts
If you get permission denied, use:
```bash
bash scripts/script_name.sh
```

### Tools Not Found
Install tools:
```bash
uv pip install black flake8 isort autopep8
```

### Use Python -m Instead
If direct execution fails, use:
```bash
python -m black .
python -m isort .
python -m flake8 .
```
