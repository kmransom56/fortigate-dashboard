#!/usr/bin/env python3
"""
Simple usage examples for the Fortinet MCP Server
Demonstrates how to use the server components directly in your applications
"""

import sys
import os
import json
from datetime import datetime

# Add the MCP server to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MCP server components
from fortinet_server_enhanced import fg_api, fm_api, api_parser, discovered_endpoints

def example_basic_usage():
    """Basic usage examples"""
    print("=== BASIC MCP SERVER USAGE ===")
    
    # Test connection
    print("1. Testing FortiGate connection...")
    connection_result = fg_api.test_connection()
    print(f"   Result: {connection_result}")
    
    # Get system status
    print("\n2. Getting system status...")
    status = fg_api._make_request("GET", "monitor/system/status")
    if "error" not in status:
        print(f"   Hostname: {status.get('results', {}).get('hostname', 'Unknown')}")
        print(f"   Version: {status.get('results', {}).get('version', 'Unknown')}")
        print(f"   Serial: {status.get('results', {}).get('serial', 'Unknown')}")
    else:
        print(f"   Error: {status['error']}")
    
    # Get detected devices (your original curl command functionality)
    print("\n3. Getting detected devices...")
    devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
    if "error" not in devices and "results" in devices:
        print(f"   Found {len(devices['results'])} detected devices:")
        for device in devices['results'][:3]:  # Show first 3
            print(f"     - MAC: {device.get('mac', 'Unknown')} on port {device.get('port_name', 'Unknown')}")
    else:
        print(f"   Error or no devices: {devices.get('error', 'No results')}")

def example_api_discovery():
    """API discovery examples"""
    print("\n=== API DISCOVERY EXAMPLES ===")
    
    # Show total endpoints discovered
    print(f"1. Total endpoints discovered: {len(discovered_endpoints)}")
    print(f"   Categories: {list(api_parser.categories.keys())}")
    
    # Show endpoints by category
    print("\n2. Endpoints by category:")
    for category, endpoints in api_parser.categories.items():
        print(f"   {category}: {len(endpoints)} endpoints")
    
    # Show switch-specific endpoints
    print("\n3. Switch controller endpoints:")
    switch_endpoints = api_parser.get_endpoints_by_category("switch_direct")
    for endpoint_key in switch_endpoints[:5]:  # Show first 5
        endpoint_info = api_parser.get_endpoint_info(endpoint_key)
        print(f"   - {endpoint_key}: {endpoint_info.get('path', '')} ({endpoint_info.get('method', 'GET')})")

def example_dynamic_endpoint_calling():
    """Dynamic endpoint calling examples"""
    print("\n=== DYNAMIC ENDPOINT CALLING ===")
    
    # Find and call a specific endpoint
    print("1. Searching for 'detected-device' endpoints...")
    matching_endpoints = []
    for key, info in discovered_endpoints.items():
        if "detected" in key.lower() or "detected" in info.get("path", "").lower():
            matching_endpoints.append((key, info))
    
    if matching_endpoints:
        print(f"   Found {len(matching_endpoints)} matching endpoints:")
        for key, info in matching_endpoints[:3]:  # Show first 3
            print(f"     - {key}: {info.get('path', '')}")
            
            # Try calling the first one
            if key == matching_endpoints[0][0]:
                print(f"\n   Calling {key}...")
                result = fg_api._make_request(info.get("method", "GET"), info.get("path", ""))
                if "error" not in result:
                    print(f"     Success: Got {len(result.get('results', []))} results")
                else:
                    print(f"     Error: {result['error']}")

def example_switch_management():
    """Switch management examples"""
    print("\n=== SWITCH MANAGEMENT EXAMPLES ===")
    
    # Get switch direct endpoints
    switch_endpoints = api_parser.get_endpoints_by_category("switch_direct")
    print(f"1. Available switch direct endpoints: {len(switch_endpoints)}")
    
    # Group by functionality
    port_endpoints = [ep for ep in switch_endpoints if "port" in ep.lower()]
    vlan_endpoints = [ep for ep in switch_endpoints if "vlan" in ep.lower()]
    stats_endpoints = [ep for ep in switch_endpoints if "stats" in ep.lower()]
    
    print(f"   - Port management: {len(port_endpoints)} endpoints")
    print(f"   - VLAN management: {len(vlan_endpoints)} endpoints")
    print(f"   - Statistics: {len(stats_endpoints)} endpoints")
    
    # Try to get port statistics if available
    if stats_endpoints:
        print(f"\n2. Trying to get statistics from {stats_endpoints[0]}...")
        endpoint_info = api_parser.get_endpoint_info(stats_endpoints[0])
        result = fg_api._make_request(
            endpoint_info.get("method", "GET"), 
            endpoint_info.get("path", "")
        )
        if "error" not in result:
            print(f"   Success: Statistics retrieved")
        else:
            print(f"   Info: {result.get('error', 'No data')}")

