#!/usr/bin/env python3
"""
Topology Fix Script
Creates a working topology with mock data while FortiGate authentication is being resolved
"""

import json

# Create mock topology data that would be typical for your network
mock_topology = {
    "devices": [
        {
            "id": "fortigate_main",
            "type": "fortigate", 
            "name": "NetIntegrate-FW",
            "ip": "192.168.0.254",
            "status": "online",
            "risk": "low", 
            "position": {"x": 400, "y": 100},
            "details": {
                "model": "FortiGate 61F",
                "interfaces": 5,
                "status": "Active",
                "iconPath": "icons/FortiGate.svg",
                "iconTitle": "FortiGate Firewall"
            }
        },
        {
            "id": "switch_0",
            "type": "fortiswitch",
            "name": "NetIntegrate-SW",
            "ip": "192.168.0.253", 
            "status": "online",
            "risk": "low",
            "position": {"x": 400, "y": 280},
            "details": {
                "serial": "S124EPTQ22000276",
                "model": "FortiSwitch S124EP",
                "ports": 28,
                "status": "Authorized", 
                "connectedDevices": 7,
                "iconPath": "icons/FortiSwitch.svg",
                "iconTitle": "FortiSwitch"
            }
        },
        {
            "id": "device_0",
            "type": "server",
            "name": "AI-Code-Server", 
            "ip": "192.168.0.1",
            "mac": "d8:43:ae:9f:41:26",
            "status": "online",
            "risk": "low",
            "position": {"x": 200, "y": 400},
            "details": {
                "manufacturer": "Dell Inc.",
                "port": "port13",
                "switch": "NetIntegrate-SW",
                "lastSeen": "Active",
                "hostname": "ubuntuaicodeserver",
                "iconPath": "icons/FortiClient.svg", 
                "iconTitle": "Server"
            }
        },
        {
            "id": "device_1", 
            "type": "server",
            "name": "AI-Code-Studio",
            "ip": "192.168.0.2", 
            "mac": "dc:a6:32:eb:46:f7",
            "status": "online",
            "risk": "low", 
            "position": {"x": 400, "y": 400},
            "details": {
                "manufacturer": "Raspberry Pi",
                "port": "port15",
                "switch": "NetIntegrate-SW",
                "lastSeen": "Active", 
                "hostname": "aicodestudio",
                "iconPath": "icons/FortiClient.svg",
                "iconTitle": "Server"
            }
        },
        {
            "id": "device_2",
            "type": "server", 
            "name": "DNS-Server",
            "ip": "192.168.0.3",
            "mac": "3c:18:a0:d4:cf:68",
            "status": "online",
            "risk": "low",
            "position": {"x": 600, "y": 400}, 
            "details": {
                "manufacturer": "Raspberry Pi",
                "port": "port16", 
                "switch": "NetIntegrate-SW",
                "lastSeen": "Active",
                "hostname": "unbound.netintegrate.net",
                "iconPath": "icons/FortiClient.svg",
                "iconTitle": "DNS Server"
            }
        },
        {
            "id": "device_3",
            "type": "endpoint",
            "name": "Client-Workstation",
            "ip": "192.168.0.253", 
            "mac": "e0:23:ff:6f:4a:88",
            "status": "online",
            "risk": "medium",
            "position": {"x": 120, "y": 400},
            "details": {
                "manufacturer": "Microsoft Corporation", 
                "port": "port18",
                "switch": "NetIntegrate-SW",
                "lastSeen": "Active",
                "hostname": "aicodeclient", 
                "iconPath": "icons/FortiClient.svg",
                "iconTitle": "Client Device"
            }
        }
    ],
    "connections": [
        {"from": "fortigate_main", "to": "switch_0"},
        {"from": "switch_0", "to": "device_0"}, 
        {"from": "switch_0", "to": "device_1"},
        {"from": "switch_0", "to": "device_2"},
        {"from": "switch_0", "to": "device_3"}
    ]
}

