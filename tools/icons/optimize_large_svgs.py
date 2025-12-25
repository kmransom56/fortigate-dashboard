#!/usr/bin/env python3
"""
Optimize the largest SVG files first for maximum impact
"""

import os
import subprocess
import shutil
from pathlib import Path
import json
import time

def get_file_size(path):
    """Get file size in bytes"""
    try:
        return Path(path).stat().st_size
    except:
        return 0

def optimize_svg_file(input_path, output_path):
    """Optimize a single SVG file using SVGO with focused settings"""
    try:
        # Simple but effective SVGO command
        cmd = [
            "svgo",
            "--multipass",
            "--config", json.dumps({
                "plugins": [
                    "preset-default",
                    {"name": "removeComments"},
                    {"name": "removeMetadata"},
                    {"name": "cleanupNumericValues", "params": {"floatPrecision": 2}},
                    {"name": "convertPathData", "params": {"floatPrecision": 2}},
                    {"name": "removeViewBox", "active": False}
                ]
            }),
            "--input", str(input_path),
            "--output", str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
        
    except Exception as e:
        return False, str(e)

def optimize_largest_files():
    """Focus on optimizing the largest files for maximum impact"""
    icons_dir = Path("../../app/static/icons")
    
    if not icons_dir.exists():
        print("❌ Icons directory not found")
        return
    
    print("🎯 Optimizing Largest SVG Files")
    print("=" * 40)
    
    # Get all SVG files with sizes
    svg_files = []
    for svg_path in icons_dir.glob("*.svg"):
        size = get_file_size(svg_path)
        svg_files.append((svg_path, size))
    
    # Sort by size (largest first)
    svg_files.sort(key=lambda x: x[1], reverse=True)
    
    # Focus on files larger than 50KB (these will have the most impact)
    large_files = [(path, size) for path, size in svg_files if size > 50000]
    
    print(f"📊 Found {len(large_files)} files > 50KB")
    if len(large_files) == 0:
        print("✅ No large files need optimization")
        return
    
    total_original = 0
    total_optimized = 0
    processed = 0
    
    for svg_path, original_size in large_files[:20]:  # Process top 20 largest files
        print(f"\n🔄 {svg_path.name} ({original_size//1024}KB)")
        
        # Create backup
        backup_path = svg_path.with_suffix('.svg.backup')
        if not backup_path.exists():
            shutil.copy2(svg_path, backup_path)
        
        # Optimize to temporary file
        temp_path = svg_path.with_suffix('.svg.temp')
        success, error = optimize_svg_file(svg_path, temp_path)
        
        if success and temp_path.exists():
            optimized_size = get_file_size(temp_path)
            
            if optimized_size > 0:
                reduction = original_size - optimized_size
                reduction_pct = (reduction / original_size) * 100
                
                print(f"   ✅ {original_size//1024}KB → {optimized_size//1024}KB (-{reduction_pct:.1f}%)")
                
                # Replace original with optimized
                shutil.move(temp_path, svg_path)
                
                total_original += original_size
                total_optimized += optimized_size
                processed += 1
            else:
                print(f"   ❌ Optimization produced empty file")
                temp_path.unlink(missing_ok=True)
        else:
            print(f"   ❌ Optimization failed: {error}")
            temp_path.unlink(missing_ok=True)
    
    print(f"\n📊 Results")
    print(f"   Processed: {processed} files")
    total_reduction = total_original - total_optimized
    reduction_pct = (total_reduction / total_original) * 100 if total_original > 0 else 0
    print(f"   Size reduction: {total_reduction:,} bytes ({total_reduction/1024/1024:.1f} MB, {reduction_pct:.1f}%)")

def quick_optimization_sample():
    """Run optimization on a small sample first"""
    icons_dir = Path("../../app/static/icons")
    
    # Test with a few large files
    test_files = [
        "FG-4400_4401F.svg",
        "FG-4800_4801F.svg",
        "FG-3980E.svg"
    ]
    
    print("🧪 Testing Optimization on Sample Files")
    print("=" * 40)
    
    for filename in test_files:
        svg_path = icons_dir / filename
        if not svg_path.exists():
            continue
            
        original_size = get_file_size(svg_path)
        print(f"\n📁 {filename} ({original_size//1024}KB)")
        
        # Create temp optimized version
        temp_path = svg_path.with_suffix('.svg.test')
        success, error = optimize_svg_file(svg_path, temp_path)
        
        if success and temp_path.exists():
            optimized_size = get_file_size(temp_path)
            reduction = original_size - optimized_size
            reduction_pct = (reduction / original_size) * 100
            
            print(f"   ✅ Would reduce by {reduction:,} bytes ({reduction_pct:.1f}%)")
            
            # Check if optimized file looks valid
            try:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                if '<svg' in content and '</svg>' in content:
                    print(f"   ✅ Optimized file appears valid")
                else:
                    print(f"   ⚠️  Optimized file may be corrupted")
            except:
                print(f"   ❌ Cannot read optimized file")
            
            temp_path.unlink()
        else:
            print(f"   ❌ Optimization failed: {error}")

def main():
    """Run SVG optimization"""
    print("🚀 SVG Optimization - Focused Approach")
    print("=" * 50)
    
    # Check SVGO
    try:
        result = subprocess.run(["svgo", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SVGO available: {result.stdout.strip()}")
        else:
            print("❌ SVGO not working properly")
            return
    except:
        print("❌ SVGO not found. Install with: npm install -g svgo")
        return
    
    # First, test optimization on a few files
    quick_optimization_sample()
    
    # Then optimize the largest files
    optimize_largest_files()
    
    print(f"\n🎉 Optimization complete!")
    print(f"💾 Backup files created with .backup extension")

if __name__ == "__main__":
    main()