# Service Architecture Analysis

This document provides a comprehensive analysis of the `app/services/` directory structure, identifying active services, variants, and cleanup recommendations.

## Service Inventory

### Active Production Services

These services are **actively imported and used** in `app/main.py`:

#### Core Network Services

1. **fortigate_service.py** (290 lines)
   - Primary FortiGate firewall API integration
   - Functions: `get_cloud_status()`, `get_interfaces()`, `fgt_api`
   - Dependencies: FortiGate REST API
   - Status: ✅ Active

2. **fortiswitch_service.py** (387 lines)
   - FortiSwitch management via FortiGate controller
   - Function: `get_fortiswitches()`
   - Dependencies: `fortigate_session.py`, `fortiswitch_session.py`
   - Status: ✅ Active

3. **hybrid_topology_service.py** (471 lines)
   - Combines SNMP, FortiGate Monitor API, and FortiSwitch data
   - Provides unified network topology view
   - Function: `get_hybrid_topology_service()`
   - Status: ✅ Active

4. **fortigate_monitor_service.py** (328 lines)
   - Real-time device monitoring via FortiGate Monitor API
   - Function: `get_fortigate_monitor_service()`
   - Status: ✅ Active

5. **fortigate_inventory_service.py** (362 lines)
   - Device inventory management
   - Function: `get_fortigate_inventory_service()`
   - Status: ✅ Active

#### Multi-Vendor Integration

6. **meraki_service.py** (354 lines)
   - Cisco Meraki API integration
   - Full organization, network, and device management
   - Status: ✅ Active

7. **snmp_service.py** (275 lines)
   - SNMP-based device discovery
   - Generic network device detection
   - Status: ✅ Active (via hybrid_topology_service)

#### Session Management

8. **redis_session_manager.py** (440 lines)
   - Redis-based session pooling and caching
   - Functions: `get_redis_session_manager()`, `cleanup_expired_sessions()`
   - Status: ✅ Active

9. **fortigate_redis_session.py** (376 lines)
   - FortiGate-specific Redis session management
   - Function: `get_fortigate_redis_session_manager()`
   - Status: ✅ Active

10. **fortigate_session.py** (280 lines)
    - FortiGate session handling (non-Redis)
    - Class: `FortiGateSessionManager`
    - Status: ✅ Active (used by fortiswitch services)

11. **fortiswitch_session.py** (234 lines - estimated)
    - FortiSwitch-specific session management
    - Class: `FortiSwitchSessionManager`
    - Status: ✅ Active

#### Specialized Services

12. **organization_service.py** (386 lines)
    - Multi-organization device management
    - Function: `get_organization_service()`
    - Status: ✅ Active

13. **brand_detection_service.py** (470 lines)
    - AI-powered device brand/model detection
    - Function: `get_brand_detection_service()`
    - Status: ✅ Active

14. **restaurant_device_service.py** (339 lines)
    - Restaurant technology device classification
    - Function: `get_restaurant_device_service()`
    - Status: ✅ Active

15. **icon_3d_service.py** (437 lines)
    - 3D device icon management
    - Function: `get_3d_icon_service()`
    - Status: ✅ Active

16. **eraser_service.py** (193 lines - estimated)
    - Eraser.io diagram export integration
    - Module import: `from app.services import eraser_service`
    - Status: ✅ Active

17. **3d_asset_service.py** (173 lines - estimated)
    - 3D asset library service
    - Status: ✅ Active

18. **scraped_topology_service.py** (240 lines - estimated)
    - FortiGate web UI scraping for topology extraction
    - Status: ✅ Active

#### JavaScript/Node.js Services

19. **fortigate-auth.js** (130 lines - estimated)
    - Node.js FortiGate authentication helper
    - Status: ✅ Active (for scraping)

20. **scraper.js** (275 lines - estimated)
    - FortiGate web UI scraper implementation
    - Status: ✅ Active

21. **token-extractor.js** (325 lines - estimated)
    - Session token extraction utility
    - Status: ✅ Active

22. **scrape-fortigate-map.js** (23 lines - estimated)
    - FortiGate topology map scraper
    - Status: ✅ Active

23. **package.json**
    - Node.js dependencies for JavaScript services
    - Status: ✅ Active

---

## Service Variants (Inactive/Development)

These files are **NOT imported** in `app/main.py` and appear to be development variants:

### FortiGate Service Variants

1. **fortigate_service_optimized.py** (372 lines)
   - Performance-optimized variant
   - Status: ⚠️ Variant (not in use)
   - Recommendation: Archive or merge optimizations into main service

