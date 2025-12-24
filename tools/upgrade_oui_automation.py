# Migration Script: Enhanced OUI Lookup Automation
# Run this to upgrade your device management automation

import shutil
import os

print("Upgrading OUI lookup automation...")

# Backup original
if os.path.exists("app/utils/oui_lookup.py"):
    shutil.copy("app/utils/oui_lookup.py", "app/utils/oui_lookup_backup.py")
    print("Backed up original to oui_lookup_backup.py")

# Replace with enhanced version
if os.path.exists("app/utils/oui_lookup_enhanced.py"):
    shutil.copy("app/utils/oui_lookup_enhanced.py", "app/utils/oui_lookup.py")
    print("Enhanced OUI lookup activated!")
    print("")
    print("Power Automate-style features now active:")
    print("  - Intelligent rate limiting (50 req/min)")
    print("  - Persistent caching to disk")
    print("  - Exponential backoff for API limits")
    print("  - Expanded device manufacturer database")
    print("  - Performance monitoring metrics")
    print("")
    print("Next: Restart your Docker container to apply changes:")
    print("  docker compose restart dashboard")

else:
    print("Enhanced file not found. Create it first.")
