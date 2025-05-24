# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import paramiko
import time
import re
import ipaddress
import socket
import os
import json
import csv
from datetime import datetime
import threading
from functools import wraps
import secrets
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import warnings
import logging.handlers
import queue
import signal
import sys
import ssl
from OpenSSL import crypto
import redis

# Filter out cryptography deprecation warning
warnings.filterwarnings('ignore', category=DeprecationWarning, module='cryptography')

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, 
    template_folder=os.path.join(PROJECT_ROOT, 'app', 'templates'),
    static_folder=os.path.join(PROJECT_ROOT, 'app', 'static')
)
app.secret_key = secrets.token_hex(16)

# Configure Flask to handle socket errors during reload
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Load environment variables
load_dotenv()

# Always use logs directory at the project root
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'fortigate_troubleshooter.log')

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

# Helper functions for session storage
SESSION_PREFIX = 'ftg_session:'

def save_session(session_id, troubleshooter):
    # Serialize status and results only (not SSH client)
    try:
        data = {
            'status_messages': troubleshooter.status_messages,
            'results': troubleshooter.results,
            'progress': troubleshooter.progress,
            'is_connected': troubleshooter.is_connected,
            'is_running': troubleshooter.is_running,
            'error': troubleshooter.error,
            'fortigate_version': getattr(troubleshooter, 'fortigate_version', None),
            'completed_at': getattr(troubleshooter, 'completed_at', None),
        }
        
        # Log the data being saved for debugging
        app.logger.debug(f"Saving session {session_id} with results keys: {list(troubleshooter.results.keys())}")
        
        # Ensure all data is JSON serializable
        json_data = json.dumps(data, default=str)
        redis_client.set(SESSION_PREFIX + session_id, json_data)
    except Exception as e:
        app.logger.error(f"Error saving session to Redis: {str(e)}")

def load_session(session_id):
    try:
        data = redis_client.get(SESSION_PREFIX + session_id)
        if not data:
            app.logger.warning(f"No data found in Redis for session {session_id}")
            return None
        
        # Log the raw data for debugging
        app.logger.debug(f"Raw data from Redis for session {session_id}: {data[:200]}...")
        
        data = json.loads(data)
        
        # Log the parsed data for debugging
        app.logger.debug(f"Parsed data for session {session_id}, results keys: {list(data.get('results', {}).keys())}")
        
        # Create a dummy troubleshooter object for status/results
        t = type('DummyTroubleshooter', (), {})()
        t.status_messages = data.get('status_messages', [])
        t.results = data.get('results', {})
        t.progress = data.get('progress', 0)
        t.is_connected = data.get('is_connected', False)
        t.is_running = data.get('is_running', False)
        t.error = data.get('error', None)
        t.fortigate_version = data.get('fortigate_version', None)
        t.completed_at = data.get('completed_at', None)
        
        # Add method to the dummy object
        def add_status(self, message, level="info"):
            timestamp = datetime.now().strftime("%H:%M:%S")
            status_msg = {
                "time": timestamp,
                "message": message,
                "level": level
            }
            self.status_messages.append(status_msg)
            app.logger.info(f"[{timestamp}] {message}")
        
        t.add_status = add_status.__get__(t)
        
        return t
    except Exception as e:
        app.logger.error(f"Error loading session from Redis: {str(e)}")
        return None

def delete_session(session_id):
    redis_client.delete(SESSION_PREFIX + session_id)

# Brand configuration
BRANDS = {
    'arbys': {
        'name': 'Arbys',
        'password_env': 'FORTIGATE_PASSWORD_ARBYS',
        'csv_env': 'CSV_PATH_ARBYS',
        'default_csv': 'storelans-arbys.csv'
    },
    'bww': {
        'name': 'Buffalo Wild Wings',
        'password_env': 'FORTIGATE_PASSWORD_BWW',
        'csv_env': 'CSV_PATH_BWW',
        'default_csv': 'storelans-bww.csv'
    }
}

def get_brand_config(brand):
    """Get configuration for a specific brand."""
    if brand not in BRANDS:
        raise ValueError(f"Unsupported brand: {brand}")
    return BRANDS[brand]

def validate_store_number(store_number):
    """Validate the store number format (e.g., ARG00001)"""
    pattern = r'^ARG\d{5}$'
    if not re.match(pattern, store_number):
        raise ValueError(f"Invalid store number format. Expected format: ARG00001, got: {store_number}")
    return store_number

def get_store_info(store_number, brand='arbys'):
    """Get store information from CSV file.
    
    Args:
        store_number: The store number to look up, or None to get all stores
        brand: The brand to look up (default: 'arbys')
        
    Returns:
        If store_number is None, returns a list of all stores.
        If store_number is provided, returns a dictionary with store information.
    """
    brand_config = get_brand_config(brand)
    
    # Get CSV path from environment or use default
    csv_filename = os.getenv(brand_config['csv_env']) or brand_config['default_csv']
    csv_path = os.path.join(PROJECT_ROOT, csv_filename)
    
    # Check if we're requesting all stores
    if store_number is None:
        all_stores = []
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Defensive check for missing keys
                    if not all(key in row for key in ['store_number', 'ip_address', 'mgmtintname']):
                        app.logger.error(f"Malformed row in CSV: {row}")
                        continue
                    if not row['store_number'] or not row['ip_address'] or not row['mgmtintname']:
                        app.logger.error(f"Row with missing values in CSV: {row}")
                        continue
                    
                    all_stores.append({
                        'store_number': row['store_number'],
                        'ip_address': row['ip_address'],
                        'mgmtintname': row['mgmtintname'],
                        'brand': brand
                    })
            return all_stores
        except Exception as e:
            app.logger.error(f"Error reading CSV file {csv_path}: {str(e)}")
            return []
    
    # Validate store number for single store lookup
    store_number = validate_store_number(store_number)
    
    # Look up a specific store
    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Defensive check for missing keys
                if not all(key in row for key in ['store_number', 'ip_address', 'mgmtintname']):
                    app.logger.error(f"Malformed row in CSV: {row}")
                    continue
                if not row['store_number'] or not row['ip_address'] or not row['mgmtintname']:
                    app.logger.error(f"Row with missing values in CSV: {row}")
                    continue
                if row['store_number'] == store_number:
                    return {
                        'store_number': row['store_number'],
                        'ip_address': row['ip_address'],
                        'mgmtintname': row['mgmtintname'],
                        'brand': brand
                    }
        
        # If we get here, the store wasn't found
        app.logger.error(f"Store number {store_number} not found in CSV file for brand {brand_config['name']}")
        return None
    except Exception as e:
        app.logger.error(f"Error reading CSV file {csv_path}: {str(e)}")
        return None

class ThreadSafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, *args, **kwargs):
        # Initialize locks and attributes before parent class
        self._file_lock = threading.Lock()
        self._current_file = None
        self._current_size = 0
        self._last_rotation = 0
        self._rotation_interval = 300  # 5 minutes between rotation attempts
        self._error_count = 0
        self._max_errors = 3
        
        # Initialize queue and thread after parent class
        super().__init__(*args, **kwargs)
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self._process_logs, daemon=True)
        self.thread.start()
        self.lock = threading.Lock()

    def _open(self):
        """Override _open to use our custom file handling"""
        with self._file_lock:
            try:
                if self._current_file is None or self._current_file.closed:
                    self._current_file = open(self.baseFilename, 'a', encoding=self.encoding)
                    self._current_size = os.path.getsize(self.baseFilename)
                    self._error_count = 0  # Reset error count on successful open
                return self._current_file
            except Exception as e:
                self._error_count += 1
                if self._error_count >= self._max_errors:
                    raise RuntimeError(f"Failed to open log file after {self._max_errors} attempts: {e}")
                return None

    def _close(self):
        """Safely close the current file"""
        with self._file_lock:
            if self._current_file is not None and not self._current_file.closed:
                try:
                    self._current_file.flush()
                    self._current_file.close()
                except Exception as e:
                    print(f"Error closing log file: {e}", file=sys.stderr)
                finally:
                    self._current_file = None

    def _rotate_file(self):
        """Safely rotate the log file"""
        with self._file_lock:
            try:
                # Close current file
                self._close()
                
                # Rename existing files
                for i in range(self.backupCount - 1, 0, -1):
                    old = f"{self.baseFilename}.{i}"
                    new = f"{self.baseFilename}.{i + 1}"
                    if os.path.exists(old):
                        if os.path.exists(new):
                            os.remove(new)
                        os.rename(old, new)
                
                # Rename current file
                if os.path.exists(self.baseFilename):
                    new = f"{self.baseFilename}.1"
                    if os.path.exists(new):
                        os.remove(new)
                    os.rename(self.baseFilename, new)
                
                # Open new file
                self._open()
                self._current_size = 0
                self._last_rotation = time.time()
                self._error_count = 0  # Reset error count after successful rotation
                
            except Exception as e:
                print(f"Error rotating log file: {e}", file=sys.stderr)
                # If rotation fails, try to reopen the current file
                self._open()
                return False
            return True

    def _process_logs(self):
        while True:
            try:
                record = self.queue.get()
                if record is None:
                    break
                
                with self._file_lock:
                    # Check if we need to rotate
                    current_time = time.time()
                    if (current_time - self._last_rotation > self._rotation_interval and 
                        self._current_size >= self.maxBytes):
                        self._rotate_file()
                    
                    # Write the log record
                    try:
                        msg = self.format(record)
                        if self._current_file is None:
                            self._open()
                        if self._current_file is not None:
                            self._current_file.write(msg + '\n')
                            self._current_file.flush()
                            self._current_size += len(msg) + 1
                            self._error_count = 0  # Reset error count on successful write
                    except Exception as e:
                        self._error_count += 1
                        print(f"Error writing to log file: {e}", file=sys.stderr)
                        if self._error_count >= self._max_errors:
                            print("Maximum error count reached, attempting to reopen log file", file=sys.stderr)
                            self._close()
                            self._open()
                        
            except Exception as e:
                print(f"Error in log processing thread: {e}", file=sys.stderr)
                time.sleep(1)  # Prevent tight loop on errors

    def emit(self, record):
        try:
            self.queue.put(record)
        except Exception as e:
            print(f"Error queueing log record: {e}", file=sys.stderr)

    def close(self):
        try:
            self.queue.put(None)
            self.thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
            self._close()
        except Exception as e:
            print(f"Error closing logger: {e}", file=sys.stderr)

# Configure the logger with thread-safe handler
file_handler = ThreadSafeRotatingFileHandler(
    LOG_FILE,
    maxBytes=10485760,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s\n'
    '    File: %(pathname)s:%(lineno)d\n'
    '    Function: %(funcName)s\n'
    '    Thread: %(threadName)s\n'
    '    Process: %(processName)s\n'
    '----------------------------------------'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Add StreamHandler for console logging with a simpler format
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
))
console_handler.setLevel(logging.INFO)
app.logger.addHandler(console_handler)

# Log startup message
app.logger.info("FortiGate Troubleshooter application starting up")
app.logger.info(f"Log file location: {LOG_FILE}")
class FortiGateTroubleshooter:

    def run_network_diagnostics(self, target_host=None):
        """Run network diagnostics commands."""
        self.add_status("Running network diagnostics...")
        results = {}
        
        # Basic connectivity tests
        if target_host:
            results['execute_ping'] = self.execute_command(f'execute ping {target_host}')
            results['execute_traceroute'] = self.execute_command(f'execute traceroute {target_host}')
        
        # Enhanced routing information
        results['get_router_info_routing_table_all'] = self.execute_command('get router info routing-table all')
        results['diagnose_ip_route_list'] = self.execute_command('diagnose ip route list')
        results['diagnose_ip_rtcache_list'] = self.execute_command('diagnose ip rtcache list')
        
        # Interface and ARP information
        results['get_system_arp'] = self.execute_command('get system arp')
        results['get_system_interface'] = self.execute_command('get system interface')
        results['diagnose_netlink_interface_list'] = self.execute_command('diagnose netlink interface list')
        results['diagnose_netlink_aggregate_list'] = self.execute_command('diagnose netlink aggregate list')
        
        # DNS diagnostics
        results['diagnose_dns_proxy_list'] = self.execute_command('diagnose dns proxy list')
        results['diagnose_dns_proxy_statistics'] = self.execute_command('diagnose dns proxy statistics')
        
        self.results['network_diagnostics'] = results
        return results

    def run_session_table_and_flow_debug(self, source_ip=None, destination_ip=None):
        """Run session table and flow debug commands."""
        self.add_status("Running session table and flow debug...")
        results = {}
        
        # Clear existing filters
        self.execute_command('diagnose sys session filter clear')
        self.execute_command('diagnose debug flow filter clear')
        
        # Session table information
        results['diagnose_sys_session_list'] = self.execute_command('diagnose sys session list')
        results['diagnose_sys_session_list_verbose'] = self.execute_command('diagnose sys session list verbose')
        
        # Apply filters if provided
        if source_ip:
            self.execute_command(f'diagnose sys session filter src {source_ip}')
        if destination_ip:
            self.execute_command(f'diagnose sys session filter dst {destination_ip}')
        
        results['diagnose_sys_session_filter'] = self.execute_command('diagnose sys session filter')
        
        # Flow debug with enhanced output
        self.execute_command('diagnose debug reset')
        if source_ip:
            self.execute_command(f'diagnose debug flow filter addr {source_ip}')
        if destination_ip:
            self.execute_command(f'diagnose debug flow filter addr {destination_ip}')
        
        self.execute_command('diagnose debug flow show function-name enable')
        self.execute_command('diagnose debug flow trace start 10')
        self.execute_command('diagnose debug enable')
        
        # Wait for traffic capture
        time.sleep(5)
        results['diagnose_debug_flow'] = self.execute_command('diagnose debug disable')
        
        self.results['session_table_and_flow_debug'] = results
        return results

    def run_utm_and_webfiltering(self):
        """Run UTM and web filtering diagnostics."""
        self.add_status("Running UTM and web filtering diagnostics...")
        results = {}
        
        # Web filter diagnostics
        results['diagnose_webfilter_fortiguard_categories'] = self.execute_command('diagnose webfilter fortiguard categories')
        results['diagnose_webfilter_fortiguard_statistics'] = self.execute_command('diagnose webfilter fortiguard statistics')
        results['diagnose_webfilter_urlfilter_statistics'] = self.execute_command('diagnose webfilter urlfilter statistics')
        
        # Application debugging
        results['diagnose_debug_application_dnsproxy'] = self.execute_command('diagnose debug application dnsproxy -1')
        results['diagnose_debug_application_urlfilter'] = self.execute_command('diagnose debug application urlfilter -1')
        results['diagnose_debug_application_webfilter'] = self.execute_command('diagnose debug application webfilter -1')
        
        # Log analysis
        self.execute_command('execute log filter category all')
        self.execute_command('execute log filter severity warning')
        results['execute_log_display'] = self.execute_command('execute log display last 100')
        results['execute_log_filter'] = self.execute_command('execute log filter category utm-webfilter')
        
        self.results['utm_and_webfiltering'] = results
        return results

    def run_vpn_and_authentication(self):
        """Run VPN and authentication diagnostics."""
        self.add_status("Running VPN and authentication diagnostics...")
        results = {}
        
        # VPN diagnostics
        results['diagnose_vpn_ike_gateway_list'] = self.execute_command('diagnose vpn ike gateway list')
        results['diagnose_vpn_tunnel_list'] = self.execute_command('diagnose vpn tunnel list')
        results['diagnose_vpn_ssl_statistics'] = self.execute_command('diagnose vpn ssl statistics')
        
        # Authentication debugging
        results['diagnose_debug_application_fnbamd'] = self.execute_command('diagnose debug application fnbamd -1')
        results['diagnose_debug_application_sslvpn'] = self.execute_command('diagnose debug application sslvpn -1')
        
        self.results['vpn_and_authentication'] = results
        return results

    def run_hardware_and_ha(self):
        """Run hardware and high availability diagnostics."""
        self.add_status("Running hardware and HA diagnostics...")
        results = {}
        
        # HA status
        results['get_system_ha_status'] = self.execute_command('get system ha status')
        results['diagnose_sys_ha_status'] = self.execute_command('diagnose sys ha status')
        
        # Hardware diagnostics
        results['diagnose_hardware_deviceinfo'] = self.execute_command('diagnose hardware deviceinfo disk')
        results['diagnose_hardware_deviceinfo_nic'] = self.execute_command('diagnose hardware deviceinfo nic')
        results['diagnose_hardware_deviceinfo_memory'] = self.execute_command('diagnose hardware deviceinfo memory')
        results['diagnose_hardware_deviceinfo_temperature'] = self.execute_command('diagnose hardware deviceinfo temperature')
        results['diagnose_hardware_deviceinfo_fan'] = self.execute_command('diagnose hardware deviceinfo fan')
        
        self.results['hardware_and_ha'] = results
        return results

    def run_full_diagnostics(self, target_host=None, source_ip=None, destination_ip=None):
        """Run all diagnostic sections."""
        self.run_system_diagnostics()
        self.run_network_diagnostics(target_host=target_host)
        self.run_session_table_and_flow_debug(source_ip=source_ip, destination_ip=destination_ip)
        self.run_utm_and_webfiltering()
        self.run_vpn_and_authentication()
        self.run_hardware_and_ha()
        self.add_status("Full diagnostics completed.", "success")
    def run_full_test(self, target, source_ip=None, policy_id=None):
        """Run a complete troubleshooting test for a target."""
        self.is_running = True
        self.add_status(f"Starting full connectivity test to {target}...")
        self.progress = 10
        
        try:
            # Determine if target is hostname or IP
            try:
                ipaddress.ip_address(target)
                is_ip = True
                hostname = None
                ip_address = target
            except ValueError:
                is_ip = False
                hostname = target
                ip_address = None
            
            # Step 1: DNS resolution (if target is a hostname)
            if not is_ip:
                dns_success, resolved_ips = self.test_dns_resolution(hostname)
                if dns_success and resolved_ips:
                    ip_address = resolved_ips[0]
            
            # Step 2: Ping test
            ping_success = self.test_ping(target, source_ip)
            
            # Step 3: Check firewall policy
            webfilter_enabled, webfilter_profile = self.check_firewall_policy(policy_id)
            
            # Step 4: Check web filter config if enabled
            if webfilter_enabled and webfilter_profile:
                urlfilter_output = self.check_webfilter_config(webfilter_profile)
            
            # Step 5: Check web filter logs
            block_count, pass_count, blocked_reason = self.check_webfilter_logs(
                target_ip=ip_address if is_ip else None,
                target_host=hostname if not is_ip else None
            )
            
            # Step 6: Debug flow traffic
            if source_ip and ip_address:
                debug_output = self.debug_flow_traffic(source_ip, ip_address, "tcp")
            
            # Step 7: Generate suggestions
            suggestions = self.suggest_fixes()
            
            self.progress = 100
            self.add_status("Troubleshooting completed successfully.", "success")
            
            return self.results, suggestions
            
        except Exception as e:
            self.add_status(f"Error during troubleshooting: {str(e)}", "error")
            self.error = str(e)
            return None, None
        finally:
            self.is_running = False

    def run_system_diagnostics(self):
        """Run system diagnostics commands."""
        self.add_status("Running system diagnostics...")
        results = {}
        
        # Basic system status
        results['get_system_status'] = self.execute_command('get system status')
        results['get_system_performance_status'] = self.execute_command('get system performance status')
        
        # Enhanced system diagnostics
        results['diagnose_sys_top'] = self.execute_command('diagnose sys top 5 3')  # 5 seconds, 3 times
        results['diagnose_sys_top_mem'] = self.execute_command('diagnose sys top-mem 5 3')
        results['diagnose_sys_session_stat'] = self.execute_command('diagnose sys session stat')
        results['diagnose_sys_ha_status'] = self.execute_command('diagnose sys ha status')
        results['diagnose_sys_link_monitor_status'] = self.execute_command('diagnose sys link-monitor status')
        
        # Hardware diagnostics
        results['diagnose_hardware_deviceinfo_disk'] = self.execute_command('diagnose hardware deviceinfo disk')
        results['diagnose_hardware_deviceinfo_nic'] = self.execute_command('diagnose hardware deviceinfo nic')
        results['diagnose_hardware_deviceinfo_memory'] = self.execute_command('diagnose hardware deviceinfo memory')
        results['diagnose_hardware_deviceinfo_temperature'] = self.execute_command('diagnose hardware deviceinfo temperature')
        results['diagnose_hardware_deviceinfo_fan'] = self.execute_command('diagnose hardware deviceinfo fan')
        
        self.results['system_diagnostics'] = results
        return results

    def run_network_diagnostics(self, target_host=None):
        """Run network diagnostics commands."""
        self.add_status("Running network diagnostics...")
        results = {}
        
        # Basic connectivity tests
        if target_host:
            results['execute_ping'] = self.execute_command(f'execute ping {target_host}')
            results['execute_traceroute'] = self.execute_command(f'execute traceroute {target_host}')
        
        # Enhanced routing information
        results['get_router_info_routing_table_all'] = self.execute_command('get router info routing-table all')
        results['diagnose_ip_route_list'] = self.execute_command('diagnose ip route list')
        results['diagnose_ip_rtcache_list'] = self.execute_command('diagnose ip rtcache list')
        
        # Interface and ARP information
        results['get_system_arp'] = self.execute_command('get system arp')
        results['get_system_interface'] = self.execute_command('get system interface')
        results['diagnose_netlink_interface_list'] = self.execute_command('diagnose netlink interface list')
        results['diagnose_netlink_aggregate_list'] = self.execute_command('diagnose netlink aggregate list')
        
        # DNS diagnostics
        results['diagnose_dns_proxy_list'] = self.execute_command('diagnose dns proxy list')
        results['diagnose_dns_proxy_statistics'] = self.execute_command('diagnose dns proxy statistics')
        
        self.results['network_diagnostics'] = results
        return results

    def run_session_table_and_flow_debug(self, source_ip=None, destination_ip=None):
        """Run session table and flow debug commands."""
        self.add_status("Running session table and flow debug...")
        results = {}
        
        # Clear existing filters
        self.execute_command('diagnose sys session filter clear')
        self.execute_command('diagnose debug flow filter clear')
        
        # Session table information
        results['diagnose_sys_session_list'] = self.execute_command('diagnose sys session list')
        results['diagnose_sys_session_list_verbose'] = self.execute_command('diagnose sys session list verbose')
        
        # Apply filters if provided
        if source_ip:
            self.execute_command(f'diagnose sys session filter src {source_ip}')
        if destination_ip:
            self.execute_command(f'diagnose sys session filter dst {destination_ip}')
        
        results['diagnose_sys_session_filter'] = self.execute_command('diagnose sys session filter')
        
        # Flow debug with enhanced output
        self.execute_command('diagnose debug reset')
        if source_ip:
            self.execute_command(f'diagnose debug flow filter addr {source_ip}')
        if destination_ip:
            self.execute_command(f'diagnose debug flow filter addr {destination_ip}')
        
        self.execute_command('diagnose debug flow show function-name enable')
        self.execute_command('diagnose debug flow trace start 10')
        self.execute_command('diagnose debug enable')
        
        # Wait for traffic capture
        time.sleep(5)
        results['diagnose_debug_flow'] = self.execute_command('diagnose debug disable')
        
        self.results['session_table_and_flow_debug'] = results
        return results

    # Add this method to your FortiGateTroubleshooter class
