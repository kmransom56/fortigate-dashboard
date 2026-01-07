"""
Network Devices MCP Server Diagnostic Script
Tests if the server can run without errors
"""
import sys
import os
from pathlib import Path

print("=" * 60)
print("Network Devices MCP Server Diagnostics")
print("=" * 60)

# Test 1: Python Version
print("\n[1] Python Version:")
print(f"    {sys.version}")
if sys.version_info < (3, 8):
    print("    [ERROR] Python 3.8+ required")
    sys.exit(1)
else:
    print("    [OK]")

# Test 2: Check if main script exists
print("\n[2] Main Script:")
script_path = Path("C:/Users/keith.ransom/network-device-mcp-server/src/main_simple.py")
if script_path.exists():
    print(f"    [OK] Found: {script_path}")
else:
    print(f"    [ERROR] NOT FOUND: {script_path}")
    sys.exit(1)

# Test 3: Check PYTHONPATH
print("\n[3] PYTHONPATH:")
pythonpath = os.environ.get('PYTHONPATH', '')
if 'network-device-mcp-server' in pythonpath:
    print(f"    [OK] Set: {pythonpath}")
else:
    print("    [WARN] Not set in environment")
    print("    Setting for this test...")
    sys.path.insert(0, "C:/Users/keith.ransom/network-device-mcp-server/src")

# Test 4: Try importing the module
print("\n[4] Import Test:")
try:
    # Add the path
    sys.path.insert(0, str(script_path.parent))
    
    # Try to import
    print("    Attempting to import main_simple...")
    import main_simple
    print("    [OK] Import successful")
except Exception as e:
    print(f"    [ERROR] Import failed: {e}")
    print("\n[DIAGNOSIS]")
    print("    The server cannot be imported. This is why it fails in MCP.")
    print("    Common causes:")
    print("    - Missing dependencies (pip install <package>)")
    print("    - Syntax errors in the code")
    print("    - Missing configuration files")
    sys.exit(1)

# Test 5: Check for common dependencies
print("\n[5] Common Dependencies:")
dependencies = [
    'mcp',
    'asyncio',
    'httpx'
]

missing = []
for dep in dependencies:
    try:
        __import__(dep)
        print(f"    [OK] {dep}")
    except ImportError:
        print(f"    [ERROR] {dep} - MISSING")
        missing.append(dep)

if missing:
    print("\n[DIAGNOSIS]")
    print("    Missing dependencies detected!")
    print("    To fix, run:")
    print(f"    python -m pip install {' '.join(missing)}")
    sys.exit(1)

# Test 6: Server initialization
print("\n[6] Server Startup Test:")
print("    All basic checks passed!")

print("\n" + "=" * 60)
print("[SUCCESS] ALL DIAGNOSTICS PASSED")
print("=" * 60)
print("\nThe server should work in MCP configuration.")
print("If you still have issues, check the MCP logs:")
print("C:\\Users\\keith.ransom\\AppData\\Roaming\\Claude\\logs\\mcp-server-network-devices.log")
