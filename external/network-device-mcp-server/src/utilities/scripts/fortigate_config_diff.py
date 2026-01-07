#!/usr/bin/env python3
"""
Fortigate Configuration Comparison Tool
Compares two Fortigate configuration files while filtering out expected differences
like IP addresses, passwords, secrets, certificates, serial numbers, etc.
"""

import re
import argparse
import difflib
from typing import List, Dict, Set, Tuple
from pathlib import Path
import json


class FortigateConfigParser:
    """Parser for Fortigate configuration files with normalization capabilities."""
    
    def __init__(self):
        # Patterns for data that should be normalized/masked in comparisons
        self.normalization_patterns = {
            # IP addresses and subnets
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}(?:\s+(?:\d{1,3}\.){3}\d{1,3})?\b',
            
            # Serial numbers and hardware identifiers
            'serial_number': r'#serialno=\w+',
            'mgmt_data': r'#mgmt\.dat[a2]=[\d,]+',
            'config_version': r'#config-version=[^:]+:[^:]+:[^:]+:user=\w+',
            
            # Encrypted passwords and secrets
            'encrypted_password': r'set password ENC \S*',
            'old_password': r'set old-password ENC \S*',
            'shared_secret': r'set shared-secret ENC \S*',
            'psksecret': r'set psksecret ENC \S*',
            'private_key': r'set private-key "[^"]*"',
            'certificate_content': r'set certificate "[^"]*"',
            'ca_certificate': r'set ca-certificate "[^"]*"',
            
            # Base64 encoded content (images, certificates, etc.)
            'image_base64': r"set image-base64 '.*?'",
            'image_base64_empty': r"set image-base64 ''",
            'image_base64_multiline': r'set image-base64\s*\n',
            
            # Site-specific identifiers
            'hostname': r'set hostname "[^"]*"',
            'alias': r'set alias "[^"]*"',
            'description': r'set description "[^"]*"',
            'comment': r'set comment "[^"]*"',
            
            # Certificate and key references
            'certificate_ref': r'set admin-server-cert "[^"]*"',
            'server_cert': r'set server-cert "[^"]*"',
            'ca_cert': r'set ca-cert "[^"]*"',
            
            # Timestamps and expiration dates
            'password_expire': r'set password-expire \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            'cert_expire': r'set cert-expire \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            
            # Hardware and build info
            'hwrev': r'#hwrev=\S+',
            'build': r'#build=\d+',
            'branch_pt': r'#branch_pt=\d+',
            'platform': r'#platform=[\w-]+',
            
            # Network configuration (environment-specific)
            'trusthost': r'set trusthost\d+ (?:\d{1,3}\.){3}\d{1,3} (?:\d{1,3}\.){3}\d{1,3}',
            'set_ip': r'set ip (?:\d{1,3}\.){3}\d{1,3} (?:\d{1,3}\.){3}\d{1,3}',
            'gateway': r'set gateway (?:\d{1,3}\.){3}\d{1,3}',
            'dns_primary': r'set primary (?:\d{1,3}\.){3}\d{1,3}',
            'dns_secondary': r'set secondary (?:\d{1,3}\.){3}\d{1,3}',
            'server_ip': r'set server "[^"]*"',
            'radius_server': r'set server (?:\d{1,3}\.){3}\d{1,3}',
            
            # SNMP and monitoring indices
            'snmp_index': r'set snmp-index \d+',
            
            # VPN and tunnel specifics
            'peer_ip': r'set remote-gw (?:\d{1,3}\.){3}\d{1,3}',
            'local_id': r'set localid "[^"]*"',
            'peer_id': r'set peerid "[^"]*"',
            
            # URL patterns that might be site-specific
            'url_pattern': r'set url "[^"]*\.com[^"]*"',
            
            # MAC addresses
            'mac_address': r'\b[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\b',
            
            # DHCP ranges and reservations (site-specific)
            'dhcp_range': r'set start-ip (?:\d{1,3}\.){3}\d{1,3}|set end-ip (?:\d{1,3}\.){3}\d{1,3}',
            
            # Log disk and storage paths
            'logdisk': r'#logdisk=\d+',
            'partition': r'set partition "[^"]*"',
            'device_path': r'set device "[^"]*"',
        }
        
        # Replacement tokens for normalized values
        self.replacements = {
            'ip_address': 'IP_ADDRESS_MASKED',
            'serial_number': '#serialno=SERIAL_MASKED',
            'mgmt_data': '#mgmt.data=MGMT_DATA_MASKED',
            'config_version': '#config-version=VERSION_MASKED:opmode=0:vdom=0:user=USER_MASKED',
            'encrypted_password': 'set password ENC PASSWORD_MASKED',
            'old_password': 'set old-password ENC OLD_PASSWORD_MASKED',
            'shared_secret': 'set shared-secret ENC SECRET_MASKED',
            'psksecret': 'set psksecret ENC PSK_MASKED',
            'private_key': 'set private-key "PRIVATE_KEY_MASKED"',
            'certificate_content': 'set certificate "CERTIFICATE_MASKED"',
            'ca_certificate': 'set ca-certificate "CA_CERT_MASKED"',
            'image_base64': "set image-base64 'BASE64_MASKED'",
            'image_base64_empty': "set image-base64 'BASE64_EMPTY'",
            'image_base64_multiline': 'set image-base64 BASE64_MULTILINE_MASKED\n',
            'hostname': 'set hostname "HOSTNAME_MASKED"',
            'alias': 'set alias "ALIAS_MASKED"',
            'description': 'set description "DESCRIPTION_MASKED"',
            'comment': 'set comment "COMMENT_MASKED"',
            'certificate_ref': 'set admin-server-cert "CERT_REF_MASKED"',
            'server_cert': 'set server-cert "SERVER_CERT_MASKED"',
            'ca_cert': 'set ca-cert "CA_CERT_MASKED"',
            'password_expire': 'set password-expire DATE_MASKED',
            'cert_expire': 'set cert-expire DATE_MASKED',
            'hwrev': '#hwrev=HWREV_MASKED',
            'build': '#build=BUILD_MASKED',
            'branch_pt': '#branch_pt=BRANCH_MASKED',
            'platform': '#platform=PLATFORM_MASKED',
            'trusthost': 'set trusthost# IP_ADDRESS_MASKED IP_ADDRESS_MASKED',
            'set_ip': 'set ip IP_ADDRESS_MASKED SUBNET_MASKED',
            'gateway': 'set gateway IP_ADDRESS_MASKED',
            'dns_primary': 'set primary IP_ADDRESS_MASKED',
            'dns_secondary': 'set secondary IP_ADDRESS_MASKED',
            'server_ip': 'set server "SERVER_MASKED"',
            'radius_server': 'set server IP_ADDRESS_MASKED',
            'snmp_index': 'set snmp-index INDEX_MASKED',
            'peer_ip': 'set remote-gw IP_ADDRESS_MASKED',
            'local_id': 'set localid "LOCAL_ID_MASKED"',
            'peer_id': 'set peerid "PEER_ID_MASKED"',
            'url_pattern': 'set url "URL_MASKED"',
            'mac_address': 'MAC_ADDRESS_MASKED',
            'dhcp_range': 'set start-ip IP_ADDRESS_MASKED',
            'logdisk': '#logdisk=LOGDISK_MASKED',
            'partition': 'set partition "PARTITION_MASKED"',
            'device_path': 'set device "DEVICE_PATH_MASKED"',
        }

        # Configuration section types for better analysis
        self.config_sections = {
            'system': ['system global', 'system interface', 'system admin', 'system storage', 
                      'system password-policy', 'system ha', 'system dns', 'system dhcp server'],
            'security': ['firewall policy', 'firewall address', 'firewall service', 'antivirus profile',
                        'webfilter profile', 'dnsfilter profile', 'ips sensor'],
            'vpn': ['vpn ipsec phase1-interface', 'vpn ipsec phase2-interface', 'vpn ssl settings',
                   'vpn certificate ca', 'vpn certificate local'],
            'routing': ['router static', 'router ospf', 'router bgp', 'router rip', 'router policy'],
            'wireless': ['wireless-controller vap', 'wireless-controller wtp', 'wireless-controller setting'],
            'switch': ['switch-controller security-policy', 'switch-controller qos', 'switch-controller traffic-policy'],
            'logging': ['log syslogd', 'log fortianalyzer', 'log memory setting', 'log disk setting'],
            'user': ['user radius', 'user group', 'user fortitoken', 'user setting'],
            'automation': ['system automation-trigger', 'system automation-action', 'system automation-stitch'],
            'content': ['wanopt content-delivery-network-rule', 'webfilter urlfilter', 'application list']
        }

    def read_config(self, file_path: str) -> List[str]:
        """Read configuration file and return lines."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.readlines()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.readlines()

    def normalize_line(self, line: str) -> str:
        """Normalize a single line by masking sensitive/variable data."""
        normalized = line.strip()
        
        # Apply all normalization patterns
        for pattern_name, pattern in self.normalization_patterns.items():
            if pattern_name == 'trusthost':
                # Special handling for trusthost to preserve the number
                def trusthost_replacer(match):
                    original = match.group(0)
                    # Extract the trusthost number
                    trusthost_num = re.search(r'trusthost(\d+)', original)
                    if trusthost_num:
                        return f'set trusthost{trusthost_num.group(1)} IP_ADDRESS_MASKED IP_ADDRESS_MASKED'
                    return self.replacements[pattern_name]
                normalized = re.sub(pattern, trusthost_replacer, normalized)
            else:
                normalized = re.sub(pattern, self.replacements[pattern_name], normalized)
        
        return normalized

    def normalize_config(self, lines: List[str]) -> List[str]:
        """Normalize entire configuration by masking sensitive data."""
        normalized_lines = []
        
        for line in lines:
            # Skip empty lines and preserve structure
            if line.strip() == '':
                normalized_lines.append('')
                continue
                
            normalized_line = self.normalize_line(line)
            normalized_lines.append(normalized_line)
        
        return normalized_lines

    def parse_config_blocks(self, lines: List[str]) -> Dict[str, List[str]]:
        """Parse configuration into logical blocks for better comparison."""
        blocks = {}
        current_block = None
        current_lines = []
        block_stack = []  # To handle nested config blocks
        
        for line in lines:
            stripped = line.strip()
            
            # Detect start of new config block
            if stripped.startswith('config '):
                # If we have a current block, save it
                if current_block:
                    block_key = ' -> '.join(block_stack + [current_block])
                    if block_key not in blocks:
                        blocks[block_key] = []
                    blocks[block_key].extend(current_lines)
                
                # Handle nested config blocks
                if current_block:
                    block_stack.append(current_block)
                
                current_block = stripped[7:]  # Remove 'config '
                current_lines = [line]
                
            elif stripped == 'end' and current_block:
                current_lines.append(line)
                
                # Save the current block
                block_key = ' -> '.join(block_stack + [current_block])
                if block_key not in blocks:
                    blocks[block_key] = []
                blocks[block_key].extend(current_lines)
                
                # Pop the stack for nested blocks
                if block_stack:
                    current_block = block_stack.pop()
                    current_lines = []
                else:
                    current_block = None
                    current_lines = []
                    
            elif stripped.startswith('edit ') and current_block:
                # Handle edit sections within config blocks
                current_lines.append(line)
                
            elif stripped == 'next' and current_block:
                # Handle end of edit sections
                current_lines.append(line)
                
            elif current_block:
                current_lines.append(line)
                
            else:
                # Handle header lines and other content
                if 'header' not in blocks:
                    blocks['header'] = []
                blocks['header'].append(line)
        
        return blocks

    def categorize_section(self, section_name: str) -> str:
        """Categorize a configuration section into functional groups."""
        section_lower = section_name.lower()
        
        for category, patterns in self.config_sections.items():
            for pattern in patterns:
                if pattern.lower() in section_lower:
                    return category
        
        return 'other'

    def analyze_section_differences(self, blocks1: Dict, blocks2: Dict) -> Dict:
        """Analyze differences by configuration section category."""
        categorized_diffs = {
            'system': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'security': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'vpn': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'routing': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'wireless': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'switch': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'logging': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'user': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'automation': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'content': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []},
            'other': {'missing_in_config2': [], 'missing_in_config1': [], 'different': []}
        }
        
        # Analyze missing sections
        for block_name in blocks1:
            if block_name not in blocks2:
                category = self.categorize_section(block_name)
                categorized_diffs[category]['missing_in_config2'].append(block_name)
        
        for block_name in blocks2:
            if block_name not in blocks1:
                category = self.categorize_section(block_name)
                categorized_diffs[category]['missing_in_config1'].append(block_name)
        
        # Analyze different sections
        common_blocks = set(blocks1.keys()) & set(blocks2.keys())
        for block_name in common_blocks:
            if blocks1[block_name] != blocks2[block_name]:
                category = self.categorize_section(block_name)
                categorized_diffs[category]['different'].append(block_name)
        
        return categorized_diffs

    def compare_configs(self, file1: str, file2: str, output_file: str = None) -> Dict:
        """Compare two Fortigate configuration files."""
        print(f"Reading configuration files...")
        
        # Read both config files
        config1_lines = self.read_config(file1)
        config2_lines = self.read_config(file2)
        
        print(f"Config 1: {len(config1_lines)} lines")
        print(f"Config 2: {len(config2_lines)} lines")
        
        # Normalize both configurations
        print("Normalizing configurations...")
        normalized_config1 = self.normalize_config(config1_lines)
        normalized_config2 = self.normalize_config(config2_lines)
        
        # Parse into blocks for structured comparison
        print("Parsing configuration blocks...")
        blocks1 = self.parse_config_blocks(normalized_config1)
        blocks2 = self.parse_config_blocks(normalized_config2)
        
        print(f"Found {len(blocks1)} blocks in config 1")
        print(f"Found {len(blocks2)} blocks in config 2")
        
        # Find differences
        print("Analyzing differences...")
        differences = self._find_block_differences(blocks1, blocks2)
        categorized_differences = self.analyze_section_differences(blocks1, blocks2)
        
        # Generate unified diff
        unified_diff = list(difflib.unified_diff(
            normalized_config1,
            normalized_config2,
            fromfile=f'{file1} (normalized)',
            tofile=f'{file2} (normalized)',
            lineterm=''
        ))
        
        # Prepare results
        results = {
            'files_compared': [file1, file2],
            'total_differences': len([d for d in unified_diff if d.startswith(('+', '-'))]),
            'block_differences': differences,
            'categorized_differences': categorized_differences,
            'unified_diff': unified_diff,
            'summary': self._generate_summary(differences, categorized_differences, len(unified_diff)),
            'block_counts': {
                'config1_blocks': len(blocks1),
                'config2_blocks': len(blocks2),
                'common_blocks': len(set(blocks1.keys()) & set(blocks2.keys()))
            }
        }
        
        # Save results if output file specified
        if output_file:
            self._save_results(results, output_file)
        
        return results

    def _find_block_differences(self, blocks1: Dict, blocks2: Dict) -> Dict:
        """Find differences between configuration blocks."""
        differences = {
            'missing_in_config2': [],
            'missing_in_config1': [],
            'different_blocks': []
        }
        
        # Find blocks missing in config2
        for block_name in blocks1:
            if block_name not in blocks2:
                differences['missing_in_config2'].append(block_name)
        
        # Find blocks missing in config1
        for block_name in blocks2:
            if block_name not in blocks1:
                differences['missing_in_config1'].append(block_name)
        
        # Find blocks that exist in both but are different
        common_blocks = set(blocks1.keys()) & set(blocks2.keys())
        for block_name in common_blocks:
            if blocks1[block_name] != blocks2[block_name]:
                block_diff = list(difflib.unified_diff(
                    blocks1[block_name],
                    blocks2[block_name],
                    fromfile=f'Config1: {block_name}',
                    tofile=f'Config2: {block_name}',
                    lineterm=''
                ))
                if block_diff:
                    differences['different_blocks'].append({
                        'block_name': block_name,
                        'diff': block_diff
                    })
        
        return differences

    def _generate_summary(self, differences: Dict, categorized_differences: Dict, total_diff_lines: int) -> str:
        """Generate a human-readable summary of differences."""
        summary = []
        summary.append("=== FORTIGATE CONFIGURATION COMPARISON SUMMARY ===\n")
        
        if total_diff_lines == 0:
            summary.append("✅ No significant differences found (after normalization)")
            return "\n".join(summary)
        
        summary.append(f"📊 Total difference lines: {total_diff_lines}")
        
        # Overall block differences
        summary.append(f"\n📋 Configuration Block Summary:")
        summary.append(f"   • Blocks missing in Config 2: {len(differences['missing_in_config2'])}")
        summary.append(f"   • Blocks missing in Config 1: {len(differences['missing_in_config1'])}")
        summary.append(f"   • Modified blocks: {len(differences['different_blocks'])}")
        
        # Categorized analysis
        summary.append(f"\n🔍 Differences by Category:")
        category_totals = {}
        for category, cat_diffs in categorized_differences.items():
            total_cat_diffs = (len(cat_diffs['missing_in_config1']) + 
                             len(cat_diffs['missing_in_config2']) + 
                             len(cat_diffs['different']))
            if total_cat_diffs > 0:
                category_totals[category] = total_cat_diffs
                summary.append(f"   • {category.title()}: {total_cat_diffs} differences")
        
        # Detailed breakdown for significant categories
        for category in sorted(category_totals.keys(), key=lambda x: category_totals[x], reverse=True)[:5]:
            cat_diffs = categorized_differences[category]
            if category_totals[category] > 0:
                summary.append(f"\n📂 {category.title()} Category Details:")
                if cat_diffs['missing_in_config2']:
                    summary.append(f"   Missing in Config 2 ({len(cat_diffs['missing_in_config2'])}):")
                    for block in cat_diffs['missing_in_config2'][:3]:  # Show first 3
                        summary.append(f"     - {block}")
                    if len(cat_diffs['missing_in_config2']) > 3:
                        summary.append(f"     ... and {len(cat_diffs['missing_in_config2']) - 3} more")
                
                if cat_diffs['missing_in_config1']:
                    summary.append(f"   Missing in Config 1 ({len(cat_diffs['missing_in_config1'])}):")
                    for block in cat_diffs['missing_in_config1'][:3]:  # Show first 3
                        summary.append(f"     - {block}")
                    if len(cat_diffs['missing_in_config1']) > 3:
                        summary.append(f"     ... and {len(cat_diffs['missing_in_config1']) - 3} more")
                
                if cat_diffs['different']:
                    summary.append(f"   Modified ({len(cat_diffs['different'])}):")
                    for block in cat_diffs['different'][:3]:  # Show first 3
                        summary.append(f"     - {block}")
                    if len(cat_diffs['different']) > 3:
                        summary.append(f"     ... and {len(cat_diffs['different']) - 3} more")
        
        summary.append("\n🔒 Normalization Applied:")
        summary.append("   • IP addresses, passwords, secrets, and certificates masked")
        summary.append("   • Serial numbers and hardware identifiers masked")
        summary.append("   • Site-specific hostnames and aliases masked")
        summary.append("   • Timestamps and expiration dates masked")
        
        summary.append(f"\n💡 Comparison focused on functional configuration differences")
        
        return "\n".join(summary)

    def _save_results(self, results: Dict, output_file: str):
        """Save comparison results to file."""
        output_path = Path(output_file)
        
        # Save as text report
        with open(output_path.with_suffix('.txt'), 'w') as f:
            f.write(results['summary'])
            f.write("\n\n=== DETAILED DIFFERENCES ===\n\n")
            f.write('\n'.join(results['unified_diff']))
        
        # Save as JSON for programmatic access
        json_results = {
            'files_compared': results['files_compared'],
            'total_differences': results['total_differences'],
            'summary': results['summary'],
            'block_differences': results['block_differences']
        }
        
        with open(output_path.with_suffix('.json'), 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"Results saved to:")
        print(f"  - {output_path.with_suffix('.txt')} (human-readable)")
        print(f"  - {output_path.with_suffix('.json')} (machine-readable)")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Compare Fortigate configuration files while filtering out expected differences'
    )
    parser.add_argument('config1', help='First configuration file')
    parser.add_argument('config2', help='Second configuration file')
    parser.add_argument('-o', '--output', help='Output file prefix (will create .txt and .json files)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Create parser instance
    parser = FortigateConfigParser()
    
    try:
        # Compare configurations
        results = parser.compare_configs(args.config1, args.config2, args.output)
        
        # Display summary
        print("\n" + results['summary'])
        
        if args.verbose and results['total_differences'] > 0:
            print("\n=== DETAILED DIFFERENCES ===")
            for line in results['unified_diff']:
                print(line)
    
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found - {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()


# Example usage as a module:
"""
from fortigate_config_diff import FortigateConfigParser

# Create parser
parser = FortigateConfigParser()

# Compare two configurations
results = parser.compare_configs('config1.txt', 'config2.txt', 'comparison_results')

# Access results
print(results['summary'])
print(f"Total differences: {results['total_differences']}")

# Check if configurations are essentially the same
if results['total_differences'] == 0:
    print("Configurations are equivalent (ignoring expected differences)")
else:
    print("Configurations have meaningful differences")
"""