# Comprehensive QSR Restaurant Technology Device Research

## Executive Summary

This research compiles comprehensive information about technology devices commonly found in quick-service restaurants (QSR) and casual dining establishments, specifically focusing on Arby's, Buffalo Wild Wings (BWW), and Sonic Drive-In. The data includes device types, manufacturers, MAC address OUI information, and network characteristics to enhance network device identification and icon mapping systems.

## Restaurant-Specific Technology Implementations

### Arby's Restaurant Technology Stack

**Point of Sale (POS) Systems:**
- **PAR Technology** - Primary POS provider for franchisees
- **NCR Aloha POS** - Radiant Systems/NCR Aloha Enterprise Suite for 1,150+ company-operated locations
  - MAC OUI: `00:21:9b` (NCR Corporation)
  - Includes: Aloha Quick Service POS, Aloha Command Center, Aloha Configuration Center, Aloha Insight
- **ItsaCheckmate Integration** - Third-party delivery order integration across 1,100+ units
- **Retail Data Systems (RDS)** - Alternative POS provider

**Recent Technology Investments (2024-2025):**
- Major POS hardware/software upgrade completed across 800 corporate locations
- Average of 4 POS terminals per location
- 5-month implementation timeframe for complete rollout

### Buffalo Wild Wings (BWW) Technology Infrastructure

**POS System Partnerships:**
- **NCR Voyix** - Primary POS platform (renewed 2024)
- **Hospitality Solutions International** - Microsoft Windows-based Profit Series POS for corporate stores
- **24-7 Hospitality Technology** - Franchise POS provider (200+ locations)

**Kitchen Display Systems:**
- **QSR Automations ConnectSmart** - Kitchen display software (40+ franchise locations)
- Integrated recipe viewer, seating, and wait list management
- Connected to wait list, kitchen, cash management, and accounting systems

**Integration Capabilities:**
- Real-time inventory data integration across 1,200+ restaurant POS systems
- Advanced beer inventory management requiring configuration before sales

### Sonic Drive-In Technology Platform

**POS Systems:**
- **MICROS POS** - New system replacing 20-year-old legacy platform
- **POPS (Point of Personalized Service)** - Digital ordering system with touchscreen kiosks
- Investment: ~$135,000 total ($100,000 net after vendor contributions)
- 3-year rollout timeline for complete implementation

**Digital Menu Board Systems:**
- **POP System** - Digital drive-in menu boards with dynamic content
- Real-time price adjustments and targeted messaging capabilities
- Daypart displays with personalized content delivery

**Drive-Thru Communication:**
- Integrated mobile app connectivity
- Touchscreen ordering interfaces at drive-in stalls
- Mobile app integration for seamless order transition

## Device Categories and Manufacturer Analysis

### 1. Point of Sale (POS) Systems

| Manufacturer | MAC OUI | Models | Network Type | Classification |
|--------------|---------|---------|--------------|---------------|
| NCR Corporation | `00:21:9b` | Aloha POS terminals | Wired Ethernet | POS Terminal |
| PAR Technology | TBD | PAR Phase series | Wired/WiFi | POS Terminal |
| MICROS Systems | TBD | MICROS POS | Wired Ethernet | POS Terminal |
| 24-7 Hospitality | TBD | Various models | Wired Ethernet | POS Terminal |
| Retail Data Systems | TBD | RDS POS systems | Wired Ethernet | POS Terminal |

**Common Characteristics:**
- Network: Primarily wired Ethernet connections
- Power: Standard AC power with UPS backup
- Integration: Connected to payment processors, kitchen displays, inventory systems

### 2. Kitchen Display Systems (KDS)

| Manufacturer | Features | Network Type | Integration |
|--------------|----------|--------------|-------------|
| QSR Automations | ConnectSmart platform | Wired Ethernet | POS, inventory, timers |
| NCR/Aloha | Kitchen display modules | Wired Ethernet | Aloha POS ecosystem |
| PAR Technology | Kitchen display solutions | Wired/WiFi | PAR POS integration |

**Technical Specifications:**
- Display: Industrial-grade LCD/LED displays
- Connectivity: Ethernet primary, WiFi backup
- Power: 24V DC or PoE (Power over Ethernet)

### 3. Digital Menu Boards and Signage

**Common Manufacturers:**
- Samsung Commercial Displays
- LG Commercial Solutions
- NEC Display Solutions
- Sharp/NEC commercial displays