# Make sure it's properly indented as part of the class!

class FortiGateTroubleshooter:
    # ... existing methods ...
    
    def run_utm_and_webfiltering(self):
        """Run UTM and web filtering diagnostics."""
        self.add_status("Running UTM and web filtering diagnostics...")
        results = {}
        
        # Web filter diagnostics
        self.add_status("Checking web filter FortiGuard categories...", "info")
        results['diagnose_webfilter_fortiguard_categories'] = self.execute_command('diagnose webfilter fortiguard categories')
        
        self.add_status("Checking web filter FortiGuard statistics...", "info")
        results['diagnose_webfilter_fortiguard_statistics'] = self.execute_command('diagnose webfilter fortiguard statistics')
        
        self.add_status("Checking URL filter statistics...", "info")
        results['diagnose_webfilter_urlfilter_statistics'] = self.execute_command('diagnose webfilter urlfilter statistics')
        
        # Application debugging
        self.add_status("Enabling DNS proxy debugging...", "info")
        results['diagnose_debug_application_dnsproxy'] = self.execute_command('diagnose debug application dnsproxy -1')
        
        self.add_status("Enabling URL filter debugging...", "info")
        results['diagnose_debug_application_urlfilter'] = self.execute_command('diagnose debug application urlfilter -1')
        
        self.add_status("Enabling web filter debugging...", "info")
        results['diagnose_debug_application_webfilter'] = self.execute_command('diagnose debug application webfilter -1')
        
        # Log analysis
        self.add_status("Setting up log filters...", "info")
        self.execute_command('execute log filter category all')
        self.execute_command('execute log filter severity warning')
        
        self.add_status("Retrieving system logs...", "info")
        results['execute_log_display'] = self.execute_command('execute log display last 100')
        
        self.add_status("Applying UTM web filter log filter...", "info")
        results['execute_log_filter'] = self.execute_command('execute log filter category utm-webfilter')
        
        # Store results in the main results dictionary
        self.results['utm_and_webfiltering'] = results
        
        # Count successful results
        successful_commands = sum(1 for v in results.values() if v and len(str(v).strip()) > 0)
        self.add_status(f"UTM diagnostics completed. {successful_commands}/{len(results)} commands returned data.", "info")
        
        return results

    def run_system_diagnostics(self):
        """Run system diagnostics commands."""
        self.add_status("Running system diagnostics...")
        results = {}
        
        # Basic system status
        self.add_status("Getting system status...", "info")
        results['get_system_status'] = self.execute_command('get system status')
        
        self.add_status("Getting system performance status...", "info")
        results['get_system_performance_status'] = self.execute_command('get system performance status')
        
        # Enhanced system diagnostics
        self.add_status("Running system top...", "info")
        results['diagnose_sys_top'] = self.execute_command('diagnose sys top 5 3')  # 5 seconds, 3 times
        
        self.add_status("Running system memory top...", "info")
        results['diagnose_sys_top_mem'] = self.execute_command('diagnose sys top-mem 5 3')
        
        self.add_status("Getting session statistics...", "info")
        results['diagnose_sys_session_stat'] = self.execute_command('diagnose sys session stat')
        
        self.add_status("Getting HA status...", "info")
        results['diagnose_sys_ha_status'] = self.execute_command('diagnose sys ha status')
        
        self.add_status("Getting link monitor status...", "info")
        results['diagnose_sys_link_monitor_status'] = self.execute_command('diagnose sys link-monitor status')
        
        # Hardware diagnostics
        self.add_status("Getting hardware disk info...", "info")
        results['diagnose_hardware_deviceinfo_disk'] = self.execute_command('diagnose hardware deviceinfo disk')
        
        self.add_status("Getting hardware NIC info...", "info")
        results['diagnose_hardware_deviceinfo_nic'] = self.execute_command('diagnose hardware deviceinfo nic')
        
        self.add_status("Getting hardware memory info...", "info")
        results['diagnose_hardware_deviceinfo_memory'] = self.execute_command('diagnose hardware deviceinfo memory')
        
        self.add_status("Getting hardware temperature info...", "info")
        results['diagnose_hardware_deviceinfo_temperature'] = self.execute_command('diagnose hardware deviceinfo temperature')
        
        self.add_status("Getting hardware fan info...", "info")
        results['diagnose_hardware_deviceinfo_fan'] = self.execute_command('diagnose hardware deviceinfo fan')
        
        self.results['system_diagnostics'] = results
        
        # Count successful results
        successful_commands = sum(1 for v in results.values() if v and len(str(v).strip()) > 0)
        self.add_status(f"System diagnostics completed. {successful_commands}/{len(results)} commands returned data.", "info")
        
        return results

    def run_network_diagnostics(self, target_host=None):
        """Run network diagnostics commands."""
        self.add_status("Running network diagnostics...")
        results = {}
        
        # Basic connectivity tests
        if target_host:
            self.add_status(f"Testing ping to {target_host}...", "info")
            results['execute_ping'] = self.execute_command(f'execute ping {target_host}')
            
            self.add_status(f"Running traceroute to {target_host}...", "info")
            results['execute_traceroute'] = self.execute_command(f'execute traceroute {target_host}')
        
        # Enhanced routing information
        self.add_status("Getting routing table...", "info")
        results['get_router_info_routing_table_all'] = self.execute_command('get router info routing-table all')
        
        self.add_status("Getting IP route list...", "info")
        results['diagnose_ip_route_list'] = self.execute_command('diagnose ip route list')
        
        self.add_status("Getting IP route cache...", "info")
        results['diagnose_ip_rtcache_list'] = self.execute_command('diagnose ip rtcache list')
        
        # Interface and ARP information
        self.add_status("Getting ARP table...", "info")
        results['get_system_arp'] = self.execute_command('get system arp')
        
        self.add_status("Getting system interfaces...", "info")
        results['get_system_interface'] = self.execute_command('get system interface')
        
        self.add_status("Getting netlink interface list...", "info")
        results['diagnose_netlink_interface_list'] = self.execute_command('diagnose netlink interface list')
        
        self.add_status("Getting netlink aggregate list...", "info")
        results['diagnose_netlink_aggregate_list'] = self.execute_command('diagnose netlink aggregate list')
        
        # DNS diagnostics
        self.add_status("Getting DNS proxy list...", "info")
        results['diagnose_dns_proxy_list'] = self.execute_command('diagnose dns proxy list')
        
        self.add_status("Getting DNS proxy statistics...", "info")
        results['diagnose_dns_proxy_statistics'] = self.execute_command('diagnose dns proxy statistics')
        
        self.results['network_diagnostics'] = results
        
        # Count successful results
        successful_commands = sum(1 for v in results.values() if v and len(str(v).strip()) > 0)
        self.add_status(f"Network diagnostics completed. {successful_commands}/{len(results)} commands returned data.", "info")
        
        return results

    def run_session_table_and_flow_debug(self, source_ip=None, destination_ip=None):
        """Run session table and flow debug commands."""
        self.add_status("Running session table and flow debug...")
        results = {}
        
        # Clear existing filters
        self.execute_command('diagnose sys session filter clear')
        self.execute_command('diagnose debug flow filter clear')
        
        # Session table information
        self.add_status("Getting session list...", "info")
        results['diagnose_sys_session_list'] = self.execute_command('diagnose sys session list')
        
        self.add_status("Getting verbose session list...", "info")
        results['diagnose_sys_session_list_verbose'] = self.execute_command('diagnose sys session list verbose')
        
        # Apply filters if provided
        if source_ip:
            self.add_status(f"Applying source IP filter: {source_ip}", "info")
            self.execute_command(f'diagnose sys session filter src {source_ip}')
        if destination_ip:
            self.add_status(f"Applying destination IP filter: {destination_ip}", "info")
            self.execute_command(f'diagnose sys session filter dst {destination_ip}')
        
        results['diagnose_sys_session_filter'] = self.execute_command('diagnose sys session filter')
        
        # Flow debug with enhanced output
        self.add_status("Setting up flow debug...", "info")
        self.execute_command('diagnose debug reset')
        if source_ip:
            self.execute_command(f'diagnose debug flow filter addr {source_ip}')
        if destination_ip:
            self.execute_command(f'diagnose debug flow filter addr {destination_ip}')
        
        self.execute_command('diagnose debug flow show function-name enable')
        self.execute_command('diagnose debug flow trace start 10')
        self.execute_command('diagnose debug enable')
        
        # Wait for traffic capture
        self.add_status("Waiting for traffic capture (5 seconds)...", "info")
        time.sleep(5)
        results['diagnose_debug_flow'] = self.execute_command('diagnose debug disable')
        
        self.results['session_table_and_flow_debug'] = results
        
        # Count successful results
        successful_commands = sum(1 for v in results.values() if v and len(str(v).strip()) > 0)
        self.add_status(f"Session and flow debug completed. {successful_commands}/{len(results)} commands returned data.", "info")
        
        return results

    def run_vpn_and_authentication(self):
        """Run VPN and authentication diagnostics."""
        self.add_status("Running VPN and authentication diagnostics...")
        results = {}
        
        # VPN diagnostics
        self.add_status("Getting VPN IKE gateway list...", "info")
        results['diagnose_vpn_ike_gateway_list'] = self.execute_command('diagnose vpn ike gateway list')
        
        self.add_status("Getting VPN tunnel list...", "info")
        results['diagnose_vpn_tunnel_list'] = self.execute_command('diagnose vpn tunnel list')
        
        self.add_status("Getting SSL VPN statistics...", "info")
        results['diagnose_vpn_ssl_statistics'] = self.execute_command('diagnose vpn ssl statistics')
        
        # Authentication debugging
        self.add_status("Enabling authentication debugging...", "info")
        results['diagnose_debug_application_fnbamd'] = self.execute_command('diagnose debug application fnbamd -1')
        
        self.add_status("Enabling SSL VPN debugging...", "info")
        results['diagnose_debug_application_sslvpn'] = self.execute_command('diagnose debug application sslvpn -1')
        
        self.results['vpn_and_authentication'] = results
        
        # Count successful results
        successful_commands = sum(1 for v in results.values() if v and len(str(v).strip()) > 0)
        self.add_status(f"VPN and authentication diagnostics completed. {successful_commands}/{len(results)} commands returned data.", "info")
        
        return results

    def run_hardware_and_ha(self):
        """Run hardware and high availability diagnostics."""
        self.add_status("Running hardware and HA diagnostics...")
        results = {}
        
        # HA status
        self.add_status("Getting HA status...", "info")
        results['get_system_ha_status'] = self.execute_command('get system ha status')
        results['diagnose_sys_ha_status'] = self.execute_command('diagnose sys ha status')
        
        # Hardware diagnostics
        self.add_status("Getting hardware disk info...", "info")
        results['diagnose_hardware_deviceinfo'] = self.execute_command('diagnose hardware deviceinfo disk')
        
        self.add_status("Getting hardware NIC info...", "info")
        results['diagnose_hardware_deviceinfo_nic'] = self.execute_command('diagnose hardware deviceinfo nic')
        
        self.add_status("Getting hardware memory info...", "info")
        results['diagnose_hardware_deviceinfo_memory'] = self.execute_command('diagnose hardware deviceinfo memory')
        
        self.add_status("Getting hardware temperature info...", "info")
        results['diagnose_hardware_deviceinfo_temperature'] = self.execute_command('diagnose hardware deviceinfo temperature')
        
        self.add_status("Getting hardware fan info...", "info")
        results['diagnose_hardware_deviceinfo_fan'] = self.execute_command('diagnose hardware deviceinfo fan')
        
        self.results['hardware_and_ha'] = results
        
        # Count successful results
        successful_commands = sum(1 for v in results.values() if v and len(str(v).strip()) > 0)
        self.add_status(f"Hardware and HA diagnostics completed. {successful_commands}/{len(results)} commands returned data.", "info")
        
        return results

    def run_full_diagnostics(self, target_host=None, source_ip=None, destination_ip=None):
        """Run all diagnostic sections."""
        self.add_status("Starting full diagnostics...", "info")
        
        self.run_system_diagnostics()
        self.run_network_diagnostics(target_host=target_host)
        self.run_session_table_and_flow_debug(source_ip=source_ip, destination_ip=destination_ip)
        self.run_utm_and_webfiltering()
        self.run_vpn_and_authentication()
        self.run_hardware_and_ha()
        
        self.add_status("Full diagnostics completed.", "success")

    def auto_run_diagnostics(self):
        """Automatically run diagnostics based on output patterns."""
        if not hasattr(self, '_automation_run'):
            self._automation_run = set()
        # Example: If ping fails, run session/flow debug
        net_diag = self.results.get('network_diagnostics', {})
        if 'network_ping_auto' not in self._automation_run:
            ping_out = net_diag.get('execute_ping', '')
            if ping_out and ('100% packet loss' in ping_out or 'unreachable' in ping_out):
                self.add_status('Ping failed, auto-running session table and flow debug...', 'warning')
                self.run_session_table_and_flow_debug()
                self._automation_run.add('network_ping_auto')
        # Example: If flow debug shows denied, run policy check
        flow_diag = self.results.get('session_table_and_flow_debug', {})
        if 'flow_denied_auto' not in self._automation_run:
            flow_out = flow_diag.get('diagnose_debug_flow', '')
            if flow_out and re.search(r'denied', flow_out, re.IGNORECASE):
                self.add_status('Flow debug shows denied, auto-running firewall policy check...', 'warning')
                self.check_firewall_policy()
                self._automation_run.add('flow_denied_auto')
        # Add more automation rules as needed

    def export_results_text(self):
        """Export results as a text file."""
        output = "FortiGate Diagnostics Results\n============================\n"
        for section, content in self.results.items():
            output += f"\n## {section.replace('_', ' ').title()}\n"
            if isinstance(content, dict):
                for key, value in content.items():
                    output += f"{key}:\n{value}\n"
            else:
                output += f"{content}\n"
        return output

    def export_results_csv(self):
        """Export results as CSV (flat key-value)."""
        import io, csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Section', 'Key', 'Value'])
        for section, content in self.results.items():
            if isinstance(content, dict):
                for key, value in content.items():
                    writer.writerow([section, key, value])
            else:
                writer.writerow([section, '', content])
        return output.getvalue()
