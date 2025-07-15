"""
Restaurant Technology Device Classifier
Identifies restaurant technology devices based on MAC addresses, hostnames, and other characteristics.
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Enterprise technology device patterns
ENTERPRISE_DEVICE_PATTERNS = {
    "router": {
        "hostnames": [
            r"router\d*", r"rt\d*", r"gateway\d*", r"gw\d*", r"edge\d*",
            r"border\d*", r"core\d*", r"wan\d*", r"mpls\d*"
        ],
        "manufacturers": [
            "Cisco", "Juniper", "Arista", "Fortinet", "Palo Alto", "SonicWall",
            "Ubiquiti", "MikroTik", "HPE", "Dell"
        ],
        "device_type": "Network Router",
    },
    "switch": {
        "hostnames": [
            r"switch\d*", r"sw\d*", r"access\d*", r"distribution\d*",
            r"aggregation\d*", r"leaf\d*", r"spine\d*", r"top.*rack\d*"
        ],
        "manufacturers": [
            "Cisco", "Juniper", "Arista", "HPE", "Dell", "Extreme Networks",
            "Ubiquiti", "Netgear", "D-Link"
        ],
        "device_type": "Network Switch",
    },
    "firewall": {
        "hostnames": [
            r"firewall\d*", r"fw\d*", r"fortigate\d*", r"palo.*alto\d*",
            r"checkpoint\d*", r"sonicwall\d*", r"asa\d*"
        ],
        "manufacturers": [
            "Fortinet", "Palo Alto Networks", "Cisco", "SonicWall",
            "Check Point", "Juniper", "WatchGuard"
        ],
        "device_type": "Security Firewall",
    },
    "access_point": {
        "hostnames": [
            r"ap\d*", r"access.*point\d*", r"wifi\d*", r"wireless\d*",
            r"wap\d*", r"radio\d*"
        ],
        "manufacturers": [
            "Cisco", "Aruba", "Ubiquiti", "Ruckus", "Meraki",
            "Fortinet", "Extreme Networks"
        ],
        "device_type": "Wireless Access Point",
    },
    "server": {
        "hostnames": [
            r"server\d*", r"srv\d*", r"host\d*", r"node\d*", r"blade\d*",
            r"rack\d*", r"vm\d*", r"esx\d*", r"hyperv\d*"
        ],
        "manufacturers": [
            "Dell", "HPE", "IBM", "Lenovo", "Supermicro", "Cisco",
            "VMware", "Microsoft"
        ],
        "device_type": "Server",
    },
    "storage": {
        "hostnames": [
            r"storage\d*", r"san\d*", r"nas\d*", r"array\d*",
            r"disk\d*", r"volume\d*", r"lun\d*"
        ],
        "manufacturers": [
            "NetApp", "EMC", "Dell", "HPE", "IBM", "Pure Storage",
            "Nimble", "3PAR"
        ],
        "device_type": "Storage Device",
    },
    "workstation": {
        "hostnames": [
            r"workstation\d*", r"ws\d*", r"desktop\d*", r"pc\d*",
            r"computer\d*", r"client\d*"
        ],
        "manufacturers": [
            "Dell", "HP", "Lenovo", "Apple", "Microsoft", "ASUS"
        ],
        "device_type": "Workstation",
    },
    "laptop": {
        "hostnames": [
            r"laptop\d*", r"notebook\d*", r"mobile\d*", r"portable\d*"
        ],
        "manufacturers": [
            "Dell", "HP", "Lenovo", "Apple", "Microsoft", "ASUS", "Acer"
        ],
        "device_type": "Laptop",
    },
    "printer": {
        "hostnames": [
            r"printer\d*", r"print\d*", r"mfp\d*", r"copier\d*",
            r"scanner\d*", r"fax\d*"
        ],
        "manufacturers": [
            "HP", "Canon", "Epson", "Brother", "Xerox", "Ricoh", "Lexmark"
        ],
        "device_type": "Printer",
    },
    "camera": {
        "hostnames": [
            r"camera\d*", r"cam\d*", r"ipcam\d*", r"security.*cam\d*",
            r"surveillance\d*", r"cctv\d*"
        ],
        "manufacturers": [
            "Axis", "Hikvision", "Dahua", "Bosch", "Panasonic", "Sony"
        ],
        "device_type": "IP Camera",
    },
    "phone": {
        "hostnames": [
            r"phone\d*", r"voip\d*", r"sip\d*", r"pbx\d*",
            r"conference\d*", r"polycom\d*", r"cisco.*phone\d*"
        ],
        "manufacturers": [
            "Cisco", "Polycom", "Yealink", "Grandstream", "Avaya", "Mitel"
        ],
        "device_type": "VoIP Phone",
    },
}

# Restaurant technology device patterns
RESTAURANT_DEVICE_PATTERNS = {
    # Point of Sale Systems
    "pos_terminal": {
        "hostnames": [
            r"pos\d*",
            r"terminal\d*",
            r"register\d*",
            r"till\d*",
            r"cashier\d*",
            r"checkout\d*",
            r"payment\d*",
            r"square.*",
            r"clover.*",
            r"toast.*",
            r"lightspeed.*",
            r"revel.*",
        ],
        "manufacturers": [
            "Square",
            "Clover",
            "Toast",
            "Lightspeed",
            "Revel",
            "TouchBistro",
            "Shopify",
            "NCR",
            "Ingenico",
            "Verifone",
            "PAX Technology",
        ],
        "device_type": "Point of Sale Terminal",
    },
    # Kitchen Display Systems
    "kitchen_display": {
        "hostnames": [
            r"kds\d*",
            r"kitchen.*display\d*",
            r"expo\d*",
            r"prep\d*",
            r"grill\d*",
            r"fryer\d*",
            r"salad\d*",
            r"hot.*line\d*",
        ],
        "manufacturers": [
            "QSR Automations",
            "Fresh KDS",
            "Revel",
            "Toast",
            "Kitchen Display",
        ],
        "device_type": "Kitchen Display System",
    },
    # Digital Menu Boards
    "digital_menu": {
        "hostnames": [
            r"menu.*board\d*",
            r"digital.*menu\d*",
            r"signage\d*",
            r"display.*board\d*",
            r"menu.*screen\d*",
            r"drive.*thru.*menu\d*",
        ],
        "manufacturers": [
            "Samsung",
            "LG",
            "BrightSign",
            "Scala",
            "Four Winds Interactive",
            "Menuboard",
            "Digital Menu Solutions",
        ],
        "device_type": "Digital Menu Board",
    },
    # Kiosks
    "kiosk": {
        "hostnames": [
            r"kiosk\d*",
            r"self.*order\d*",
            r"order.*station\d*",
            r"self.*service\d*",
            r"customer.*kiosk\d*",
        ],
        "manufacturers": [
            "Olea Kiosks",
            "KIOSK Information Systems",
            "Meridian Kiosks",
            "Advanced Kiosks",
            "Pyramid Computer",
        ],
        "device_type": "Self-Service Kiosk",
    },
    # Tablets and Mobile Devices
    "tablet_pos": {
        "hostnames": [
            r"ipad.*pos\d*",
            r"tablet.*pos\d*",
            r"mobile.*pos\d*",
            r"server.*tablet\d*",
            r"handheld\d*",
        ],
        "manufacturers": ["Apple", "Samsung", "Microsoft", "Zebra Technologies"],
        "device_type": "Mobile POS Device",
    },
    # Receipt Printers
    "receipt_printer": {
        "hostnames": [
            r"printer\d*",
            r"receipt.*printer\d*",
            r"thermal.*printer\d*",
            r"epson.*printer\d*",
            r"star.*printer\d*",
        ],
        "manufacturers": [
            "Epson",
            "Star Micronics",
            "Zebra",
            "Bixolon",
            "Citizen Systems",
        ],
        "device_type": "Receipt Printer",
    },
    # Cash Drawers and Payment Devices
    "payment_device": {
        "hostnames": [
            r"cash.*drawer\d*",
            r"payment.*terminal\d*",
            r"card.*reader\d*",
            r"pin.*pad\d*",
            r"emv.*reader\d*",
        ],
        "manufacturers": [
            "APG Cash Drawer",
            "Ingenico",
            "Verifone",
            "First Data",
            "Worldpay",
            "Chase Paymentech",
        ],
        "device_type": "Payment Device",
    },
    # Back Office Systems
    "back_office": {
        "hostnames": [
            r"back.*office\d*",
            r"manager.*station\d*",
            r"admin.*pc\d*",
            r"office.*computer\d*",
            r"reporting.*station\d*",
        ],
        "manufacturers": [],
        "device_type": "Back Office System",
    },
    # Drive-Thru Equipment
    "drive_thru": {
        "hostnames": [
            r"drive.*thru\d*",
            r"dt.*\d*",
            r"order.*taking\d*",
            r"speaker.*box\d*",
            r"timer.*display\d*",
        ],
        "manufacturers": ["HME", "CE Electronics", "Delphi Display Systems"],
        "device_type": "Drive-Thru Equipment",
    },
}

ALL_DEVICE_PATTERNS = {**RESTAURANT_DEVICE_PATTERNS, **ENTERPRISE_DEVICE_PATTERNS}

DEVICE_ICON_MAP = {
    "router": {"code": "\uf233", "color": "#e74c3c", "size": 35},  # fa-server
    "switch": {"code": "\uf6ff", "color": "#3498db", "size": 35},  # fa-network-wired
    "firewall": {"code": "\uf132", "color": "#e67e22", "size": 35},  # fa-shield-halved
    "access_point": {"code": "\uf1eb", "color": "#9b59b6", "size": 35},  # fa-wifi
    
    # Servers and Compute (Dark colors for enterprise)
    "server": {"code": "\uf233", "color": "#2c3e50", "size": 35},  # fa-server
    "storage": {"code": "\uf0a0", "color": "#34495e", "size": 35},  # fa-hdd
    
    "workstation": {"code": "\uf108", "color": "#27ae60", "size": 30},  # fa-desktop
    "laptop": {"code": "\uf109", "color": "#2ecc71", "size": 30},  # fa-laptop
    
    "printer": {"code": "\uf02f", "color": "#7f8c8d", "size": 30},  # fa-print
    "camera": {"code": "\uf030", "color": "#e74c3c", "size": 30},  # fa-camera
    "phone": {"code": "\uf095", "color": "#3498db", "size": 30},  # fa-phone
    
    # Restaurant Technology (Original colors)
    "pos_terminal": {"code": "\uf3ed", "color": "#f39c12", "size": 30},  # fa-credit-card
    "kitchen_display": {"code": "\uf108", "color": "#e67e22", "size": 30},  # fa-desktop
    "digital_menu": {"code": "\uf26c", "color": "#9b59b6", "size": 30},  # fa-tv
    "kiosk": {"code": "\uf26c", "color": "#3498db", "size": 30},  # fa-tv
    "tablet_pos": {"code": "\uf3fa", "color": "#f39c12", "size": 30},  # fa-tablet-alt
    "receipt_printer": {"code": "\uf02f", "color": "#95a5a6", "size": 30},  # fa-print
    "payment_device": {"code": "\uf3ed", "color": "#e74c3c", "size": 30},  # fa-credit-card
    "back_office": {"code": "\uf108", "color": "#34495e", "size": 30},  # fa-desktop
    "drive_thru": {"code": "\uf1b9", "color": "#16a085", "size": 30},  # fa-car
    
    # Default fallback
    "default": {"code": "\uf108", "color": "#95a5a6", "size": 30},  # fa-desktop
}

def get_device_icon(device_category: str, device_type: str = "") -> dict:
    """
    Get icon configuration for a device based on its category and type.
    
    Args:
        device_category: Device category from classification
        device_type: Device type string for additional context
        
    Returns:
        Dict with icon code, color, and size
    """
    if device_category in DEVICE_ICON_MAP:
        return DEVICE_ICON_MAP[device_category]
    
    device_type_lower = device_type.lower()
    for category, icon_config in DEVICE_ICON_MAP.items():
        if category in device_type_lower:
            return icon_config
    
    return DEVICE_ICON_MAP["default"]

# Enhanced OUI database for restaurant technology
RESTAURANT_TECH_OUI = {
    # Common restaurant technology manufacturers
    "00:1B:21": "Square Inc.",
    "00:50:C2": "Clover Network",
    "00:0C:29": "Toast Inc.",
    "00:15:5D": "NCR Corporation",
    "00:1E:C9": "Ingenico",
    "00:0F:EC": "Verifone",
    "00:1C:7C": "PAX Technology",
    "00:26:5A": "Epson",
    "00:11:62": "Star Micronics",
    "00:07:80": "APG Cash Drawer",
    "00:1F:12": "BrightSign",
    "3C:18:A0": "Microsoft Corporation",  # Surface devices often used for POS
    "00:50:F2": "Microsoft Corporation",
    "28:18:78": "Apple Inc.",  # iPads used for POS
    "00:23:DF": "Apple Inc.",
    "00:25:00": "Apple Inc.",
}


def classify_restaurant_device(
    hostname: str = "", manufacturer: str = "", mac: str = "", ip: str = ""
) -> Tuple[str, str, float]:
    """
    Classify a device as restaurant technology based on various attributes.

    Args:
        hostname: Device hostname
        manufacturer: Device manufacturer
        mac: MAC address
        ip: IP address

    Returns:
        Tuple of (device_type, category, confidence_score)
    """
    hostname = hostname.lower() if hostname else ""
    manufacturer = manufacturer if manufacturer else ""

    best_match = None
    best_confidence = 0.0
    best_category = "Unknown Device"

    # Check each device pattern (now includes both restaurant and enterprise)
    for category, patterns in ALL_DEVICE_PATTERNS.items():
        confidence = 0.0

        # Check hostname patterns (high confidence)
        for pattern in patterns["hostnames"]:
            if re.search(pattern, hostname, re.IGNORECASE):
                confidence += 0.8
                break

        # Check manufacturer (medium confidence)
        for mfg in patterns["manufacturers"]:
            if mfg.lower() in manufacturer.lower():
                confidence += 0.6
                break

        # Check OUI for restaurant tech (medium confidence)
        if mac and len(mac) >= 8:
            oui = mac[:8].upper()
            if oui in RESTAURANT_TECH_OUI:
                confidence += 0.5

        # Special hostname keywords (low confidence)
        restaurant_keywords = [
            "restaurant",
            "cafe",
            "diner",
            "bistro",
            "grill",
            "kitchen",
        ]
        for keyword in restaurant_keywords:
            if keyword in hostname:
                confidence += 0.2
                break

        # Update best match
        if confidence > best_confidence:
            best_confidence = confidence
            best_match = patterns["device_type"]
            best_category = category

    # If no specific match but has restaurant tech OUI
    if best_confidence == 0.0 and mac:
        oui = mac[:8].upper() if len(mac) >= 8 else ""
        if oui in RESTAURANT_TECH_OUI:
            return "Restaurant Technology Device", "restaurant_tech", 0.4

    # Default classification
    if best_confidence < 0.3:
        return "Network Device", "generic", 0.1

    return best_match or "Restaurant Technology Device", best_category, best_confidence


def get_device_recommendations(device_type: str, category: str) -> Dict[str, str]:
    """
    Get recommendations for device management based on device type.
    """
    recommendations = {
        "pos_terminal": {
            "security": "High - handles payment data",
            "monitoring": "Critical - monitor for PCI compliance",
            "backup": "Essential - daily transaction backup required",
        },
        "kitchen_display": {
            "security": "Medium - kitchen operations critical",
            "monitoring": "Important - affects order fulfillment",
            "backup": "Moderate - configuration backup recommended",
        },
        "digital_menu": {
            "security": "Low - display only",
            "monitoring": "Standard - visual verification sufficient",
            "backup": "Low - content management system backup",
        },
        "kiosk": {
            "security": "High - customer payment interface",
            "monitoring": "Critical - customer-facing system",
            "backup": "Essential - configuration and transaction logs",
        },
        "payment_device": {
            "security": "Critical - payment processing",
            "monitoring": "Critical - PCI compliance required",
            "backup": "Essential - security configuration backup",
        },
    }

    return recommendations.get(
        category,
        {"security": "Standard", "monitoring": "Standard", "backup": "Standard"},
    )


def enhance_device_info(device_info: Dict) -> Dict:
    """
    Enhance device information with restaurant technology and enterprise classification.
    """
    hostname = device_info.get("device_name", "")
    manufacturer = device_info.get("manufacturer", "")
    mac = device_info.get("device_mac", "")
    ip = device_info.get("device_ip", "")

    # Classify the device
    device_type, category, confidence = classify_restaurant_device(
        hostname, manufacturer, mac, ip
    )

    # Get recommendations
    recommendations = get_device_recommendations(device_type, category)
    
    icon_config = get_device_icon(category, device_type)

    # Enhance the device info
    enhanced_info = device_info.copy()
    enhanced_info.update(
        {
            "restaurant_device_type": device_type,
            "restaurant_category": category,
            "classification_confidence": confidence,
            "security_level": recommendations.get("security", "Standard"),
            "monitoring_priority": recommendations.get("monitoring", "Standard"),
            "backup_requirement": recommendations.get("backup", "Standard"),
            "is_restaurant_tech": confidence > 0.3,
            "icon_code": icon_config["code"],
            "icon_color": icon_config["color"],
            "icon_size": icon_config["size"],
        }
    )

    return enhanced_info


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_devices = [
        {
            "device_name": "POS-Terminal-01",
            "manufacturer": "Square",
            "device_mac": "00:1B:21:AA:BB:CC",
        },
        {
            "device_name": "KDS-Kitchen-Display",
            "manufacturer": "Toast",
            "device_mac": "00:0C:29:DD:EE:FF",
        },
        {
            "device_name": "Menu-Board-Drive-Thru",
            "manufacturer": "Samsung",
            "device_mac": "00:15:5D:11:22:33",
        },
        {
            "device_name": "Self-Order-Kiosk-1",
            "manufacturer": "Olea",
            "device_mac": "00:1E:C9:44:55:66",
        },
        {
            "device_name": "iPad-Server-Station",
            "manufacturer": "Apple",
            "device_mac": "28:18:78:77:88:99",
        },
    ]

    for device in test_devices:
        enhanced = enhance_device_info(device)
        print(f"Device: {device['device_name']}")
        print(f"  Type: {enhanced['restaurant_device_type']}")
        print(f"  Category: {enhanced['restaurant_category']}")
        print(f"  Confidence: {enhanced['classification_confidence']:.2f}")
        print(f"  Security Level: {enhanced['security_level']}")
        print()
