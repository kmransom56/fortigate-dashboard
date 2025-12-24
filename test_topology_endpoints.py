#!/usr/bin/env python3
"""
Test script for topology API endpoints
Tests the fixed endpoints to ensure they return real data (no mock/fallback)
"""

import os
import sys
import requests
import json
from typing import Dict, Any

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

BASE_URL = os.getenv("DASHBOARD_URL", "http://localhost:8001")

def test_endpoint(endpoint: str, description: str) -> Dict[str, Any]:
    """Test an API endpoint and return results"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Endpoint: {endpoint}")
    print(f"{'='*60}")
    
    try:
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for error in metadata
            if isinstance(data, dict):
                metadata = data.get('metadata', {})
                if metadata.get('source') == 'error':
                    error_msg = metadata.get('error', 'Unknown error')
                    print(f"❌ ERROR in response: {error_msg}")
                    return {"success": False, "error": error_msg, "data": data}
                
                # Check for devices/connections
                devices = data.get('devices', [])
                connections = data.get('connections', [])
                
                print(f"✅ Success")
                print(f"   Devices: {len(devices)}")
                print(f"   Connections: {len(connections)}")
                print(f"   Source: {metadata.get('source', 'unknown')}")
                
                if devices:
                    print(f"\n   Sample device:")
                    sample = devices[0]
                    print(f"     - ID: {sample.get('id')}")
                    print(f"     - Name: {sample.get('name')}")
                    print(f"     - Type: {sample.get('type')}")
                    print(f"     - Status: {sample.get('status')}")
                
                return {"success": True, "devices": len(devices), "connections": len(connections), "data": data}
            else:
                print(f"⚠️  Unexpected response format: {type(data)}")
                return {"success": False, "error": "Unexpected format", "data": data}
                
        else:
            error_text = response.text[:200] if response.text else "No error message"
            print(f"❌ HTTP Error {response.status_code}: {error_text}")
            return {"success": False, "error": f"HTTP {response.status_code}", "status_code": response.status_code}
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection Error: Could not connect to {BASE_URL}")
        print(f"   Make sure the dashboard is running on {BASE_URL}")
        return {"success": False, "error": "Connection failed"}
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: Request took longer than 30 seconds")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def main():
    """Run all endpoint tests"""
    print("="*60)
    print("FortiGate Dashboard - Topology Endpoints Test")
    print("="*60)
    print(f"Testing against: {BASE_URL}")
    print(f"Note: This tests for real data (no mock/fallback per AGENTS.md)")
    
    results = []
    
    # Test topology endpoints
    endpoints = [
        ("/api/topology_data", "Topology Data (Main Endpoint)"),
        ("/api/scraped_topology", "Scraped Topology (Alternative)"),
        ("/api/debug/topology", "Debug Topology (Diagnostics)"),
    ]
    
    for endpoint, description in endpoints:
        result = test_endpoint(endpoint, description)
        results.append({
            "endpoint": endpoint,
            "description": description,
            **result
        })
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r.get("success"))
    total_count = len(results)
    
    for result in results:
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"{status} - {result['description']}")
        if not result.get("success"):
            print(f"      Error: {result.get('error', 'Unknown')}")
    
    print(f"\nResults: {success_count}/{total_count} endpoints passed")
    
    # Check for mock data violations
    print(f"\n{'='*60}")
    print("Mock Data Check (AGENTS.md Compliance)")
    print(f"{'='*60}")
    
    mock_violations = []
    for result in results:
        if result.get("success") and result.get("data"):
            data = result["data"]
            metadata = data.get("metadata", {})
            source = metadata.get("source", "")
            
            # Check for fallback/mock indicators
            if source in ["fallback", "demo", "mock", "sample"]:
                mock_violations.append({
                    "endpoint": result["endpoint"],
                    "source": source,
                    "message": f"Endpoint returns {source} data - violates AGENTS.md"
                })
    
    if mock_violations:
        print("❌ Mock data violations found:")
        for violation in mock_violations:
            print(f"   - {violation['endpoint']}: {violation['message']}")
    else:
        print("✅ No mock data violations - all endpoints comply with AGENTS.md")
    
    return 0 if success_count == total_count and not mock_violations else 1

if __name__ == "__main__":
    exit(main())


