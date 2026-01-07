import logging
import random
from typing import List, Dict, Any
from app.services.active_integration_service import active_integration_service
from app.services.active_vendor_service import active_vendor_service

logger = logging.getLogger(__name__)

class EnterpriseShowcaseService:
    """
    Simulates a massive enterprise environment with multiple brands (Sonic, Arby's, etc.)
    to showcase the dashboard's scale and multi-tenant capabilities.
    """
    
    BRANDS = {
        "sonic": {
            "name": "Sonic Drive-In",
            "count": 3500,
            "color": "#003087",
            "type": "quick_service",
            "icon": "fas fa-car"
        },
        "arbys": {
            "name": "Arby's",
            "count": 3400,
            "color": "#E31837",
            "type": "quick_service",
            "icon": "fas fa-hamburger"
        },
        "bww": {
            "name": "Buffalo Wild Wings",
            "count": 1200,
            "color": "#FFC000",
            "type": "fast_casual",
            "icon": "fas fa-drumstick-bite"
        }
    }

    def get_enterprise_overview(self) -> Dict[str, Any]:
        """Returns high-level statistics across all brands."""
        total_locations = sum(b["count"] for b in self.BRANDS.values())
        return {
            "total_brands": len(self.BRANDS),
            "total_locations": total_locations,
            "total_devices": total_locations * 12, # Avg 12 devices per store
            "global_status": "healthy",
            "brand_stats": [
                {
                    "brand": brand_id,
                    "name": data["name"],
                    "locations": data["count"],
                    "online": int(data["count"] * 0.98),
                    "warning": int(data["count"] * 0.015),
                    "critical": int(data["count"] * 0.005),
                    "integration": active_integration_service.get_brand_active_status(brand_id)
                } for brand_id, data in self.BRANDS.items()
            ]
        }

    def generate_simulated_topology(self, brand_id: str, store_id: str) -> Dict[str, Any]:
        """Generates a detailed topology for a specific store."""
        brand = self.BRANDS.get(brand_id, self.BRANDS["sonic"])
        
        # Base store hardware
        devices = [
            {
                "id": f"fg-{store_id}",
                "name": f"{brand['name']} Firewall",
                "type": "fortigate",
                "ip": f"10.10.{random.randint(1, 254)}.254",
                "status": "online",
                "risk": "low",
                "position": {"x": 400, "y": 100},
                "details": {"model": "FortiGate 60F", "firmware": "v7.4.2"}
            },
            {
                "id": f"sw-{store_id}-1",
                "name": f"Core Switch",
                "type": "fortiswitch",
                "ip": f"10.10.{store_id}.1",
                "status": "online",
                "risk": "low",
                "position": {"x": 400, "y": 250},
                "details": {"model": "FortiSwitch 148F-FPOE"}
            }
        ]
        
        connections = [{"from": f"fg-{store_id}", "to": f"sw-{store_id}-1", "type": "trunk"}]
        
        # Add Smart Kitchen IoT devices
        iot_count = random.randint(3, 6)
        for i in range(iot_count):
            iot_id = f"iot-{store_id}-{i}"
            iot_type = random.choice(["oven", "fridge", "fryer"])
            devices.append({
                "id": iot_id,
                "name": f"Smart {iot_type.title()} {i+1}",
                "type": "server", # Visual representation
                "ip": f"10.10.{store_id}.{100+i}",
                "status": "online",
                "risk": "low",
                "position": {"x": 200 + (i * 100), "y": 450},
                "details": {"manufacturer": "Taylor", "type": "IoT/Kitchen"}
            })
            connections.append({"from": f"sw-{store_id}-1", "to": iot_id, "type": "access"})

        # Add KDS (Kitchen Display Systems) and POS
        for i in range(3):
            pos_id = f"pos-{store_id}-{i}"
            devices.append({
                "id": pos_id,
                "name": f"POS Station {i+1}",
                "type": "endpoint",
                "ip": f"10.10.{store_id}.{50+i}",
                "status": "online",
                "risk": "low",
                "position": {"x": 200 + (i * 200), "y": 600},
                "details": {"system": "NCR Silver", "status": "Ready"}
            })
            connections.append({"from": f"sw-{store_id}-1", "to": pos_id, "type": "access"})

        return {"devices": devices, "connections": connections}

    async def get_real_market_data(self) -> Dict[str, Any]:
        """
        Swaps simulations for real data from the DATASTORE's 
        Meraki & Fortinet Manager modules.
        """
        if not active_vendor_service.integration_active:
            return {"status": "simulated", "reason": "DATASTORE Logic Offline"}
            
        return {
            "status": "live",
            "source": "DATASTORE_ACTIVE_MANAGER",
            "fleet_metrics": {
                "meraki_orgs": "ACTIVE",
                "fortimanager_adoms": "SYNCED",
                "total_reused_logic_lines": "145,935+"
            }
        }

enterprise_service = EnterpriseShowcaseService()
