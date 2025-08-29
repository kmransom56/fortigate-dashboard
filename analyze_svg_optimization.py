#!/usr/bin/env python3
"""
Analyze SVG files to identify optimization opportunities
"""

import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET

def analyze_svg_file(svg_path):
    """Analyze a single SVG file for optimization opportunities"""
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        size = len(content)
        
        # Basic analysis
        analysis = {
            'path': str(svg_path),
            'size': size,
            'issues': [],
            'optimizable': False
        }
        
        # Check for common optimization opportunities
        if '<!-- ' in content or '<!--' in content:
            analysis['issues'].append('Contains comments')
            analysis['optimizable'] = True
        
        if 'style=' in content and len(re.findall(r'style="[^"]*"', content)) > 3:
            analysis['issues'].append('Inline styles (could be optimized)')
            analysis['optimizable'] = True
            
        if 'transform=' in content and len(re.findall(r'transform="[^"]*"', content)) > 5:
            analysis['issues'].append('Many transforms (could be simplified)')
            analysis['optimizable'] = True
        
        # Check for excessive precision in numbers
        if len(re.findall(r'\d+\.\d{4,}', content)) > 0:
            analysis['issues'].append('High precision numbers')
            analysis['optimizable'] = True
            
        # Check for excessive viewBox size (some Visio exports are huge)
        viewbox_match = re.search(r'viewBox="([^"]*)"', content)
        if viewbox_match:
            try:
                viewbox = viewbox_match.group(1).split()
                if len(viewbox) == 4:
                    width = float(viewbox[2])
                    height = float(viewbox[3]) 
                    if width > 1000 or height > 1000:
                        analysis['issues'].append(f'Large viewBox: {width}x{height}')
                        analysis['optimizable'] = True
            except:
                pass
        
        # Check for very large files
        if size > 10000:  # 10KB
            analysis['issues'].append(f'Large file size: {size} bytes')
            analysis['optimizable'] = True
        
        # Check for empty or minimal content
        if '<g' not in content and '<path' not in content and '<rect' not in content:
            analysis['issues'].append('Minimal/empty content')
        
        return analysis
        
    except Exception as e:
        return {
            'path': str(svg_path),
            'size': 0,
            'issues': [f'Error reading file: {e}'],
            'optimizable': False
        }

def analyze_svg_directory(directory):
    """Analyze all SVG files in a directory"""
    svg_files = list(Path(directory).glob("*.svg"))
    
    print(f"🔍 Analyzing {len(svg_files)} SVG files in {directory}")
    print("-" * 60)
    
    total_size = 0
    total_issues = 0
    optimizable_files = 0
    size_categories = {'small': 0, 'medium': 0, 'large': 0, 'huge': 0}
    
    analyses = []
    
    for svg_path in svg_files:
        analysis = analyze_svg_file(svg_path)
        analyses.append(analysis)
        
        total_size += analysis['size']
        total_issues += len(analysis['issues'])
        
        if analysis['optimizable']:
            optimizable_files += 1
        
        # Categorize by size
        if analysis['size'] < 1000:  # < 1KB
            size_categories['small'] += 1
        elif analysis['size'] < 5000:  # < 5KB
            size_categories['medium'] += 1
        elif analysis['size'] < 20000:  # < 20KB
            size_categories['large'] += 1
        else:
            size_categories['huge'] += 1
    
    # Summary statistics
    print(f"📊 Summary Statistics")
    print(f"   Total files: {len(svg_files)}")
    print(f"   Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    print(f"   Average size: {total_size/len(svg_files):.0f} bytes")
    print(f"   Optimizable files: {optimizable_files} ({optimizable_files/len(svg_files)*100:.1f}%)")
    print(f"   Total issues found: {total_issues}")
    
    print(f"\n📈 Size Distribution")
    for category, count in size_categories.items():
        percentage = count/len(svg_files)*100
        print(f"   {category.capitalize()}: {count} files ({percentage:.1f}%)")
    
    # Show largest files
    largest_files = sorted(analyses, key=lambda x: x['size'], reverse=True)[:10]
    print(f"\n🔥 Largest Files (Top 10)")
    for analysis in largest_files:
        filename = Path(analysis['path']).name
        size_kb = analysis['size'] / 1024
        issues = ', '.join(analysis['issues'][:2])  # Show first 2 issues
        if len(analysis['issues']) > 2:
            issues += f" (+{len(analysis['issues'])-2} more)"
        print(f"   {filename:<25} {size_kb:>6.1f}KB  {issues}")
    
    # Show most problematic files
    most_issues = sorted(analyses, key=lambda x: len(x['issues']), reverse=True)[:10]
    print(f"\n⚠️  Most Issues (Top 10)")
    for analysis in most_issues:
        if len(analysis['issues']) > 0:
            filename = Path(analysis['path']).name
            issues = ', '.join(analysis['issues'])
            print(f"   {filename:<25} {len(analysis['issues'])} issues: {issues}")
    
    return analyses

def estimate_optimization_potential(analyses):
    """Estimate potential space savings from optimization"""
    print(f"\n💡 Optimization Potential")
    print("-" * 40)
    
    total_size = sum(a['size'] for a in analyses)
    optimizable_size = sum(a['size'] for a in analyses if a['optimizable'])
    
    # Conservative estimate: 20-50% reduction for optimizable files
    conservative_savings = optimizable_size * 0.20
    aggressive_savings = optimizable_size * 0.50
    
    print(f"   Current total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    print(f"   Optimizable size: {optimizable_size:,} bytes ({optimizable_size/1024/1024:.1f} MB)")
    print(f"   Conservative savings (20%): {conservative_savings:,} bytes ({conservative_savings/1024/1024:.1f} MB)")
    print(f"   Aggressive savings (50%): {aggressive_savings:,} bytes ({aggressive_savings/1024/1024:.1f} MB)")
    
    # Specific recommendations
    comment_files = [a for a in analyses if any('comment' in issue.lower() for issue in a['issues'])]
    large_precision = [a for a in analyses if any('precision' in issue.lower() for issue in a['issues'])]
    large_viewbox = [a for a in analyses if any('viewbox' in issue.lower() for issue in a['issues'])]
    
    print(f"\n🎯 Specific Optimizations")
    print(f"   Remove comments: {len(comment_files)} files")
    print(f"   Reduce precision: {len(large_precision)} files")
    print(f"   Optimize viewBox: {len(large_viewbox)} files")

def main():
    """Main analysis function"""
    print("🎨 SVG Optimization Analysis")
    print("=" * 60)
    
    icons_dir = "app/static/icons"
    
    if not Path(icons_dir).exists():
        print(f"❌ Icons directory not found: {icons_dir}")
        return
    
    analyses = analyze_svg_directory(icons_dir)
    estimate_optimization_potential(analyses)
    
    print(f"\n✅ Analysis complete!")
    print(f"\n🚀 Next steps:")
    print(f"   1. Install SVGO: npm install -g svgo")
    print(f"   2. Run bulk optimization on files with issues")
    print(f"   3. Test that optimized files still render correctly")
    print(f"   4. Compare file sizes before/after")

if __name__ == "__main__":
    main()