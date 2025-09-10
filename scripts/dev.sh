#!/usr/bin/env bash
set -euo pipefail

export PYTHONUNBUFFERED=1

exec uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload

