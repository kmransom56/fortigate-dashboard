#!/usr/bin/env python3
"""
Script to populate the icon database with Fortinet device icons extracted from VSS files.
"""

import os
import re
import sqlite3
from pathlib import Path

# Database setup
DB_PATH = "app/static/icons.db"

def init_db():
    """Initialize database with required tables"""
    with sqlite3.connect(DB_PATH) as conn:
        # Use existing schema - don't recreate if it exists
        conn.execute("""
        CREATE TABLE IF NOT EXISTS icon_bindings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_type TEXT NOT NULL,
            key_value TEXT NOT NULL,
            device_type TEXT,
            title TEXT,
            icon_path TEXT NOT NULL,
            priority INTEGER DEFAULT 100,
            UNIQUE(key_type, key_value)
        );
        """)
        conn.commit()

def classify_fortinet_device(filename):
    """Classify Fortinet devices based on filename patterns"""
    filename_lower = filename.lower()
    
    # FortiGate devices
    if filename_lower.startswith(('fg-', 'fgr-', 'fg_fwf-')):
        return {
            'manufacturer': 'Fortinet',
            'device_type': 'fortigate', 
            'category': 'firewall',
            'tags': 'fortinet,firewall,security,fortigate'
        }
    
    # FortiSwitch devices
    elif filename_lower.startswith(('fsw-', 'fsr-')):
        return {
            'manufacturer': 'Fortinet',
            'device_type': 'fortiswitch',
            'category': 'switch', 
            'tags': 'fortinet,switch,networking,fortiswitch'
        }
    
    # FortiAP devices
    elif filename_lower.startswith('fap-'):
        return {
            'manufacturer': 'Fortinet',
            'device_type': 'fortiap',
            'category': 'wireless',
            'tags': 'fortinet,wireless,access_point,fortiap'
        }
    
    # FortiAnalyzer/Manager/etc
    elif filename_lower.startswith(('faz-', 'fmg-', 'fml-', 'fac-')):
        return {
            'manufacturer': 'Fortinet',
            'device_type': 'fortinet_management',
            'category': 'management',
            'tags': 'fortinet,management,analyzer,security'
        }
    
    # FortiController
    elif filename_lower.startswith('fctrl-'):
        return {
            'manufacturer': 'Fortinet',
            'device_type': 'controller',
            'category': 'controller',
            'tags': 'fortinet,controller,management'
        }
    
    # Wireless Controllers
    elif filename_lower.startswith('wlc-'):
        return {
            'manufacturer': 'Fortinet',
            'device_type': 'wireless_controller',
            'category': 'wireless',
            'tags': 'fortinet,wireless,controller'
        }
    
    # Transceivers and accessories
    elif any(x in filename_lower for x in ['transceiver', 'sfp', 'qsfp', 'antenna']):
        return {
            'manufacturer': 'Generic',
            'device_type': 'transceiver',
            'category': 'accessory',
            'tags': 'transceiver,networking,fiber,copper'
        }
    
    # Default Fortinet device
    else:
        return {
            'manufacturer': 'Fortinet',
            'device_type': 'fortinet_device',
            'category': 'device',
            'tags': 'fortinet,device,networking,security'
        }

def create_slug(filename):
    """Create a URL-friendly slug from filename"""
    # Remove extension
    name = Path(filename).stem
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', name)
    # Remove leading/trailing hyphens
    slug = slug.strip('-').lower()
    return slug

def clean_title(filename):
    """Create a clean title from filename"""
    # Remove extension and replace underscores/hyphens with spaces
    title = Path(filename).stem.replace('_', ' ').replace('-', ' ')
    # Capitalize words
    title = ' '.join(word.capitalize() for word in title.split())
    return title

