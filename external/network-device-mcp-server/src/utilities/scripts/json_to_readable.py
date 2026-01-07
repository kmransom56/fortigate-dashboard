#!/usr/bin/env python3
"""
FortiGuard PSIRT JSON to Readable Format Converter
Converts JSON advisory files to CSV, HTML, and formatted text reports
"""

import json
import csv
import sys
from datetime import datetime
from pathlib import Path
import argparse

def load_json_file(filepath):
    """Load and parse JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None

def convert_to_csv(advisories, output_file):
    """Convert advisories to CSV format"""
    if not advisories:
        print("No advisories to convert")
        return
    
    fieldnames = ['advisory_id', 'cve_id', 'title', 'published', 'link', 'summary']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for advisory in advisories:
            # Handle both old and new JSON formats
            if isinstance(advisory, str):
                continue  # Skip if it's just a string
            
            # Extract data with fallbacks for different formats
            advisory_id = advisory.get('id') or advisory.get('advisory_id', 'N/A')
            cve_ids = advisory.get('cve_ids', []) or [advisory.get('cve_id', '')]
            cve_id = ', '.join(cve_ids) if cve_ids and cve_ids != [''] else 'N/A'
            title = advisory.get('title', '')
            published = advisory.get('published_date') or advisory.get('published', '')
            link = advisory.get('url') or advisory.get('link', '')
            summary = advisory.get('summary', '')
            
            # Truncate summary if too long
            if len(summary) > 200:
                summary = summary[:200] + '...'
            
            row = {
                'advisory_id': advisory_id,
                'cve_id': cve_id,
                'title': title,
                'published': published,
                'link': link,
                'summary': summary
            }
            writer.writerow(row)
    
    print(f"CSV file saved: {output_file}")

def convert_to_html(advisories, output_file):
    """Convert advisories to HTML table format"""
    if not advisories:
        print("No advisories to convert")
        return
    
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>FortiGuard PSIRT Advisories</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .cve { font-weight: bold; color: #d73502; }
        .advisory-id { font-weight: bold; color: #0066cc; }
        .summary { max-width: 400px; word-wrap: break-word; }
        .title { font-weight: bold; }
    </style>
</head>
<body>
    <h1>FortiGuard PSIRT Security Advisories</h1>
    <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    <p>Total Advisories: """ + str(len(advisories)) + """</p>
    
    <table>
        <thead>
            <tr>
                <th>Advisory ID</th>
                <th>CVE ID</th>
                <th>Title</th>
                <th>Published</th>
                <th>Summary</th>
                <th>Link</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for advisory in advisories:
        # Handle both old and new JSON formats
        if isinstance(advisory, str):
            continue  # Skip if it's just a string
        
        # Extract data with fallbacks for different formats
        advisory_id = advisory.get('id') or advisory.get('advisory_id', 'N/A')
        cve_ids = advisory.get('cve_ids', []) or [advisory.get('cve_id', '')]
        cve_id = ', '.join(cve_ids) if cve_ids and cve_ids != [''] else 'N/A'
        title = advisory.get('title', '')
        published = advisory.get('published_date') or advisory.get('published', '')
        link = advisory.get('url') or advisory.get('link', '')
        summary = advisory.get('summary', '')
        
        # Truncate summary if too long
        if len(summary) > 300:
            summary = summary[:300] + '...'
        
        html_content += f"""
            <tr>
                <td class="advisory-id">{advisory_id}</td>
                <td class="cve">{cve_id}</td>
                <td class="title">{title}</td>
                <td>{published}</td>
                <td class="summary">{summary}</td>
                <td><a href="{link}" target="_blank">View</a></td>
            </tr>
        """
    
    html_content += """
        </tbody>
    </table>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML file saved: {output_file}")

