#!/usr/bin/env python3
"""
FortiManager Application Deployment Configuration Generator

This script compares baseline and post-deployment Fortigate configurations to extract
only the changes needed for a new application, then generates FortiManager-compatible
configuration templates for deployment across multiple stores.
"""

import re
import sys
import argparse
import json
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import difflib
from datetime import datetime


class FortiManagerConfigGenerator:
    def __init__(self):
        # Patterns for store-specific values that should be templated
        self.template_patterns = {
            'store_ip_ranges': r'\b(10\.(\d{1,3})\.(\d{1,3})\.\d{1,3}(?:/\d{1,2})?)\b',
            'store_subnets': r'\b(192\.168\.(\d{1,3})\.\d{1,3}(?:/\d{1,2})?)\b',
            'wan_interfaces': r'(port\d+|wan\d*)',
            'lan_interfaces': r'(internal|dmz|port\d+)',
            'store_names': r'(store\d+|branch\d+|location\d+)',
        }
        
        # Configuration sections that typically change for new applications
        self.app_config_sections = [
            'firewall policy',
            'firewall address',
            'firewall addrgrp',
            'firewall service',
            'firewall schedule',
            'system interface',
            'router static',
            'firewall vip',
            'firewall central-snat-map',
            'application list',
            'ips sensor',
            'webfilter profile'
        ]

    def parse_fortigate_config(self, config_text: str) -> Dict[str, Dict]:
        """
        Parse Fortigate configuration into structured blocks
        """
        config_blocks = {}
        lines = config_text.split('\n')
        current_section = None
        current_subsection = None
        current_block = []
        indent_level = 0
        
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            original_line = line
            
            # Count indentation
            indent = len(line) - len(line.lstrip())
            
            if stripped.startswith('config '):
                # Save previous block
                if current_section and current_block:
                    self._save_block(config_blocks, current_section, current_subsection, current_block)
                
                current_section = stripped[7:]  # Remove 'config '
                current_subsection = None
                current_block = [original_line]
                indent_level = indent
                
            elif stripped.startswith('edit '):
                if current_section:
                    current_subsection = stripped[5:].strip('"')  # Remove 'edit ' and quotes
                    current_block.append(original_line)
                    
            elif stripped in ['end', 'next']:
                if current_section:
                    current_block.append(original_line)
                    if stripped == 'end':
                        # End of config section
                        self._save_block(config_blocks, current_section, current_subsection, current_block)
                        current_section = None
                        current_subsection = None
                        current_block = []
                    elif stripped == 'next' and current_subsection:
                        # End of edit subsection, but continue with config section
                        current_subsection = None
                        
            else:
                if current_section:
                    current_block.append(original_line)
        
        # Save final block
        if current_section and current_block:
            self._save_block(config_blocks, current_section, current_subsection, current_block)
            
        return config_blocks

    def _save_block(self, config_blocks: Dict, section: str, subsection: Optional[str], block: List[str]):
        """Helper to save configuration blocks"""
        if section not in config_blocks:
            config_blocks[section] = {}
        
        key = subsection if subsection else '_main_'
        config_blocks[section][key] = '\n'.join(block)

    def extract_application_changes(self, baseline_config: str, deployed_config: str) -> Dict:
        """
        Extract only the configuration changes related to application deployment
        """
        baseline_blocks = self.parse_fortigate_config(baseline_config)
        deployed_blocks = self.parse_fortigate_config(deployed_config)
        
        changes = {
            'new_sections': {},
            'modified_sections': {},
            'new_objects': {},
            'modified_objects': {},
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'baseline_sections': len(baseline_blocks),
                'deployed_sections': len(deployed_blocks)
            }
        }
        
        # Find new and modified sections
        for section in deployed_blocks:
            if section not in baseline_blocks:
                # Completely new section
                changes['new_sections'][section] = deployed_blocks[section]
            else:
                # Check for modifications within existing sections
                baseline_section = baseline_blocks[section]
                deployed_section = deployed_blocks[section]
                
                section_changes = {}
                
                for obj_name in deployed_section:
                    if obj_name not in baseline_section:
                        # New object in existing section
                        section_changes[obj_name] = {
                            'type': 'new',
                            'config': deployed_section[obj_name]
                        }
                    elif deployed_section[obj_name] != baseline_section[obj_name]:
                        # Modified object
                        section_changes[obj_name] = {
                            'type': 'modified',
                            'config': deployed_section[obj_name],
                            'diff': self._generate_object_diff(
                                baseline_section[obj_name], 
                                deployed_section[obj_name]
                            )
                        }
                
                if section_changes:
                    changes['modified_sections'][section] = section_changes
        
        return changes

    def _generate_object_diff(self, baseline: str, deployed: str) -> List[str]:
        """Generate unified diff for a configuration object"""
        return list(difflib.unified_diff(
            baseline.splitlines(keepends=True),
            deployed.splitlines(keepends=True),
            fromfile='baseline',
            tofile='deployed',
            lineterm=''
        ))

    def create_fortimanager_template(self, changes: Dict, template_vars: Dict = None) -> Dict:
        """
        Create FortiManager-compatible configuration template
        """
        if template_vars is None:
            template_vars = {
                'store_id': '{{store_id}}',
                'store_subnet': '{{store_subnet}}',
                'wan_interface': '{{wan_interface}}',
                'lan_interface': '{{lan_interface}}',
                'store_name': '{{store_name}}'
            }
        
        template = {
            'template_name': f"app_deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'description': 'Auto-generated application deployment template',
            'variables': template_vars,
            'configuration_blocks': [],
            'deployment_order': []
        }
        
        # Process new sections
        for section_name, section_config in changes.get('new_sections', {}).items():
            template_block = self._templatize_config_block(section_name, section_config, template_vars)
            template['configuration_blocks'].append(template_block)
            template['deployment_order'].append(section_name)
        
        # Process modified sections (only new/changed objects)
        for section_name, section_changes in changes.get('modified_sections', {}).items():
            for obj_name, obj_change in section_changes.items():
                if obj_change['type'] in ['new', 'modified']:
                    template_block = self._templatize_config_block(
                        f"{section_name} -> {obj_name}", 
                        obj_change['config'], 
                        template_vars
                    )
                    template['configuration_blocks'].append(template_block)
                    if section_name not in template['deployment_order']:
                        template['deployment_order'].append(section_name)
        
        return template

    def _templatize_config_block(self, block_name: str, config_text: str, template_vars: Dict) -> Dict:
        """
        Convert configuration block to template format with variables
        """
        templated_config = config_text
        
        # Apply template variable substitutions
        for var_name, var_placeholder in template_vars.items():
            if var_name == 'store_subnet':
                # Replace store-specific IP ranges
                templated_config = re.sub(
                    r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?\b',
                    var_placeholder,
                    templated_config
                )
                templated_config = re.sub(
                    r'\b192\.168\.\d{1,3}\.\d{1,3}(?:/\d{1,2})?\b',
                    var_placeholder,
                    templated_config
                )
            elif var_name == 'store_name':
                # Replace store identifiers
                templated_config = re.sub(
                    r'\b(store|branch|location)\d+\b',
                    var_placeholder,
                    templated_config,
                    flags=re.IGNORECASE
                )
        
        return {
            'name': block_name,
            'config': templated_config,
            'requires_validation': self._requires_validation(config_text)
        }

    def _requires_validation(self, config_text: str) -> List[str]:
        """
        Identify configuration elements that require validation before deployment
        """
        validations = []
        
        # Check for interface references
        if re.search(r'set interface ', config_text):
            validations.append('interface_exists')
            
        # Check for IP ranges that might conflict
        if re.search(r'set subnet ', config_text):
            validations.append('subnet_availability')
            
        # Check for service ports
        if re.search(r'set portrange ', config_text):
            validations.append('port_availability')
            
        return validations

    def generate_fortimanager_script(self, template: Dict, output_format: str = 'cli') -> str:
        """
        Generate deployment script for FortiManager
        """
        if output_format == 'cli':
            return self._generate_cli_script(template)
        elif output_format == 'json':
            return json.dumps(template, indent=2)
        elif output_format == 'api':
            return self._generate_api_script(template)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_cli_script(self, template: Dict) -> str:
        """Generate CLI commands for FortiManager"""
        script_lines = [
            f"# {template['description']}",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Template: {template['template_name']}",
            "",
            "# Variables to be replaced before deployment:",
        ]
        
        for var_name, var_placeholder in template['variables'].items():
            script_lines.append(f"# {var_name}: {var_placeholder}")
        
        script_lines.extend([
            "",
            "# Configuration blocks:",
            ""
        ])
        
        for block in template['configuration_blocks']:
            script_lines.append(f"# --- {block['name']} ---")
            script_lines.append(block['config'])
            script_lines.append("")
            
            if block['requires_validation']:
                script_lines.append(f"# VALIDATION REQUIRED: {', '.join(block['requires_validation'])}")
                script_lines.append("")
        
        return '\n'.join(script_lines)

    def _generate_api_script(self, template: Dict) -> str:
        """Generate API deployment script"""
        api_script = f'''#!/bin/bash
# FortiManager API Deployment Script
# Template: {template['template_name']}

FORTIMANAGER_IP="${{FORTIMANAGER_IP:-192.168.1.100}}"
USERNAME="${{USERNAME:-admin}}"
PASSWORD="${{PASSWORD}}"
ADOM="${{ADOM:-root}}"

# Login and get session token
curl -X POST "https://$FORTIMANAGER_IP/jsonrpc" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "method": "exec",
    "params": [{{
      "url": "/sys/login/user",
      "data": {{
        "user": "'$USERNAME'",
        "passwd": "'$PASSWORD'"
      }}
    }}],
    "id": 1
  }}'

# Deploy configuration blocks
'''
        for i, block in enumerate(template['configuration_blocks']):
            api_script += f'''
# Deploy {block['name']}
curl -X POST "https://$FORTIMANAGER_IP/jsonrpc" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "method": "add",
    "params": [{{
      "url": "/pm/config/adom/$ADOM/obj/firewall/address",
      "data": {json.dumps(block['config'], indent=6)}
    }}],
    "id": {i+2}
  }}'
'''
        return api_script


