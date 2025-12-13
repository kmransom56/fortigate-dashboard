"""
Icon Mapper Service for Enhanced Topology Visualization
Maps devices to appropriate SVG icons from the extensive icon library
"""

import re
from typing import Optional, Dict

class IconMapper:
    """
    Maps FortiGate devices to appropriate icons from the 2600+ icon library.
    Handles FortiGate, FortiSwitch, FortiAP, and various endpoint types.
    """

    # FortiGate model mapping (based on hardware_family or OS version)
    FORTIGATE_MODELS = {
        # Entry models
        r'40[CF]': 'FG-40C_40F.svg',
        r'60[EF]': 'FG-60E_60F.svg',
        r'80[EF]': 'FG-80E_80F.svg',
        r'100[EF]': 'FG-100_101E.svg',
        r'100[F]': 'FG-100F_101F.svg',

        # Mid-range models
        r'200[EF]': 'FG-200_201E.svg',
        r'200[FG]': 'FG-200_201F.svg',
        r'300[EF]': 'FG-300_301E.svg',
        r'400[EF]': 'FG-400_401E.svg',
        r'600[EF]': 'FG-600_601E.svg',

        # High-end models
        r'1000[EF]': 'FG-1000_1001F.svg',
        r'1100[E]': 'FG-1100E_1101E.svg',
        r'1500[D]': 'FG-1500D_.svg',
        r'2000[E]': 'FG-2000E.svg',
        r'2200[E]': 'FG-2200E_2201E.svg',
        r'3000[D]': 'FG-3000D.svg',
        r'3600[E]': 'FG-3600_3601E.svg',

        # Default
        'default': 'FG-100F_101F.svg'
    }

    # FortiSwitch model mapping
    FORTISWITCH_MODELS = {
        # 8-port models
        r'108[DEF]': 'FSW-108E.svg',
        r'108.*POE': 'FSW-108E-POE.svg',
        r'108.*FPOE': 'FSW-108E-FPOE.svg',

        # 24-port models
        r'124[BDEF]': 'FSW-124E.svg',
        r'124.*POE': 'FSW-124E-POE.svg',
        r'124.*FPOE': 'FSW-124E-FPOE.svg',

        # 48-port models
        r'148[EF]': 'FSW-148F.svg',
        r'148.*POE': 'FSW-148F-POE.svg',
        r'148.*FPOE': 'FSW-148F-FPOE.svg',

        # Datacenter models
        r'224': 'FSW-224E.svg',
        r'448': 'FSW-448E.svg',
        r'524': 'FSW-524D.svg',
        r'548': 'FSW-548D.svg',
        r'1024': 'FSW-1024E__F_.svg',
        r'1048': 'FSW-1048E__F_.svg',
        r'2048': 'FSW-2048F.svg',

        # Default
        'default': 'FSW-124E.svg'
    }

    # FortiAP model mapping
    FORTIAP_MODELS = {
        # Indoor models
        r'221[EBC]': 'FAP-221_223E.svg',
        r'222[E]': 'FAP-222E.svg',
        r'223[EBC]': 'FAP-221_223E.svg',
        r'224[E]': 'FAP-224E.svg',
        r'231[EFK]': 'FAP-231E.svg',
        r'234[FG]': 'FAP-234G__R_.svg',
        r'241[K]': 'FAP-241K.svg',
        r'243[K]': 'FAP-243K.svg',

        # Outdoor models
        r'321[EBC]': 'FAP-321E.svg',
        r'421[E]': 'FAP-421_423E.svg',
        r'423[E]': 'FAP-421_423E.svg',
        r'431[F]': 'FAP-231F_233F_431F_433F.svg',
        r'433[F]': 'FAP-231F_233F_431F_433F.svg',

        # Universal models
        r'U221': 'FAP-U221_223EV.svg',
        r'U223': 'FAP-U221_223EV.svg',
        r'U321': 'FAP-U321_323EV.svg',
        r'U323': 'FAP-U321_323EV.svg',
        r'U421': 'FAP-U421_423EV.svg',
        r'U422': 'FAP-U422EV.svg',
        r'U431': 'FAP-U431_433F.svg',
        r'U432': 'FAP-U432F__F_.svg',

        # Default
        'default': 'FAP-221_223E.svg'
    }

    # Vendor-specific icons
    VENDOR_ICONS = {
        'apple': 'apple.svg',
        'microsoft': 'microsoft.svg',
        'dell': 'dell.svg',
        'hp': 'hp.svg',
        'lenovo': 'lenovo.svg',
        'cisco': 'cisco.svg',
        'vmware': 'vmware.svg',
        'linux': 'linux.svg',
        'windows': 'windows.svg',
        'android': 'android.svg',
        'samsung': 'samsung.svg',
        'asus': 'asus.svg',
        'sony': 'sony.svg',
        'lg': 'lg.svg'
    }

    # Device type icons
    DEVICE_TYPE_ICONS = {
        'server': 'Server.svg',
        'desktop': 'Desktop.svg',
        'laptop': 'Laptop.svg',
        'mobile': 'Mobile.svg',
        'tablet': 'Tablet.svg',
        'phone': 'Phone.svg',
        'printer': 'Printer.svg',
        'camera': 'Camera.svg',
        'router': 'Router.svg',
        'switch': 'Switch.svg',
        'access_point': 'Access Point.svg',
        'iot': 'IoT.svg',
        'application': 'Application.svg',
        'cloud': 'Cloud.svg',
        'database': 'Database.svg',
        'storage': 'Storage.svg'
    }

    @staticmethod
    def get_icon_for_device(device: Dict) -> str:
        """
        Get the best matching icon for a device.

        Args:
            device: Device dictionary with hardware_family, vendor, os, etc.

        Returns:
            Icon path relative to /static/icons/
        """
        hardware_family = device.get('hardware_family', '')
        hardware_type = device.get('hardware_type', '')
        vendor = device.get('vendor', '').lower()
        os = device.get('os', '').lower()
        role = device.get('role', '').lower()
        hostname = device.get('hostname', '').lower()

        # FortiGate devices
        if hardware_family == 'FortiGate' or 'fortigate' in vendor.lower():
            return f"icons/{IconMapper._match_fortigate_model(hostname, hardware_type, os)}"

        # FortiSwitch devices
        if hardware_family == 'FortiSwitch' or 'fortiswitch' in vendor.lower():
            return f"icons/{IconMapper._match_fortiswitch_model(hostname, hardware_type)}"

        # FortiAP devices
        if hardware_family == 'FortiAP' or 'fortiap' in vendor.lower():
            return f"icons/{IconMapper._match_fortiap_model(hostname, hardware_type)}"

        # Vendor-specific icons
        for vendor_key, icon in IconMapper.VENDOR_ICONS.items():
            if vendor_key in vendor:
                return f"icons/{icon}"

        # OS-based icons
        if 'windows' in os:
            return "icons/windows.svg"
        elif 'linux' in os or 'ubuntu' in os or 'debian' in os:
            return "icons/linux.svg"
        elif 'android' in os:
            return "icons/android.svg"
        elif 'ios' in os or 'iphone' in os or 'ipad' in os:
            return "icons/apple.svg"

        # Role-based icons
        if role in IconMapper.DEVICE_TYPE_ICONS:
            return f"icons/{IconMapper.DEVICE_TYPE_ICONS[role]}"

        # Hardware type
        if hardware_type:
            hw_lower = hardware_type.lower()
            if 'server' in hw_lower:
                return "icons/Server.svg"
            elif 'desktop' in hw_lower or 'workstation' in hw_lower:
                return "icons/Desktop.svg"
            elif 'laptop' in hw_lower or 'notebook' in hw_lower:
                return "icons/Laptop.svg"
            elif 'mobile' in hw_lower or 'phone' in hw_lower:
                return "icons/Mobile.svg"
            elif 'printer' in hw_lower:
                return "icons/Printer.svg"
            elif 'camera' in hw_lower:
                return "icons/Camera.svg"

        # Default fallback
        return "icons/Application.svg"

    @staticmethod
    def _match_fortigate_model(hostname: str, hardware_type: str, os: str) -> str:
        """Match FortiGate device to specific model icon."""
        # Try hostname first
        for pattern, icon in IconMapper.FORTIGATE_MODELS.items():
            if pattern != 'default' and re.search(pattern, hostname, re.IGNORECASE):
                return icon

        # Try hardware type
        if hardware_type:
            for pattern, icon in IconMapper.FORTIGATE_MODELS.items():
                if pattern != 'default' and re.search(pattern, hardware_type, re.IGNORECASE):
                    return icon

        # Try OS version
        if os:
            for pattern, icon in IconMapper.FORTIGATE_MODELS.items():
                if pattern != 'default' and re.search(pattern, os, re.IGNORECASE):
                    return icon

        return IconMapper.FORTIGATE_MODELS['default']

    @staticmethod
    def _match_fortiswitch_model(hostname: str, hardware_type: str) -> str:
        """Match FortiSwitch device to specific model icon."""
        search_text = f"{hostname} {hardware_type}".lower()

        for pattern, icon in IconMapper.FORTISWITCH_MODELS.items():
            if pattern != 'default' and re.search(pattern, search_text, re.IGNORECASE):
                return icon

        return IconMapper.FORTISWITCH_MODELS['default']

    @staticmethod
    def _match_fortiap_model(hostname: str, hardware_type: str) -> str:
        """Match FortiAP device to specific model icon."""
        search_text = f"{hostname} {hardware_type}".lower()

        for pattern, icon in IconMapper.FORTIAP_MODELS.items():
            if pattern != 'default' and re.search(pattern, search_text, re.IGNORECASE):
                return icon

        return IconMapper.FORTIAP_MODELS['default']

    @staticmethod
    def get_icon_catalog() -> Dict[str, list]:
        """
        Get a catalog of available icons by category.

        Returns:
            Dictionary with icon categories and lists of icons
        """
        return {
            'fortigate': list(set(IconMapper.FORTIGATE_MODELS.values())),
            'fortiswitch': list(set(IconMapper.FORTISWITCH_MODELS.values())),
            'fortiap': list(set(IconMapper.FORTIAP_MODELS.values())),
            'vendors': list(IconMapper.VENDOR_ICONS.values()),
            'device_types': list(IconMapper.DEVICE_TYPE_ICONS.values())
        }


# Convenience function
def get_device_icon(device: Dict) -> str:
    """Get icon for a device dictionary."""
    return IconMapper.get_icon_for_device(device)
