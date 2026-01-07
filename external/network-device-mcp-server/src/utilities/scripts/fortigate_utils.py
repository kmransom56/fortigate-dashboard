#!/usr/bin/env python3
"""
Fortigate Configuration Utilities & Examples
Additional tools and usage examples for the Fortigate Config Comparison Tool
"""

import os
import glob
import re
from pathlib import Path
from typing import List, Dict
import csv
from datetime import datetime


class FortigateConfigUtils:
    """Utility functions for Fortigate configuration management."""
    
    def __init__(self, parser=None):
        if parser is None:
            from fortigate_config_diff import FortigateConfigParser
            self.parser = FortigateConfigParser()
        else:
            self.parser = parser

    def batch_compare_configs(self, config_directory: str, output_dir: str = None) -> Dict:
        """
        Compare all configuration files in a directory against each other.
        Useful for comparing multiple site configurations.
        """
        if output_dir is None:
            output_dir = "batch_comparison_results"
        
        Path(output_dir).mkdir(exist_ok=True)
        
        # Find all config files
        config_files = glob.glob(os.path.join(config_directory, "*.txt")) + \
                      glob.glob(os.path.join(config_directory, "*.conf")) + \
                      glob.glob(os.path.join(config_directory, "*.cfg"))
        
        if len(config_files) < 2:
            raise ValueError(f"Need at least 2 config files in {config_directory}")
        
        print(f"Found {len(config_files)} configuration files:")
        for f in config_files:
            print(f"  - {os.path.basename(f)}")
        
        results = {}
        comparison_count = 0
        
        # Compare each file against every other file
        for i, file1 in enumerate(config_files):
            for j, file2 in enumerate(config_files[i+1:], i+1):
                comparison_count += 1
                file1_name = os.path.basename(file1)
                file2_name = os.path.basename(file2)
                
                print(f"\nComparing {file1_name} vs {file2_name}...")
                
                output_prefix = os.path.join(output_dir, f"comparison_{comparison_count}_{file1_name}_vs_{file2_name}")
                
                try:
                    result = self.parser.compare_configs(file1, file2, output_prefix)
                    results[f"{file1_name} vs {file2_name}"] = {
                        'differences': result['total_differences'],
                        'summary': result['summary'],
                        'files': [file1, file2]
                    }
                except Exception as e:
                    print(f"Error comparing {file1_name} vs {file2_name}: {e}")
                    results[f"{file1_name} vs {file2_name}"] = {
                        'error': str(e),
                        'files': [file1, file2]
                    }
        
        # Generate batch summary report
        self._generate_batch_report(results, output_dir)
        
        return results

    def extract_config_info(self, config_file: str) -> Dict:
        """Extract key information from a Fortigate configuration file."""
        lines = self.parser.read_config(config_file)
        
        info = {
            'filename': os.path.basename(config_file),
            'total_lines': len(lines),
            'version': None,
            'build': None,
            'platform': None,
            'serial_number': None,
            'hostname': None,
            'interfaces': [],
            'vlans': [],
            'admin_users': [],
            'vpn_tunnels': []
        }
        
        # Extract header information
        for line in lines[:20]:  # Check first 20 lines for header info
            if line.startswith('#version='):
                info['version'] = line.split('=')[1].strip()
            elif line.startswith('#build='):
                info['build'] = line.split('=')[1].strip()
            elif line.startswith('#platform='):
                info['platform'] = line.split('=')[1].strip()
            elif line.startswith('#serialno='):
                info['serial_number'] = line.split('=')[1].strip()
        
        # Extract configuration details
        current_section = None
        current_interface = None
        
        for line in lines:
            stripped = line.strip()
            
            # Track current configuration section
            if stripped.startswith('config system global'):
                current_section = 'global'
            elif stripped.startswith('config system interface'):
                current_section = 'interface'
            elif stripped.startswith('config system admin'):
                current_section = 'admin'
            elif stripped.startswith('config vpn ipsec'):
                current_section = 'vpn'
            elif stripped == 'end':
                current_section = None
                current_interface = None
            
            # Extract specific information based on section
            if current_section == 'global' and 'set hostname' in stripped:
                hostname_match = re.search(r'set hostname "([^"]*)"', stripped)
                if hostname_match:
                    info['hostname'] = hostname_match.group(1)
            
            elif current_section == 'interface':
                if stripped.startswith('edit "'):
                    current_interface = stripped[6:-1]  # Remove 'edit "' and '"'
                elif current_interface and 'set ip' in stripped:
                    ip_match = re.search(r'set ip (\S+) (\S+)', stripped)
                    if ip_match:
                        info['interfaces'].append({
                            'name': current_interface,
                            'ip': ip_match.group(1),
                            'netmask': ip_match.group(2)
                        })
                elif current_interface and 'set vlanid' in stripped:
                    vlan_match = re.search(r'set vlanid (\d+)', stripped)
                    if vlan_match:
                        info['vlans'].append({
                            'interface': current_interface,
                            'vlan_id': vlan_match.group(1)
                        })
            
            elif current_section == 'admin' and stripped.startswith('edit "'):
                admin_user = stripped[6:-1]  # Remove 'edit "' and '"'
                if admin_user not in info['admin_users']:
                    info['admin_users'].append(admin_user)
        
        return info

    def generate_config_inventory(self, config_directory: str, output_file: str = "config_inventory.csv"):
        """Generate an inventory of all configuration files in a directory."""
        config_files = glob.glob(os.path.join(config_directory, "*.txt")) + \
                      glob.glob(os.path.join(config_directory, "*.conf")) + \
                      glob.glob(os.path.join(config_directory, "*.cfg"))
        
        inventory = []
        
        print(f"Analyzing {len(config_files)} configuration files...")
        
        for config_file in config_files:
            print(f"Processing {os.path.basename(config_file)}...")
            try:
                info = self.extract_config_info(config_file)
                inventory.append(info)
            except Exception as e:
                print(f"Error processing {config_file}: {e}")
                inventory.append({
                    'filename': os.path.basename(config_file),
                    'error': str(e)
                })
        
        # Write to CSV
        if inventory:
            fieldnames = ['filename', 'hostname', 'version', 'build', 'platform', 
                         'serial_number', 'total_lines', 'interface_count', 
                         'vlan_count', 'admin_user_count']
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in inventory:
                    if 'error' not in item:
                        row = {
                            'filename': item['filename'],
                            'hostname': item.get('hostname', 'N/A'),
                            'version': item.get('version', 'N/A'),
                            'build': item.get('build', 'N/A'),
                            'platform': item.get('platform', 'N/A'),
                            'serial_number': item.get('serial_number', 'N/A'),
                            'total_lines': item.get('total_lines', 0),
                            'interface_count': len(item.get('interfaces', [])),
                            'vlan_count': len(item.get('vlans', [])),
                            'admin_user_count': len(item.get('admin_users', []))
                        }
                    else:
                        row = {
                            'filename': item['filename'],
                            'hostname': f"ERROR: {item['error']}",
                            'version': 'N/A',
                            'build': 'N/A',
                            'platform': 'N/A',
                            'serial_number': 'N/A',
                            'total_lines': 0,
                            'interface_count': 0,
                            'vlan_count': 0,
                            'admin_user_count': 0
                        }
                    writer.writerow(row)
        
        print(f"Inventory saved to {output_file}")
        return inventory

    def analyze_config_complexity(self, config_file: str) -> Dict:
        """Analyze the complexity and characteristics of a Fortigate configuration."""
        lines = self.parser.read_config(config_file)
        
        analysis = {
            'filename': os.path.basename(config_file),
            'total_lines': len(lines),
            'config_sections': {},
            'security_features': {},
            'network_interfaces': 0,
            'firewall_policies': 0,
            'vpn_tunnels': 0,
            'complexity_score': 0
        }
        
        current_section = None
        section_line_count = 0
        in_firewall_policy = False
        in_vpn_tunnel = False
        
        for line in lines:
            stripped = line.strip()
            
            # Track configuration sections
            if stripped.startswith('config '):
                if current_section and section_line_count > 0:
                    analysis['config_sections'][current_section] = section_line_count
                
                current_section = stripped[7:]  # Remove 'config '
                section_line_count = 0
                
                # Track specific features
                if 'firewall policy' in current_section:
                    in_firewall_policy = True
                elif 'vpn ipsec' in current_section:
                    in_vpn_tunnel = True
                    
            elif stripped == 'end':
                if current_section and section_line_count > 0:
                    analysis['config_sections'][current_section] = section_line_count
                current_section = None
                section_line_count = 0
                in_firewall_policy = False
                in_vpn_tunnel = False
                
            elif current_section:
                section_line_count += 1
                
                # Count interfaces
                if 'system interface' in current_section and stripped.startswith('edit "'):
                    analysis['network_interfaces'] += 1
                
                # Count firewall policies
                if in_firewall_policy and stripped.startswith('edit '):
                    analysis['firewall_policies'] += 1
                
                # Count VPN tunnels
                if in_vpn_tunnel and stripped.startswith('edit "'):
                    analysis['vpn_tunnels'] += 1
                
                # Track security features
                if 'antivirus' in stripped:
                    analysis['security_features']['antivirus'] = True
                elif 'webfilter' in stripped:
                    analysis['security_features']['webfilter'] = True
                elif 'ips' in stripped:
                    analysis['security_features']['ips'] = True
                elif 'ssl-ssh-profile' in stripped:
                    analysis['security_features']['ssl_inspection'] = True
        
        # Calculate complexity score
        analysis['complexity_score'] = (
            len(analysis['config_sections']) * 2 +
            analysis['network_interfaces'] * 5 +
            analysis['firewall_policies'] * 10 +
            analysis['vpn_tunnels'] * 15 +
            len(analysis['security_features']) * 20
        )
        
        return analysis

    def compare_config_complexity(self, config_directory: str, output_file: str = "complexity_analysis.csv"):
        """Compare complexity across multiple configuration files."""
        config_files = glob.glob(os.path.join(config_directory, "*.txt")) + \
                      glob.glob(os.path.join(config_directory, "*.conf")) + \
                      glob.glob(os.path.join(config_directory, "*.cfg"))
        
        complexity_data = []
        
        print(f"Analyzing complexity of {len(config_files)} configuration files...")
        
        for config_file in config_files:
            print(f"Analyzing {os.path.basename(config_file)}...")
            try:
                analysis = self.analyze_config_complexity(config_file)
                complexity_data.append(analysis)
            except Exception as e:
                print(f"Error analyzing {config_file}: {e}")
        
        # Sort by complexity score
        complexity_data.sort(key=lambda x: x.get('complexity_score', 0), reverse=True)
        
        # Write results to CSV
        if complexity_data:
            fieldnames = ['filename', 'complexity_score', 'total_lines', 'network_interfaces', 
                         'firewall_policies', 'vpn_tunnels', 'config_sections_count',
                         'has_antivirus', 'has_webfilter', 'has_ips', 'has_ssl_inspection']
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for analysis in complexity_data:
                    row = {
                        'filename': analysis['filename'],
                        'complexity_score': analysis['complexity_score'],
                        'total_lines': analysis['total_lines'],
                        'network_interfaces': analysis['network_interfaces'],
                        'firewall_policies': analysis['firewall_policies'],
                        'vpn_tunnels': analysis['vpn_tunnels'],
                        'config_sections_count': len(analysis['config_sections']),
                        'has_antivirus': analysis['security_features'].get('antivirus', False),
                        'has_webfilter': analysis['security_features'].get('webfilter', False),
                        'has_ips': analysis['security_features'].get('ips', False),
                        'has_ssl_inspection': analysis['security_features'].get('ssl_inspection', False)
                    }
                    writer.writerow(row)
        
        print(f"Complexity analysis saved to {output_file}")
        return complexity_data
        """
        Find the configuration that could serve as a template (most similar to others).
        Useful for identifying a baseline configuration.
        """
        config_files = glob.glob(os.path.join(config_directory, "*.txt")) + \
                      glob.glob(os.path.join(config_directory, "*.conf")) + \
                      glob.glob(os.path.join(config_directory, "*.cfg"))
        
        if len(config_files) < 2:
            raise ValueError("Need at least 2 config files to find template")
        
        similarity_scores = {}
        
        for candidate in config_files:
            total_differences = 0
            comparisons = 0
            
            for other_config in config_files:
                if candidate != other_config:
                    try:
                        result = self.parser.compare_configs(candidate, other_config)
                        total_differences += result['total_differences']
                        comparisons += 1
                    except Exception as e:
                        print(f"Error comparing {candidate} vs {other_config}: {e}")
            
            if comparisons > 0:
                avg_differences = total_differences / comparisons
                similarity_scores[candidate] = avg_differences
        
        # Find the config with lowest average differences (most similar to others)
        if similarity_scores:
            template_config = min(similarity_scores.keys(), key=lambda k: similarity_scores[k])
            print(f"Recommended template configuration: {os.path.basename(template_config)}")
            print(f"Average differences with other configs: {similarity_scores[template_config]:.1f}")
            return template_config
        
        return None

    def _generate_batch_report(self, results: Dict, output_dir: str):
        """Generate a summary report for batch comparison results."""
        report_file = os.path.join(output_dir, "batch_comparison_summary.txt")
        
        with open(report_file, 'w') as f:
            f.write("FORTIGATE CONFIGURATION BATCH COMPARISON REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total comparisons: {len(results)}\n\n")
            
            # Summary statistics
            differences_list = [r['differences'] for r in results.values() if 'differences' in r]
            if differences_list:
                f.write(f"Average differences per comparison: {sum(differences_list) / len(differences_list):.1f}\n")
                f.write(f"Maximum differences: {max(differences_list)}\n")
                f.write(f"Minimum differences: {min(differences_list)}\n\n")
            
            # Detailed results
            f.write("DETAILED COMPARISON RESULTS:\n")
            f.write("-" * 30 + "\n")
            
            for comparison_name, result in results.items():
                f.write(f"\n{comparison_name}:\n")
                if 'differences' in result:
                    f.write(f"  Differences: {result['differences']}\n")
                    if result['differences'] == 0:
                        f.write("  ✅ Configurations are equivalent (after normalization)\n")
                    else:
                        f.write("  ⚠️  Configurations have meaningful differences\n")
                else:
                    f.write(f"  ❌ Error: {result.get('error', 'Unknown error')}\n")
        
        print(f"Batch comparison summary saved to {report_file}")


