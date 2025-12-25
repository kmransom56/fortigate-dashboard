# Root Directory Cleanup Plan

## Analysis Date
2025-01-XX

## Current State
The root directory contains **60+ files** including:
- 30+ documentation files (.md)
- 20+ Python scripts (.py)
- 5+ shell scripts (.sh)
- Various configuration and log files

## Files That MUST Stay in Root

### Critical Application Files
- `README.md` - Project documentation (referenced by users)
- `requirements.txt` - Python dependencies (used by Dockerfile, pip)
- `pyproject.toml` - Python project configuration
- `Dockerfile` - Container build file
- `docker-compose.yml` - Container orchestration
- `docker-compose.*.yml` - Environment-specific compose files
- `.gitignore` - Git ignore rules
- `AGENTS.md` - AI agent documentation (referenced in code comments)
- `CLAUDE.md` - Development guide (referenced in code comments)

### Configuration Files
- `redis.conf` - Redis configuration
- `svgo.config.js` / `svgo.config.json` - SVG optimization config
- `.env` - Environment variables (if exists, should be in .gitignore)

### Essential Directories
- `app/` - Application code
- `docs/` - Documentation
- `tools/` - Development tools
- `scripts/` - Deployment scripts
- `secrets/` - Secrets (gitignored)
- `api_definitions/` - API documentation
- `extras/` - Additional integrations

---

## Files Safe to Move/Organize

### Documentation Files → `docs/archive/`

These are historical documentation that can be archived:

1. **Analysis/Implementation Docs** (Move to `docs/archive/analysis/`):
   - `AI_AGENT_IMPLEMENTATION_COMPLETE.md`
   - `AI_AGENT_INTEGRATION_ANALYSIS.md`
   - `ALL_ENDPOINTS_IMPLEMENTED.md`
   - `API_CODE_ANALYSIS.md`
   - `API_IMPLEMENTATION_SUMMARY.md`
   - `COMPLETE_API_COVERAGE_ANALYSIS.md`
   - `SYSTEM_API_COVERAGE.md`
   - `PERFORMANCE_OPTIMIZATION_SUMMARY.md`
   - `ICON_ORGANIZATION_SUMMARY.md`
   - `ICON_PROJECT_SUMMARY.md`

2. **Troubleshooting/Reports** (Move to `docs/archive/reports/`):
   - `api_token_troubleshoot.md`
   - `fortiswitch_troubleshooting_report.md`
   - `performance_analysis_report.md`
   - `icon_catalog_report.md`
   - `deployment_summary.md`
   - `device_inventory.md`
   - `optimization_implementation_guide.md`

3. **Feature Documentation** (Move to `docs/archive/features/`):
   - `3D_TOPOLOGY_ENHANCEMENTS.md`
   - `ENTERPRISE_ARCHITECTURE.md`
   - `QSR_RESTAURANT_TECHNOLOGY_RESEARCH.md`
   - `REDIS_SESSION_MIGRATION_GUIDE.md`
   - `DOCKER_DEPLOYMENT_GUIDE.md`
   - `SCANOPY_INTEGRATION.md` (already has copy in docs/)

4. **Quick Reference** (Move to `docs/archive/quickref/`):
   - `QUICK_FIX.md`
   - `QUICKSTART_AUTOGEN.md`
   - `CODE_FIXING_GUIDE.md`
   - `README_AUTOGEN_AGENT.md`

5. **API Reference** (Move to `docs/api/`):
   - `API_ENDPOINTS_REFERENCE.md` (should be in docs/api/)

6. **Agent Documentation** (Keep in root or move to `docs/agents/`):
   - `AGENTS.bak` - Backup file, can be removed
   - `GEMINI.md` - Move to `docs/agents/`
   - `CLAUDE.local.md` - Move to `docs/agents/` or remove if duplicate

### Python Scripts → `tools/` or `scripts/`

1. **Icon Management Scripts** (Move to `tools/icons/`):
   - `catalog_icons.py`
   - `get_icons.py`
   - `populate_fortinet_icons.py`
   - `scrape_icons.py`
   - `simple_Icons.py`
   - `simple_svg_optimize.py`
   - `optimize_svg_files.py`
   - `optimize_large_svgs.py`
   - `analyze_svg_optimization.py`
   - `extract_visio_stencils.py`

2. **Testing Scripts** (Move to `tools/tests/`):
   - `test_complete_topology.py`
   - `test_enhanced_fortiswitch.py`
   - `test_fortiswitch_improved.py`
   - `test_fortiswitch.py`
   - `test_icon_integration.py`
   - `test_topology_endpoints.py`
   - `test_topology_icons.py`
   - `simple_test.py`
   - `performance_test.py`

3. **Troubleshooting Scripts** (Move to `tools/troubleshoot/`):
   - `topology_troubleshoot.py`
   - `topology_fix.py`
   - `fix_fortiswitch_auth.py`
   - `get_new_api_token.py`
   - `fortigate_self_api_doc.py`

4. **Utility Scripts** (Move to `tools/utils/`):
   - `fix_code.py` - Code formatting utility
   - `wan_monitor.py` - Network monitoring (already in tools/)
   - `scrape_topology.py` - Topology scraper

