#!/usr/bin/env python3
"""
Simple test to verify the Flask server is working
"""
import requests
import sys

def test_server():
    print("🧪 Testing Network MCP Server...")
    
    # Test ports 5000-5005 in case server is on different port
    for port in range(5000, 5006):
        try:
            print(f"Trying port {port}...")
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ Server found on port {port}!")
                print(f"Response: {response.json()}")
                return port
        except Exception as e:
            print(f"❌ Port {port}: {str(e)}")
    
    print("❌ No server found on any port")
    return None

if __name__ == "__main__":
    port = test_server()
    if port:
        print(f"\n🌐 Your server is running at: http://localhost:{port}")
        print(f"📊 API documentation at: http://localhost:{port}/api")
    else:
        print("\n🔧 Server is not responding. Check server logs for errors.")
