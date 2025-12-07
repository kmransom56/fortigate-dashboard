# Fortinet FortiAP Access Point Visio Stencils

## Official Download Sources

### Primary Source - Fortinet Community
- **URL**: https://community.fortinet.com/t5/Customer-Service/Technical-Tip-Fortinet-stencils-for-use-in-diagrams-VSS-SVG-PNG/ta-p/193532
- **Format**: VSS (Visio Stencil) files, SVG, PNG formats available
- **Access**: Fortinet Icon Library and Partner Portal

### Secondary Sources
- **Partner Portal**: https://partnerportal.fortinet.com (Navigate: Technical -> Download Visio Stencils)
- **Fortinet Website**: Official Icon Library section
- **VisioCafe**: Third-party repository with Fortinet stencils

### Important Note
From Fortinet documentation: *"Certain drawings and presentations may not be publicly available and are not explicitly permitted for use without Fortinet's consent."*

For newer product stencils, contact your local Fortinet sales team.

## Available FortiAP Series Models

Based on existing icons in the system, the following FortiAP models are supported:

### Indoor Access Points

#### FAP-221 Series (Entry-Level)
- **FAP-221E**: Basic indoor AP, 802.11ac Wave 1
- **FAP-221B/221C/321C**: Business-grade indoor models
- **FAP-222E**: Enhanced performance model
- **FAP-223B/223C**: Advanced indoor models

#### FAP-231 Series (Mid-Range) - **Most Common for Restaurants**
- **FAP-231E**: 802.11ac Wave 2, 2x2:2 MIMO
- **FAP-231F**: Wi-Fi 6 (802.11ax), ideal for high-density environments
- **FAP-233F**: Enhanced Wi-Fi 6 model with better performance
- **FAP-231K**: Compact wall-mount design

#### FAP-234 Series (High-Performance)
- **FAP-234G**: High-performance indoor AP
- **FAP-234G-R**: **Rugged version for harsh environments** (kitchen areas)

### Outdoor/Rugged Access Points

#### FAP-320 Series
- **FAP-320B/320C**: Outdoor weatherproof models
- **FAP-321E**: Enhanced outdoor performance

#### FAP-400 Series (Enterprise Outdoor)
- **FAP-421E/423E**: High-power outdoor models
- **FAP-431F/433F**: Wi-Fi 6 outdoor models
- **FAP-432F**: Enhanced outdoor Wi-Fi 6

### Vehicle/Mobile Access Points
- **FAP-U Series**: Designed for vehicle/mobile deployments
- **FAP-U221/223EV**: Vehicle-mounted models
- **FAP-U321/323EV**: Enhanced vehicle models
- **FAP-U431/433F**: Wi-Fi 6 vehicle models

## Restaurant Industry Usage by Brand

### Sonic Drive-In Infrastructure (FortiGate + FortiSwitch + FortiAP)
**Typical Deployment**: 4 APs per location
- **Indoor Dining**: FAP-231F (Wi-Fi 6, high density)
- **Kitchen Area**: FAP-234G-R (rugged model for harsh environment)
- **Drive-Thru**: FAP-321E (outdoor-rated for weather resistance)
- **Parking/Outdoor**: FAP-431F (high-power outdoor coverage)

**Coverage Requirements**:
- Indoor dining area: High-density client support
- Kitchen: Rugged design for heat/moisture
- Drive-thru: Weather resistance and extended range
- Outdoor seating: Long-range coverage

### Buffalo Wild Wings Infrastructure (FortiGate + Meraki + FortiAP)
**Typical Deployment**: 6 APs per location (larger venues)
- **Main Dining**: 2x FAP-233F (high-performance Wi-Fi 6)
- **Bar Area**: 2x FAP-231F (high-density entertainment support)
- **Kitchen**: FAP-234G-R (rugged for commercial kitchen)
- **Outdoor Patio**: FAP-431F (weather-resistant outdoor)

**Special Requirements**:
- High client density during sports events
- Streaming video support for multiple screens
- Guest and staff network separation
- Enhanced security for payment systems

### Arby's Infrastructure (FortiGate + Meraki + FortiAP)
**Typical Deployment**: 3 APs per location (smaller footprint)
- **Dining Area**: FAP-231F (Wi-Fi 6, efficient coverage)
- **Kitchen/Back Office**: FAP-231E (cost-effective indoor)
- **Drive-Thru/Outdoor**: FAP-321E (outdoor coverage)

**Design Considerations**:
- Cost-effective deployment for franchise model
- Reliable coverage for POS and inventory systems
- Guest Wi-Fi for dining area
- Staff access for operational systems

## Technical Specifications Comparison

