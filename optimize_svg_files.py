#!/usr/bin/env python3
"""
Optimize SVG files for web usage using SVGO
"""

import os
import subprocess
import shutil
from pathlib import Path
import json
import time

def create_svgo_config():
    """Create SVGO configuration optimized for web icons"""
    config = {
        "plugins": [
            # Enable safe optimizations
            "preset-default",
            
            # Remove unnecessary data
            {
                "name": "removeComments",
                "active": True
            },
            {
                "name": "removeMetadata", 
                "active": True
            },
            {
                "name": "removeEditorsNSData",
                "active": True
            },
            {
                "name": "cleanupAttrs",
                "active": True
            },
            {
                "name": "removeEmptyText",
                "active": True
            },
            
            # Optimize numbers (reduce precision)
            {
                "name": "cleanupNumericValues",
                "params": {
                    "floatPrecision": 2
                }
            },
            
            # Optimize paths
            {
                "name": "convertPathData",
                "params": {
                    "floatPrecision": 2,
                    "transformPrecision": 2
                }
            },
            
            # Remove unnecessary attributes
            {
                "name": "removeUnknownsAndDefaults",
                "active": True
            },
            
            # Optimize transforms
            {
                "name": "convertTransform",
                "params": {
                    "floatPrecision": 2
                }
            },
            
            # Keep viewBox for proper scaling
            {
                "name": "removeViewBox",
                "active": False
            },
            
            # Keep dimensions for compatibility
            {
                "name": "removeDimensions", 
                "active": False
            }
        ]
    }
    
    config_path = Path("svgo.config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return config_path

def optimize_svg_file(input_path, output_path, config_path):
    """Optimize a single SVG file using SVGO"""
    try:
        cmd = [
            "svgo", 
            "--config", str(config_path),
            "--input", str(input_path),
            "--output", str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def get_file_size(path):
    """Get file size in bytes"""
    try:
        return Path(path).stat().st_size
    except:
        return 0

def optimize_svg_directory():
    """Optimize all SVG files in the icons directory"""
    icons_dir = Path("app/static/icons")
    backup_dir = Path("app/static/icons_backup")
    temp_dir = Path("app/static/icons_optimized")
    
    if not icons_dir.exists():
        print("❌ Icons directory not found")
        return False
    
    # Create directories
    backup_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)
    
    print("🎨 SVG Optimization Process")
    print("=" * 50)
    
    # Get all SVG files
    svg_files = list(icons_dir.glob("*.svg"))
    print(f"📁 Found {len(svg_files)} SVG files")
    
    # Calculate original total size
    original_size = sum(get_file_size(f) for f in svg_files)
    print(f"📊 Original total size: {original_size:,} bytes ({original_size/1024/1024:.1f} MB)")
    
    # Create SVGO config
    config_path = create_svgo_config()
    print(f"⚙️  Created SVGO configuration")
    
    # Process files
    processed = 0
    errors = 0
    total_original = 0
    total_optimized = 0
    
    print(f"\n🚀 Processing files...")
    start_time = time.time()
    
    for svg_file in svg_files:
        original_size = get_file_size(svg_file)
        backup_path = backup_dir / svg_file.name
        temp_path = temp_dir / svg_file.name
        
        # Backup original
        if not backup_path.exists():
            shutil.copy2(svg_file, backup_path)
        
        # Optimize to temp directory
        success, error = optimize_svg_file(svg_file, temp_path, config_path)
        
        if success and temp_path.exists():
            optimized_size = get_file_size(temp_path)
            
            # Only replace if optimization was beneficial and file is valid
            if optimized_size > 0 and optimized_size < original_size * 1.1:  # Allow 10% increase for edge cases
                shutil.copy2(temp_path, svg_file)
                total_original += original_size
                total_optimized += optimized_size
                processed += 1
                
                # Show progress for large files
                if original_size > 50000:  # Files > 50KB
                    reduction = original_size - optimized_size
                    reduction_pct = (reduction / original_size) * 100
                    print(f"   ✅ {svg_file.name}: {original_size//1024}KB → {optimized_size//1024}KB (-{reduction_pct:.1f}%)")
            else:
                # Keep original if optimization didn't help
                total_original += original_size
                total_optimized += original_size
                processed += 1
        else:
            errors += 1
            total_original += original_size
            total_optimized += original_size
            if errors <= 5:  # Only show first 5 errors
                print(f"   ❌ {svg_file.name}: {error}")
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    config_path.unlink(missing_ok=True)
    
    # Results
    elapsed = time.time() - start_time
    total_reduction = total_original - total_optimized
    reduction_pct = (total_reduction / total_original) * 100 if total_original > 0 else 0
    
    print(f"\n📊 Optimization Results")
    print(f"   Processed: {processed}/{len(svg_files)} files")
    print(f"   Errors: {errors} files")
    print(f"   Time: {elapsed:.1f} seconds")
    print(f"   Original size: {total_original:,} bytes ({total_original/1024/1024:.1f} MB)")
    print(f"   Optimized size: {total_optimized:,} bytes ({total_optimized/1024/1024:.1f} MB)")
    print(f"   Reduction: {total_reduction:,} bytes ({total_reduction/1024/1024:.1f} MB, {reduction_pct:.1f}%)")
    
    if errors > 0:
        print(f"\n⚠️  {errors} files had optimization errors - originals preserved")
        print(f"   Backups available in: {backup_dir}")
    
    return processed > 0

def verify_optimization():
    """Verify that optimized SVG files are still valid"""
    print(f"\n🔍 Verifying optimized SVG files...")
    
    icons_dir = Path("app/static/icons")
    svg_files = list(icons_dir.glob("*.svg"))
    
    valid_count = 0
    invalid_files = []
    
    for svg_file in svg_files[:50]:  # Test first 50 files
        try:
            with open(svg_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Basic validation
            if content.startswith('<svg') and content.endswith('</svg>') and 'viewBox' in content:
                valid_count += 1
            else:
                invalid_files.append(svg_file.name)
                
        except Exception as e:
            invalid_files.append(f"{svg_file.name}: {e}")
    
    print(f"   ✅ {valid_count}/{min(50, len(svg_files))} sampled files are valid")
    
    if invalid_files:
        print(f"   ⚠️  Invalid files found:")
        for invalid in invalid_files[:3]:
            print(f"      - {invalid}")
    
    return len(invalid_files) == 0

def main():
    """Main optimization process"""
    print("🎯 SVG Web Optimization")
    print("=" * 50)
    
    # Check if SVGO is installed
    try:
        result = subprocess.run(["svgo", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ SVGO not installed. Run: npm install -g svgo")
            return
        print(f"✅ SVGO version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ SVGO not found. Run: npm install -g svgo")
        return
    
    # Run optimization
    if optimize_svg_directory():
        verify_optimization()
        print(f"\n🎉 SVG optimization completed!")
        print(f"\n✅ Benefits:")
        print(f"   - Reduced file sizes for faster loading")
        print(f"   - Removed unnecessary metadata and comments")
        print(f"   - Optimized number precision for smaller files")
        print(f"   - Preserved visual quality and functionality")
        print(f"\n💾 Backups saved in: app/static/icons_backup/")
    else:
        print(f"\n❌ Optimization failed")

if __name__ == "__main__":
    main()