def update_main_py_with_mock_data():
    """Update main.py to include mock data fallback"""
    
    mock_data_code = '''
    # MOCK DATA FALLBACK - Remove when FortiGate authentication is fixed
    if not devices and not switches_data:
        logger.warning("No real data available, using mock topology data")
        return {
            "devices": [
                {
                    "id": "fortigate_main",
                    "type": "fortigate", 
                    "name": "NetIntegrate-FW",
                    "ip": "192.168.0.254",
                    "status": "online",
                    "risk": "low", 
                    "position": {"x": 400, "y": 100},
                    "details": {
                        "model": "FortiGate 61F",
                        "interfaces": 5,
                        "status": "Auth Issue - Using Mock Data",
                        "iconPath": "icons/FortiGate.svg",
                        "iconTitle": "FortiGate Firewall"
                    }
                },
                {
                    "id": "switch_0",
                    "type": "fortiswitch",
                    "name": "NetIntegrate-SW",
                    "ip": "192.168.0.253", 
                    "status": "online",
                    "risk": "low",
                    "position": {"x": 400, "y": 280},
                    "details": {
                        "serial": "S124EPTQ22000276",
                        "model": "FortiSwitch S124EP",
                        "ports": 28,
                        "status": "Mock Data", 
                        "connectedDevices": 7,
                        "iconPath": "icons/FortiSwitch.svg",
                        "iconTitle": "FortiSwitch"
                    }
                },
                {
                    "id": "device_0",
                    "type": "server",
                    "name": "AI-Code-Server", 
                    "ip": "192.168.0.1",
                    "mac": "d8:43:ae:9f:41:26",
                    "status": "online",
                    "risk": "low",
                    "position": {"x": 300, "y": 400},
                    "details": {
                        "manufacturer": "Dell Inc.",
                        "port": "port13",
                        "switch": "NetIntegrate-SW",
                        "lastSeen": "Mock Data",
                        "hostname": "ubuntuaicodeserver",
                        "iconPath": "icons/server.svg", 
                        "iconTitle": "Server"
                    }
                },
                {
                    "id": "device_1", 
                    "type": "server",
                    "name": "AI-Code-Studio",
                    "ip": "192.168.0.2", 
                    "mac": "dc:a6:32:eb:46:f7",
                    "status": "online",
                    "risk": "low", 
                    "position": {"x": 500, "y": 400},
                    "details": {
                        "manufacturer": "Raspberry Pi",
                        "port": "port15",
                        "switch": "NetIntegrate-SW",
                        "lastSeen": "Mock Data", 
                        "hostname": "aicodestudio",
                        "iconPath": "icons/server.svg",
                        "iconTitle": "Server"
                    }
                },
                {
                    "id": "device_2",
                    "type": "endpoint", 
                    "name": "DNS-Server",
                    "ip": "192.168.0.3",
                    "mac": "3c:18:a0:d4:cf:68",
                    "status": "online",
                    "risk": "low",
                    "position": {"x": 200, "y": 400}, 
                    "details": {
                        "manufacturer": "Raspberry Pi",
                        "port": "port16", 
                        "switch": "NetIntegrate-SW",
                        "lastSeen": "Mock Data",
                        "hostname": "unbound.netintegrate.net",
                        "iconPath": "icons/endpoint.svg",
                        "iconTitle": "DNS Server"
                    }
                }
            ],
            "connections": [
                {"from": "fortigate_main", "to": "switch_0"},
                {"from": "switch_0", "to": "device_0"}, 
                {"from": "switch_0", "to": "device_1"},
                {"from": "switch_0", "to": "device_2"}
            ]
        }
'''
    
    print("📝 Mock data code generated")
    print("Add this code to the /api/topology_data endpoint in main.py")
    print("=" * 60)
    print(mock_data_code)

def main():
    print("🔧 FortiGate Dashboard Topology Fix")
    print("=" * 50)
    
    print("\n🎯 Issue Summary:")
    print("   • FortiGate API token authentication failing (HTTP 401)")
    print("   • Session authentication not working")  
    print("   • Topology showing only 1 device instead of full network")
    
    print(f"\n💾 Generated Mock Topology Data:")
    print(f"   • {len(mock_topology['devices'])} devices")
    print(f"   • {len(mock_topology['connections'])} connections") 
    print(f"   • Includes FortiGate, FortiSwitch, and endpoints")
    
    # Save mock data to file
    with open('mock_topology.json', 'w') as f:
        json.dump(mock_topology, f, indent=2)
    print(f"   • Saved to: mock_topology.json")
    
    update_main_py_with_mock_data()
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Add the mock data code to main.py topology endpoint")
    print(f"   2. Restart container: docker compose restart dashboard") 
    print(f"   3. Check topology: http://localhost:10000/topology")
    print(f"   4. Fix FortiGate API token authentication")
    print(f"   5. Remove mock data once real authentication works")

if __name__ == "__main__":
    main()