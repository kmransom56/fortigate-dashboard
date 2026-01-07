# debug_config.py - Debug the configuration loading step by step
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("Debug: Configuration Loading Process")
print("=" * 50)

# Step 1: Check current working directory
print(f"1. Current working directory: {os.getcwd()}")
print(f"   .env file exists: {Path('.env').exists()}")

# Step 2: Load .env manually first
print("\n2. Loading .env file manually:")
try:
    from dotenv import load_dotenv
    result = load_dotenv()
    print(f"   load_dotenv() result: {result}")
    
    # Check specific variables after loading
    test_vars = ['FORTIMANAGER_ARBYS_HOST', 'FORTIMANAGER_ARBYS_USERNAME', 'FORTIMANAGER_ARBYS_PASSWORD']
    for var in test_vars:
        value = os.getenv(var)
        print(f"   {var}: {'✓ Found' if value else '✗ Missing'}")
        
except Exception as e:
    print(f"   Error loading .env: {e}")

# Step 3: Import and test config module
print("\n3. Testing config module import:")
try:
    from config import NetworkConfig
    print("   ✓ Config module imported successfully")
    
    # Create config instance with debug
    print("\n4. Creating NetworkConfig instance:")
    config = NetworkConfig()
    
    print(f"   FortiManager instances found: {len(config.fortimanager_instances)}")
    print(f"   FortiGate devices found: {len(config.fortigate_devices)}")
    print(f"   Meraki configured: {config.has_meraki_config()}")
    
    if config.fortimanager_instances:
        print("   FortiManager details:")
        for fm in config.fortimanager_instances:
            print(f"     - {fm['name']}: {fm['host']}")
    else:
        print("   No FortiManager instances loaded")
        
        # Debug: Check environment variables again after config creation
        print("\n   Environment variables after config creation:")
        for var in ['FORTIMANAGER_ARBYS_HOST', 'FORTIMANAGER_BWW_HOST', 'FORTIMANAGER_SONIC_HOST']:
            value = os.getenv(var)
            print(f"     {var}: {value if value else 'NOT FOUND'}")
            
except Exception as e:
    print(f"   Error with config module: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Test manual environment variable loading
print("\n5. Manual configuration test:")
configs = [("ARBYS", "FORTIMANAGER_ARBYS"), ("BWW", "FORTIMANAGER_BWW"), ("SONIC", "FORTIMANAGER_SONIC")]
manual_instances = []

for name, prefix in configs:
    host = os.getenv(f"{prefix}_HOST")
    username = os.getenv(f"{prefix}_USERNAME")
    password = os.getenv(f"{prefix}_PASSWORD")
    
    print(f"   {name}:")
    print(f"     Host: {host if host else 'MISSING'}")
    print(f"     Username: {username if username else 'MISSING'}")
    print(f"     Password: {'SET' if password else 'MISSING'}")
    
    if host and username and password:
        manual_instances.append({
            "name": name,
            "host": host,
            "username": username,
            "password": password
        })

print(f"\n   Manual loading result: {len(manual_instances)} instances")

print("\n" + "=" * 50)
print("Summary:")
if manual_instances:
    print("✓ Environment variables are available")
    print("✗ Config module is not loading them correctly")
    print("→ There's a bug in the config module logic")
else:
    print("✗ Environment variables are not available")
    print("→ .env file is not being loaded properly")
