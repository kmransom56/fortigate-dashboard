#!/usr/bin/env python3
"""
Simple SVG optimization using SVGO
"""

import subprocess
import os
from pathlib import Path
import time

def get_file_size(path):
    """Get file size in bytes"""
    try:
        return Path(path).stat().st_size
    except:
        return 0

def optimize_largest_svgs():
    """Optimize the 20 largest SVG files"""
    icons_dir = Path("../../app/static/icons")
    
    # Get SVG files with sizes
    svg_files = []
    for svg_path in icons_dir.glob("*.svg"):
        size = get_file_size(svg_path)
        svg_files.append((svg_path, size))
    
    # Sort by size (largest first) and take top 20
    svg_files.sort(key=lambda x: x[1], reverse=True)
    largest_files = svg_files[:20]
    
    print("🎯 Optimizing 20 Largest SVG Files")
    print("=" * 50)
    
    total_original = 0
    total_optimized = 0
    
    for i, (svg_path, original_size) in enumerate(largest_files, 1):
        print(f"[{i}/20] {svg_path.name} ({original_size//1024}KB)")
        
        # Create backup
        backup_path = svg_path.with_suffix('.svg.backup')
        if not backup_path.exists():
            os.rename(svg_path, backup_path)
        
        try:
            # Run SVGO optimization
            cmd = [
                "svgo",
                "--config", "svgo.config.js",
                "-i", str(backup_path),
                "-o", str(svg_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                optimized_size = get_file_size(svg_path)
                if optimized_size > 0:
                    reduction = original_size - optimized_size
                    reduction_pct = (reduction / original_size) * 100
                    print(f"   ✅ {original_size//1024}KB → {optimized_size//1024}KB (-{reduction_pct:.1f}%)")
                    
                    total_original += original_size
                    total_optimized += optimized_size
                else:
                    print(f"   ❌ Optimization failed - keeping backup")
                    os.rename(backup_path, svg_path)
            else:
                print(f"   ❌ SVGO error: {result.stderr}")
                os.rename(backup_path, svg_path)
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Restore from backup if optimization failed
            if backup_path.exists():
                os.rename(backup_path, svg_path)
    
    # Summary
    if total_original > 0:
        total_reduction = total_original - total_optimized
        reduction_pct = (total_reduction / total_original) * 100
        
        print(f"\n📊 Summary")
        print(f"   Original size: {total_original//1024} KB")
        print(f"   Optimized size: {total_optimized//1024} KB")  
        print(f"   Total reduction: {total_reduction//1024} KB ({reduction_pct:.1f}%)")
    
    print(f"\n✅ Optimization complete!")

if __name__ == "__main__":
    optimize_largest_svgs()