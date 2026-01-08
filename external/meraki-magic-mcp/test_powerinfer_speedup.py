#!/usr/bin/env python3
"""
Test PowerInfer speedup vs Ollama
"""

import sys
import time
import os

# Add project to path
sys.path.insert(0, '.')

from reusable.simple_ai import get_ai_assistant
from reusable.config import AIConfig, AgentBackend

def test_inference_speed(backend_name: str, test_prompt: str = "Write a Python function to calculate fibonacci numbers"):
    """Test inference speed for a given backend"""
    print(f"\n{'='*60}")
    print(f"Testing: {backend_name}")
    print(f"{'='*60}")
    
    try:
        # Get assistant with specific backend
        if backend_name.lower() == "powerinfer":
            backend = AgentBackend.POWERINFER
        elif backend_name.lower() == "ollama":
            backend = AgentBackend.OLLAMA
        else:
            print(f"Unknown backend: {backend_name}")
            return None
        
        assistant = get_ai_assistant(
            app_name="meraki_magic_mcp",
            backend=backend,
            auto_setup=False
        )
        
        if not assistant or not assistant.agent.is_available():
            print(f"❌ {backend_name} not available")
            return None
        
        print(f"✅ {backend_name} initialized")
        print(f"   Model: {assistant.agent.get_backend_name()}")
        print(f"   Prompt: {test_prompt[:50]}...")
        print("")
        
        # Warm up (first call is often slower)
        print("Warming up...")
        try:
            assistant.agent.chat("Hello", system_prompt="You are a helpful assistant.")
        except:
            pass
        
        # Test inference speed
        print("Running inference test...")
        start_time = time.time()
        
        try:
            response = assistant.agent.chat(
                test_prompt,
                system_prompt="You are a helpful coding assistant. Provide concise, accurate code."
            )
            end_time = time.time()
            
            elapsed = end_time - start_time
            tokens = len(response.split()) if response else 0
            tokens_per_sec = tokens / elapsed if elapsed > 0 else 0
            
            print(f"✅ Response received")
            print(f"   Time: {elapsed:.2f}s")
            print(f"   Tokens: ~{tokens}")
            print(f"   Speed: ~{tokens_per_sec:.2f} tokens/sec")
            print(f"   Response preview: {response[:100]}...")
            
            return {
                "backend": backend_name,
                "time": elapsed,
                "tokens": tokens,
                "tokens_per_sec": tokens_per_sec,
                "available": True
            }
        except Exception as e:
            print(f"❌ Error during inference: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error initializing {backend_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("="*60)
    print("PowerInfer Speedup Test")
    print("="*60)
    print("")
    print("This test compares inference speed between:")
    print("  1. PowerInfer (with TurboSparse models)")
    print("  2. Ollama (standard models)")
    print("")
    
    # Set PowerInfer path
    os.environ['POWERINFER_PATH'] = '/media/keith/DATASTORE/PowerInfer/build/bin/main'
    
    test_prompt = "Write a Python function to calculate fibonacci numbers with memoization"
    
    results = {}
    
    # Test Ollama
    ollama_result = test_inference_speed("ollama", test_prompt)
    if ollama_result:
        results["ollama"] = ollama_result
    
    # Test PowerInfer
    powerinfer_result = test_inference_speed("powerinfer", test_prompt)
    if powerinfer_result:
        results["powerinfer"] = powerinfer_result
    
    # Compare results
    print("\n" + "="*60)
    print("Speedup Comparison")
    print("="*60)
    
    if "ollama" in results and "powerinfer" in results:
        ollama_time = results["ollama"]["time"]
        powerinfer_time = results["powerinfer"]["time"]
        speedup = ollama_time / powerinfer_time if powerinfer_time > 0 else 0
        
        print(f"\nOllama:     {ollama_time:.2f}s ({results['ollama']['tokens_per_sec']:.2f} tokens/sec)")
        print(f"PowerInfer: {powerinfer_time:.2f}s ({results['powerinfer']['tokens_per_sec']:.2f} tokens/sec)")
        print(f"\n🚀 Speedup: {speedup:.2f}×")
        
        if speedup >= 2.0:
            print("✅ Excellent! PowerInfer is providing significant speedup!")
        elif speedup >= 1.5:
            print("✅ Good! PowerInfer is faster than Ollama")
        elif speedup >= 1.0:
            print("⚠️  PowerInfer is slightly faster")
        else:
            print("⚠️  PowerInfer is slower (may need model optimization)")
    elif "ollama" in results:
        print("\n✅ Ollama working")
        print("⚠️  PowerInfer not available (models may not be loaded)")
    elif "powerinfer" in results:
        print("\n✅ PowerInfer working")
        print("⚠️  Ollama not available for comparison")
    else:
        print("\n❌ Neither backend available")
        print("   Check configuration and model availability")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
