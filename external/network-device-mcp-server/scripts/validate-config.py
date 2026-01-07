# scripts/validate-config.py
"""
Validation script for Network Device MCP Server configuration
"""
import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from config import get_config
except ImportError as e:
    print(f"Failed to import config module: {e}")
    print("Make sure you're running this from the repository root")
    sys.exit(1)

def validate_network_connectivity():
    """Test basic network connectivity to configured hosts"""
    import socket
    
    config = get_config()
    results = []
    
    # Test FortiManager instances
    for fm in config.fortimanager_instances:
        host = fm['host']
        try:
            socket.create_connection((host, 443), timeout=5)
            results.append(f"✓ FortiManager {fm['name']} ({host}) - Reachable")
        except Exception as e:
            results.append(f"✗ FortiManager {fm['name']} ({host}) - Unreachable: {e}")
    
    # Test FortiGate devices
    for fg in config.fortigate_devices:
        host = fg['host']
        try:
            socket.create_connection((host, 443), timeout=5)
            results.append(f"✓ FortiGate {fg['name']} ({host}) - Reachable")
        except Exception as e:
            results.append(f"✗ FortiGate {fg['name']} ({host}) - Unreachable: {e}")
    
    return results

def check_required_secrets():
    """Check if required GitHub secrets are available"""
    required_secrets = [
        'FORTIMANAGER_ARBYS_HOST',
        'FORTIMANAGER_BWW_HOST', 
        'FORTIMANAGER_SONIC_HOST'
    ]
    
    results = []
    for secret in required_secrets:
        value = os.getenv(secret)
        if value:
            results.append(f"✓ {secret} - Available")
        else:
            results.append(f"✗ {secret} - Missing")
    
    return results

def validate_paths():
    """Validate backup and report paths"""
    config = get_config()
    results = []
    
    for path_name, path_value in [("Backup", config.backup_path), ("Report", config.report_path)]:
        if path_value:
            path = Path(path_value)
            if path.exists():
                results.append(f"✓ {path_name} path ({path_value}) - Exists")
            else:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    results.append(f"✓ {path_name} path ({path_value}) - Created")
                except Exception as e:
                    results.append(f"✗ {path_name} path ({path_value}) - Cannot create: {e}")
        else:
            results.append(f"✗ {path_name} path - Not configured")
    
    return results

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'mcp',
        'httpx', 
        'python-dotenv',
        'requests',
        'pydantic'
    ]
    
    results = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            results.append(f"✓ {package} - Installed")
        except ImportError:
            results.append(f"✗ {package} - Missing")
    
    return results

def check_ssl_configuration():
    """Check SSL configuration for corporate environments"""
    ssl_vars = {
        'UV_INSECURE': os.getenv('UV_INSECURE'),
        'PYTHONHTTPSVERIFY': os.getenv('PYTHONHTTPSVERIFY'),
        'SSL_VERIFY': os.getenv('SSL_VERIFY')
    }
    
    results = []
    for var, value in ssl_vars.items():
        if value:
            results.append(f"✓ {var}={value} - Configured for corporate environment")
        else:
            results.append(f"✗ {var} - Not set (may cause SSL issues in corporate environments)")
    
    return results

def main():
    print("Network Device MCP Server Configuration Validation")
    print("=" * 60)
    
    # Load configuration
    try:
        config = get_config()
        print(f"✓ Configuration loaded successfully")
        print(f"  - FortiManager instances: {len(config.fortimanager_instances)}")
        print(f"  - FortiGate devices: {len(config.fortigate_devices)}")
        print(f"  - Meraki configured: {config.has_meraki_config()}")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return 1
    
    print("\n1. Checking required secrets/environment variables...")
    for result in check_required_secrets():
        print(f"   {result}")
    
    print("\n2. Checking Python dependencies...")
    for result in check_dependencies():
        print(f"   {result}")
    
    print("\n3. Validating paths...")
    for result in validate_paths():
        print(f"   {result}")
    
    print("\n4. Checking SSL configuration...")
    for result in check_ssl_configuration():
        print(f"   {result}")
    
    print("\n5. Testing network connectivity...")
    for result in validate_network_connectivity():
        print(f"   {result}")
    
    # Summary
    print("\n" + "=" * 60)
    
    # Check if running in GitHub Actions
    if os.getenv('GITHUB_ACTIONS'):
        print("Running in GitHub Actions environment")
        print("✓ GitHub secrets should be available as environment variables")
    elif os.path.exists('.env'):
        print("Using local .env file for configuration")
    else:
        print("⚠️  No .env file found and not in GitHub Actions")
        print("   Either create .env file or set up GitHub secrets")
    
    # Configuration summary
    validation_results = config.validate_config()
    if validation_results['fortimanager_instances'] > 0:
        print("✓ Ready for FortiManager operations")
    else:
        print("✗ No FortiManager instances configured")
    
    if validation_results['fortigate_devices'] > 0:
        print("✓ Ready for FortiGate operations")
    else:
        print("✗ No FortiGate devices configured")
    
    if validation_results['meraki_configured']:
        print("✓ Ready for Meraki operations")
    else:
        print("✗ Meraki not configured")
    
    print("\nValidation completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())