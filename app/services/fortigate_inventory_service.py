"""
FortiGate Inventory Service

Loads and manages real FortiGate management IP addresses from CSV file.
Provides location-specific FortiGate access for enterprise-scale operations.
"""

import logging
import csv
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import ipaddress

logger = logging.getLogger(__name__)


@dataclass
class FortiGateLocation:
    store_number: str
    mgmt_interface: str
    ip_address: str
    subnet_mask: str
    brand: str
    network: Optional[str] = None
    region: Optional[str] = None
    status: str = "unknown"
    last_seen: Optional[datetime] = None
    model: Optional[str] = None
    firmware: Optional[str] = None


class FortiGateInventoryService:
    """Service for managing enterprise FortiGate inventory"""

    def __init__(self, csv_path: str = "downloaded_files/vlan10_interfaces.csv"):
        self.csv_path = csv_path
        self.locations: Dict[str, FortiGateLocation] = {}
        self.brand_mapping = {
            "Arbys": "arbys",
            "BWW": "bww",
            "Sonic": "sonic",
            "Unknown": "unknown",
        }

        # Load data on initialization
        self._load_fortigate_inventory()

    def _load_fortigate_inventory(self) -> None:
        """Load FortiGate inventory from CSV file"""
        csv_file_path = os.path.join(os.getcwd(), self.csv_path)

        if not os.path.exists(csv_file_path):
            logger.error(f"FortiGate inventory CSV not found: {csv_file_path}")
            return

        try:
            with open(csv_file_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    store_number = row.get("store_number", "").strip()
                    mgmt_interface = row.get("mgmtintname", "").strip()
                    ip_cidr = row.get("ip_address", "").strip()
                    brand = row.get("brand", "").strip()

                    if not store_number or not ip_cidr:
                        continue

                    # Parse IP address and subnet
                    try:
                        if "/" in ip_cidr:
                            ip_addr, cidr = ip_cidr.split("/")
                            # Convert CIDR notation to subnet mask if needed
                            if "." not in cidr:
                                # CIDR notation (e.g., /24)
                                subnet_mask = str(
                                    ipaddress.IPv4Network(
                                        f"0.0.0.0/{cidr}", strict=False
                                    ).netmask
                                )
                            else:
                                # Already in subnet mask format
                                subnet_mask = cidr
                        else:
                            ip_addr = ip_cidr
                            subnet_mask = "255.255.255.0"  # Default assumption

                        # Determine region from store number or IP
                        region = self._determine_region(store_number, ip_addr)

                        location = FortiGateLocation(
                            store_number=store_number,
                            mgmt_interface=mgmt_interface,
                            ip_address=ip_addr,
                            subnet_mask=subnet_mask,
                            brand=brand,
                            region=region,
                        )

                        self.locations[store_number] = location

                    except Exception as e:
                        logger.warning(f"Failed to parse location {store_number}: {e}")
                        continue

                logger.info(
                    f"Loaded {len(self.locations)} FortiGate locations from inventory"
                )

                # Log brand distribution
                brand_counts = {}
                for location in self.locations.values():
                    brand_counts[location.brand] = (
                        brand_counts.get(location.brand, 0) + 1
                    )

                logger.info(f"Brand distribution: {brand_counts}")

        except Exception as e:
            logger.error(f"Failed to load FortiGate inventory: {e}")

    def _determine_region(self, store_number: str, ip_address: str) -> str:
        """Determine region from store number patterns or IP address"""
        try:
            # Parse IP for regional determination
            ip = ipaddress.IPv4Address(ip_address)

            # Common IP ranges for regional classification
            if ip in ipaddress.IPv4Network("10.211.0.0/16"):
                return "central"
            elif ip in ipaddress.IPv4Network("10.212.0.0/16"):
                return "east"
            elif ip in ipaddress.IPv4Network("10.213.0.0/16"):
                return "west"
            elif ip in ipaddress.IPv4Network("10.214.0.0/16"):
                return "south"
            else:
                return "unknown"

        except Exception:
            # Fall back to store number analysis
            if store_number.startswith("IBR_SONIC-01"):
                return "region_1"
            elif store_number.startswith("IBR_SONIC-02"):
                return "region_2"
            elif store_number.startswith("IBR-BWW"):
                return "bww_region"
            elif store_number.startswith("ARG"):
                return "arbys_region"
            else:
                return "unknown"

    def get_location(self, store_number: str) -> Optional[FortiGateLocation]:
        """Get FortiGate location by store number"""
        return self.locations.get(store_number)

    def get_locations_by_brand(
        self, brand: str, limit: int = None
    ) -> List[FortiGateLocation]:
        """Get locations filtered by brand"""
        brand_locations = [
            loc for loc in self.locations.values() if loc.brand.lower() == brand.lower()
        ]

        if limit:
            brand_locations = brand_locations[:limit]

        return brand_locations

    def get_locations_by_region(self, region: str) -> List[FortiGateLocation]:
        """Get locations filtered by region"""
        return [
            loc
            for loc in self.locations.values()
            if loc.region and loc.region.lower() == region.lower()
        ]

    def get_all_locations(
        self, limit: int = None, offset: int = 0
    ) -> List[FortiGateLocation]:
        """Get all locations with pagination"""
        all_locs = list(self.locations.values())

        if limit:
            return all_locs[offset : offset + limit]

        return all_locs[offset:]

    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get comprehensive inventory summary"""
        brand_stats = {}
        region_stats = {}
        ip_range_stats = {}

        for location in self.locations.values():
            # Brand statistics
            brand = location.brand
            if brand not in brand_stats:
                brand_stats[brand] = {"count": 0, "regions": set(), "ip_ranges": set()}
            brand_stats[brand]["count"] += 1
            if location.region:
                brand_stats[brand]["regions"].add(location.region)

            # Add IP range
            try:
                ip = ipaddress.IPv4Address(location.ip_address)
                ip_range = f"{ip.packed[0]}.{ip.packed[1]}.x.x"
                brand_stats[brand]["ip_ranges"].add(ip_range)

                # IP range statistics
                if ip_range not in ip_range_stats:
                    ip_range_stats[ip_range] = {"count": 0, "brands": set()}
                ip_range_stats[ip_range]["count"] += 1
                ip_range_stats[ip_range]["brands"].add(brand)

            except Exception:
                pass

            # Region statistics
            if location.region:
                region_stats[location.region] = region_stats.get(location.region, 0) + 1

        # Convert sets to lists for JSON serialization
        for brand_data in brand_stats.values():
            brand_data["regions"] = list(brand_data["regions"])
            brand_data["ip_ranges"] = list(brand_data["ip_ranges"])

        for ip_data in ip_range_stats.values():
            ip_data["brands"] = list(ip_data["brands"])

        return {
            "total_locations": len(self.locations),
            "brands": brand_stats,
            "regions": region_stats,
            "ip_ranges": ip_range_stats,
            "data_source": self.csv_path,
            "loaded_at": datetime.now().isoformat(),
        }

    def get_fortigate_connection_info(
        self, store_number: str
    ) -> Optional[Dict[str, Any]]:
        """Get connection information for a specific FortiGate"""
        location = self.get_location(store_number)
        if not location:
            return None

        # Standard FortiGate connection details
        connection_info = {
            "store_number": location.store_number,
            "ip_address": location.ip_address,
            "management_port": 443,  # Standard HTTPS management port
            "alt_management_port": 80,  # HTTP fallback
            "ssh_port": 22,
            "snmp_port": 161,
            "brand": location.brand,
            "region": location.region,
            "mgmt_interface": location.mgmt_interface,
            "subnet_mask": location.subnet_mask,
            "management_url": f"https://{location.ip_address}",
            "api_base_url": f"https://{location.ip_address}/api/v2",
            "status": location.status,
            "last_seen": location.last_seen.isoformat() if location.last_seen else None,
        }

        return connection_info

    def update_location_status(self, store_number: str, status: str, **kwargs) -> bool:
        """Update status and other properties of a location"""
        location = self.get_location(store_number)
        if not location:
            return False

        location.status = status
        location.last_seen = datetime.now()

        # Update additional properties
        for key, value in kwargs.items():
            if hasattr(location, key):
                setattr(location, key, value)

        return True

    def get_locations_for_discovery(
        self, brand: str = None, region: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get locations formatted for discovery operations"""
        locations = list(self.locations.values())

        # Apply filters
        if brand:
            locations = [loc for loc in locations if loc.brand.lower() == brand.lower()]

        if region:
            locations = [
                loc
                for loc in locations
                if loc.region and loc.region.lower() == region.lower()
            ]

        # Limit results
        if limit:
            locations = locations[:limit]

        # Format for discovery
        discovery_locations = []
        for location in locations:
            discovery_info = {
                "store_number": location.store_number,
                "ip_address": location.ip_address,
                "brand": location.brand,
                "region": location.region,
                "api_url": f"https://{location.ip_address}/api/v2",
                "management_url": f"https://{location.ip_address}",
                "priority": self._get_discovery_priority(location.brand),
                "expected_model": self._get_expected_model(location.brand),
                "connection_timeout": self._get_connection_timeout(location.brand),
            }
            discovery_locations.append(discovery_info)

        return discovery_locations

    def _get_discovery_priority(self, brand: str) -> int:
        """Get discovery priority based on brand"""
        priorities = {
            "Sonic": 1,  # Highest priority - most locations
            "Arbys": 2,  # Medium priority
            "BWW": 3,  # Lower priority
            "Unknown": 99,  # Lowest priority
        }
        return priorities.get(brand, 5)

    def _get_expected_model(self, brand: str) -> str:
        """Get expected FortiGate model based on brand"""
        models = {
            "Sonic": "FG-100F",  # Typical model for smaller locations
            "Arbys": "FG-100F",
            "BWW": "FG-200F",  # Larger locations might have bigger models
            "Unknown": "FG-100F",
        }
        return models.get(brand, "FG-100F")

    def _get_connection_timeout(self, brand: str) -> int:
        """Get connection timeout based on brand (seconds)"""
        timeouts = {
            "Sonic": 10,  # Standard timeout
            "Arbys": 15,  # Slightly longer
            "BWW": 15,  # Slightly longer
            "Unknown": 30,  # Longest timeout for unknown
        }
        return timeouts.get(brand, 10)

    def search_locations(self, query: str, limit: int = 50) -> List[FortiGateLocation]:
        """Search locations by store number, IP, or brand"""
        query = query.lower()
        results = []

        for location in self.locations.values():
            if (
                query in location.store_number.lower()
                or query in location.ip_address
                or query in location.brand.lower()
                or (location.region and query in location.region.lower())
            ):
                results.append(location)

                if len(results) >= limit:
                    break

        return results


# Global service instance
_fortigate_inventory_service = None


def get_fortigate_inventory_service() -> FortiGateInventoryService:
    """Get the global FortiGate inventory service instance"""
    global _fortigate_inventory_service
    if _fortigate_inventory_service is None:
        _fortigate_inventory_service = FortiGateInventoryService()
    return _fortigate_inventory_service
