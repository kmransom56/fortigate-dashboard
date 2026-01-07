"""
Working data functions for network device management
Provides fallback data when MCP modules are not available
"""

def get_working_brands_data():
    """Get working brands data"""
    return {
        "success": True,
        "brands": [
            {
                "code": "BWW",
                "name": "Buffalo Wild Wings",
                "device_count": 678,
                "status": "active",
                "fortimanager": "10.128.145.4"
            },
            {
                "code": "ARBYS",
                "name": "Arby's",
                "device_count": 1057,
                "status": "active",
                "fortimanager": "10.128.144.132"
            },
            {
                "code": "SONIC",
                "name": "Sonic Drive-In",
                "device_count": 3454,
                "status": "active",
                "fortimanager": "10.128.156.36"
            }
        ],
        "total_brands": 3,
        "total_devices": 5189
    }

def get_working_bww_overview():
    """Get BWW overview data"""
    return {
        "success": True,
        "brand": "BWW",
        "overview": {
            "total_stores": 678,
            "online_stores": 658,
            "offline_stores": 20,
            "last_updated": "2024-08-27T14:30:00Z"
        }
    }

def get_working_store_security(brand, store_id):
    """Get store security data"""
    return {
        "success": True,
        "brand": brand,
        "store_id": store_id,
        "security_status": {
            "overall": "GOOD",
            "firewall": "ACTIVE",
            "last_policy_update": "2024-08-26T14:30:00Z",
            "threat_level": "LOW",
            "recent_events": 3
        }
    }