def example_configuration_management():
    """Configuration management examples"""
    print("\n=== CONFIGURATION MANAGEMENT ===")
    
    # Get configuration endpoints
    config_endpoints = api_parser.get_endpoints_by_category("configuration")
    print(f"1. Available configuration endpoints: {len(config_endpoints)}")
    
    for endpoint_key in config_endpoints[:3]:  # Show first 3
        endpoint_info = api_parser.get_endpoint_info(endpoint_key)
        print(f"   - {endpoint_key}: {endpoint_info.get('path', '')} ({endpoint_info.get('method', 'GET')})")
    
    # Example: Get ARP table (if available)
    arp_endpoints = [ep for ep in config_endpoints if "arp" in ep.lower()]
    if arp_endpoints:
        print(f"\n2. ARP table management endpoints available:")
        for ep in arp_endpoints:
            endpoint_info = api_parser.get_endpoint_info(ep)
            print(f"   - {ep}: {endpoint_info.get('method', 'GET')} {endpoint_info.get('path', '')}")

def example_health_monitoring():
    """Health monitoring examples"""
    print("\n=== HEALTH MONITORING ===")
    
    # Basic health check
    print("1. Basic health indicators:")
    
    # System status
    status = fg_api._make_request("GET", "monitor/system/status")
    system_healthy = "error" not in status
    print(f"   - System API: {'✓' if system_healthy else '✗'}")
    
    # Interface stats
    interfaces = fg_api._make_request("GET", "monitor/system/interface")
    interfaces_healthy = "error" not in interfaces
    print(f"   - Interfaces: {'✓' if interfaces_healthy else '✗'}")
    
    # Switch controller
    switches = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
    switches_healthy = "error" not in switches
    print(f"   - Switch Controller: {'✓' if switches_healthy else '✗'}")
    
    # Overall health score
    health_checks = [system_healthy, interfaces_healthy, switches_healthy]
    health_score = (sum(health_checks) / len(health_checks)) * 100
    print(f"\n   Overall Health Score: {health_score:.1f}%")

def example_automation_script():
    """Example automation script"""
    print("\n=== AUTOMATION EXAMPLE ===")
    
    # Create a simple monitoring report
    report = {
        "timestamp": datetime.now().isoformat(),
        "server_info": {
            "total_endpoints": len(discovered_endpoints),
            "categories": list(api_parser.categories.keys()),
            "mcp_server_version": "enhanced"
        },
        "fortigate_status": {},
        "detected_devices": {},
        "health_summary": {}
    }
    
    # Get FortiGate status
    print("1. Collecting FortiGate status...")
    status = fg_api._make_request("GET", "monitor/system/status")
    if "error" not in status:
        report["fortigate_status"] = {
            "hostname": status.get("results", {}).get("hostname", "Unknown"),
            "version": status.get("results", {}).get("version", "Unknown"),
            "serial": status.get("results", {}).get("serial", "Unknown"),
            "status": "online"
        }
    else:
        report["fortigate_status"] = {"status": "error", "error": status.get("error", "")}
    
    # Get detected devices
    print("2. Collecting detected devices...")
    devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
    if "error" not in devices and "results" in devices:
        report["detected_devices"] = {
            "count": len(devices["results"]),
            "devices": [
                {
                    "mac": device.get("mac", ""),
                    "port": device.get("port_name", ""),
                    "switch_id": device.get("switch_id", ""),
                    "vlan_id": device.get("vlan_id", "")
                }
                for device in devices["results"]
            ]
        }
    else:
        report["detected_devices"] = {"count": 0, "error": devices.get("error", "")}
    
    # Health summary
    report["health_summary"] = {
        "fortigate_online": report["fortigate_status"].get("status") == "online",
        "devices_detected": report["detected_devices"].get("count", 0) > 0,
        "mcp_server_functional": True
    }
    
    print("3. Report generated:")
    print(json.dumps(report, indent=2))
    
    return report

def main():
    """Main function to run all examples"""
    print("Fortinet MCP Server Usage Examples")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_api_discovery()
        example_dynamic_endpoint_calling()
        example_switch_management()
        example_configuration_management()
        example_health_monitoring()
        
        print("\n" + "=" * 50)
        report = example_automation_script()
        
        # Save report to file
        report_file = f"fortinet_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure your FortiGate is accessible and API token is valid")
    
    print(f"\n=== SUMMARY ===")
    print(f"✓ MCP server components loaded successfully")
    print(f"✓ {len(discovered_endpoints)} API endpoints available")
    print(f"✓ {len(api_parser.categories)} endpoint categories")
    print(f"✓ Examples completed")

if __name__ == "__main__":
    main()