# Add this route to your Flask app to verify the methods exist

def background_task(session_id, store_number, brand, port, target, source_ip, policy_id, diagnostics):
    """Run troubleshooting in a background thread."""
    try:
        # Create troubleshooter instance
        troubleshooter = FortiGateTroubleshooter(
            store_number=store_number,
            brand=brand,
            port=port
        )
        
        # Update session immediately
        save_session(session_id, troubleshooter)
        
        # Log selected diagnostics
        app.logger.info(f"Running diagnostics: {diagnostics}")
        
        # Attempt connection
        if not troubleshooter.connect():
            troubleshooter.add_status("Failed to connect to device", "error")
            return
        
        # Run only the selected diagnostics
        if not diagnostics:  # If no diagnostics selected
            troubleshooter.add_status("No diagnostics selected. Connection successful.", "success")
        elif 'full' in diagnostics:
            troubleshooter.run_full_diagnostics(target_host=target, source_ip=source_ip, destination_ip=None)
        else:
            if 'system' in diagnostics:
                troubleshooter.run_system_diagnostics()
            if 'network' in diagnostics:
                net_results = troubleshooter.run_network_diagnostics(target_host=target)
                # If ping fails, run session/flow debug automatically
                if net_results and 'execute_ping' in net_results and net_results['execute_ping'] and '100% packet loss' in net_results['execute_ping']:
                    troubleshooter.add_status("Ping failed, running additional diagnostics...", "warning")
                    troubleshooter.run_session_table_and_flow_debug(source_ip=source_ip, destination_ip=None)
            if 'session' in diagnostics:
                troubleshooter.run_session_table_and_flow_debug(source_ip=source_ip, destination_ip=None)
            if 'utm' in diagnostics:
                troubleshooter.run_utm_and_webfiltering()
            if 'vpn' in diagnostics:
                troubleshooter.run_vpn_and_authentication()
            if 'hardware' in diagnostics:
                troubleshooter.run_hardware_and_ha()
        
        # Mark as complete
        troubleshooter.progress = 100
        troubleshooter.is_running = False
        troubleshooter.completed_at = time.time()
        troubleshooter.add_status("Test completed successfully", "success")
        
        # Update session
        save_session(session_id, troubleshooter)
        
    except Exception as e:
        app.logger.error(f"Background task error: {str(e)}")
        # Load the session from Redis
        troubleshooter = load_session(session_id)
        if troubleshooter:
            troubleshooter.add_status(f"Error: {str(e)}", "error")
            troubleshooter.error = str(e)
            troubleshooter.is_running = False
            troubleshooter.completed_at = time.time()
            # Save the updated session back to Redis
            save_session(session_id, troubleshooter)