def populate_fortinet_icons():
    """Populate database with Fortinet icons"""
    icons_dir = Path("app/static/icons")
    
    if not icons_dir.exists():
        print(f"Icons directory not found: {icons_dir}")
        return
    
    init_db()
    
    # Get all SVG files
    svg_files = list(icons_dir.glob("*.svg"))
    print(f"Found {len(svg_files)} SVG files")
    
    with sqlite3.connect(DB_PATH) as conn:
        fortinet_count = 0
        updated_count = 0
        
        for svg_file in svg_files:
            filename = svg_file.name
            
            # Skip if already exists
            cursor = conn.execute("SELECT id FROM icons WHERE filename = ?", (filename,))
            if cursor.fetchone():
                updated_count += 1
                continue
            
            # Classify the device
            device_info = classify_fortinet_device(filename)
            
            # Create metadata
            slug = create_slug(filename)
            title = clean_title(filename)
            icon_path = f"icons/{filename}"
            
            # Insert into database using the correct schema
            conn.execute("""
                INSERT INTO icons (
                    filename, path, full_path, size, hash, width, height, modified,
                    manufacturer, device_type, slug, title, icon_path, source_url, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                filename,
                "icons/",
                f"app/static/icons/{filename}",
                None,  # size - calculate later if needed
                None,  # hash - calculate later if needed
                None,  # width - extract from SVG later if needed  
                None,  # height - extract from SVG later if needed
                None,  # modified - could set to file mtime
                device_info['manufacturer'],
                device_info['device_type'], 
                slug,
                title,
                icon_path,
                "Fortinet Visio Stencils 2025Q2",
                device_info['tags']
            ))
            
            if device_info['manufacturer'] == 'Fortinet':
                fortinet_count += 1
        
        conn.commit()
        
        print(f"Added {fortinet_count} new Fortinet icons")
        print(f"Skipped {updated_count} existing icons")
        print(f"Total icons processed: {len(svg_files)}")

def create_device_bindings():
    """Create icon bindings for known device types"""
    bindings = [
        # FortiGate bindings
        ('manufacturer', 'Fortinet', 'fortigate', 'FortiGate Firewall', 'icons/FG-100D.svg', 90),
        ('device_type', 'fortigate', 'fortigate', 'FortiGate Firewall', 'icons/FG-100D.svg', 100),
        ('device_type', 'firewall', 'fortigate', 'Firewall', 'icons/FG-100D.svg', 80),
        
        # FortiSwitch bindings
        ('device_type', 'fortiswitch', 'fortiswitch', 'FortiSwitch', 'icons/FSW-124D__F_.svg', 100),
        ('device_type', 'switch', 'fortiswitch', 'Network Switch', 'icons/FSW-124D__F_.svg', 80),
        
        # FortiAP bindings
        ('device_type', 'fortiap', 'fortiap', 'FortiAP Wireless', 'icons/FAP-221_223E.svg', 100),
        ('device_type', 'wireless', 'fortiap', 'Wireless Access Point', 'icons/FAP-221_223E.svg', 80),
        
        # Generic device types
        ('device_type', 'endpoint', 'endpoint', 'Network Device', 'icons/nd/laptop.svg', 50),
        ('device_type', 'server', 'server', 'Server', 'icons/nd/server.svg', 50),
        ('device_type', 'router', 'router', 'Router', 'icons/FG-60E-POE.svg', 70),
    ]
    
    with sqlite3.connect(DB_PATH) as conn:
        for key_type, key_value, device_type, title, icon_path, priority in bindings:
            conn.execute("""
                INSERT OR REPLACE INTO icon_bindings 
                (key_type, key_value, device_type, title, icon_path, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (key_type, key_value, device_type, title, icon_path, priority))
        
        conn.commit()
        print(f"Created {len(bindings)} icon bindings")

def show_stats():
    """Show database statistics"""
    with sqlite3.connect(DB_PATH) as conn:
        # Total icons
        cursor = conn.execute("SELECT COUNT(*) FROM icons")
        total_icons = cursor.fetchone()[0]
        
        # By manufacturer
        cursor = conn.execute("""
            SELECT manufacturer, COUNT(*) 
            FROM icons 
            GROUP BY manufacturer 
            ORDER BY COUNT(*) DESC
        """)
        by_manufacturer = cursor.fetchall()
        
        # By device type
        cursor = conn.execute("""
            SELECT device_type, COUNT(*) 
            FROM icons 
            WHERE manufacturer = 'Fortinet'
            GROUP BY device_type 
            ORDER BY COUNT(*) DESC
        """)
        by_device_type = cursor.fetchall()
        
        print(f"\n=== Icon Database Statistics ===")
        print(f"Total icons: {total_icons}")
        print(f"\nBy manufacturer:")
        for manufacturer, count in by_manufacturer:
            print(f"  {manufacturer}: {count}")
        
        print(f"\nFortinet devices by type:")
        for device_type, count in by_device_type:
            print(f"  {device_type}: {count}")

if __name__ == "__main__":
    print("Populating Fortinet icons database...")
    populate_fortinet_icons()
    create_device_bindings()
    show_stats()
    print("\nDone!")