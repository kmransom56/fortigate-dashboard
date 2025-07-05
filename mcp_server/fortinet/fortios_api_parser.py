#!/usr/bin/env python3
"""
Fortinet API Parser - Automatically generate MCP endpoints from Fortinet API JSON files
"""

import json
import os
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path

class FortinetAPIParser:
    """Parse Fortinet API documentation and generate MCP endpoints"""
    
    def __init__(self, api_files_dir: str = "./api_docs"):
        self.api_files_dir = Path(api_files_dir)
        self.endpoints = {}
        self.categories = {}
        
    def parse_api_files(self):
        """Parse all JSON API files in the directory"""
        if not self.api_files_dir.exists():
            print(f"API files directory {self.api_files_dir} not found")
            return
            
        for api_file in self.api_files_dir.glob("*.json"):
            print(f"Parsing {api_file.name}...")
            try:
                with open(api_file, 'r') as f:
                    api_data = json.load(f)
                self._extract_endpoints(api_data, api_file.stem)
            except Exception as e:
                print(f"Error parsing {api_file}: {e}")
    
    def _extract_endpoints(self, api_data: Dict, source_file: str):
        """Extract endpoint information from API data"""
        # Handle different API documentation formats
        
        # Check for OpenAPI/Swagger format
        if "paths" in api_data:
            self._parse_openapi_format(api_data, source_file)
        
        # Check for FortiOS API format
        elif "results" in api_data or isinstance(api_data, list):
            self._parse_fortios_format(api_data, source_file)
        
        # Check for custom format
        else:
            self._parse_custom_format(api_data, source_file)
    
    def _parse_openapi_format(self, api_data: Dict, source_file: str):
        """Parse OpenAPI/Swagger format"""
        paths = api_data.get("paths", {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete']:
                    endpoint_info = {
                        'path': path,
                        'method': method.upper(),
                        'summary': details.get('summary', ''),
                        'description': details.get('description', ''),
                        'parameters': details.get('parameters', []),
                        'responses': details.get('responses', {}),
                        'tags': details.get('tags', []),
                        'source_file': source_file
                    }
                    
                    endpoint_key = f"{method.upper()}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
                    self.endpoints[endpoint_key] = endpoint_info
                    
                    # Categorize endpoint
                    category = self._determine_category(path, details.get('tags', []))
                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append(endpoint_key)
    
    def _parse_fortios_format(self, api_data: Dict, source_file: str):
        """Parse FortiOS specific API format"""
        # This handles the format typically found in FortiOS API documentation
        
        if isinstance(api_data, dict) and "results" in api_data:
            results = api_data["results"]
        elif isinstance(api_data, list):
            results = api_data
        else:
            results = [api_data]
        
        for item in results:
            if isinstance(item, dict):
                # Extract path information
                path = item.get("path", item.get("url", ""))
                if path:
                    endpoint_info = {
                        'path': path,
                        'method': 'GET',  # Default to GET, can be overridden
                        'summary': item.get('name', ''),
                        'description': item.get('description', ''),
                        'parameters': item.get('parameters', []),
                        'schema': item.get('schema', {}),
                        'source_file': source_file
                    }
                    
                    endpoint_key = f"GET_{path.replace('/', '_').replace('-', '_')}"
                    self.endpoints[endpoint_key] = endpoint_info
                    
                    category = self._determine_category(path, [])
                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append(endpoint_key)
    
    def _parse_custom_format(self, api_data: Dict, source_file: str):
        """Parse custom or unknown API format"""
        # Try to extract any useful endpoint information
        
        def extract_paths(obj, prefix=""):
            """Recursively extract potential API paths"""
            paths = []
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{prefix}/{key}" if prefix else key
                    
                    # Check if this looks like an API endpoint
                    if self._looks_like_endpoint(key, value):
                        paths.append({
                            'path': current_path,
                            'data': value,
                            'key': key
                        })
                    
                    # Recurse into nested objects
                    if isinstance(value, (dict, list)):
                        paths.extend(extract_paths(value, current_path))
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict):
                        paths.extend(extract_paths(item, f"{prefix}[{i}]"))
            
            return paths
        
        extracted_paths = extract_paths(api_data)
        
        for path_info in extracted_paths:
            endpoint_info = {
                'path': path_info['path'],
                'method': 'GET',
                'summary': path_info['key'],
                'description': str(path_info['data'])[:200] + "..." if len(str(path_info['data'])) > 200 else str(path_info['data']),
                'source_file': source_file,
                'raw_data': path_info['data']
            }
            
            endpoint_key = f"GET_{path_info['path'].replace('/', '_').replace('-', '_')}"
            self.endpoints[endpoint_key] = endpoint_info
            
            category = self._determine_category(path_info['path'], [])
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(endpoint_key)
    
    def _looks_like_endpoint(self, key: str, value: Any) -> bool:
        """Determine if a key-value pair looks like an API endpoint"""
        endpoint_indicators = [
            'api', 'endpoint', 'url', 'path', 'route',
            'get', 'post', 'put', 'delete', 'patch',
            'monitor', 'cmdb', 'log', 'report'
        ]
        
        key_lower = key.lower()
        return any(indicator in key_lower for indicator in endpoint_indicators)
    
    def _determine_category(self, path: str, tags: List[str]) -> str:
        """Determine the category for an endpoint based on path and tags"""
        path_lower = path.lower()
        
        # Category mapping based on common Fortinet API patterns
        categories = {
            'system': ['system', 'status', 'global', 'admin', 'interface'],
            'firewall': ['firewall', 'policy', 'address', 'service', 'schedule'],
            'network': ['network', 'routing', 'dns', 'dhcp', 'interface'],
            'vpn': ['vpn', 'ipsec', 'ssl', 'tunnel'],
            'security': ['security', 'antivirus', 'ips', 'application', 'web-filter'],
            'monitoring': ['monitor', 'log', 'traffic', 'performance'],
            'management': ['management', 'config', 'backup', 'restore'],
            'user': ['user', 'group', 'authentication', 'ldap'],
            'wireless': ['wireless', 'wifi', 'ap', 'ssid'],
            'switching': ['switch', 'port', 'vlan', 'stp']
        }
        
        # Check tags first
        for tag in tags:
            tag_lower = tag.lower()
            for category, keywords in categories.items():
                if any(keyword in tag_lower for keyword in keywords):
                    return category
        
        # Check path
        for category, keywords in categories.items():
            if any(keyword in path_lower for keyword in keywords):
                return category
        
        return 'misc'
    
    def generate_mcp_code(self) -> str:
        """Generate MCP server code with all discovered endpoints"""
        code_parts = []
        
        # Header
        code_parts.append('''#!/usr/bin/env python3
"""
Auto-generated Fortinet MCP Server with comprehensive API coverage
Generated from Fortinet API documentation
"""

import asyncio
import json
import logging
import os
import requests
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("fortinet-comprehensive-server")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
FORTIGATE_HOST = os.getenv("FORTIGATE_HOST", "192.168.1.1")
FORTIGATE_USERNAME = os.getenv("FORTIGATE_USERNAME", "admin")
FORTIGATE_PASSWORD = os.getenv("FORTIGATE_PASSWORD", "")
FORTIGATE_API_TOKEN = os.getenv("FORTIGATE_API_TOKEN", "")

class FortigateAPI:
    """Enhanced Fortigate API client with comprehensive endpoint support"""
    
    def __init__(self, host, username, password, api_token=""):
        self.host = host
        self.username = username
        self.password = password
        self.api_token = api_token
        self.session = requests.Session()
        self.session.verify = False
        
    def _get_headers(self):
        if self.api_token:
            return {"Authorization": f"Bearer {self.api_token}"}
        return {}
    
    def _make_request(self, method, endpoint, data=None, params=None):
        url = f"https://{self.host}/api/v2/{endpoint}"
        headers = self._get_headers()
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}

# Initialize API client
fortigate = FortigateAPI(FORTIGATE_HOST, FORTIGATE_USERNAME, FORTIGATE_PASSWORD, FORTIGATE_API_TOKEN)

''')
        
        # Generate resources by category
        for category, endpoint_keys in self.categories.items():
            code_parts.append(f'\n# {category.upper()} RESOURCES\n')
            
            for endpoint_key in endpoint_keys[:5]:  # Limit to 5 per category for now
                endpoint = self.endpoints[endpoint_key]
                resource_uri = f"fortinet://{category}/{endpoint_key.lower()}"
                
                code_parts.append(f'''
@mcp.resource("{resource_uri}")
async def {endpoint_key.lower()}_resource() -> str:
    """{endpoint.get('summary', 'API endpoint')} - {endpoint.get('description', '')[:100]}"""
    try:
        result = fortigate._make_request("{endpoint['method']}", "{endpoint['path'].replace('/api/v2/', '')}")
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error accessing {endpoint_key}: {{str(e)}}"
''')
        
        # Generate tools by category
        for category, endpoint_keys in self.categories.items():
            code_parts.append(f'\n# {category.upper()} TOOLS\n')
            
            # Create a general tool for each category
            code_parts.append(f'''
@mcp.tool()
async def get_{category}_info(endpoint: str = "status") -> str:
    """Get {category} information from various endpoints.
    
    Args:
        endpoint: Specific {category} endpoint to query
    """
    try:
        # Map common endpoint names to actual API paths
        endpoint_map = {{''')
            
            for endpoint_key in endpoint_keys[:10]:  # More endpoints in tools
                endpoint = self.endpoints[endpoint_key]
                simple_name = endpoint_key.split('_')[-1]
                code_parts.append(f'            "{simple_name}": "{endpoint["path"].replace("/api/v2/", "")}",')
            
            code_parts.append(f'''        }}
        
        api_path = endpoint_map.get(endpoint, f"monitor/{category}/{{endpoint}}")
        result = fortigate._make_request("GET", api_path)
        return f"{category.title()} {{endpoint}} Information:\\n{{json.dumps(result, indent=2)}}"
    except Exception as e:
        return f"Error getting {category} info: {{str(e)}}"
''')
        
        # Add main execution
        code_parts.append('''
# Prompts for comprehensive analysis
@mcp.prompt()
async def comprehensive_analysis_prompt(category: str = "system") -> str:
    """Generate a comprehensive analysis workflow for a specific category.
    
    Args:
        category: Category to analyze (system, firewall, network, etc.)
    """
    return f"""
Please perform a comprehensive analysis of the {category} configuration and status:

1. **Current Status Assessment**
   - Get current {category} status and health
   - Review configuration settings
   - Check for any alerts or issues

2. **Performance Analysis**
   - Analyze {category} performance metrics
   - Identify potential bottlenecks
   - Review resource utilization

3. **Security Review**
   - Check {category} security settings
   - Review access controls
   - Identify potential vulnerabilities

4. **Optimization Recommendations**
   - Suggest configuration improvements
   - Recommend performance optimizations
   - Provide security enhancements

Use the available {category} tools to gather this information systematically.
"""

if __name__ == "__main__":
    mcp.run()
''')
        
        return ''.join(code_parts)
    
    def save_generated_code(self, filename: str = "fortinet_comprehensive_server.py"):
        """Save the generated MCP code to a file"""
        code = self.generate_mcp_code()
        with open(filename, 'w') as f:
            f.write(code)
        print(f"Generated comprehensive server saved to {filename}")
    
    def create_endpoint_documentation(self) -> str:
        """Create documentation for all discovered endpoints"""
        doc_parts = []
        
        doc_parts.append("# Fortinet API Endpoints Documentation\n")
        doc_parts.append(f"Total endpoints discovered: {len(self.endpoints)}\n\n")
        
        for category, endpoint_keys in self.categories.items():
            doc_parts.append(f"## {category.upper()} ({len(endpoint_keys)} endpoints)\n\n")
            
            for endpoint_key in endpoint_keys:
                endpoint = self.endpoints[endpoint_key]
                doc_parts.append(f"### {endpoint_key}\n")
                doc_parts.append(f"- **Path**: `{endpoint['path']}`\n")
                doc_parts.append(f"- **Method**: `{endpoint['method']}`\n")
                doc_parts.append(f"- **Summary**: {endpoint.get('summary', 'N/A')}\n")
                doc_parts.append(f"- **Description**: {endpoint.get('description', 'N/A')[:200]}...\n")
                doc_parts.append(f"- **Source**: {endpoint['source_file']}\n\n")
        
        return ''.join(doc_parts)
    
    def print_summary(self):
        """Print a summary of discovered endpoints"""
        print(f"\n=== API PARSING SUMMARY ===")
        print(f"Total endpoints discovered: {len(self.endpoints)}")
        print(f"Categories found: {len(self.categories)}")
        
        for category, endpoints in self.categories.items():
            print(f"  {category}: {len(endpoints)} endpoints")
        
        print(f"\nTop 10 endpoints by category:")
        for category, endpoints in list(self.categories.items())[:5]:
            print(f"\n{category.upper()}:")
            for endpoint_key in endpoints[:5]:
                endpoint = self.endpoints[endpoint_key]
                print(f"  - {endpoint_key}: {endpoint['path']}")

def main():
    """Main function to parse API files and generate MCP server"""
    parser = FortinetAPIParser()
    
    print("Starting Fortinet API parsing...")
    parser.parse_api_files()
    
    if not parser.endpoints:
        print("No endpoints found. Please ensure your API JSON files are in the ./api_docs directory")
        return
    
    parser.print_summary()
    
    # Generate comprehensive server
    parser.save_generated_code()
    
    # Create documentation
    with open("api_endpoints_documentation.md", "w") as f:
        f.write(parser.create_endpoint_documentation())
    print("API documentation saved to api_endpoints_documentation.md")
    
    print("\nNext steps:")
    print("1. Review the generated fortinet_comprehensive_server.py")
    print("2. Test with: npx @modelcontextprotocol/inspector python fortinet_comprehensive_server.py")
    print("3. Customize the endpoints based on your specific needs")

if __name__ == "__main__":
    main()