#!/usr/bin/env python3
"""
SNMP Store Connectivity Checker
Tests SNMPv3 connectivity across multiple store locations
"""

import subprocess
import json
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys

class SNMPChecker:
    def __init__(self, username, auth_password, priv_password, 
                 auth_protocol="SHA", priv_protocol="AES", timeout=10, retries=3):
        self.username = username
        self.auth_password = auth_password
        self.priv_password = priv_password
        self.auth_protocol = auth_protocol
        self.priv_protocol = priv_protocol
        self.timeout = timeout
        self.retries = retries
        
        # Common OIDs for testing
        self.test_oids = {
            "sysDescr": "1.3.6.1.2.1.1.1.0",      # System Description
            "sysUpTime": "1.3.6.1.2.1.1.3.0",     # System Uptime
            "sysName": "1.3.6.1.2.1.1.5.0"        # System Name
        }

    def test_snmp_device(self, device_info):
        """Test SNMP connectivity to a single device"""
        ip = device_info.get('ip')
        store_name = device_info.get('store_name', ip)
        device_type = device_info.get('device_type', 'Unknown')
        
        result = {
            'store_name': store_name,
            'ip': ip,
            'device_type': device_type,
            'status': 'FAILED',
            'response_time': None,
            'error': None,
            'system_info': {},
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Test with system description first (quick test)
            start_time = datetime.now()
            
            cmd = [
                'snmpget', '-v3',
                '-u', self.username,
                '-a', self.auth_protocol,
                '-A', self.auth_password,
                '-x', self.priv_protocol,
                '-X', self.priv_password,
                '-l', 'authPriv',
                '-t', str(self.timeout),
                '-r', str(self.retries),
                ip,
                self.test_oids['sysDescr']
            ]
            
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if process.returncode == 0:
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds()
                
                result['status'] = 'SUCCESS'
                result['response_time'] = round(response_time, 3)
                
                # Get additional system info if basic test succeeds
                self._get_system_info(ip, result)
                
            else:
                result['error'] = process.stderr.strip() or "SNMP query failed"
                
        except subprocess.TimeoutExpired:
            result['error'] = f"Timeout after {self.timeout} seconds"
        except FileNotFoundError:
            result['error'] = "snmpget command not found - install net-snmp-utils"
        except Exception as e:
            result['error'] = str(e)
            
        return result

    def _get_system_info(self, ip, result):
        """Get additional system information"""
        for info_name, oid in self.test_oids.items():
            try:
                cmd = [
                    'snmpget', '-v3',
                    '-u', self.username,
                    '-a', self.auth_protocol,
                    '-A', self.auth_password,
                    '-x', self.priv_protocol,
                    '-X', self.priv_password,
                    '-l', 'authPriv',
                    '-Oqv',  # Output format: quiet, value only
                    '-t', '5',
                    ip, oid
                ]
                
                process = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if process.returncode == 0:
                    value = process.stdout.strip().strip('"')
                    result['system_info'][info_name] = value
                    
            except Exception:
                # If additional info fails, don't mark the whole test as failed
                pass

    def check_stores(self, stores, max_workers=10):
        """Check SNMP connectivity for multiple stores concurrently"""
        results = []
        
        print(f"Testing SNMP connectivity for {len(stores)} devices...")
        print(f"Using credentials: {self.username} with {self.auth_protocol}+{self.priv_protocol}")
        print("-" * 80)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_store = {
                executor.submit(self.test_snmp_device, store): store 
                for store in stores
            }
            
            # Process completed tasks
            for future in as_completed(future_to_store):
                result = future.result()
                results.append(result)
                
                # Real-time progress update
                status_icon = "✓" if result['status'] == 'SUCCESS' else "✗"
                response_info = f"({result['response_time']}s)" if result['response_time'] else ""
                error_info = f" - {result['error']}" if result['error'] else ""
                
                print(f"{status_icon} {result['store_name']} ({result['ip']}) {response_info}{error_info}")
        
        return sorted(results, key=lambda x: x['store_name'])

    def generate_report(self, results, output_format='console'):
        """Generate reports in different formats"""
        
        if output_format == 'console':
            self._print_console_report(results)
        elif output_format == 'csv':
            self._save_csv_report(results)
        elif output_format == 'json':
            self._save_json_report(results)

    def _print_console_report(self, results):
        """Print detailed console report"""
        success_count = len([r for r in results if r['status'] == 'SUCCESS'])
        total_count = len(results)
        
        print("\n" + "="*80)
        print(f"SNMP CONNECTIVITY REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        print(f"Total Devices: {total_count}")
        print(f"Successful: {success_count}")
        print(f"Failed: {total_count - success_count}")
        print(f"Success Rate: {(success_count/total_count)*100:.1f}%")
        print("-"*80)
        
        # Successful connections
        print("\n✓ SUCCESSFUL CONNECTIONS:")
        for result in results:
            if result['status'] == 'SUCCESS':
                sys_name = result['system_info'].get('sysName', 'N/A')
                print(f"  {result['store_name']} ({result['ip']}) - {result['response_time']}s - {sys_name}")
        
        # Failed connections
        failed_results = [r for r in results if r['status'] == 'FAILED']
        if failed_results:
            print(f"\n✗ FAILED CONNECTIONS ({len(failed_results)}):")
            for result in failed_results:
                print(f"  {result['store_name']} ({result['ip']}) - {result['error']}")

    def _save_csv_report(self, results):
        """Save results to CSV file"""
        filename = f"snmp_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['store_name', 'ip', 'device_type', 'status', 'response_time', 
                         'error', 'sysName', 'sysDescr', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                row = {
                    'store_name': result['store_name'],
                    'ip': result['ip'],
                    'device_type': result['device_type'],
                    'status': result['status'],
                    'response_time': result['response_time'],
                    'error': result['error'],
                    'sysName': result['system_info'].get('sysName', ''),
                    'sysDescr': result['system_info'].get('sysDescr', ''),
                    'timestamp': result['timestamp']
                }
                writer.writerow(row)
        
        print(f"\nCSV report saved to: {filename}")

    def _save_json_report(self, results):
        """Save results to JSON file"""
        filename = f"snmp_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total_devices': len(results),
            'successful': len([r for r in results if r['status'] == 'SUCCESS']),
            'failed': len([r for r in results if r['status'] == 'FAILED']),
            'results': results
        }
        
        with open(filename, 'w') as jsonfile:
            json.dump(report_data, jsonfile, indent=2)
        
        print(f"\nJSON report saved to: {filename}")


def load_stores_from_csv(filename):
    """Load store list from CSV file"""
    stores = []
    try:
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                stores.append({
                    'store_name': row.get('store_name') or row.get('name'),
                    'ip': row.get('ip') or row.get('address'),
                    'device_type': row.get('device_type', 'Unknown')
                })
    except FileNotFoundError:
        print(f"Error: File {filename} not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    
    return stores


def main():
    parser = argparse.ArgumentParser(description='Test SNMP connectivity across multiple stores')
    parser.add_argument('--username', '-u', required=True, help='SNMPv3 username')
    parser.add_argument('--auth-password', '-A', required=True, help='Authentication password')
    parser.add_argument('--priv-password', '-X', required=True, help='Privacy password')
    parser.add_argument('--stores-csv', '-f', help='CSV file with store information')
    parser.add_argument('--output', '-o', choices=['console', 'csv', 'json'], 
                       default='console', help='Output format')
    parser.add_argument('--timeout', '-t', type=int, default=10, help='SNMP timeout (seconds)')
    parser.add_argument('--workers', '-w', type=int, default=10, help='Max concurrent workers')
    
    args = parser.parse_args()
    
    # Initialize checker
    checker = SNMPChecker(
        username=args.username,
        auth_password=args.auth_password,
        priv_password=args.priv_password,
        timeout=args.timeout
    )
    
    # Load stores
    if args.stores_csv:
        stores = load_stores_from_csv(args.stores_csv)
    else:
        # Example store list - replace with your actual stores
        stores = [
            {'store_name': 'ibue1pfntftg03', 'ip': '10.130.2.132', 'device_type': 'Fortigate'},
            {'store_name': 'IBR-BWW-00015', 'ip': '10.96.6.1', 'device_type': 'Fortigate'},
            # Add more stores here...
        ]
    
    if not stores:
        print("No stores to test. Please provide a CSV file or modify the script.")
        sys.exit(1)
    
    # Run tests
    results = checker.check_stores(stores, max_workers=args.workers)
    
    # Generate report
    checker.generate_report(results, output_format=args.output)


if __name__ == "__main__":
    main()