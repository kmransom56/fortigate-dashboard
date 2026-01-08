#!/usr/bin/env python3
"""Test Ollama integration"""

import sys
sys.path.insert(0, 'reusable')

from reusable.ollama_client import OllamaClient
from reusable.config import AIConfig, AgentBackend
from reusable.agent_framework_wrapper import AgentFrameworkWrapper

print("="*60)
print("Testing Ollama Integration")
print("="*60)

# Test 1: Check if Ollama is available
print("\n1. Checking Ollama availability...")
available = AIConfig._check_ollama_available()
print(f"   Ollama available: {available}")

# Test 2: Try different ports/interfaces
if not available:
    print("\n2. Trying alternative configurations...")
    for port in [11434, 8080, 3000]:
        for host in ["localhost", "127.0.0.1"]:
            try:
                import requests
                url = f"http://{host}:{port}/api/tags"
                r = requests.get(url, timeout=1)
                if r.status_code == 200:
                    print(f"   ✓ Found Ollama at {url}")
                    available = True
                    break
            except:
                pass
        if available:
            break

# Test 3: Test Ollama client
if available:
    print("\n3. Testing Ollama client...")
    try:
        client = OllamaClient()
        print(f"   Model: {client.model}")
        print(f"   Available: {client.is_available()}")
        
        models = client.list_models()
        print(f"   Models: {models}")
        
        # Test a simple chat
        print("\n4. Testing chat...")
        response = client.chat("Hello, can you respond?", system_prompt="You are a helpful assistant.")
        if response:
            print(f"   ✓ Chat response: {response[:100]}...")
        else:
            print("   ✗ No response")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n⚠️  Ollama is not accessible")
    print("   Service status: active (but API not responding)")
    print("   Possible issues:")
    print("   - Ollama listening on different port/interface")
    print("   - Firewall blocking connection")
    print("   - Service needs restart")

# Test 4: Test agent framework wrapper
print("\n5. Testing AgentFrameworkWrapper with Ollama...")
try:
    wrapper = AgentFrameworkWrapper(backend=AgentBackend.OLLAMA)
    print(f"   Backend: {wrapper.get_backend_name()}")
    print(f"   Available: {wrapper.is_available()}")
    
    if wrapper.is_available():
        print("\n6. Testing wrapper chat...")
        response = wrapper.chat("Say hello", system_prompt="You are a coding assistant.")
        if response:
            print(f"   ✓ Response: {response[:100]}...")
        else:
            print("   ✗ No response")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test Complete")
print("="*60)