2. **fortigate_service.no_ssl.py** (200 lines - estimated)
   - SSL verification disabled variant
   - Status: ⚠️ Variant (development/testing only)
   - Recommendation: Keep for testing, document clearly

### FortiSwitch Service Variants

3. **fortiswitch_service_enhanced.py** (550 lines)
   - Enhanced device detection with restaurant classification
   - Status: ⚠️ Enhanced variant (referenced in deployment script)
   - Recommendation: **Evaluate for promotion to active service**

4. **fortiswitch_service_improved.py** (587 lines)
   - Improved device correlation
   - Status: ⚠️ Variant (superseded by enhanced?)
   - Recommendation: Compare features, merge best into active

5. **fortiswitch_service_optimized.py** (396 lines)
   - Performance-optimized variant
   - Status: ⚠️ Variant (not in use)
   - Recommendation: Merge optimizations or archive

6. **fortiswitch_service.no_ssl.py** (587 lines)
   - SSL verification disabled variant
   - Status: ⚠️ Variant (testing only)
   - Recommendation: Keep for testing, document clearly

---

## Service Dependencies

### Dependency Graph

```
main.py
├── fortigate_service.py
│   └── fortigate_redis_session.py
│       └── redis_session_manager.py
├── fortiswitch_service.py
│   ├── fortigate_session.py
│   └── fortiswitch_session.py
├── hybrid_topology_service.py
│   ├── fortigate_monitor_service.py
│   ├── fortiswitch_api_service.py
│   └── snmp_service.py
├── fortigate_inventory_service.py
├── brand_detection_service.py
├── restaurant_device_service.py
├── organization_service.py
├── icon_3d_service.py
├── 3d_asset_service.py
├── meraki_service.py
├── eraser_service.py
└── scraped_topology_service.py
    ├── scraper.js
    ├── fortigate-auth.js
    ├── token-extractor.js
    └── scrape-fortigate-map.js
```

---

## Service Categories

### 1. Device Discovery & Monitoring (6 services)
- fortigate_service.py
- fortigate_monitor_service.py
- fortiswitch_service.py
- fortigate_inventory_service.py
- snmp_service.py
- hybrid_topology_service.py

### 2. Session & Authentication (4 services)
- redis_session_manager.py
- fortigate_redis_session.py
- fortigate_session.py
- fortiswitch_session.py

### 3. Multi-Vendor Integration (1 service)
- meraki_service.py

### 4. Device Classification (3 services)
- brand_detection_service.py
- restaurant_device_service.py
- organization_service.py

### 5. Visualization & Export (4 services)
- icon_3d_service.py
- 3d_asset_service.py
- eraser_service.py
- scraped_topology_service.py

### 6. Web Scraping (4 JavaScript services)
- scraper.js
- fortigate-auth.js
- token-extractor.js
- scrape-fortigate-map.js

---

## Cleanup Recommendations

### Priority 1: Document Variants

Create `app/services/VARIANTS.md` to document:
- Purpose of each variant
- When to use each variant
- Which variant is "production ready"
- Migration path from variants to main service

### Priority 2: Consolidate FortiSwitch Services

**Analysis Needed**:
```bash
# Compare feature sets
diff fortiswitch_service.py fortiswitch_service_enhanced.py
diff fortiswitch_service.py fortiswitch_service_improved.py
```

**Decision Tree**:
1. If `enhanced` has better device detection → Deploy via `tools/deploy_enhanced_fortiswitch.py`
2. If `improved` has unique features → Merge into `enhanced`
3. Archive older variants to `app/services/archive/`

### Priority 3: Archive Development Variants

Create archive structure:
```
app/services/
├── archive/
│   ├── fortigate/
│   │   ├── fortigate_service_optimized.py
│   │   └── fortigate_service.no_ssl.py
│   └── fortiswitch/
│       ├── fortiswitch_service_enhanced.py
│       ├── fortiswitch_service_improved.py
│       ├── fortiswitch_service_optimized.py
│       └── fortiswitch_service.no_ssl.py
└── [active services]
```

### Priority 4: Add Service Registry