def main():
    parser = argparse.ArgumentParser(description='Generate FortiManager deployment configuration from application changes')
    parser.add_argument('baseline_config', help='Path to baseline configuration file')
    parser.add_argument('deployed_config', help='Path to post-deployment configuration file')
    parser.add_argument('-o', '--output', help='Output file for the deployment script')
    parser.add_argument('-f', '--format', choices=['cli', 'json', 'api'], default='cli', 
                       help='Output format (default: cli)')
    parser.add_argument('-t', '--template-vars', help='JSON file with template variables')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Validate input files
    for config_file in [args.baseline_config, args.deployed_config]:
        if not Path(config_file).exists():
            print(f"Error: Configuration file '{config_file}' not found")
            sys.exit(1)
    
    # Load template variables if provided
    template_vars = None
    if args.template_vars:
        with open(args.template_vars, 'r') as f:
            template_vars = json.load(f)
    
    # Create generator and process configurations
    generator = FortiManagerConfigGenerator()
    
    if args.verbose:
        print(f"Analyzing changes between {args.baseline_config} and {args.deployed_config}...")
    
    try:
        # Read configuration files
        with open(args.baseline_config, 'r') as f:
            baseline_config = f.read()
        with open(args.deployed_config, 'r') as f:
            deployed_config = f.read()
        
        # Extract changes
        changes = generator.extract_application_changes(baseline_config, deployed_config)
        
        if args.verbose:
            print(f"Found {len(changes['new_sections'])} new sections")
            print(f"Found {len(changes['modified_sections'])} modified sections")
        
        # Create FortiManager template
        template = generator.create_fortimanager_template(changes, template_vars)
        
        # Generate deployment script
        script = generator.generate_fortimanager_script(template, args.format)
        
        # Output result
        if args.output:
            with open(args.output, 'w') as f:
                f.write(script)
            print(f"Deployment script saved to: {args.output}")
        else:
            print(script)
            
    except Exception as e:
        print(f"Error during processing: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()