| Model | Wi-Fi Standard | MIMO | Power | Mounting | Best Use Case |
|-------|---------------|------|-------|----------|---------------|
| FAP-231E | 802.11ac Wave 2 | 2x2:2 | Standard | Indoor | Basic restaurant coverage |
| FAP-231F | 802.11ax (Wi-Fi 6) | 2x2:2 | Enhanced | Indoor | High-density dining areas |
| FAP-233F | 802.11ax (Wi-Fi 6) | 3x3:3 | High | Indoor | Premium restaurant locations |
| FAP-234G-R | 802.11ac Wave 2 | 4x4:4 | High | Rugged | Kitchen/harsh environments |
| FAP-321E | 802.11ac Wave 2 | 2x2:2 | High | Outdoor | Drive-thru/patio coverage |
| FAP-431F | 802.11ax (Wi-Fi 6) | 2x2:2 | High | Outdoor | Large outdoor areas |

## Icon Integration with FortiGate Dashboard

### Current Icon Storage
FortiAP icons are stored in multiple locations:
- **Root Icons**: `/app/static/icons/FAP-*.svg` (26 total models)
- **Organized**: `/app/static/icons/fortiap/` (key models copied)

### Restaurant-Optimized Selection
Based on the 3 restaurant brands' infrastructure needs:

```
/app/static/icons/fortiap/
├── FAP-231E.svg          # Basic indoor (Arby's)
├── FAP-231F_233F_431F_433F.svg  # Multi-model (all brands)
├── FAP-234G__R_.svg      # Rugged kitchen model
└── FAP-321E.svg          # Outdoor/drive-thru
```

### 3D Topology Integration
1. **Brand Detection**: Automatically select appropriate FortiAP models based on restaurant brand
2. **Environment Mapping**: Choose rugged vs standard models based on location (kitchen, dining, outdoor)
3. **Eraser AI Conversion**: Convert 2D Visio stencils to 3D models for topology visualization
4. **Coverage Visualization**: Show Wi-Fi coverage areas and client connections

## Deployment Recommendations

### FortiAP Controller Integration
All restaurant brands use **FortiGate as the wireless controller**:
- Centralized management through FortiGate dashboard
- Unified security policies across wired and wireless
- Integration with brand detection service
- Automatic configuration based on restaurant type

### Security Considerations
- **Guest Network Isolation**: Separate VLANs for customer and staff access
- **PCI Compliance**: Secure wireless for payment processing
- **Network Segmentation**: IoT devices (cameras, sensors) on dedicated networks
- **Captive Portal**: Branded guest access with terms acceptance

### Performance Optimization
- **Wi-Fi 6 Deployment**: FAP-231F/233F for high-density areas
- **Band Steering**: Automatic client distribution between 2.4GHz and 5GHz
- **Load Balancing**: Multiple APs for large venues (BWW)
- **Mesh Capability**: Wireless backhaul for difficult installations

## API Integration Points

### FortiAP Management via FortiGate
```python
# Brand-specific FortiAP detection in brand_detection_service.py
async def _discover_fortiap_devices(self, ip_address: str) -> List[Dict[str, Any]]:
    """Discover FortiAP devices (all brands use FortiGate controller)"""
    # Uses FortiGate wireless controller API
    # GET /api/v2/monitor/wifi/managed_ap
    # Returns: AP status, client count, radio information
```

### Expected API Endpoints
- `/api/v2/monitor/wifi/managed_ap` - List all managed APs
- `/api/v2/monitor/wifi/client` - Connected wireless clients  
- `/api/v2/cmdb/wireless-controller/wtp` - AP configuration
- `/api/v2/monitor/wifi/spectrum` - Spectrum analysis

### Restaurant-Specific Data
```json
{
  "ap_serial": "FAP231F2021000123",
  "model": "FAP-231F", 
  "location": "dining_area",
  "environment": "indoor",
  "client_count": 45,
  "restaurant_brand": "sonic",
  "coverage_area": "zone_1"
}
```

## Installation Requirements

### Software Requirements
- Microsoft Visio Standard or Professional (2013+)
- Compatible with Visio for Microsoft 365

### File Formats
- **.vss** files (Visio stencil format)
- **.svg** files (Scalable Vector Graphics)
- **.png** files (Raster graphics)

### Integration Workflow
1. **Download** official Fortinet stencils from Partner Portal
2. **Extract** desired FortiAP models
3. **Convert** to SVG format for web compatibility  
4. **Optimize** for 3D topology system
5. **Integrate** with brand detection service

## Support and Updates

### Official Support Channels
- **Fortinet TAC**: Technical support for licensed customers
- **Partner Portal**: Access to latest stencil updates
- **Community Forums**: User discussions and custom stencils

### Update Schedule
- **Official Stencils**: Updated with new product releases
- **Community Versions**: Maintained by user community
- **Custom Development**: Contact Fortinet sales for specific requirements

For the most current FortiAP stencils and documentation, always check the official Fortinet Partner Portal or contact your local Fortinet sales team.