def convert_to_text_report(advisories, output_file):
    """Convert advisories to formatted text report"""
    if not advisories:
        print("No advisories to convert")
        return
    
    report = f"""
FortiGuard PSIRT Security Advisories Report
==========================================
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Advisories: {len(advisories)}

"""
    
    # Group by product
    products = {}
    for advisory in advisories:
        if isinstance(advisory, str):
            continue  # Skip if it's just a string
        
        # Use affected_products field if available, otherwise check title
        affected_products = advisory.get('affected_products', [])
        title = advisory.get('title', '')
        
        if affected_products:
            for product in affected_products:
                products[product] = products.get(product, 0) + 1
        else:
            # Fallback to title checking
            if 'FortiOS' in title:
                products['FortiOS'] = products.get('FortiOS', 0) + 1
            elif 'FortiGate' in title:
                products['FortiGate'] = products.get('FortiGate', 0) + 1
            elif 'FortiAnalyzer' in title:
                products['FortiAnalyzer'] = products.get('FortiAnalyzer', 0) + 1
            elif 'FortiManager' in title:
                products['FortiManager'] = products.get('FortiManager', 0) + 1
            else:
                products['Other'] = products.get('Other', 0) + 1
    
    report += "Summary by Product:\n"
    report += "-" * 20 + "\n"
    for product, count in products.items():
        report += f"{product}: {count}\n"
    
    report += "\n" + "=" * 80 + "\n"
    report += "DETAILED ADVISORIES\n"
    report += "=" * 80 + "\n\n"
    
    for i, advisory in enumerate(advisories, 1):
        if isinstance(advisory, str):
            continue  # Skip if it's just a string
        
        # Extract data with fallbacks for different formats
        advisory_id = advisory.get('id') or advisory.get('advisory_id', 'N/A')
        cve_ids = advisory.get('cve_ids', []) or [advisory.get('cve_id', '')]
        cve_id = ', '.join(cve_ids) if cve_ids and cve_ids != [''] else 'N/A'
        title = advisory.get('title', '')
        published = advisory.get('published_date') or advisory.get('published', '')
        summary = advisory.get('summary', '')
        link = advisory.get('url') or advisory.get('link', '')
        
        report += f"[{i}] {title}\n"
        report += f"    Advisory ID: {advisory_id}\n"
        report += f"    CVE ID: {cve_id}\n"
        report += f"    Published: {published}\n"
        report += f"    Link: {link}\n"
        if summary:
            report += f"    Summary: {summary[:200]}{'...' if len(summary) > 200 else ''}\n"
        report += "\n" + "-" * 80 + "\n\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Text report saved: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Convert FortiGuard PSIRT JSON to readable formats')
    parser.add_argument('json_file', help='Input JSON file path')
    parser.add_argument('--format', choices=['csv', 'html', 'txt', 'all'], default='all',
                        help='Output format (default: all)')
    parser.add_argument('--output', help='Output file prefix (default: based on input filename)')
    
    args = parser.parse_args()
    
    # Load JSON data
    advisories = load_json_file(args.json_file)
    if not advisories:
        return
    
    # Determine output prefix
    if args.output:
        output_prefix = args.output
    else:
        input_path = Path(args.json_file)
        output_prefix = input_path.stem
    
    # Convert to requested formats
    if args.format in ['csv', 'all']:
        csv_file = f"{output_prefix}.csv"
        convert_to_csv(advisories, csv_file)
    
    if args.format in ['html', 'all']:
        html_file = f"{output_prefix}.html"
        convert_to_html(advisories, html_file)
    
    if args.format in ['txt', 'all']:
        txt_file = f"{output_prefix}_report.txt"
        convert_to_text_report(advisories, txt_file)
    
    print(f"\nConversion complete! Processed {len(advisories)} advisories.")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Interactive mode if no arguments provided
        print("FortiGuard PSIRT JSON to Readable Format Converter")
        print("=" * 50)
        
        json_file = input("Enter JSON file path: ").strip().strip('"')
        if not json_file or not Path(json_file).exists():
            print("Invalid file path!")
            sys.exit(1)
        
        print("\nAvailable formats:")
        print("1. CSV")
        print("2. HTML")
        print("3. Text Report")
        print("4. All formats")
        
        choice = input("Select format (1-4): ").strip()
        format_map = {'1': 'csv', '2': 'html', '3': 'txt', '4': 'all'}
        selected_format = format_map.get(choice, 'all')
        
        # Load and convert
        advisories = load_json_file(json_file)
        if not advisories:
            sys.exit(1)
        
        output_prefix = Path(json_file).stem
        
        if selected_format in ['csv', 'all']:
            convert_to_csv(advisories, f"{output_prefix}.csv")
        
        if selected_format in ['html', 'all']:
            convert_to_html(advisories, f"{output_prefix}.html")
        
        if selected_format in ['txt', 'all']:
            convert_to_text_report(advisories, f"{output_prefix}_report.txt")
        
        print(f"\nConversion complete! Processed {len(advisories)} advisories.")
    else:
        main()