@app.route('/')
def index():
    """Render the main page."""
    # Get list of stores from CSV for each brand
    stores = {}
    for brand, config in BRANDS.items():
        try:
            csv_filename = os.getenv(config['csv_env']) or config['default_csv']
            csv_path = os.path.join(PROJECT_ROOT, csv_filename)
            app.logger.info(f"Reading CSV file from: {csv_path}")
            
            brand_stores = []
            with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                app.logger.info(f"CSV fieldnames: {reader.fieldnames}")
                
                # Verify required columns exist
                required_columns = ['store_number', 'ip_address']
                if not all(col in reader.fieldnames for col in required_columns):
                    missing_columns = [col for col in required_columns if col not in reader.fieldnames]
                    app.logger.error(f"Missing columns in CSV: {missing_columns}")
                    raise ValueError(f"CSV file must contain columns: {', '.join(required_columns)}")
                
                for row in reader:
                    if row['store_number'] and row['ip_address']:  # Only add if both fields have values
                        brand_stores.append({
                            'store_number': row['store_number'].strip(),
                            'ip_address': row['ip_address'].strip()
                        })
            
            stores[brand] = brand_stores
            
        except FileNotFoundError:
            app.logger.error(f"CSV file not found for brand {config['name']}")
            flash(f"Store list file not found for {config['name']}", "error")
        except Exception as e:
            app.logger.error(f"Error reading store list for {config['name']}: {str(e)}")
            flash(f"Error loading store list for {config['name']}: {str(e)}", "error")
    
    return render_template('index.html', stores=stores, brands=BRANDS)

@app.route('/start_test', methods=['POST'])
def start_test():
    """Start a troubleshooting test."""
    try:
        # Get form data
        store_number = request.form.get('store_number')
        brand = request.form.get('brand', 'arbys')
        if not store_number:
            raise ValueError("Store number is required")
        
        # Validate store number
        validate_store_number(store_number)
        
        port = int(request.form.get('port', 222))
        target = request.form.get('target')
        source_ip = request.form.get('source_ip') or None
        policy_id = request.form.get('policy_id') or None
        
        # Handle diagnostics selection
        diagnostics = request.form.get('diagnostics')
        app.logger.info(f"Received diagnostics: {diagnostics}")  # Debug log
        
        if diagnostics:
            try:
                # Try to parse as JSON array
                if diagnostics.startswith('[') and diagnostics.endswith(']'):
                    diagnostics = json.loads(diagnostics)
                else:
                    # If not JSON array, treat as single diagnostic string
                    diagnostics = [diagnostics]
                app.logger.info(f"Parsed diagnostics: {diagnostics}")  # Debug log
            except Exception as e:
                app.logger.error(f"Error parsing diagnostics JSON: {e}")
                # Fallback: treat as single diagnostic string
                diagnostics = [diagnostics]
        else:
            diagnostics = []
        
        # Create a unique session ID
        session_id = secrets.token_hex(8)
        
        # Do not save a placeholder session; session will be saved after troubleshooter is created
        # save_session(session_id, None)
        
        # Start the background task
        thread = threading.Thread(
            target=background_task,
            args=(session_id, store_number, brand, port, target, source_ip, policy_id, diagnostics)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Test started successfully'
        })
        
    except ValueError as e:
        app.logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
    except Exception as e:
        app.logger.error(f"Error starting test: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/test_status/<session_id>')
def test_status(session_id):
    """Get the status of a running test."""
    try:
        # Check if session exists in Redis
        if not redis_client.exists(SESSION_PREFIX + session_id):
            return jsonify({
                'success': True,
                'connected': False,
                'running': False,
                'progress': 0,
                'status_messages': [],
                'error': None,
                'completed': False
            })
        
        troubleshooter = load_session(session_id)
        if troubleshooter is None:
            return jsonify({
                'success': True,
                'connected': False,
                'running': True,
                'progress': 0,
                'status_messages': [{
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'message': 'Initializing connection...',
                    'level': 'info'
                }],
                'error': None,
                'completed': False
            })
        
        # Format status messages consistently
        formatted_messages = []
        for msg in troubleshooter.status_messages:
            if isinstance(msg, dict) and all(k in msg for k in ['time', 'message', 'level']):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'message': str(msg) if not isinstance(msg, dict) else msg.get('message', ''),
                    'level': 'info'
                })
        
        return jsonify({
            'success': True,
            'connected': getattr(troubleshooter, 'is_connected', False),
            'running': getattr(troubleshooter, 'is_running', True),
            'progress': troubleshooter.progress,
            'status_messages': formatted_messages,
            'error': troubleshooter.error if hasattr(troubleshooter, 'error') else None,
            'completed': not troubleshooter.is_running
        })
        
    except Exception as e:
        app.logger.error(f"Error in test_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/test_results/<session_id>')
def test_results(session_id):
    try:
        app.logger.info(f"Fetching results for session: {session_id}")
        
        # Check if session exists in Redis
        if not redis_client.exists(SESSION_PREFIX + session_id):
            app.logger.warning(f"Session {session_id} not found in Redis.")
            return jsonify({
                'success': False,
                'error': 'Session not found'
            })
        
        # Load the session from Redis
        troubleshooter = load_session(session_id)
        if not troubleshooter:
            app.logger.error(f"Failed to load session {session_id} from Redis.")
            return jsonify({
                'success': False,
                'error': 'Failed to load session data'
            })
        
        # Log the raw results for debugging
        app.logger.info(f"Raw results for session {session_id}: {list(troubleshooter.results.keys())}")
        
        # If results are empty but the test is completed, return a special flag
        if not troubleshooter.results and not troubleshooter.is_running and troubleshooter.completed_at:
            app.logger.warning(f"Test completed but no results found for session {session_id}")
            return jsonify({
                'success': True,
                'results': {'_empty_results': True},  # Special flag for frontend
                'status_messages': troubleshooter.status_messages,
                'completed': True
            })
        
        # Clean up the results for JSON serialization
        clean_results = {}
        for key, value in troubleshooter.results.items():
            if isinstance(value, dict):
                clean_dict = {}
                for k, v in value.items():
                    if isinstance(v, list) and k == 'outputs':
                        clean_dict[k] = [{'command': cmd, 'output': out} for cmd, out in v]
                    else:
                        clean_dict[k] = v
                clean_results[key] = clean_dict
            else:
                clean_results[key] = value
        
        # Log the cleaned results for debugging
        app.logger.info(f"Returning results for session {session_id}: {list(clean_results.keys())}")
        
        # Return the results as JSON
        return jsonify({
            'success': True,
            'results': clean_results,
            'suggestions': troubleshooter.results.get('suggestions', []),
            'status_messages': troubleshooter.status_messages,
            'completed': not troubleshooter.is_running
        })
    except Exception as e:
        app.logger.error(f"Error in test_results for session {session_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error retrieving results: {str(e)}'
        })