# Example usage functions
def example_single_comparison():
    """Example: Compare two configuration files."""
    from fortigate_config_diff import FortigateConfigParser
    
    parser = FortigateConfigParser()
    
    # Compare two configs
    results = parser.compare_configs(
        'config1.txt', 
        'config2.txt', 
        'comparison_output'
    )
    
    print(results['summary'])
    return results


def example_batch_processing():
    """Example: Process multiple configuration files."""
    utils = FortigateConfigUtils()
    
    # Compare all configs in a directory
    batch_results = utils.batch_compare_configs(
        config_directory='./configs',
        output_dir='./batch_results'
    )
    
    # Generate inventory
    inventory = utils.generate_config_inventory(
        config_directory='./configs',
        output_file='config_inventory.csv'
    )
    
    # Find template configuration
    template = utils.find_template_config('./configs')
    
    return batch_results, inventory, template


def example_comprehensive_analysis():
    """Example: Comprehensive analysis of Fortigate configurations."""
    from fortigate_config_diff import FortigateConfigParser
    
    parser = FortigateConfigParser()
    utils = FortigateConfigUtils(parser)
    
    print("=== COMPREHENSIVE FORTIGATE CONFIGURATION ANALYSIS ===\n")
    
    # Step 1: Analyze complexity of all configs
    print("1. Analyzing configuration complexity...")
    complexity_data = utils.compare_config_complexity('./configs')
    
    print(f"   Most complex config: {complexity_data[0]['filename']} (score: {complexity_data[0]['complexity_score']})")
    print(f"   Least complex config: {complexity_data[-1]['filename']} (score: {complexity_data[-1]['complexity_score']})")
    
    # Step 2: Compare two configs with detailed categorization
    print("\n2. Detailed comparison between two configurations...")
    if len(complexity_data) >= 2:
        config1 = f"./configs/{complexity_data[0]['filename']}"
        config2 = f"./configs/{complexity_data[1]['filename']}"
        
        results = parser.compare_configs(config1, config2, "detailed_comparison")
        
        print(f"   Total differences: {results['total_differences']}")
        print(f"   Configuration blocks compared: {results['block_counts']['common_blocks']}")
        
        # Show categorized differences
        for category, diffs in results['categorized_differences'].items():
            total_diffs = len(diffs['missing_in_config1']) + len(diffs['missing_in_config2']) + len(diffs['different'])
            if total_diffs > 0:
                print(f"   {category.title()} differences: {total_diffs}")
    
    # Step 3: Find template/baseline
    print("\n3. Finding template configuration...")
    template = utils.find_template_config('./configs')
    
    # Step 4: Generate comprehensive reports
    print("\n4. Generating comprehensive reports...")
    inventory = utils.generate_config_inventory('./configs', 'full_inventory.csv')
    batch_results = utils.batch_compare_configs('./configs', './comprehensive_results')
    
    print("\n✅ Comprehensive analysis complete!")
    print("Check the following files for results:")
    print("   - complexity_analysis.csv (complexity scores)")
    print("   - full_inventory.csv (configuration inventory)")
    print("   - ./comprehensive_results/ (detailed comparisons)")
    
    return {
        'complexity_data': complexity_data,
        'template_config': template,
        'inventory': inventory,
        'batch_results': batch_results
    }


