# Cisco Meraki MS Series Switch Visio Stencils

## Official Download Sources

### Primary Source - Cisco Meraki Official
- **URL**: https://meraki.cisco.com/product-collateral/cisco-meraki-visio-stencils/
- **Direct Download**: Available from the official Cisco Meraki website
- **Content**: Complete Meraki product line including MS series switches

### Secondary Source - Cisco Products
- **URL**: https://www.cisco.com/c/en/us/products/visio-stencil-listing.html  
- **Content**: All Cisco product stencils including Meraki

### Security Devices Specific
- **Direct Download**: https://www.cisco.com/c/dam/assets/prod/visio/visio/security-cisco-meraki.zip
- **Content**: Meraki security devices and switches

## Available MS Series Switch Models

Based on community discussions and official resources, the following MS series models should be included in the Visio stencils:

### MS120 Series (Entry-Level)
- MS120-8 (8-port)
- MS120-24P (24-port PoE+)
- MS120-48FP-HW (48-port)
- MS120-48LP-HW (48-port low power)

### MS130 Series (Small Business)
- MS130-12X (12-port 10G)
- MS130-24P (24-port PoE+)
- MS130-24X (24-port 10G uplinks)
- MS130-48P (48-port PoE+)

### MS210 Series (Campus Access)
- MS210-24 (24-port)
- MS210-24P (24-port PoE+)
- MS210-48FP-HW (48-port full PoE+)

### MS220 Series (Campus Access)
- MS220-8 (8-port)
- MS220-24P (24-port PoE+)
- MS220-48FP (48-port full PoE+)

### MS250 Series (Campus Core)
- MS250-24 (24-port)
- MS250-48 (48-port)

### MS350 Series (Campus Distribution)
- MS350-24 (24-port)
- MS350-48 (48-port)

### MS390 Series (Campus Core)
- MS390-24 (24-port)
- MS390-48 (48-port)

### MS425 Series (Data Center)
- MS425-16 (16-port 10G)
- MS425-32 (32-port 10G)

## Restaurant Industry Usage

For BWW and Arby's locations using Meraki infrastructure:

### Typical Models for Restaurant Deployments
- **MS120-24P**: Small restaurants, 24 ports with PoE+ for cameras/APs
- **MS220-24P**: Mid-size locations with more PoE requirements
- **MS220-48FP**: Large restaurants needing full PoE+ on all ports
- **MS130-24P**: Sonic locations (though Sonic uses FortiSwitch)

### Infrastructure Context
- **BWW**: FortiGate + Meraki MS + FortiAP (900 locations)
- **Arby's**: FortiGate + Meraki MS + FortiAP (1,500 locations)
- **Sonic**: FortiGate + FortiSwitch + FortiAP (3,500 locations) - *Not Meraki*

## Installation Requirements

### Software Requirements
- Microsoft Visio Standard or Professional
- Compatible with Visio 2013, 2016, 2019, and Visio for Microsoft 365

### File Format
- **.vss** files (Visio stencil format)
- Packaged in **.zip** archives
- Connection points pre-configured for easy linking

## Known Issues & Notes

### Stencil Updates
- **Last Major Update**: 2019
- **Issue**: Newer MS model numbers may be missing from stencils
- **Status**: Cisco team working on updates

### Alternative Sources
If official stencils are missing specific models:
- **VisionSource**: Third-party Visio shapes repository
- **Community**: Meraki community forums for user-created shapes
- **Custom Creation**: SVG import from product datasheets

## Integration with FortiGate Dashboard

### 3D Topology Icons
The Meraki MS series Visio stencils can be converted for use in the 3D topology system:

1. **SVG Conversion**: Export Visio shapes to SVG format
2. **Eraser AI Integration**: Convert 2D shapes to 3D models
3. **Icon Database**: Add to `/app/static/icons/meraki/` directory
4. **Brand Detection**: Automatic selection for BWW/Arby's locations

### Icon Naming Convention
```
/app/static/icons/meraki/
├── MS120-24P.svg
├── MS220-24P.svg
├── MS220-48FP.svg
└── MS350-48.svg
```

## Usage in Network Documentation

### Network Diagrams
- Use appropriate MS model based on location size
- Include PoE requirements for restaurant devices (POS, cameras, APs)
- Show uplink connections to FortiGate firewall

### Topology Visualization
- 2D SVG for traditional network diagrams
- 3D models for interactive topology (via Eraser AI conversion)
- Brand-specific device selection based on restaurant type

## Download Instructions

1. Visit the official Cisco Meraki Visio stencils page
2. Download the complete stencil package
3. Extract the ZIP file to your Visio stencils directory
4. Open Microsoft Visio and access through "More Shapes" menu
5. Navigate to "Network" or "Cisco" categories to find Meraki stencils

## Support

For issues with Visio stencils:
- **Cisco TAC**: Technical support for licensed customers
- **Meraki Community**: Community forums for user discussions
- **Cisco Documentation**: Official product documentation and guides