@app.route('/download_results/<session_id>')
def download_results(session_id):
    """Download test results as a text file."""
    if not redis_client.exists(SESSION_PREFIX + session_id):
        return jsonify({
            'success': False,
            'error': 'Session not found'
        })
    
    troubleshooter = load_session(session_id)
    
    # Create a text file
    output = "FortiGate Connectivity Troubleshooting Results\n"
    output += "===========================================\n\n"
    output += f"FortiOS Version: {troubleshooter.fortigate_version}\n"
    output += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Add status messages
    output += "Status Messages:\n"
    for msg in troubleshooter.status_messages:
        output += f"[{msg['time']}] [{msg['level']}] {msg['message']}\n"
    output += "\n"
    
    # Add results
    for section, data in troubleshooter.results.items():
        output += f"## {section.replace('_', ' ').title()}\n"
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key != 'output' and key != 'outputs':
                    output += f"{key}: {value}\n"
            
            if 'output' in data:
                output += "\nOutput:\n"
                output += "```\n"
                output += data['output']
                output += "\n```\n\n"
            
            if 'outputs' in data:
                output += "\nOutputs:\n"
                for cmd, out in data['outputs']:
                    output += f"Command: {cmd}\n"
                    output += "```\n"
                    output += out
                    output += "\n```\n\n"
        else:
            output += f"{data}\n\n"
    
    # Add suggestions
    if 'suggestions' in troubleshooter.results:
        output += "## Suggested Fixes\n"
        for i, suggestion in enumerate(troubleshooter.results['suggestions'], 1):
            output += f"{i}. {suggestion}\n"
    
    # Create a response with the file
    from flask import Response
    response = Response(
        output,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename=fortigate_troubleshoot_{session_id}.txt"}
    )
    
    return response

@app.route('/end_session/<session_id>')
def end_session(session_id):
    """End a session and clean up resources."""
    if redis_client.exists(SESSION_PREFIX + session_id):
        troubleshooter = load_session(session_id)
        
        # Disconnect from FortiGate
        if troubleshooter.is_connected:
            troubleshooter.disconnect()
        
        # Remove from Redis
        delete_session(session_id)
        
        return jsonify({
            'success': True,
            'message': 'Session ended successfully'
        })
    
    return jsonify({
        'success': False,
        'error': 'Session not found'
    })
