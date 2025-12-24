#!/usr/bin/env python3
"""
FortiGate API Endpoint Discovery

Discovers available API endpoints for FortiSwitch management
by testing common endpoint patterns and variations.
"""

import requests
import json
from typing import List, Dict, Any
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortiGateAPIDiscovery:
    def __init__(self):
        self.base_url = "https://192.168.0.254"
        self.token = "zpq4gHxqj8dzpGxfkzmskc54Qhbzq3"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        print("🔍 FortiGate API Endpoint Discovery")
        print("=" * 50)

    def test_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Test a single API endpoint"""
        try:
            url = f"{self.base_url}/api/v2/{endpoint}"
            response = requests.get(url, headers=self.headers, verify=False, timeout=5)

            result = {
                "endpoint": endpoint,
                "status_code": response.status_code,
                "available": response.status_code == 200,
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        result["response_keys"] = list(data.keys())
                        if "results" in data:
                            results = data["results"]
                            if isinstance(results, dict):
                                result["result_count"] = len(results)
                                result["result_keys"] = list(results.keys())[
                                    :10
                                ]  # First 10 keys
                            elif isinstance(results, list):
                                result["result_count"] = len(results)
                                if results:
                                    result["sample_item_keys"] = (
                                        list(results[0].keys())
                                        if isinstance(results[0], dict)
                                        else []
                                    )
                except:
                    result["response_preview"] = response.text[:200]
            elif response.status_code == 404:
                result["error"] = "Endpoint not found"
            elif response.status_code == 403:
                result["error"] = "Access forbidden"
            else:
                result["error"] = f"HTTP {response.status_code}"

            return result

        except Exception as e:
            return {
                "endpoint": endpoint,
                "status_code": None,
                "available": False,
                "error": str(e),
            }

    def discover_fortiswitch_endpoints(self) -> List[Dict[str, Any]]:
        """Discover FortiSwitch-related API endpoints"""
        print("\n📡 Testing FortiSwitch API Endpoints")
        print("-" * 40)

        # Common FortiSwitch endpoint patterns
        endpoints = [
            # Monitor endpoints
            "monitor/switch-controller/managed-switch",
            "monitor/switch-controller/switch",
            "monitor/switch-controller/fortilink",
            "monitor/switch-controller/status",
            "monitor/switch-controller/health",
            "monitor/fortilink/switch",
            "monitor/fortilink/managed-switch",
            "monitor/fortilink/health-check",
            "monitor/fortilink/status",
            "monitor/fortiswitch",
            "monitor/managed-switch",
            # CMDB endpoints
            "cmdb/switch-controller/managed-switch",
            "cmdb/switch-controller/switch",
            "cmdb/switch-controller/system",
            "cmdb/switch-controller/global",
            "cmdb/fortilink/switch",
            "cmdb/fortiswitch",
            # System endpoints
            "monitor/system/fortiswitch",
            "monitor/system/switch",
            "monitor/system/managed-switch",
            # Network endpoints
            "monitor/network/fortiswitch",
            "monitor/network/switch",
        ]

        results = []
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint)
            results.append(result)

            if result["available"]:
                print(f"✅ {endpoint}")
                if "result_count" in result:
                    print(f"   📊 Results: {result['result_count']}")
                if "result_keys" in result:
                    print(f"   🔑 Keys: {', '.join(result['result_keys'])}")
            else:
                status = result.get("status_code", "ERROR")
                print(f"❌ {endpoint} (HTTP {status})")

        return results

    def discover_network_endpoints(self) -> List[Dict[str, Any]]:
        """Discover general network monitoring endpoints"""
        print("\n🌐 Testing Network Monitoring Endpoints")
        print("-" * 40)

        endpoints = [
            "monitor/system/interface",
            "monitor/system/status",
            "monitor/router/routing-table",
            "monitor/network/dns",
            "monitor/network/interface",
            "cmdb/system/interface",
            "cmdb/router/static",
            "monitor/system/arp",
            "monitor/system/dns",
            "monitor/network/lldp",
        ]

        results = []
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint)
            results.append(result)

            if result["available"]:
                print(f"✅ {endpoint}")
                if "result_count" in result:
                    print(f"   📊 Results: {result['result_count']}")
            else:
                status = result.get("status_code", "ERROR")
                print(f"❌ {endpoint} (HTTP {status})")

        return results

    def generate_report(
        self, fortiswitch_results: List[Dict], network_results: List[Dict]
    ):
        """Generate discovery report"""
        print(f"\n📋 DISCOVERY REPORT")
        print("=" * 50)

        # Count available endpoints
        fs_available = [r for r in fortiswitch_results if r["available"]]
        net_available = [r for r in network_results if r["available"]]

        print(
            f"FortiSwitch Endpoints: {len(fs_available)}/{len(fortiswitch_results)} available"
        )
        print(
            f"Network Endpoints: {len(net_available)}/{len(network_results)} available"
        )

        if fs_available:
            print(f"\n✅ Available FortiSwitch Endpoints:")
            for result in fs_available:
                print(f"   • {result['endpoint']}")
                if "result_count" in result:
                    print(f"     📊 {result['result_count']} results")
        else:
            print(f"\n❌ No FortiSwitch endpoints available")
            print("   Recommendation: Use SNMP approach for switch discovery")

        if net_available:
            print(f"\n✅ Available Network Endpoints:")
            for result in net_available[:5]:  # Show first 5
                print(f"   • {result['endpoint']}")

        # Save detailed results
        all_results = {
            "fortiswitch_endpoints": fortiswitch_results,
            "network_endpoints": network_results,
            "summary": {
                "fortiswitch_available": len(fs_available),
                "network_available": len(net_available),
                "total_tested": len(fortiswitch_results) + len(network_results),
            },
        }

        with open("api_endpoint_discovery.json", "w") as f:
            json.dump(all_results, f, indent=2)

        print(f"\n💾 Detailed results saved to: api_endpoint_discovery.json")

    def run_discovery(self):
        """Run complete endpoint discovery"""
        fortiswitch_results = self.discover_fortiswitch_endpoints()
        network_results = self.discover_network_endpoints()
        self.generate_report(fortiswitch_results, network_results)


if __name__ == "__main__":
    discovery = FortiGateAPIDiscovery()
    discovery.run_discovery()
