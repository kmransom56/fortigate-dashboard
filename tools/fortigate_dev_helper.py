"""
FortiGate API Development Helper
Enhanced tools for FortiGate API development, testing, and debugging
"""

import requests
import json
import logging
import time
import urllib3
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import os
from dotenv import load_dotenv

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()

class FortiGateDevAPI:
    """Enhanced FortiGate API client for development and debugging"""
    
    def __init__(self, host: str = None, token: str = None, verify_ssl: bool = False):
        self.host = host or os.getenv('FORTIGATE_HOST', 'https://192.168.0.254')
        self.token = token or os.getenv('FORTIGATE_API_TOKEN')
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
        # Setup logging
        self.setup_logging()
        
        # API endpoints commonly used in development
        self.endpoints = {
            'system_status': '/api/v2/monitor/system/status',
            'system_interface': '/api/v2/monitor/system/interface',
            'system_performance': '/api/v2/monitor/system/performance',
            'dhcp_leases': '/api/v2/monitor/dhcp/leases',
            'arp_table': '/api/v2/monitor/system/arp',
            'firewall_policies': '/api/v2/cmdb/firewall/policy',
            'firewall_addresses': '/api/v2/cmdb/firewall/address',
            'system_config': '/api/v2/cmdb/system/global',
            'switch_managed': '/api/v2/monitor/switch-controller/managed-switch',
            'switch_ports': '/api/v2/monitor/switch-controller/switch-port',
            'detected_devices': '/api/v2/monitor/switch-controller/detected-device',
            'system_resources': '/api/v2/monitor/system/resource',
            'vpn_ssl': '/api/v2/monitor/vpn/ssl',
            'log_memory': '/api/v2/log/memory',
            'router_info': '/api/v2/monitor/router/lookup',
            'wifi_clients': '/api/v2/monitor/wifi/client'
        }
        
        # Common query parameters
        self.common_params = {
            'access_token': self.token,
            'format': 'json',
            'plain-text-password': '1'
        }
    
    def setup_logging(self):
        """Setup logging for API calls and debugging"""
        log_dir = Path('automation/logs')
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup main logger
        self.logger = logging.getLogger('FortiGateAPI')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_dir / 'fortigate_api.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # File handler for API calls only
        api_handler = logging.FileHandler(log_dir / 'api_calls.log')
        api_handler.setLevel(logging.INFO)
        api_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(api_handler)
        self.logger.addHandler(console_handler)
    
    def test_connection(self) -> Dict[str, Any]:
        """Enhanced connection test with detailed diagnostics"""
        result = {
            'success': False,
            'host': self.host,
            'timestamp': datetime.now().isoformat(),
            'response_time': None,
            'status_code': None,
            'error': None,
            'system_info': None
        }
        
        try:
            start_time = time.time()
            
            response = self.session.get(
                f"{self.host}{self.endpoints['system_status']}",
                params=self.common_params,
                timeout=10
            )
            
            end_time = time.time()
            result['response_time'] = round((end_time - start_time) * 1000, 2)  # ms
            result['status_code'] = response.status_code
            
            if response.status_code == 200:
                data = response.json()
                result['success'] = True
                result['system_info'] = {
                    'hostname': data.get('results', {}).get('hostname'),
                    'version': data.get('results', {}).get('version'),
                    'serial': data.get('results', {}).get('serial'),
                    'uptime': data.get('results', {}).get('uptime')
                }
                self.logger.info(f"✅ Connection successful - {result['response_time']}ms")
            else:
                result['error'] = f"HTTP {response.status_code}: {response.text}"
                self.logger.error(f"❌ Connection failed - {result['error']}")
                
        except requests.exceptions.Timeout:
            result['error'] = "Connection timeout"
            self.logger.error("❌ Connection timeout")
        except requests.exceptions.ConnectionError as e:
            result['error'] = f"Connection error: {str(e)}"
            self.logger.error(f"❌ Connection error: {str(e)}")
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            self.logger.error(f"❌ Unexpected error: {str(e)}")
        
        return result
    
    def make_request(self, endpoint: str, method: str = 'GET', 
                    params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Enhanced API request with comprehensive logging and error handling"""
        
        # Prepare parameters
        request_params = self.common_params.copy()
        if params:
            request_params.update(params)
        
        # Full URL
        url = f"{self.host}{endpoint}"
        
        # Log the request
        self.logger.info(f"🔄 {method} {endpoint}")
        if params:
            self.logger.debug(f"   Parameters: {params}")
        if data:
            self.logger.debug(f"   Data: {json.dumps(data, indent=2)}")
        
        result = {
            'success': False,
            'method': method,
            'endpoint': endpoint,
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'response_time': None,
            'status_code': None,
            'data': None,
            'error': None,
            'raw_response': None
        }
        
        try:
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=request_params, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=request_params, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, params=request_params, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=request_params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            end_time = time.time()
            result['response_time'] = round((end_time - start_time) * 1000, 2)
            result['status_code'] = response.status_code
            result['raw_response'] = response.text
            
            if response.status_code == 200:
                try:
                    result['data'] = response.json()
                    result['success'] = True
                    self.logger.info(f"✅ {method} {endpoint} - {result['response_time']}ms")
                except json.JSONDecodeError:
                    result['data'] = response.text
                    result['success'] = True
                    self.logger.info(f"✅ {method} {endpoint} - Non-JSON response")
            else:
                result['error'] = f"HTTP {response.status_code}: {response.text}"
                self.logger.error(f"❌ {method} {endpoint} - {result['error']}")
        
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"❌ {method} {endpoint} - Exception: {str(e)}")
        
        # Save detailed logs
        self.save_request_log(result)
        
        return result
    
    def save_request_log(self, result: Dict[str, Any]):
        """Save detailed request logs for debugging"""
        log_dir = Path('automation/logs/api_requests')
        log_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        endpoint_safe = result['endpoint'].replace('/', '_').replace('?', '_')
        filename = f"{timestamp}_{result['method']}_{endpoint_safe}.json"
        
        log_file = log_dir / filename
        with open(log_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
    
    def get_all_endpoints_status(self) -> Dict[str, Any]:
        """Test all common endpoints and return status"""
        results = {}
        
        self.logger.info("🔍 Testing all common endpoints...")
        
        for name, endpoint in self.endpoints.items():
            self.logger.info(f"Testing {name}...")
            result = self.make_request(endpoint)
            results[name] = {
                'success': result['success'],
                'status_code': result['status_code'],
                'response_time': result['response_time'],
                'error': result['error']
            }
            
            # Small delay between requests
            time.sleep(0.5)
        
        return results
    
    def export_api_responses(self, output_dir: str = 'automation/api_exports'):
        """Export responses from all endpoints for development reference"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for name, endpoint in self.endpoints.items():
            self.logger.info(f"Exporting {name}...")
            
            result = self.make_request(endpoint)
            
            if result['success'] and result['data']:
                filename = f"{timestamp}_{name}_response.json"
                filepath = output_path / filename
                
                with open(filepath, 'w') as f:
                    json.dump(result['data'], f, indent=2, default=str)
                
                self.logger.info(f"   Exported to {filepath}")
            else:
                self.logger.warning(f"   Failed to export {name}: {result['error']}")
            
            time.sleep(0.5)
    
    def monitor_endpoint(self, endpoint: str, interval: int = 30, duration: int = 300):
        """Monitor an endpoint for changes over time"""
        self.logger.info(f"📊 Monitoring {endpoint} every {interval}s for {duration}s")
        
        monitor_data = []
        start_time = time.time()
        
        while (time.time() - start_time) < duration:
            result = self.make_request(endpoint)
            
            monitor_entry = {
                'timestamp': datetime.now().isoformat(),
                'success': result['success'],
                'response_time': result['response_time'],
                'status_code': result['status_code']
            }
            
            if result['success']:
                # Store key metrics depending on endpoint
                if 'system/performance' in endpoint:
                    perf_data = result['data'].get('results', {})
                    monitor_entry['cpu_usage'] = perf_data.get('cpu')
                    monitor_entry['memory_usage'] = perf_data.get('memory')
                elif 'system/status' in endpoint:
                    status_data = result['data'].get('results', {})
                    monitor_entry['uptime'] = status_data.get('uptime')
            
            monitor_data.append(monitor_entry)
            
            self.logger.info(f"📈 Monitored at {monitor_entry['timestamp']} - "
                           f"Success: {monitor_entry['success']}, "
                           f"Response: {monitor_entry['response_time']}ms")
            
            time.sleep(interval)
        
        # Save monitoring results
        monitor_file = Path(f'automation/logs/monitoring_{endpoint.replace("/", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(monitor_file, 'w') as f:
            json.dump(monitor_data, f, indent=2)
        
        self.logger.info(f"📊 Monitoring completed. Results saved to {monitor_file}")
        return monitor_data
    
    def create_test_suite(self):
        """Create a comprehensive test suite for API validation"""
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'host': self.host,
            'tests': []
        }
        
        # Connection test
        connection_result = self.test_connection()
        test_results['tests'].append({
            'name': 'Connection Test',
            'passed': connection_result['success'],
            'details': connection_result
        })
        
        # Endpoint availability tests
        for name, endpoint in self.endpoints.items():
            result = self.make_request(endpoint)
            test_results['tests'].append({
                'name': f'Endpoint: {name}',
                'passed': result['success'],
                'response_time': result['response_time'],
                'status_code': result['status_code'],
                'error': result['error']
            })
            time.sleep(0.2)
        
        # Performance tests
        perf_result = self.make_request(self.endpoints['system_performance'])
        if perf_result['success']:
            perf_data = perf_result['data'].get('results', {})
            cpu_usage = perf_data.get('cpu', 0)
            memory_usage = perf_data.get('memory', 0)
            
            test_results['tests'].append({
                'name': 'Performance Check',
                'passed': cpu_usage < 80 and memory_usage < 80,
                'details': f"CPU: {cpu_usage}%, Memory: {memory_usage}%"
            })
        
        # Save test results
        test_file = Path(f'automation/logs/test_suite_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(test_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        passed_tests = sum(1 for test in test_results['tests'] if test['passed'])
        total_tests = len(test_results['tests'])
        
        self.logger.info(f"🧪 Test Suite Complete: {passed_tests}/{total_tests} tests passed")
        self.logger.info(f"📄 Results saved to {test_file}")
        
        return test_results

def main():
    """Main function for running the FortiGate API development helper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FortiGate API Development Helper')
    parser.add_argument('--test-connection', action='store_true', help='Test API connection')
    parser.add_argument('--test-all-endpoints', action='store_true', help='Test all endpoints')
    parser.add_argument('--export-responses', action='store_true', help='Export API responses')
    parser.add_argument('--monitor', type=str, help='Monitor endpoint (e.g., system/performance)')
    parser.add_argument('--test-suite', action='store_true', help='Run comprehensive test suite')
    parser.add_argument('--host', type=str, help='FortiGate host URL')
    parser.add_argument('--token', type=str, help='API token')
    
    args = parser.parse_args()
    
    # Initialize API client
    api = FortiGateDevAPI(host=args.host, token=args.token)
    
    if args.test_connection:
        result = api.test_connection()
        print(json.dumps(result, indent=2))
    
    elif args.test_all_endpoints:
        results = api.get_all_endpoints_status()
        print(json.dumps(results, indent=2))
    
    elif args.export_responses:
        api.export_api_responses()
    
    elif args.monitor:
        endpoint = f"/api/v2/monitor/{args.monitor}"
        api.monitor_endpoint(endpoint)
    
    elif args.test_suite:
        results = api.create_test_suite()
        print(f"Test Suite Results: {sum(1 for test in results['tests'] if test['passed'])}/{len(results['tests'])} passed")
    
    else:
        print("FortiGate API Development Helper")
        print("Available commands:")
        print("  --test-connection     Test API connection")
        print("  --test-all-endpoints  Test all common endpoints")
        print("  --export-responses    Export API responses for reference")
        print("  --monitor <endpoint>  Monitor endpoint changes")
        print("  --test-suite         Run comprehensive test suite")

if __name__ == '__main__':
    main()
