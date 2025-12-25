# Scripts Directory - FastAPI Migration Action Plan

**Created:** 2025-12-23
**Status:** Ready for Execution
**Priority:** HIGH - Blocks FastAPI adoption

---

## Overview

The scripts directory contains **19 Python files**, of which **8 require immediate updates** to support the new FastAPI application. The remaining scripts are either legacy (archived), utilities (path-independent), or testing tools that need FastAPI test client updates.

---

## Critical Issues Summary

| Issue | Files Affected | Severity | Est. Time |
|-------|----------------|----------|-----------|
| Flask imports instead of FastAPI | 4 files | 🔴 CRITICAL | 2-3 hours |
| Hardcoded filesystem paths | 3 files | 🔴 CRITICAL | 30 min |
| Shell injection vulnerability | 1 file | 🔴 CRITICAL | 15 min |
| Deprecated `src/` imports | 6 files | 🟡 HIGH | 1 hour |

**Total Estimated Time:** 4-5 hours

---

## Phase 1: Critical Fixes (Do First)

### 1.1 Create FastAPI Startup Script

**File:** Create new `scripts/start_fastapi_server.py`

**Action:**
```python
#!/usr/bin/env python3
"""
Start the FastAPI web application server
This script starts the FastAPI server using uvicorn on port 8000
"""

import os
import sys
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def find_and_kill_existing_server(port=8000):
    """Find and kill any process running on the specified port"""
    import subprocess
    try:
        result = subprocess.run(
            ['lsof', '-ti', f':{port}'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            print(f"Found existing process(es) on port {port}: {pids}")
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"  ✓ Terminated process {pid}")
                except (ProcessLookupError, ValueError) as e:
                    print(f"  ✗ Could not terminate {pid}: {e}")
            import time
            time.sleep(2)
    except FileNotFoundError:
        # lsof not available
        pass

def main():
    """Start the FastAPI server with uvicorn"""
    print("=" * 70)
    print("🚀 Cisco Meraki Comprehensive Web Management Interface (FastAPI)")
    print("=" * 70)

    # Check for existing server
    port = int(os.environ.get('PORT', '8000'))
    find_and_kill_existing_server(port)

    # Change to project root
    os.chdir(project_root)

    # Load environment variables
    env_file = project_root / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print("✓ Loaded environment variables from .env")

    try:
        print(f"✓ Starting server on port {port}...")
        print(f"✓ Access at: http://localhost:{port}")
        print(f"✓ API docs: http://localhost:{port}/docs")
        print(f"✓ Redoc: http://localhost:{port}/redoc")
        print("=" * 70)
        print("Press Ctrl+C to stop the server")
        print("=" * 70)

        import uvicorn

        # Get configuration
        host = os.environ.get('HOST', '0.0.0.0')
        reload = os.environ.get('RELOAD', 'False').lower() in ('true', '1', 'yes')
        workers = int(os.environ.get('WORKERS', '1'))

        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            log_level="info"
        )

    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        sys.exit(0)
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Make sure you're in the project root and dependencies are installed")
        print("Run: uv pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**Status:** ⬜ TODO

---

### 1.2 Fix Shell Injection Vulnerability

**File:** `scripts/run_automation_service.py`

**Current (Line 16):**
```python
os.system("python3 modules/automation/webhook_service.py")
```

**Replace with:**
```python
import subprocess
subprocess.run([
    sys.executable,
    "modules/automation/webhook_service.py"
], check=True, cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

**Status:** ⬜ TODO

---

### 1.3 Fix Hardcoded Paths

**File:** `scripts/seed_agent_memory.py`

**Current (Line 35):**
```python
os.chdir("/media/keith/DATASTORE/cisco-meraki-cli")
```

**Replace with:**
```python
# Get project root dynamically
project_root = Path(__file__).resolve().parent.parent
os.chdir(project_root)
```

**Files to Update:**
- `seed_agent_memory.py` (line 35)
- `test_stub_visualizer.py` (line 8)
- `seed_corporate_brain.py` (line 33)

**Status:** ⬜ TODO

---

## Phase 2: Import Updates (Do Second)

### 2.1 Update Flask → FastAPI Imports

**Files to Update:**

#### `live_route_audit.py` (Line 50)

**Current:**
```python
from web_app import app  # Flask app
```

**Replace with:**
```python
from app.main import app  # FastAPI app
from fastapi.testclient import TestClient
```

**Changes Required:**
- Replace `app.test_client()` with `TestClient(app)`
- Update HTTP response handling (FastAPI test client uses different API)

---

#### `fetch_multi_vendor_topology.py` (Line 36)

**Current:**
```python
mod = importlib.import_module('comprehensive_web_app')
app = getattr(mod, 'app')
```

**Replace with:**
```python
from app.main import app
from fastapi.testclient import TestClient
```

---

#### `route_smoke_test.py` (Line 80)

**Current:**
```python
mod = importlib.import_module('comprehensive_web_app')
app = getattr(mod, 'app')
client = app.test_client()
```

**Replace with:**
```python
from app.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
```

**Additional Changes:**
- Line 97-101: Update session transaction syntax for FastAPI
- Flask: `with client.session_transaction() as sess:`
- FastAPI: Use dependency injection or cookies

---

### 2.2 Update Deprecated `src/` Imports

**Files to Update:**

| File | Current Import | New Import |
|------|----------------|------------|
| `start_web_server.py` | `sys.path.insert(0, str(project_root / 'src'))` | Remove line (use `app/`) |
| `start_web_server.py` | `from src.comprehensive_web_app import app` | `from app.main import app` |
| `build_live_topology_html.py` | `from src.multi_vendor_topology import` | `from app.src.multi_vendor_topology import` OR move module |
| `build_live_topology_html.py` | `from src.fortinet_api import` | `from app.src.fortinet_api import` OR move module |
| `test_stub_visualizer.py` | `from src import enhanced_visualizer` | `from app.src import enhanced_visualizer` OR update path |

**Status:** ⬜ TODO

---

## Phase 3: Testing Script Updates (Do Third)

### 3.1 Update Test Clients to FastAPI

All testing scripts need to migrate from Flask's `app.test_client()` to FastAPI's `TestClient`.

**Key Differences:**

| Flask | FastAPI |
|-------|---------|
| `app.test_client()` | `TestClient(app)` |
| `client.get('/path')` | Same |
| `client.post('/path', json=data)` | Same |
| `resp.get_json()` | `resp.json()` |
| `with client.session_transaction() as sess:` | Use cookies or auth headers |

**Files Requiring Updates:**
1. `live_route_audit.py` (219 lines) - Major refactor
2. `route_smoke_test.py` (233 lines) - Major refactor
3. `fetch_multi_vendor_topology.py` (101 lines) - Medium refactor
4. `ci_route_audit.py` (79 lines) - Medium refactor (depends on live_route_audit)

**Estimated Time:** 2-3 hours

---

## Phase 4: Documentation Updates (Do Last)

### 4.1 Update README Files

**Files to Update:**
- Main README.md - Update startup instructions
- QUICKSTART_FASTAPI.md - Reference new startup script
- Scripts README (create if doesn't exist)

### 4.2 Create Scripts Documentation

**Create:** `scripts/README.md`

**Contents:**
```markdown
# Scripts Directory

## Web Server Management
- `start_fastapi_server.py` - Start FastAPI application (port 8000)
- ~~`start_web_server.py`~~ - DEPRECATED (Flask version)

## Topology & Visualization
- `build_live_topology_html.py` - Generate live multi-vendor topology HTML
- `fetch_multi_vendor_topology.py` - Fetch topology JSON via API

## AI Agent Management
- `seed_agent_memory.py` - Seed teachable agent with network knowledge
- `seed_corporate_brain.py` - Train Ollama LLM with brand standards

## Testing & CI/CD
- `live_route_audit.py` - Comprehensive route testing with real data
- `route_smoke_test.py` - Smoke test all GET endpoints
- `ci_route_audit.py` - CI-safe wrapper for route audits
- `check_links.py` - Markdown link validator

## Utilities
- `find_free_port.py` - Find available TCP port
- `clean_unused_templates.py` - Clean unused Jinja2 templates
- `test_stub_visualizer.py` - Test enhanced_visualizer
- `test_incident_parsing.py` - Test LLM incident parsing

## Automation
- `run_automation_service.py` - Launch automation webhook service
```

---

## Validation Checklist

After completing migration, verify:

- [ ] `scripts/start_fastapi_server.py` launches FastAPI on port 8000
- [ ] `http://localhost:8000/docs` shows Swagger documentation
- [ ] `live_route_audit.py` executes without errors
- [ ] `route_smoke_test.py` discovers routes from FastAPI
- [ ] No hardcoded paths remain in any script
- [ ] All `src/` imports updated to `app/` or correct paths
- [ ] Security vulnerability in `run_automation_service.py` fixed
- [ ] Legacy `start_web_server.py` marked as deprecated or removed

---

## Migration Script

**Create:** `scripts/migrate_to_fastapi.sh`

```bash
#!/bin/bash
# Automated migration helper for scripts directory

echo "🔧 FastAPI Migration Tool for Scripts Directory"
echo "================================================"

# Phase 1: Backup
echo "📦 Phase 1: Creating backup..."
tar -czf scripts_backup_$(date +%Y%m%d_%H%M%S).tar.gz scripts/
echo "✅ Backup created"

# Phase 2: Fix hardcoded paths
echo "🔧 Phase 2: Fixing hardcoded paths..."
sed -i 's|/media/keith/DATASTORE/cisco-meraki-cli|$(dirname $(dirname $(realpath $0)))|g' \
    scripts/seed_agent_memory.py \
    scripts/test_stub_visualizer.py \
    scripts/seed_corporate_brain.py
echo "✅ Hardcoded paths updated"

# Phase 3: Update imports
echo "🔧 Phase 3: Updating imports..."
sed -i 's|from src\.|from app.src.|g' scripts/build_live_topology_html.py
sed -i 's|from src import|from app.src import|g' scripts/test_stub_visualizer.py
echo "✅ Import paths updated"

# Phase 4: Fix security issue
echo "🔧 Phase 4: Fixing security vulnerability..."
# Manual intervention required for run_automation_service.py
echo "⚠️  Manual fix required: scripts/run_automation_service.py line 16"

echo ""
echo "✅ Automated migration complete!"
echo "📝 Manual steps remaining:"
echo "   1. Review and test start_fastapi_server.py"
echo "   2. Update testing scripts to use FastAPI TestClient"
echo "   3. Fix run_automation_service.py subprocess call"
echo "   4. Test all scripts with: python scripts/<script>.py --help"
```

---

## Testing Plan

### Unit Tests (Create New)

**File:** `tests/test_scripts.py`

```python
import pytest
from pathlib import Path
import sys

# Add scripts to path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

def test_find_free_port():
    from find_free_port import find_free_port
    port = find_free_port()
    assert 1024 <= port <= 65535

def test_start_fastapi_imports():
    """Verify FastAPI startup script imports correctly"""
    from start_fastapi_server import main
    assert callable(main)

# Add more tests...
```

### Integration Tests

**File:** `tests/test_fastapi_routes.py`

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_docs_available():
    """Verify FastAPI docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_health_endpoint():
    """Verify health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## Rollback Plan

If migration fails:

1. **Restore from backup:**
   ```bash
   tar -xzf scripts_backup_YYYYMMDD_HHMMSS.tar.gz
   ```

2. **Revert git changes:**
   ```bash
   git checkout scripts/
   ```

3. **Use Flask startup temporarily:**
   ```bash
   python scripts/start_web_server.py  # Old Flask version
   ```

---

## Success Metrics

Migration is complete when:

✅ All scripts execute without import errors
✅ FastAPI server starts successfully
✅ Route testing scripts work with FastAPI
✅ No hardcoded paths remain
✅ Security vulnerability fixed
✅ Documentation updated
✅ All tests pass

---

## Timeline

| Phase | Tasks | Estimated Time | Deadline |
|-------|-------|----------------|----------|
| Phase 1 | Critical fixes | 1 hour | Day 1 |
| Phase 2 | Import updates | 1.5 hours | Day 1 |
| Phase 3 | Testing scripts | 2-3 hours | Day 2 |
| Phase 4 | Documentation | 1 hour | Day 3 |

**Total:** 5.5-6.5 hours across 3 days

---

## Notes

- **Backward Compatibility:** Keep `start_web_server.py` (Flask) as `start_web_server_legacy.py` for 1 release cycle
- **Environment Variables:** Document new FastAPI environment variables (PORT, HOST, RELOAD, WORKERS)
- **API Key Handling:** FastAPI uses dependency injection instead of Flask sessions - update accordingly

---

**Migration Champion:** [Assign team member]
**Review Required:** Yes
**Approval Required:** Yes (for production deployment)
