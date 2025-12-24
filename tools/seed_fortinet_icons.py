#!/usr/bin/env python3
"""
Seed Fortinet device icons into the icon database.

This script scans the app/static/icons/fortinet/ directory and populates
the icons database with proper manufacturer, device_type, and icon_path mappings.
"""

import os
import re
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3

from app.utils.icon_db import add_icon_binding, init_db


def get_db_path():
    """Get the database path"""
    utils_dir = os.path.join(os.path.dirname(__file__), "..", "app", "utils")
    app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
    return os.path.join(app_dir, "static", "icons.db")


def parse_device_model(filename):
    """Parse device model information from filename"""
    basename = os.path.splitext(filename)[0]  # Remove .svg

    # FortiGate patterns: FG-100F, FG-3400E, etc.
    if basename.startswith("FG-"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "fortigate",
            "model": basename,
            "title": f"FortiGate {basename[3:]}",
        }

    # FortiSwitch patterns: FSW-248E-POE, FSW-548D-FPOE, etc.
    elif basename.startswith("FSW-"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "fortiswitch",
            "model": basename,
            "title": f"FortiSwitch {basename[4:]}",
        }

    # FortiAP patterns: FAP-231F, FAP-U432F, etc.
    elif basename.startswith("FAP-"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "fortiap",
            "model": basename,
            "title": f"FortiAP {basename[4:]}",
        }

    # FortiAuthenticator, FortiMail, FortiWeb, FortiSIEM, FortiCamera, FortiDDoS
    elif basename.startswith("FortiAuthenticator"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "fortiauthenticator",
            "model": basename,
            "title": "FortiAuthenticator",
        }

    elif basename.startswith("FortiMail"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "fortimail",
            "model": basename,
            "title": "FortiMail",
        }

    elif basename.startswith("FortiWeb"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "fortiweb",
            "model": basename,
            "title": "FortiWeb",
        }

    elif basename.startswith("FortiSIEM"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "fortisiem",
            "model": basename,
            "title": "FortiSIEM",
        }

    elif basename.startswith("FortiCamera"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "forticamera",
            "model": basename,
            "title": "FortiCamera",
        }

    elif basename.startswith("FortiDDoS"):
        return {
            "manufacturer": "Fortinet",
            "device_type": "fortiddos",
            "model": basename,
            "title": "FortiDDoS",
        }

    # SFP/QSFP transceivers
    elif basename.startswith(("SFP-", "QSFP-")):
        return {
            "manufacturer": "Fortinet",
            "device_type": "transceiver",
            "model": basename,
            "title": basename.replace("-", " "),
        }

    # Default fallback
    return {
        "manufacturer": "Fortinet",
        "device_type": "other",
        "model": basename,
        "title": basename,
    }


def seed_fortinet_icons():
    """Scan fortinet icon directory and seed database"""
    init_db()

    fortinet_dir = os.path.join(
        os.path.dirname(__file__), "..", "app", "static", "icons", "fortinet"
    )

    if not os.path.exists(fortinet_dir):
        print(f"❌ Fortinet icon directory not found: {fortinet_dir}")
        return

    # Statistics
    stats = {"fortigate": 0, "fortiswitch": 0, "fortiap": 0, "other": 0, "total": 0}

    # Walk through all subdirectories
    for root, dirs, files in os.walk(fortinet_dir):
        for filename in files:
            if not filename.endswith(".svg"):
                continue

            # Get relative path from static directory
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(
                full_path, os.path.join(fortinet_dir, "..", "..")
            )
            icon_path = f"/static/{relative_path.replace(os.sep, '/')}"

            # Parse device information
            device_info = parse_device_model(filename)

            # Add to database using icon_bindings table
            # Priority: exact model match (10), manufacturer match (50), device_type match (100)

            # 1. Exact model binding (highest priority)
            add_icon_binding(
                key_type="serial",
                key_value=device_info["model"],
                icon_path=icon_path,
                title=device_info["title"],
                device_type=device_info["device_type"],
                priority=10,
            )

            # 2. Manufacturer + device type binding
            manufacturer_key = (
                f"{device_info['manufacturer']}:{device_info['device_type']}"
            )
            add_icon_binding(
                key_type="manufacturer",
                key_value=manufacturer_key,
                icon_path=icon_path,
                title=device_info["title"],
                device_type=device_info["device_type"],
                priority=50,
            )

            # 3. Device type fallback binding
            add_icon_binding(
                key_type="device_type",
                key_value=device_info["device_type"],
                icon_path=icon_path,
                title=device_info["title"],
                device_type=device_info["device_type"],
                priority=100,
            )

            # Update stats
            stats[device_info["device_type"]] = (
                stats.get(device_info["device_type"], 0) + 1
            )
            stats["total"] += 1

            print(f"✅ Seeded: {device_info['title']} → {icon_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("Fortinet Icon Seeding Summary")
    print("=" * 60)
    print(f"FortiGate icons:         {stats.get('fortigate', 0)}")
    print(f"FortiSwitch icons:       {stats.get('fortiswitch', 0)}")
    print(f"FortiAP icons:           {stats.get('fortiap', 0)}")
    print(f"FortiAuthenticator:      {stats.get('fortiauthenticator', 0)}")
    print(f"FortiMail:               {stats.get('fortimail', 0)}")
    print(f"FortiWeb:                {stats.get('fortiweb', 0)}")
    print(f"FortiSIEM:               {stats.get('fortisiem', 0)}")
    print(f"FortiCamera:             {stats.get('forticamera', 0)}")
    print(f"FortiDDoS:               {stats.get('fortiddos', 0)}")
    print(f"Transceivers:            {stats.get('transceiver', 0)}")
    print(f"Other:                   {stats.get('other', 0)}")
    print("-" * 60)
    print(f"Total icons seeded:      {stats['total']}")
    print("=" * 60)


if __name__ == "__main__":
    print("Seeding Fortinet device icons into database...\n")
    seed_fortinet_icons()
    print("\n✅ Fortinet icon seeding complete!")