5. **Agent Scripts** (Move to `tools/agents/`):
   - `autogen_agent.py`
   - `example_agent_usage.py`

### Shell Scripts → `scripts/`

1. **Deployment Scripts** (Already in `scripts/` or move there):
   - `deploy.sh` - Move to `scripts/`
   - `download_icons.sh` - Move to `scripts/icons/`

### Temporary/Log Files → Remove or `.gitignore`

1. **Log Files** (Should be in .gitignore):
   - `server.log`
   - `server_10000.log`
   - `wget-log`

2. **Temporary Files**:
   - `cookies.txt` - Remove if not needed
   - `compose.yml.txt` - Remove if not needed
   - `Untitled-1` - Remove
   - `mock_topology.json` - Move to `tools/test_data/` or remove

3. **Backup Files**:
   - `AGENTS.bak` - Remove (backup of AGENTS.md)

---

## Recommended Directory Structure

```
fortigate-dashboard/
├── README.md                    # Keep in root
├── AGENTS.md                    # Keep in root (referenced)
├── CLAUDE.md                    # Keep in root (referenced)
├── requirements.txt             # Keep in root
├── pyproject.toml               # Keep in root
├── Dockerfile                   # Keep in root
├── docker-compose.yml           # Keep in root
├── docker-compose.*.yml         # Keep in root
├── .gitignore                   # Keep in root
├── redis.conf                   # Keep in root
├── svgo.config.*                # Keep in root
│
├── app/                         # Application code
├── docs/                        # Documentation
│   ├── api/                     # API documentation
│   ├── archive/                 # Historical docs
│   │   ├── analysis/
│   │   ├── reports/
│   │   ├── features/
│   │   └── quickref/
│   └── agents/                  # Agent documentation
│
├── tools/                       # Development tools
│   ├── icons/                   # Icon management scripts
│   ├── tests/                   # Test scripts
│   ├── troubleshoot/            # Troubleshooting scripts
│   ├── utils/                   # Utility scripts
│   └── agents/                 # Agent scripts
│
├── scripts/                     # Deployment scripts
│   └── icons/                   # Icon download scripts
│
├── api_definitions/             # API documentation
├── extras/                      # Additional integrations
├── secrets/                     # Secrets (gitignored)
└── [other directories...]
```

---

## Cleanup Script

A cleanup script will be created to:
1. Create necessary directories
2. Move files to appropriate locations
3. Update any references if needed
4. Create symlinks for critical files if necessary

---

## Files to Check Before Moving

These files might have references that need updating:

1. **Scripts that import from root**:
   - Check for `sys.path.append` or relative imports
   - Update imports after moving

2. **Documentation references**:
   - Check if any code references specific .md files
   - Update links in documentation

3. **Docker/Deployment references**:
   - Check Dockerfile for file references
   - Check docker-compose for volume mounts
   - Check deployment scripts

---

## Execution Plan

### Phase 1: Create Directory Structure
1. Create `docs/archive/` subdirectories
2. Create `tools/` subdirectories
3. Create `scripts/icons/` directory

### Phase 2: Move Documentation
1. Move analysis docs to `docs/archive/analysis/`
2. Move reports to `docs/archive/reports/`
3. Move feature docs to `docs/archive/features/`
4. Move quickref to `docs/archive/quickref/`
5. Move API reference to `docs/api/`
6. Move agent docs to `docs/agents/`

### Phase 3: Move Scripts
1. Move icon scripts to `tools/icons/`
2. Move test scripts to `tools/tests/`
3. Move troubleshooting scripts to `tools/troubleshoot/`
4. Move utility scripts to `tools/utils/`
5. Move agent scripts to `tools/agents/`
6. Move shell scripts to `scripts/`

### Phase 4: Clean Up Temporary Files
1. Remove log files (already in .gitignore)
2. Remove temporary files
3. Remove backup files

### Phase 5: Verify
1. Check for broken imports
2. Update any hardcoded paths
3. Test application startup
4. Verify Docker builds

---

## Risk Assessment

### Low Risk (Safe to Move)
- Documentation files (.md) - No code dependencies
- Test scripts - Not imported by application
- Icon management scripts - Standalone utilities
- Historical reports - Reference only

### Medium Risk (Check Before Moving)
- Utility scripts that might be called by deployment
- Shell scripts referenced in documentation
- Configuration files (check Dockerfile)

### High Risk (Keep in Root)
- `requirements.txt` - Used by Dockerfile
- `Dockerfile` - Build file
- `docker-compose.yml` - Deployment file
- `README.md` - User-facing documentation
- `AGENTS.md` / `CLAUDE.md` - Referenced in code comments

---

## Estimated Cleanup Results

**Before**: 60+ files in root  
**After**: ~15 essential files in root

**Files to Move**:
- ~30 documentation files → `docs/archive/`
- ~20 Python scripts → `tools/`
- ~5 shell scripts → `scripts/`
- ~5 temporary files → Remove

**Files to Keep in Root**:
- README.md
- AGENTS.md
- CLAUDE.md
- requirements.txt
- pyproject.toml
- Dockerfile
- docker-compose*.yml
- .gitignore
- redis.conf
- svgo.config.*
- Essential directories

---

**Status**: Ready for Execution  
**Estimated Time**: 30-60 minutes  
**Risk Level**: Low (with verification)
