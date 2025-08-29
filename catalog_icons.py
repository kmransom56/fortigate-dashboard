#!/usr/bin/env python3
"""
Icon Catalog Generator for FortiGate Dashboard
Scans and catalogs all SVG icons, creates a database for easy browsing
"""
import os
import json
import sqlite3
from pathlib import Path
import hashlib
import re

def get_file_info(filepath):
    """Get file information including size and hash"""
    try:
        stat = os.stat(filepath)
        with open(filepath, 'rb') as f:
            content = f.read()
            file_hash = hashlib.md5(content).hexdigest()
        
        # Try to get SVG dimensions if possible
        width, height = None, None
        if str(filepath).endswith('.svg'):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    svg_content = f.read()
                    width_match = re.search(r'width=["\']([^"\']*)["\']', svg_content)
                    height_match = re.search(r'height=["\']([^"\']*)["\']', svg_content)
                    viewbox_match = re.search(r'viewBox=["\']([^"\']*)["\']', svg_content)
                    
                    if width_match:
                        width = width_match.group(1)
                    if height_match:
                        height = height_match.group(1)
                    if viewbox_match and not width:
                        # Parse viewBox: "x y width height"
                        viewbox = viewbox_match.group(1).split()
                        if len(viewbox) >= 4:
                            width, height = viewbox[2], viewbox[3]
            except Exception as e:
                print(f"Warning: Could not parse SVG dimensions for {filepath}: {e}")
        
        return {
            'size': stat.st_size,
            'hash': file_hash,
            'width': width,
            'height': height,
            'modified': stat.st_mtime
        }
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def categorize_icon(filename, relative_path):
    """Categorize icons based on filename and path"""
    filename_lower = filename.lower()
    path_lower = relative_path.lower()
    
    categories = []
    
    # Fortinet specific
    if 'forti' in filename_lower or 'fortinet' in path_lower:
        categories.append('fortinet')
        
        # Specific Fortinet products
        forti_products = {
            'fortigate': 'firewall',
            'fortiswitch': 'switch', 
            'fortiap': 'wifi',
            'fortiwifi': 'wifi',
            'fortimail': 'email',
            'fortimanager': 'management',
            'fortianalyzer': 'analytics',
            'fortisandbox': 'security',
            'fortiweb': 'web-security',
            'fortiproxy': 'proxy',
            'fortisiem': 'siem',
            'fortisoar': 'soar',
            'fortiedr': 'endpoint',
            'fortisase': 'sase',
            'fortinac': 'nac'
        }
        
        for product, category in forti_products.items():
            if product in filename_lower:
                categories.append(category)
    
    # Network vendors
    vendors = ['cisco', 'ubiquiti', 'mikrotik', 'hp', 'dell', 'lenovo', 'aruba', 'juniper']
    for vendor in vendors:
        if vendor in filename_lower:
            categories.append('vendor')
            categories.append(vendor)
    
    # Icon types
    if any(term in filename_lower for term in ['router', 'switch', 'gateway']):
        categories.append('network-device')
    
    if any(term in filename_lower for term in ['server', 'desktop', 'laptop', 'mobile', 'tablet']):
        categories.append('device')
    
    if any(term in filename_lower for term in ['wifi', 'wireless', 'antenna']):
        categories.append('wireless')
    
    if any(term in filename_lower for term in ['security', 'shield', 'lock', 'firewall']):
        categories.append('security')
    
    if any(term in filename_lower for term in ['pos', 'point-of-sale', 'kiosk', 'retail', 'cash', 'payment']):
        categories.append('pos-retail')
    
    if any(term in filename_lower for term in ['cloud', 'virtual', 'vm']):
        categories.append('cloud-virtual')
    
    # Simple icons (from simple-icons library)
    if filename_lower.startswith('simple_'):
        categories.append('simple-icons')
    
    # Feather icons
    if filename_lower.startswith('feather_'):
        categories.append('feather-icons')
    
    # If no categories found, add general
    if not categories:
        categories.append('general')
    
    return categories

def scan_icons(icons_dir):
    """Scan the icons directory and catalog all SVG files"""
    icons = []
    icons_path = Path(icons_dir)
    
    print(f"📁 Scanning icons in: {icons_dir}")
    
    # Find all SVG files
    svg_files = list(icons_path.rglob("*.svg"))
    
    print(f"🔍 Found {len(svg_files)} SVG files")
    
    for svg_file in svg_files:
        try:
            relative_path = str(svg_file.relative_to(icons_path))
            filename = svg_file.name
            
            file_info = get_file_info(svg_file)
            if not file_info:
                continue
            
            categories = categorize_icon(filename, relative_path)
            
            icon_data = {
                'filename': filename,
                'path': relative_path,
                'full_path': str(svg_file),
                'categories': categories,
                'size': file_info['size'],
                'hash': file_info['hash'],
                'width': file_info['width'],
                'height': file_info['height'],
                'modified': file_info['modified']
            }
            
            icons.append(icon_data)
            
        except Exception as e:
            print(f"❌ Error processing {svg_file}: {e}")
    
    return icons