def example_power_automate_integration():
    """Example: Power Automate integration workflow."""
    from fortigate_config_diff import FortigateConfigParser
    
    # This example shows how to structure the output for Power Automate consumption
    parser = FortigateConfigParser()
    
    # Sample comparison (you would trigger this from Power Automate)
    results = parser.compare_configs('baseline_config.txt', 'new_config.txt')
    
    # Format results for Power Automate
    power_automate_output = {
        'comparison_status': 'SUCCESS' if results['total_differences'] >= 0 else 'ERROR',
        'significant_changes': results['total_differences'] > 50,  # Threshold for alerts
        'alert_required': results['total_differences'] > 100,     # High-priority threshold
        'categories_affected': [],
        'summary_message': '',
        'detailed_results_url': 'path/to/detailed/results.json'
    }
    
    # Identify affected categories
    for category, diffs in results['categorized_differences'].items():
        total_cat_diffs = len(diffs['missing_in_config1']) + len(diffs['missing_in_config2']) + len(diffs['different'])
        if total_cat_diffs > 0:
            power_automate_output['categories_affected'].append({
                'category': category,
                'difference_count': total_cat_diffs,
                'severity': 'HIGH' if total_cat_diffs > 20 else 'MEDIUM' if total_cat_diffs > 5 else 'LOW'
            })
    
    # Generate summary message
    if results['total_differences'] == 0:
        power_automate_output['summary_message'] = "✅ No significant configuration differences detected"
    elif results['total_differences'] < 50:
        power_automate_output['summary_message'] = f"⚠️ Minor configuration changes detected ({results['total_differences']} differences)"
    else:
        power_automate_output['summary_message'] = f"🚨 Significant configuration changes detected ({results['total_differences']} differences)"
    
    # This JSON structure can be easily consumed by Power Automate
    print("Power Automate Integration Output:")
    print(json.dumps(power_automate_output, indent=2))
    
    return power_automate_output


if __name__ == '__main__':
    # Run example workflow
    print("Fortigate Configuration Utilities")
    print("This script provides utility functions for configuration management")
    print("Import this module and use the example functions to get started")