**Network Characteristics:**
- Connection: WiFi or wired Ethernet
- Content Management: Cloud-based systems
- Power: Standard AC power
- Resolution: 4K/HD displays standard

### 4. Payment Processing Terminals

**Major Manufacturers:**
- **Ingenico** - Payment terminals
- **Verifone** - Card readers and payment devices
- **First Data/Fiserv** - Payment processing hardware
- **Square** - Mobile payment solutions

**Network Types:**
- Primary: Dedicated payment network connections
- Backup: Internet connectivity for processing
- Local: Bluetooth/NFC for mobile payments

### 5. Security Cameras and Surveillance Systems

| Manufacturer | MAC OUI Examples | Product Lines | Network Type |
|--------------|------------------|---------------|--------------|
| Hikvision | `18:68:CB`, `28:57:BE`, `44:19:B6`, `4C:BD:8F`, `54:C4:15`, `64:DB:8B`, `94:E1:AC`, `A4:14:37`, `B4:A3:82`, `BC:AD:28`, `C0:56:E3`, `C4:2F:90` | IP cameras, NVRs | Wired/WiFi |
| Axis Communications | Various OUIs | Network cameras | PoE Ethernet |
| Dahua Technology | Various OUIs | IP surveillance | Wired/WiFi |
| Uniview | Various OUIs | Network cameras | PoE Ethernet |

**Common Specifications:**
- Resolution: 1080p to 4K recording
- Storage: Network Video Recorders (NVRs)
- Power: PoE (Power over Ethernet) preferred
- Connectivity: Wired Ethernet primary, WiFi backup

### 6. WiFi Access Points and Networking Equipment

| Manufacturer | Common Models | Network Type | Use Case |
|--------------|---------------|--------------|----------|
| Cisco Meraki | MR series | WiFi 6/6E | Enterprise guest WiFi |
| Ubiquiti Networks | UniFi series | WiFi 6 | Cost-effective enterprise |
| Aruba (HPE) | InstantOn series | WiFi 6E | Branch office/retail |
| Ruckus Networks | R series | WiFi 6 | High-density environments |

**Network Architecture:**
- Guest WiFi: Separate VLAN for customers
- Staff WiFi: Corporate network access
- IoT Network: Dedicated network for devices
- Management: Out-of-band management interfaces

### 7. Drive-Thru Communication Systems

**HME (Hospitality & Specialty Communications):**
- **NEXEO HDX Platform** - Industry-leading drive-thru communication
- **Base Station BS7000** - Network-enabled base station with Ethernet
- **Wireless Transceivers** - Various models for crew communication
- **Network Requirements:** Internet connection and HME Cloud account required

**Key Features:**
- Network Status: LAN and cloud connectivity monitoring
- Web Server Port: Unique network port for communication
- IP Configuration: DHCP or static IP addressing
- MAC Address: Each component has unique MAC for network identification

### 8. Self-Service Kiosks and Ordering Terminals

| Manufacturer | Product Lines | Features | Network |
|--------------|---------------|----------|---------|
| KIOSK Information Systems | Custom kiosks | Touch displays, payment | Ethernet/WiFi |
| Square | iPad-based kiosks | iOS platform | WiFi |
| Elo Touch Solutions | All-in-one kiosks | Various screen sizes | Ethernet/WiFi |
| REDYREF | Self-service kiosks | Indoor/outdoor models | Ethernet/WiFi |
| Toast POS | Restaurant kiosks | POS integration | Ethernet/WiFi |
| INFI | QSR kiosk solutions | Mobile integration | WiFi |

**Technical Characteristics:**
- Display: 15" to 27" touch screens
- Payment: Integrated card readers, NFC
- Connectivity: Dual Ethernet/WiFi for redundancy
- Power: AC power with battery backup

### 9. Temperature Monitoring Systems

| Manufacturer | Technology | Network Type | Monitoring Scope |
|--------------|------------|--------------|------------------|
| TempGenius | WiFi 802.11, 418/900/923 MHz | Wireless/Cellular | Walk-in coolers, freezers |
| Monnit | 900 MHz, WiFi, Cellular | Wireless mesh | Environmental monitoring |
| SensoScientific | WiFi, Cellular | Wireless | Food safety compliance |
| Swift Sensors | 900 MHz, WiFi | Wireless | Refrigeration monitoring |
| Sonicu | WiFi, Cellular | Wireless | Food safety monitoring |

