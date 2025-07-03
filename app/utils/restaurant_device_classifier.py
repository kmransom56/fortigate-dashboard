"""
Restaurant Technology Device Classifier
Identifies restaurant technology devices based on MAC addresses, hostnames, and other characteristics.
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

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

    # Check each restaurant device pattern
    for category, patterns in RESTAURANT_DEVICE_PATTERNS.items():
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
    Enhance device information with restaurant technology classification.
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
