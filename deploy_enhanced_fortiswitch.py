#!/usr/bin/env python3
"""
Deployment script to replace the current FortiSwitch service with the enhanced version.
This script backs up the original service and deploys the enhanced version with restaurant device classification.
"""

import os
import shutil
import sys
from datetime import datetime


def backup_original_service():
    """Backup the original FortiSwitch service."""
    original_file = "app/services/fortiswitch_service.py"
    backup_file = f"app/services/fortiswitch_service.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"

    if os.path.exists(original_file):
        try:
            shutil.copy2(original_file, backup_file)
            print(f"✅ Backed up original service to: {backup_file}")
            return True
        except Exception as e:
            print(f"❌ Error backing up original service: {e}")
            return False
    else:
        print(f"⚠️  Original service file not found: {original_file}")
        return True  # Continue deployment even if original doesn't exist


def deploy_enhanced_service():
    """Deploy the enhanced FortiSwitch service."""
    enhanced_file = "app/services/fortiswitch_service_enhanced.py"
    target_file = "app/services/fortiswitch_service.py"

    if not os.path.exists(enhanced_file):
        print(f"❌ Enhanced service file not found: {enhanced_file}")
        return False

    try:
        shutil.copy2(enhanced_file, target_file)
        print(f"✅ Deployed enhanced service to: {target_file}")
        return True
    except Exception as e:
        print(f"❌ Error deploying enhanced service: {e}")
        return False


def verify_deployment():
    """Verify the deployment by checking imports."""
    try:
        # Add the app directory to the Python path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

        # Try to import the enhanced service
        from app.services.fortiswitch_service import get_fortiswitches_enhanced
        from app.utils.restaurant_device_classifier import enhance_device_info

        print("✅ Enhanced service imports successfully")
        print("✅ Restaurant device classifier imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error during verification: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during verification: {e}")
        return False


def create_deployment_summary():
    """Create a summary of the deployment."""
    summary = f"""
# FortiSwitch Enhanced Service Deployment Summary

**Deployment Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## What was deployed:

### 1. Enhanced FortiSwitch Service
- **File:** `app/services/fortiswitch_service_enhanced.py` → `app/services/fortiswitch_service.py`
- **Features:**
  - Improved device detection and correlation
  - Better DHCP information mapping
  - Enhanced error handling and rate limiting
  - Restaurant technology device classification
  - Comprehensive logging

### 2. Restaurant Device Classifier
- **File:** `app/utils/restaurant_device_classifier.py`
- **Features:**
  - Automatic detection of POS terminals, kitchen displays, kiosks, etc.
  - Security and monitoring recommendations
  - Enhanced OUI database for restaurant technology
  - Confidence scoring for device classification

## Key Improvements:

1. **Better Device Detection:** Enhanced correlation between detected devices, DHCP leases, and ARP entries
2. **Restaurant Technology Focus:** Specialized classification for restaurant equipment
3. **Security Insights:** Automatic security level assessment for detected devices
4. **Monitoring Priorities:** Intelligent monitoring recommendations based on device type
5. **Enhanced Logging:** Comprehensive logging for troubleshooting

## API Endpoints Used:
- `/api/v2/monitor/switch-controller/managed-switch/status` - Switch and port information
- `/api/v2/monitor/switch-controller/detected-device` - Device detection
- `/api/v2/monitor/system/dhcp` - DHCP lease correlation
- `/api/v2/monitor/system/arp` - Additional device discovery

## Next Steps:
1. Monitor the enhanced service performance
2. Check logs for any issues
3. Verify device classification accuracy
4. Consider implementing local OUI database for better performance

## Rollback Instructions:
If needed, restore the original service from the backup file created during deployment.

"""

    with open("deployment_summary.md", "w", encoding="utf-8") as f:
        f.write(summary)

    print("✅ Created deployment summary: deployment_summary.md")


def main():
    """Main deployment function."""
    print("=" * 80)
    print("FortiSwitch Enhanced Service Deployment")
    print("=" * 80)
    print()

    # Step 1: Backup original service
    print("1. Backing up original service...")
    if not backup_original_service():
        print("❌ Backup failed. Aborting deployment.")
        return False
    print()

    # Step 2: Deploy enhanced service
    print("2. Deploying enhanced service...")
    if not deploy_enhanced_service():
        print("❌ Deployment failed.")
        return False
    print()

    # Step 3: Verify deployment
    print("3. Verifying deployment...")
    if not verify_deployment():
        print("❌ Verification failed.")
        return False
    print()

    # Step 4: Create deployment summary
    print("4. Creating deployment summary...")
    create_deployment_summary()
    print()

    print("=" * 80)
    print("✅ DEPLOYMENT SUCCESSFUL!")
    print("=" * 80)
    print()
    print(
        "The enhanced FortiSwitch service has been deployed with the following features:"
    )
    print("• Enhanced device detection and correlation")
    print("• Restaurant technology device classification")
    print("• Security and monitoring recommendations")
    print("• Improved error handling and logging")
    print()
    print("Files created/modified:")
    print("• app/services/fortiswitch_service.py (enhanced service)")
    print("• app/utils/restaurant_device_classifier.py (device classifier)")
    print("• deployment_summary.md (deployment documentation)")
    print()
    print(
        "The service is now ready to use with improved device detection capabilities!"
    )

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