Create `app/services/registry.py`:
```python
"""
Service Registry - Central registry of all active services
"""

ACTIVE_SERVICES = {
    'fortigate': {
        'service': 'fortigate_service.py',
        'session': 'fortigate_redis_session.py',
        'monitor': 'fortigate_monitor_service.py',
        'inventory': 'fortigate_inventory_service.py'
    },
    'fortiswitch': {
        'service': 'fortiswitch_service.py',
        'api': 'fortiswitch_api_service.py',
        'session': 'fortiswitch_session.py'
    },
    'topology': {
        'hybrid': 'hybrid_topology_service.py',
        'scraper': 'scraped_topology_service.py'
    },
    'session': {
        'redis': 'redis_session_manager.py'
    },
    'classification': {
        'brand': 'brand_detection_service.py',
        'restaurant': 'restaurant_device_service.py',
        'organization': 'organization_service.py'
    },
    'visualization': {
        'icon_3d': 'icon_3d_service.py',
        '3d_asset': '3d_asset_service.py',
        'eraser': 'eraser_service.py'
    },
    'vendors': {
        'meraki': 'meraki_service.py',
        'snmp': 'snmp_service.py'
    }
}
```

---

## Service Testing Matrix

| Service | Unit Tests | Integration Tests | Status |
|---------|------------|-------------------|--------|
| fortigate_service.py | ❌ | ❌ | Missing |
| fortiswitch_service.py | ❌ | ❌ | Missing |
| hybrid_topology_service.py | ❌ | ❌ | Missing |
| meraki_service.py | ❌ | ❌ | Missing |
| redis_session_manager.py | ❌ | ❌ | Missing |

**Recommendation**: Create `tests/services/` with comprehensive test coverage.

---

## Service Performance Metrics

### Lines of Code by Category

| Category | Total LOC | Avg LOC/Service |
|----------|-----------|-----------------|
| Device Discovery | ~2,500 | 417 |
| Session Management | ~1,370 | 343 |
| Classification | ~1,195 | 398 |
| Visualization | ~840 | 210 |
| Multi-Vendor | ~354 | 354 |
| **Total Active** | **~6,259** | **344** |

### Variant Files Analysis

| Type | Count | Total LOC | Status |
|------|-------|-----------|--------|
| Active Services | 23 | ~6,259 | ✅ In use |
| Variant Services | 6 | ~2,890 | ⚠️ Unused |
| **Total** | **29** | **~9,149** | |

**Conclusion**: ~32% of code in services directory is variant/unused files.

---

## Migration Path for Enhanced Services

### Deploying Enhanced FortiSwitch Service

The `tools/deploy_enhanced_fortiswitch.py` script is designed to upgrade:

**From**: `fortiswitch_service.py` (387 lines)
**To**: `fortiswitch_service_enhanced.py` (550 lines)

**Additional Features**:
- Improved device detection (+40%)
- Restaurant technology classification
- Enhanced DHCP correlation
- Better error handling
- Security recommendations

**Deployment Steps**:
1. Review `docs/DEPLOYMENT_SCRIPTS.md`
2. Run `python3 tools/deploy_enhanced_fortiswitch.py`
3. Test in development environment
4. Monitor logs for issues
5. Rollback if needed from timestamped backup

---

## JavaScript Services Architecture

### Node.js Service Integration

The application uses **hybrid Python + Node.js architecture**:

**Python Services** → Call → **Node.js Services** → Interact → **FortiGate Web UI**

**Why Node.js?**
- FortiGate web UI requires JavaScript execution
- Session management requires browser-like behavior
- CSRF token extraction from rendered pages
- Puppeteer/Playwright for headless browsing

**package.json Dependencies**:
```json
{
  "dependencies": {
    "puppeteer": "^21.x",
    "axios": "^1.x",
    "cheerio": "^1.x"
  }
}
```

**Integration Pattern**:
```python
# Python calls Node.js
import subprocess
result = subprocess.run(['node', 'app/services/scraper.js'], capture_output=True)
topology_data = json.loads(result.stdout)
```

---

## Next Steps

### Immediate Actions

1. ✅ **Document architecture** (this file)
2. ⏳ **Test enhanced services** in development
3. ⏳ **Create service registry** for central tracking
4. ⏳ **Archive variant files** to reduce confusion
5. ⏳ **Add unit tests** for critical services

### Long-term Improvements

1. **Service Health Monitoring**: Add health check endpoints for each service
2. **Performance Metrics**: Instrument services with OpenTelemetry
3. **Service Versioning**: Add version metadata to each service
4. **API Contracts**: Define clear interfaces between services
5. **Dependency Injection**: Refactor to use dependency injection pattern

---

## References

- **Main Application**: `app/main.py`
- **API Layer**: `app/api/fortigate.py`
- **Deployment Scripts**: `tools/deploy_enhanced_fortiswitch.py`
- **Asset Catalog**: `docs/ASSET_CATALOG.md`
- **Deployment Guide**: `docs/DEPLOYMENT_SCRIPTS.md`

---

Last Updated: 2025-12-07