def create_database(icons, db_path):
    """Create SQLite database for icon catalog"""
    print(f"💾 Creating database: {db_path}")
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE icons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            path TEXT NOT NULL,
            full_path TEXT NOT NULL,
            size INTEGER,
            hash TEXT UNIQUE,
            width TEXT,
            height TEXT,
            modified REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE icon_categories (
            icon_id INTEGER,
            category_id INTEGER,
            FOREIGN KEY (icon_id) REFERENCES icons (id),
            FOREIGN KEY (category_id) REFERENCES categories (id),
            PRIMARY KEY (icon_id, category_id)
        )
    ''')
    
    # Insert icons
    for icon in icons:
        # Check if icon with same hash already exists
        cursor.execute('SELECT id FROM icons WHERE hash = ?', (icon['hash'],))
        existing = cursor.fetchone()
        
        if existing:
            icon_id = existing[0]
            print(f"Duplicate found: {icon['filename']} (same as existing icon)")
        else:
            cursor.execute('''
                INSERT INTO icons (filename, path, full_path, size, hash, width, height, modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                icon['filename'],
                icon['path'], 
                icon['full_path'],
                icon['size'],
                icon['hash'],
                icon['width'],
                icon['height'],
                icon['modified']
            ))
            icon_id = cursor.lastrowid
        
        # Insert categories
        for category in icon['categories']:
            cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (category,))
            cursor.execute('SELECT id FROM categories WHERE name = ?', (category,))
            category_id = cursor.fetchone()[0]
            
            cursor.execute('INSERT OR IGNORE INTO icon_categories (icon_id, category_id) VALUES (?, ?)', 
                         (icon_id, category_id))
    
    conn.commit()
    
    # Create indexes
    cursor.execute('CREATE INDEX idx_icons_filename ON icons(filename)')
    cursor.execute('CREATE INDEX idx_icons_hash ON icons(hash)')
    cursor.execute('CREATE INDEX idx_categories_name ON categories(name)')
    
    conn.commit()
    conn.close()

def generate_report(icons, report_path):
    """Generate a detailed report of the icon catalog"""
    print(f"📊 Generating report: {report_path}")
    
    # Calculate statistics
    total_icons = len(icons)
    total_size = sum(icon['size'] for icon in icons)
    
    # Group by categories
    category_counts = {}
    for icon in icons:
        for category in icon['categories']:
            category_counts[category] = category_counts.get(category, 0) + 1
    
    # Group by directory
    dir_counts = {}
    for icon in icons:
        dir_name = os.path.dirname(icon['path']) or 'root'
        dir_counts[dir_name] = dir_counts.get(dir_name, 0) + 1
    
    # Generate report
    with open(report_path, 'w') as f:
        f.write("# FortiGate Dashboard Icon Catalog Report\n\n")
        f.write(f"Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Summary\n")
        f.write(f"- **Total Icons**: {total_icons:,}\n")
        f.write(f"- **Total Size**: {total_size / 1024 / 1024:.2f} MB\n")
        f.write(f"- **Average Size**: {total_size / total_icons / 1024:.2f} KB per icon\n\n")
        
        f.write("## Categories\n")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{category}**: {count} icons\n")
        
        f.write("\n## Directories\n")
        for directory, count in sorted(dir_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{directory}**: {count} icons\n")
        
        f.write("\n## Top 20 Largest Icons\n")
        largest_icons = sorted(icons, key=lambda x: x['size'], reverse=True)[:20]
        for icon in largest_icons:
            f.write(f"- **{icon['filename']}**: {icon['size'] / 1024:.2f} KB\n")

def main():
    icons_dir = "app/static/icons"
    db_path = "app/static/icons.db"
    report_path = "icon_catalog_report.md"
    
    print("🎨 FortiGate Dashboard Icon Catalog Generator")
    print("=" * 50)
    
    # Scan icons
    icons = scan_icons(icons_dir)
    
    if not icons:
        print("❌ No SVG icons found!")
        return
    
    # Create database
    create_database(icons, db_path)
    
    # Generate report
    generate_report(icons, report_path)
    
    print(f"\n✅ Icon catalog complete!")
    print(f"📊 Cataloged {len(icons)} icons")
    print(f"💾 Database: {db_path}")
    print(f"📄 Report: {report_path}")

if __name__ == "__main__":
    main()
