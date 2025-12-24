"""
Restaurant Device Identification Service

Identifies and classifies devices commonly found in restaurant environments
across Arby's, Buffalo Wild Wings, and Sonic Drive-In locations.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RestaurantDeviceService:
    """Service for identifying restaurant-specific technology devices"""

    def __init__(self):
        self.restaurant_ouis = self._load_restaurant_ouis()
        self.device_patterns = self._load_device_patterns()
        self.restaurant_brands = {
            "arby": "Arby's",
            "bww": "Buffalo Wild Wings",
            "sonic": "Sonic Drive-In",
        }

    def _load_restaurant_ouis(self) -> Dict[str, Dict[str, str]]:
        """Load restaurant-specific OUI mappings"""
        return {
            # POS System Manufacturers
            "00:21:9b": {
                "manufacturer": "NCR Corporation",
                "device_type": "pos_terminal",
                "category": "point_of_sale",
                "common_in": ["arby", "bww"],
                "icon_hint": "pos",
            },
            "00:0c:29": {
                "manufacturer": "VMware Inc.",
                "device_type": "virtual_pos",
                "category": "point_of_sale",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "server",
            },
            # Kitchen Display Systems
            "00:50:c2": {
                "manufacturer": "IEEE Registration Authority",
                "device_type": "kitchen_display",
                "category": "kitchen_equipment",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "display",
            },
            # Security Cameras (Hikvision - very common in restaurants)
            "00:12:16": {
                "manufacturer": "Hikvision",
                "device_type": "security_camera",
                "category": "security",
            },
            "28:57:be": {
                "manufacturer": "Hikvision",
                "device_type": "security_camera",
                "category": "security",
            },
            "44:19:b6": {
                "manufacturer": "Hikvision",
                "device_type": "security_camera",
                "category": "security",
            },
            "68:64:4b": {
                "manufacturer": "Hikvision",
                "device_type": "security_camera",
                "category": "security",
            },
            "bc:ad:28": {
                "manufacturer": "Hikvision",
                "device_type": "security_camera",
                "category": "security",
            },
            # Axis Communications (Security cameras)
            "00:40:8c": {
                "manufacturer": "Axis Communications",
                "device_type": "security_camera",
                "category": "security",
            },
            "ac:cc:8e": {
                "manufacturer": "Axis Communications",
                "device_type": "security_camera",
                "category": "security",
            },
            # Payment Terminals
            "00:50:f2": {
                "manufacturer": "Ingenico",
                "device_type": "payment_terminal",
                "category": "payment_processing",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "payment",
            },
            "00:a0:98": {
                "manufacturer": "Verifone",
                "device_type": "payment_terminal",
                "category": "payment_processing",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "payment",
            },
            # Digital Signage and Menu Boards
            "00:16:6f": {
                "manufacturer": "Samsung Electronics",
                "device_type": "digital_signage",
                "category": "digital_displays",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "display",
            },
            "00:09:df": {
                "manufacturer": "LG Electronics",
                "device_type": "digital_signage",
                "category": "digital_displays",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "display",
            },
            # Self-Service Kiosks
            "00:18:fe": {
                "manufacturer": "Elo TouchSystems",
                "device_type": "kiosk",
                "category": "self_service",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "kiosk",
            },
            # WiFi Infrastructure (Common in restaurants)
            "88:dc:96": {
                "manufacturer": "Cisco Meraki",
                "device_type": "wifi_access_point",
                "category": "networking",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "wifi",
            },
            "04:18:d6": {
                "manufacturer": "Ubiquiti Inc.",
                "device_type": "wifi_access_point",
                "category": "networking",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "wifi",
            },
            # Temperature Monitoring (IoT devices)
            "00:13:a2": {
                "manufacturer": "SensorPush",
                "device_type": "temperature_sensor",
                "category": "iot_monitoring",
                "common_in": ["arby", "bww", "sonic"],
                "icon_hint": "sensor",
            },
        }

    def _load_device_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load hostname and device name patterns for restaurant devices"""
        return {
            # POS Terminal Patterns
            "pos": {
                "patterns": [
                    "pos-",
                    "register-",
                    "terminal-",
                    "aloha-",
                    "micros-",
                    "par-",
                ],
                "device_type": "pos_terminal",
                "category": "point_of_sale",
                "icon_hint": "pos",
            },
            # Kitchen Display Patterns
            "kds": {
                "patterns": ["kds-", "kitchen-", "display-", "qsr-", "connectsmart-"],
                "device_type": "kitchen_display",
                "category": "kitchen_equipment",
                "icon_hint": "display",
            },
            # Camera Patterns
            "camera": {
                "patterns": [
                    "cam-",
                    "camera-",
                    "dvr-",
                    "nvr-",
                    "security-",
                    "hikvision-",
                    "axis-",
                ],
                "device_type": "security_camera",
                "category": "security",
                "icon_hint": "camera",
            },
            # Digital Signage Patterns
            "signage": {
                "patterns": ["menu-", "sign-", "display-", "samsung-", "lg-"],
                "device_type": "digital_signage",
                "category": "digital_displays",
                "icon_hint": "display",
            },
            # Kiosk Patterns
            "kiosk": {
                "patterns": ["kiosk-", "order-", "self-", "elo-", "toast-"],
                "device_type": "kiosk",
                "category": "self_service",
                "icon_hint": "kiosk",
            },
            # Payment Terminal Patterns
            "payment": {
                "patterns": ["pay-", "card-", "ingenico-", "verifone-", "payment-"],
                "device_type": "payment_terminal",
                "category": "payment_processing",
                "icon_hint": "payment",
            },
            # Temperature Monitoring Patterns
            "temperature": {
                "patterns": ["temp-", "sensor-", "monitor-", "fridge-", "freezer-"],
                "device_type": "temperature_sensor",
                "category": "iot_monitoring",
                "icon_hint": "sensor",
            },
        }

    def identify_restaurant_device(
        self,
        mac: str,
        hostname: Optional[str] = None,
        manufacturer: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Identify restaurant-specific device based on MAC, hostname, and manufacturer

        Args:
            mac: MAC address (with or without separators)
            hostname: Device hostname if available
            manufacturer: Manufacturer name if already resolved

        Returns:
            Dict with device classification information
        """
        result = {
            "device_type": "unknown",
            "category": "general",
            "restaurant_device": False,
            "icon_hint": "laptop",
            "confidence": "low",
            "restaurant_brands": [],
            "description": "Unknown Device",
        }

        # Normalize MAC address for OUI lookup
        clean_mac = mac.replace(":", "").replace("-", "").upper()
        if len(clean_mac) >= 6:
            oui = ":".join([clean_mac[i : i + 2] for i in range(0, 6, 2)]).lower()

            # Check OUI database for restaurant devices
            if oui in self.restaurant_ouis:
                oui_info = self.restaurant_ouis[oui]
                result.update(
                    {
                        "device_type": oui_info.get("device_type", "unknown"),
                        "category": oui_info.get("category", "general"),
                        "restaurant_device": True,
                        "icon_hint": oui_info.get("icon_hint", "laptop"),
                        "confidence": "high",
                        "restaurant_brands": oui_info.get("common_in", []),
                        "description": f"{oui_info.get('manufacturer', 'Unknown')} {oui_info.get('device_type', 'Device').replace('_', ' ').title()}",
                    }
                )

        # Check hostname patterns for additional context
        if hostname and result["confidence"] != "high":
            hostname_lower = hostname.lower()
            for pattern_name, pattern_info in self.device_patterns.items():
                if any(
                    pattern in hostname_lower for pattern in pattern_info["patterns"]
                ):
                    result.update(
                        {
                            "device_type": pattern_info["device_type"],
                            "category": pattern_info["category"],
                            "restaurant_device": True,
                            "icon_hint": pattern_info["icon_hint"],
                            "confidence": "medium",
                            "description": f"Restaurant {pattern_info['device_type'].replace('_', ' ').title()}",
                        }
                    )
                    break

        # Check manufacturer name patterns
        if manufacturer and result["confidence"] == "low":
            manufacturer_lower = manufacturer.lower()
            restaurant_manufacturers = [
                "ncr",
                "par technology",
                "micros",
                "ingenico",
                "verifone",
                "hikvision",
                "axis",
                "elo touch",
                "qsr automations",
            ]

            if any(mfg in manufacturer_lower for mfg in restaurant_manufacturers):
                result.update({"restaurant_device": True, "confidence": "medium"})

        return result

    def get_restaurant_device_icon_path(
        self, device_info: Dict[str, str]
    ) -> Tuple[str, str]:
        """
        Get appropriate icon path for restaurant device

        Args:
            device_info: Device information from identify_restaurant_device

        Returns:
            Tuple of (icon_path, icon_title)
        """
        icon_hint = device_info.get("icon_hint", "laptop")
        device_type = device_info.get("device_type", "unknown")

        # Restaurant device icon mappings
        restaurant_icons = {
            "pos": ("icons/restaurant/pos-terminal.svg", "POS Terminal"),
            "payment": ("icons/restaurant/payment-terminal.svg", "Payment Terminal"),
            "camera": ("icons/restaurant/security-camera.svg", "Security Camera"),
            "display": ("icons/restaurant/digital-display.svg", "Digital Display"),
            "kiosk": ("icons/restaurant/kiosk.svg", "Self-Service Kiosk"),
            "sensor": ("icons/restaurant/temperature-sensor.svg", "Temperature Sensor"),
            "wifi": ("icons/nd/wifi-controller.svg", "WiFi Access Point"),
        }

        # Try icon hint first, then device type
        if icon_hint in restaurant_icons:
            return restaurant_icons[icon_hint]
        elif device_type in restaurant_icons:
            return restaurant_icons[device_type]
        else:
            # Fallback to generic icons
            fallback_icons = {
                "pos_terminal": ("icons/nd/server.svg", "POS Terminal"),
                "kitchen_display": ("icons/nd/server.svg", "Kitchen Display"),
                "security_camera": ("icons/nd/camera.svg", "Security Camera"),
                "digital_signage": ("icons/nd/server.svg", "Digital Signage"),
                "kiosk": ("icons/nd/server.svg", "Kiosk"),
                "payment_terminal": ("icons/nd/server.svg", "Payment Terminal"),
                "temperature_sensor": ("icons/nd/server.svg", "Temperature Sensor"),
                "wifi_access_point": ("icons/nd/wifi-controller.svg", "WiFi AP"),
            }
            return fallback_icons.get(
                device_type, ("icons/nd/laptop.svg", "Restaurant Device")
            )

    def get_device_risk_assessment(self, device_info: Dict[str, str]) -> str:
        """
        Assess security risk level for restaurant device

        Args:
            device_info: Device information from identify_restaurant_device

        Returns:
            Risk level: 'low', 'medium', 'high', 'critical'
        """
        device_type = device_info.get("device_type", "unknown")
        category = device_info.get("category", "general")

        # High-risk device categories
        if category == "payment_processing":
            return "critical"  # PCI DSS compliance required
        elif category == "point_of_sale":
            return "high"  # Contains sensitive transaction data
        elif category == "security":
            return "medium"  # Security infrastructure
        elif category == "networking":
            return "medium"  # Network infrastructure
        else:
            return "low"  # General restaurant equipment


# Global service instance
_restaurant_device_service = None


def get_restaurant_device_service() -> RestaurantDeviceService:
    """Get the global restaurant device service instance"""
    global _restaurant_device_service
    if _restaurant_device_service is None:
        _restaurant_device_service = RestaurantDeviceService()
    return _restaurant_device_service
