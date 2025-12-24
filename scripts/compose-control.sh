#!/usr/bin/env bash
set -euo pipefail

# Simple Docker Compose control script for this repo
# Usage: scripts/compose-control.sh {start|stop|restart|status|logs [service]}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

COMPOSE_FILE="${COMPOSE_FILE:-$REPO_ROOT/compose.yml}"
PROJECT_NAME="${PROJECT_NAME:-fortigate-dashboard}"

compose() {
  docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" "$@"
}

cmd="${1:-}"
case "$cmd" in
  start)
    echo "Starting containers..."
    compose up -d
    ;;
  stop)
    echo "Stopping containers..."
    compose down
    ;;
  restart)
    echo "Restarting containers..."
    compose down
    compose up -d
    ;;
  status)
    compose ps
    ;;
  logs)
    shift || true
    service="${1:-dashboard}"
    compose logs -f "$service"
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs [service]}" >&2
    echo "Environment overrides: COMPOSE_FILE, PROJECT_NAME" >&2
    exit 1
    ;;
esac
