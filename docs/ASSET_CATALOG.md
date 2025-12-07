# Asset Catalog

This document catalogs all available assets, tools, and resources in the FortiGate Dashboard project.

## Fortinet Device Icons

**Location**: `app/static/icons/fortinet/`

### Icon Summary
- **FortiGate**: 91 SVG icons (firewalls and security appliances)
- **FortiSwitch**: 63 SVG icons (network switches)
- **FortiAP**: 26 SVG icons (wireless access points)
- **FortiAuthenticator**: 1 SVG icon
- **FortiMail**: 1 SVG icon
- **FortiWeb**: 1 SVG icon
- **FortiSIEM**: 1 SVG icon
- **Other**: 6 SVG icons (cameras, transceivers, accessories)
- **Total**: 190 high-quality SVG device icons

### FortiGate Models (91 icons)
Comprehensive collection of FortiGate firewall models including:
- Entry-level: FG-40F, FG-60F, FG-80F, FG-100F
- Mid-range: FG-200F, FG-400F, FG-600F, FG-800F, FG-1000F, FG-1100F
- High-end: FG-1500D, FG-2000E, FG-2500E, FG-3000D, FG-3100D, FG-3200D, FG-3400E, FG-3600E
- Data center: FG-4200F, FG-4400F, FG-4401F, FG-5001C
- Virtual: FortiGate-VM

### FortiSwitch Models (63 icons)
Complete range of FortiSwitch models:
- PoE switches: FSW-124E, FSW-124E-POE, FSW-148E-POE, FSW-224E-POE, FSW-248E-POE
- High-density: FSW-424E, FSW-448E, FSW-524D, FSW-548D
- PoE+ models: FSW-424D-POE, FSW-448D-POE, FSW-524D-POE, FSW-548D-POE
- Fiber models: FSW-424D-FPOE, FSW-448D-FPOE, FSW-548D-FPOE
- 10G uplink models: Various D-series and E-series with 10G SFP+ ports

### FortiAP Models (26 icons)
Wireless access point collection:
- Indoor: FAP-221E, FAP-223E, FAP-231F, FAP-234F, FAP-432F, FAP-433F
- Outdoor: FAP-231K, FAP-234G, FAP-U432F, FAP-U433F
- Wave 2: FAP-321E, FAP-421E, FAP-423E
- Wi-Fi 6: FAP-231G, FAP-234G

### Other Fortinet Products (10 icons)
- **FortiAuthenticator**: Authentication and identity management
- **FortiMail**: Email security gateway
- **FortiWeb**: Web application firewall
- **FortiSIEM**: Security information and event management
- **FortiCamera**: Network video surveillance
- **Accessories**: SFP and QSFP transceivers

## Meraki Device Icons

**Location**: `app/static/icons/meraki/`

### Available Models (4 icons)
- MS120-24P: 24-port PoE+ switch
- MS220-24P: 24-port PoE+ managed switch
- MS220-48FP: 48-port PoE+ managed switch
- MS350-48: 48-port managed switch

## Additional Icon Packs

### Network Diagram Icons
**Location**: `app/static/icons/packs/`

1. **ntwrk-clean-and-flat** - Modern flat design network icons
2. **affinity** - Multi-color icon pack with variants:
   - Colors: red, gray, blue, green
   - Styles: square, circle, naked (no background)
   - Format: SVG

### Fortinet Icon Library
**Location**: `app/static/icons/Fortinet-Icon-Library/`
- Official Fortinet brand icons and logos

### Restaurant/Hospitality Icons
**Location**: `app/static/icons/restaurant/`
- Specialized icons for restaurant network deployments

## Visio Stencil Files

**Location**: `libvisio2svg/Fortinet Visio Stencil/`

### Available Stencils (2025Q2 Release)
- FortiGate_Series_R22_2025Q2.vss
- FortiSwitch_Series_R14_2025Q2.vss
- FortiAP_Series_R8_2025Q2.vss
- FortiExtender_Series_R2_2025Q2.vss
- FortiWeb_Series_R2_2025Q2.vss
- FortiAuthenticator_Series_R2_2025Q2.vss
- FortiMail_Series_R2_2025Q2.vss
- FortiDDoS_Series_R1_2025Q2.vss
- FortiSwitch-Rugged_Series_R2_2025Q2.vss
- FortiCamera_Series_R1_2025Q2.vss
- Fortinet_Icons_new_R2_2025Q2.vss
- Fortinet_Professional_Services.vss
- Accessories_New.vss

These stencils can be converted to SVG using the `libvisio2svg` tool.

## Developer Tools

**Location**: `tools/`

### Testing & Development Scripts