@app.route('/verify_methods')
def verify_methods():
    """Verify that all diagnostic methods exist on the FortiGateTroubleshooter class."""
    try:
        # Create a dummy troubleshooter instance
        troubleshooter = FortiGateTroubleshooter("ARG00001", "arbys")
        
        # Check which methods exist
        methods_to_check = [
            'run_utm_and_webfiltering',
            'run_system_diagnostics', 
            'run_network_diagnostics',
            'run_session_table_and_flow_debug',
            'run_vpn_and_authentication',
            'run_hardware_and_ha',
            'run_full_diagnostics'
        ]
        
        results = {}
        for method_name in methods_to_check:
            has_method = hasattr(troubleshooter, method_name)
            is_callable = callable(getattr(troubleshooter, method_name, None))
            results[method_name] = {
                'exists': has_method,
                'callable': is_callable,
                'status': '✓ OK' if has_method and is_callable else '✗ MISSING'
            }
        
        return jsonify({
            'success': True,
            'methods': results,
            'summary': {
                'total_methods': len(methods_to_check),
                'existing_methods': sum(1 for r in results.values() if r['exists']),
                'callable_methods': sum(1 for r in results.values() if r['callable'])
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })@app.route('/test_fortigate_commands/<session_id>')
def test_fortigate_commands(session_id):
    
    """Test basic FortiGate commands to verify connectivity."""
    try:
        troubleshooter = load_session(session_id)
        if not troubleshooter or not troubleshooter.is_connected:
            return jsonify({'error': 'No active session or not connected'})
        
        # Test basic commands
        test_commands = [
            'get system status',
            'get system interface', 
            'show system global',
            'diagnose sys top 1 1',  # Very basic diagnostic
        ]
        
        results = {}
        for cmd in test_commands:
            app.logger.info(f"Testing command: {cmd}")
            output = troubleshooter.execute_command(cmd, timeout=15)
            results[cmd] = {
                'output': output,
                'success': output is not None and len(output.strip()) > 0,
                'length': len(output) if output else 0
            }
        
        return jsonify({
            'success': True,
            'test_results': results,
            'summary': {
                'total_commands': len(test_commands),
                'successful_commands': sum(1 for r in results.values() if r['success']),
                'fortigate_version': getattr(troubleshooter, 'fortigate_version', 'Unknown')
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error testing commands: {str(e)}")
        return jsonify({'error': str(e)})
@app.route('/clear_all_sessions')
def clear_all_sessions():
    """Clear all active sessions (admin function)."""
    count = 0
    
    # Find all session keys in Redis
    for key in redis_client.scan_iter(match=SESSION_PREFIX + '*'):
        session_id = key.replace(SESSION_PREFIX, '')
        troubleshooter = load_session(session_id)
        
        # Disconnect from FortiGate if connected
        if troubleshooter and troubleshooter.is_connected:
            troubleshooter.disconnect()
        
        # Delete the session from Redis
        delete_session(session_id)
        count += 1
    
    return jsonify({
        'success': True,
        'message': f'Cleared {count} sessions'
    })

@app.route('/rerun_diagnostic/<session_id>/<section>', methods=['POST'])
def rerun_diagnostic(session_id, section):
    session = load_session(session_id)
    if session is None:
        return jsonify({'success': False, 'error': 'Session not found or not ready'})
    troubleshooter = session
    try:
        if section == 'system_diagnostics':
            troubleshooter.run_system_diagnostics()
        elif section == 'network_diagnostics':
            troubleshooter.run_network_diagnostics(target_host=troubleshooter.hostname)
        elif section == 'session_table_and_flow_debug':
            troubleshooter.run_session_table_and_flow_debug()
        elif section == 'utm_and_webfiltering':
            troubleshooter.run_utm_and_webfiltering()
        elif section == 'vpn_and_authentication':
            troubleshooter.run_vpn_and_authentication()
        elif section == 'hardware_and_ha':
            troubleshooter.run_hardware_and_ha()
        else:
            return jsonify({'success': False, 'error': 'Unknown diagnostic section'})
        return jsonify({'success': True, 'results': troubleshooter.results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_results_text/<session_id>')
def download_results_text(session_id):
    session = load_session(session_id)
    if session is None:
        return 'Session not found', 404
    troubleshooter = session
    text = troubleshooter.export_results_text()
    from flask import Response
    return Response(text, mimetype='text/plain', headers={"Content-Disposition": f"attachment;filename=fortigate_results_{session_id}.txt"})
   

@app.route('/debug_session/<session_id>')
def debug_session(session_id):
    """Debug endpoint to get raw session data."""
    try:
        # Check if session exists in Redis
        if not redis_client.exists(SESSION_PREFIX + session_id):
            return jsonify({
                'success': False,
                'error': 'Session not found'
            })
        
        # Get raw data from Redis
        raw_data = redis_client.get(SESSION_PREFIX + session_id)
        
        # Parse JSON data
        parsed_data = json.loads(raw_data)
        
        # Return debug information
        return jsonify({
            'success': True,
            'session_id': session_id,
            'raw_data_length': len(raw_data),
            'parsed_data_keys': list(parsed_data.keys()),
            'results_keys': list(parsed_data.get('results', {}).keys()),
            'status_count': len(parsed_data.get('status_messages', [])),
            'is_running': parsed_data.get('is_running', False),
            'is_connected': parsed_data.get('is_connected', False),
            'completed_at': parsed_data.get('completed_at'),
            'fortigate_version': parsed_data.get('fortigate_version')
        })
    except Exception as e:
        app.logger.error(f"Error in debug_session for {session_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/get_results_html/<session_id>')
def get_results_html(session_id):
    """Get formatted HTML results for a session."""
    try:
        # Check if session exists in Redis
        if not redis_client.exists(SESSION_PREFIX + session_id):
            return jsonify({
                'success': False,
                'error': 'Session not found'
            })
        
        # Load the session from Redis
        troubleshooter = load_session(session_id)
        if not troubleshooter:
            return jsonify({
                'success': False,
                'error': 'Failed to load session data'
            })
        
        # Generate HTML for results
        html = "<div class='results-container'>"
        
        # Add FortiOS version if available
        if troubleshooter.fortigate_version:
            html += f"<div class='result-header'><strong>FortiOS Version:</strong> {troubleshooter.fortigate_version}</div>"
        
        # Add results sections
        if troubleshooter.results:
            for section, content in troubleshooter.results.items():
                html += f"<div class='result-section'>"
                html += f"<h3>{section.replace('_', ' ').title()}</h3>"
                
                if isinstance(content, dict):
                    for key, value in content.items():
                        if key != 'output' and key != 'outputs':
                            html += f"<div><strong>{key}:</strong> {value}</div>"
                    
                    if 'output' in content and content['output']:
                        html += "<div class='output-container'>"
                        html += "<h4>Output:</h4>"
                        html += f"<pre>{content['output']}</pre>"
                        html += "</div>"
                    
                    if 'outputs' in content and content['outputs']:
                        html += "<div class='outputs-container'>"
                        html += "<h4>Outputs:</h4>"
                        for cmd, out in content['outputs']:
                            html += f"<div><strong>Command:</strong> {cmd}</div>"
                            html += f"<pre>{out}</pre>"
                        html += "</div>"
                else:
                    html += f"<pre>{content}</pre>"
                
                html += "</div>"
        else:
            html += "<div class='no-results'>No detailed results available.</div>"
        
        # Add suggestions if available
        if 'suggestions' in troubleshooter.results and troubleshooter.results['suggestions']:
            html += "<div class='suggestions-section'>"
            html += "<h3>Suggested Fixes</h3>"
            html += "<ul>"
            for suggestion in troubleshooter.results['suggestions']:
                html += f"<li>{suggestion}</li>"
            html += "</ul>"
            html += "</div>"
        
        html += "</div>"
        
        # Add download links
        html += "<div class='download-links'>"
        html += f"<a href='/download_results_text/{session_id}' class='btn btn-primary' target='_blank'>Download as Text</a> "
        html += f"<a href='/download_results_csv/{session_id}' class='btn btn-primary' target='_blank'>Download as CSV</a>"
        html += "</div>"
        
        return jsonify({
            'success': True,
            'html': html
        })
    except Exception as e:
        app.logger.error(f"Error generating results HTML for {session_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Add error handler for socket errors
@app.errorhandler(OSError)
def handle_socket_error(error):
    if "An operation was attempted on something that is not a socket" in str(error):
        app.logger.warning("Socket error during reload - this is normal during development")
        return "Server is reloading, please refresh the page", 503
    return str(error), 500

# Add cleanup handler for graceful shutdown
@app.teardown_appcontext
def cleanup(exception=None):
    """Clean up any active sessions."""
    try:
        # No need to clean up in-memory sessions; Redis handles session expiry
        pass
    except Exception as e:
        app.logger.error(f"Error in cleanup: {e}")

SESSION_CLEANUP_INTERVAL = 60  # seconds
SESSION_LIFETIME = 600  # seconds (10 minutes)

# Background thread for cleaning up old sessions
def session_cleanup_worker():
    while True:
        try:
            now = time.time()
            to_delete = []
            # Use Redis SCAN to find all session keys
            for key in redis_client.scan_iter(match=SESSION_PREFIX + '*'):
                data = redis_client.get(key)
                if not data:
                    continue
                data = json.loads(data)
                completed_at = data.get('completed_at')
                is_connected = data.get('is_connected', False)
                if completed_at and is_connected:
                    if now - completed_at > SESSION_LIFETIME:
                        to_delete.append(key)
            for key in to_delete:
                app.logger.info(f"Cleaning up expired session: {key}")
                try:
                    redis_client.delete(key)
                except Exception as e:
                    app.logger.error(f"Error cleaning up session {key}: {e}")
        except Exception as e:
            app.logger.error(f"Error in session cleanup worker: {e}")
        time.sleep(SESSION_CLEANUP_INTERVAL)

# Start the cleanup worker thread
cleanup_thread = threading.Thread(target=session_cleanup_worker, daemon=True)
cleanup_thread.start()

# Graceful shutdown on Ctrl+C
def handle_sigint(sig, frame):
    """Handle graceful shutdown on Ctrl+C."""
    app.logger.info("Received SIGINT, shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)

def create_self_signed_cert():
    """Create a self-signed certificate in the current directory."""
    # Generate key
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    # Generate certificate
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "Georgia"
    cert.get_subject().L = "Atlanta"
    cert.get_subject().O = "Arby's"
    cert.get_subject().OU = "IT"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    # Save certificate
    with open("cert.pem", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open("key.pem", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

if __name__ == '__main__':
    try:
        # Use certificates from app/certs directory
        cert_path = os.path.join(PROJECT_ROOT, 'app', 'certs', 'cert.pem')
        key_path = os.path.join(PROJECT_ROOT, 'app', 'certs', 'key.pem')
        
        # Check if certificates exist in app/certs, if not, use or create in current directory
        if os.path.exists(cert_path) and os.path.exists(key_path):
            ssl_context = (cert_path, key_path)
        else:
            # Fall back to current directory
            if not (os.path.exists('cert.pem') and os.path.exists('key.pem')):
                create_self_signed_cert()
            ssl_context = ('cert.pem', 'key.pem')
        
        # Run Flask with SSL
        app.run(
            debug=False,
            host='0.0.0.0',
            port=5000,
            ssl_context=ssl_context
        )
    except OSError as e:
        if "An operation was attempted on something that is not a socket" in str(e):
            app.logger.warning("Socket error during reload - this is normal during development")
        else:
            raise