**Communication Protocols:**
- **Primary:** WiFi 802.11 b/g/n/ac
- **Backup:** Cellular 4G/5G connectivity
- **Local:** 900 MHz mesh networking
- **Gateway:** Ethernet uplink to cloud services

### 10. Audio/Entertainment Systems

**Common Manufacturers:**
- **Bose Commercial** - Ceiling speakers, amplifiers
- **QSC Audio** - Digital signal processors, amplifiers
- **Crestron** - Audio control systems
- **Symetrix** - Digital audio processors

**Network Integration:**
- IP-based audio distribution
- Streaming media players
- Background music services (Pandora Business, Spotify Business)
- Paging system integration

### 11. Back-Office Computers and Tablets

**Hardware Types:**
- **Desktop PCs:** Dell OptiPlex, HP ProDesk series
- **Tablets:** iPad, Android tablets, Windows tablets
- **Thin Clients:** HP t-series, Dell Wyse

**Network Characteristics:**
- Wired Ethernet for desktop systems
- WiFi for mobile devices
- VPN connectivity for remote access
- Domain-joined for centralized management

### 12. Handheld Ordering Devices

**Device Categories:**
- **Tablets:** iPad, Samsung Galaxy Tab, Microsoft Surface
- **Handheld POS:** PAR handheld devices, NCR mobile POS
- **Smartphones:** iPhone, Android devices with POS apps

**Connectivity:**
- WiFi primary connection
- 4G/5G cellular backup
- Bluetooth for peripheral connectivity
- NFC for payment processing

## Network Architecture Considerations

### VLAN Segmentation
- **Guest WiFi:** Isolated network for customers
- **Corporate:** Staff and management access
- **IoT/Devices:** Separate network for restaurant equipment
- **Payment:** Isolated PCI-compliant network
- **Security:** Camera and access control systems

### Security Requirements
- **PCI DSS Compliance** for payment systems
- **WPA3 Enterprise** for WiFi networks
- **Network Access Control (NAC)** for device authentication
- **Firewall rules** for inter-VLAN communication
- **VPN access** for remote management

### Bandwidth Requirements
- **POS Systems:** 1-2 Mbps per terminal
- **Security Cameras:** 2-8 Mbps per camera (1080p-4K)
- **Guest WiFi:** 25-50 Mbps aggregate
- **Kitchen Displays:** 1-2 Mbps per display
- **Digital Signage:** 5-10 Mbps for content updates

## OUI Database Enhancement Recommendations

### Priority MAC Address OUI Additions
1. **NCR Corporation:** `00:21:9b` - POS terminals, kitchen displays
2. **Hikvision Technology:** Multiple OUIs for security cameras
3. **HME Communications:** Drive-thru communication systems
4. **PAR Technology:** Restaurant POS and management systems
5. **Temperature monitoring vendors:** Various OUIs for wireless sensors

### Device Classification Categories
- **POS-Terminal:** Point of sale hardware
- **Kitchen-Display:** Kitchen display systems
- **Security-Camera:** IP cameras and NVRs
- **WiFi-AP:** Wireless access points
- **Drive-Thru-Comm:** Drive-thru communication equipment
- **Payment-Terminal:** Card readers and payment processors
- **Digital-Signage:** Menu boards and displays
- **Temperature-Sensor:** Environmental monitoring devices
- **Audio-System:** Sound and entertainment equipment
- **Mobile-Device:** Tablets and handheld devices

## Implementation Strategy

### Phase 1: Core Restaurant Systems
- POS terminals and payment processors
- Kitchen display systems
- Security cameras and NVRs
- WiFi infrastructure equipment

### Phase 2: Operational Systems
- Drive-thru communication systems
- Digital menu boards and signage
- Temperature monitoring sensors
- Audio/entertainment systems

### Phase 3: Mobile and Emerging Technologies
- Self-service kiosks
- Handheld ordering devices
- IoT sensors and automation
- Advanced analytics platforms

## Conclusion

This comprehensive research provides detailed information about technology devices commonly found in QSR and casual dining establishments. The data includes specific manufacturer information, MAC address OUI details, network characteristics, and device classifications that can be used to enhance network device identification and icon mapping systems.

The restaurant industry continues to evolve with new technologies, requiring ongoing updates to device databases and classification systems. Regular monitoring of technology deployments and vendor partnerships will be essential for maintaining accurate device identification capabilities.

---

*Research compiled: August 2024*  
*Sources: Industry publications, manufacturer websites, technical documentation*  
*Focus: Arby's, Buffalo Wild Wings, Sonic Drive-In technology implementations*