#### FortiGate API Testing
- `test_fortigate_api.py` - Test FortiGate API connectivity and endpoints
- `fortigate_dev_helper.py` - Development helper utilities for FortiGate integration
- `watch_dev.py` - File watcher for development mode

#### FortiSwitch API Testing
- `test_fortiswitch_api.py` - Test FortiSwitch API connectivity
- `test_fortiswitch_models.py` - Test FortiSwitch device model detection

#### Authentication & Session Management
- `setup_auth.py` - Configure authentication system
- `test_redis_session_auth.py` - Test Redis-based session authentication
- `test_session_endpoints.py` - Test session management endpoints

#### Network Monitoring
- `wan_monitor.py` - WAN connection monitoring utility
- `port_scanner.py` - Network port scanning tool

#### Icon & Asset Management
- `import_icon_pack.py` - Import and organize icon packs
- `test_topology_icons.py` - Test topology icon rendering
- `simple_Icons.py` - Simple icon management utility
- `simple_svg_optimize.py` - SVG optimization tool
- `scrape_icons.py` - Icon scraping from web sources

#### Database & Storage
- `test_neo4j_topology.py` - Test Neo4j topology database
- `test_redis_connection.py` - Test Redis connectivity
- `test_postgresql.py` - Test PostgreSQL database

#### Topology & Visualization
- `test_hybrid_topology.py` - Test hybrid topology service
- `test_topology_service.py` - Test topology service endpoints
- `enhanced_network_discovery.py` - Advanced network device discovery

### Root Directory Scripts

#### Visio Stencil Processing
- `extract_visio_stencils.py` - Extract and convert Visio stencils to SVG
- Location: `/home/keith/fortigate-dashboard/`

## 3D Models & Assets

**Location**: `app/static/js/3d-device-models.js`

### Available 3D Device Models
- **FortiGate**: Realistic 3D firewall model with LED indicators and ports
- **FortiSwitch**: 8-port switch with individual port LEDs
- **Laptop**: Client device model with screen and keyboard
- **Wireless AP**: Circular access point with LED ring
- **Wireless Device**: Smartphone/tablet form factor

Color palette matches FortiGate branding (#c41e3a red accent).

## Usage Instructions

### Using Fortinet Icons in Templates
```html
<img src="/static/icons/fortinet/fortigate/FG-100F.svg" alt="FortiGate 100F">
<img src="/static/icons/fortinet/fortiswitch/FSW-248E-POE.svg" alt="FortiSwitch 248E-POE">
<img src="/static/icons/fortinet/fortiap/FAP-231F.svg" alt="FortiAP 231F">
```

### Using Meraki Icons
```html
<img src="/static/icons/meraki/MS220-24P.svg" alt="Meraki MS220-24P">
```

### Converting Visio Stencils to SVG
```bash
cd libvisio2svg
./vss2svg-conv -i "Fortinet Visio Stencil/FortiGate_Series_R22_2025Q2.vss" -o ./out/ -s 4.0
```

### Running Developer Tools
```bash
# Test FortiGate API
python tools/test_fortigate_api.py

# Monitor WAN connection
python tools/wan_monitor.py

# Import icon pack
python tools/import_icon_pack.py --source ./icons --destination app/static/icons/

# Optimize SVG files
python simple_svg_optimize.py --input app/static/icons/fortinet/
```

## Icon Naming Conventions

### Fortinet Icons
- FortiGate: `FG-[model].svg` (e.g., `FG-100F.svg`)
- FortiSwitch: `FSW-[model].svg` (e.g., `FSW-248E-POE.svg`)
- FortiAP: `FAP-[model].svg` (e.g., `FAP-231F.svg`)

### Generic Icons
- Device types use descriptive names (e.g., `laptop.svg`, `server.svg`, `router.svg`)

## Future Asset Integration

### Potential Additions
- [ ] FortiAnalyzer icons
- [ ] FortiManager icons
- [ ] FortiADC (Application Delivery Controller) icons
- [ ] Generic network device icons (routers, servers, endpoints)
- [ ] Data center equipment icons (racks, PDUs, UPS)
- [ ] Cable and connection icons

### Icon Database Integration
Icons should be registered in `app/utils/icon_db.py` for dynamic device-to-icon mapping in topology visualizations.

## Statistics

- **Total SVG Icons**: 190+ Fortinet icons, 4 Meraki icons, 100+ generic icons
- **Visio Stencils**: 13 official Fortinet stencil files
- **Developer Tools**: 20+ Python scripts for testing and development
- **3D Models**: 5 device types with realistic rendering
- **Icon Packs**: 3 complete icon sets with multiple color variants

Last Updated: 2025-12-07
