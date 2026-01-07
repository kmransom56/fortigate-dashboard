#!/usr/bin/env python3
"""
FortiManager API Migration Script
Run this on your computer that has FortiManager access
"""

import requests
import json
import time
import pandas as pd
from datetime import datetime
import urllib3
from typing import Dict, List, Optional

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FortiManagerAPI:
    def __init__(self, fmg_ip: str, username: str, password: str):
        self.fmg_ip = fmg_ip
        self.username = username
        self.password = password
        self.session_id = None
        self.base_url = f"https://{fmg_ip}/jsonrpc"
        self.headers = {'Content-Type': 'application/json'}
        self.migration_log = []
        
    def login(self):
        """Login to FortiManager and get session ID"""
        payload = {
            "id": 1,
            "method": "exec",
            "params": [{
                "url": "/sys/login/user",
                "data": {
                    "user": self.username,
                    "passwd": self.password
                }
            }]
        }
        
        try:
            response = requests.post(
                self.base_url, 
                json=payload, 
                headers=self.headers, 
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                    self.session_id = result['session']
                    self.log_action("Successfully logged into FortiManager")
                    return True
            
            self.log_action(f"Login failed: {response.text}")
            return False
            
        except Exception as e:
            self.log_action(f"Login error: {e}")
            return False
    
    def logout(self):
        """Logout from FortiManager"""
        if self.session_id:
            payload = {
                "id": 1,
                "method": "exec",
                "params": [{"url": "/sys/logout"}],
                "session": self.session_id
            }
            
            try:
                requests.post(self.base_url, json=payload, headers=self.headers, verify=False)
                self.log_action("Logged out from FortiManager")
            except:
                pass
    
    def log_action(self, message: str):
        """Log actions with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)
    
    def execute_api_call(self, method: str, url: str, data: Dict = None):
        """Execute FortiManager API call"""
        if not self.session_id:
            self.log_action("Not logged in. Please login first.")
            return None
        
        payload = {
            "id": int(time.time()),
            "method": method,
            "params": [{"url": url}],
            "session": self.session_id
        }
        
        if data:
            payload["params"][0]["data"] = data
        
        try:
            response = requests.post(
                self.base_url, 
                json=payload, 
                headers=self.headers, 
                verify=False,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('result', [{}])[0].get('status', {}).get('code') == 0:
                    return result.get('result', [{}])[0].get('data')
                else:
                    error_msg = result.get('result', [{}])[0].get('status', {}).get('message', 'Unknown error')
                    self.log_action(f"API call failed: {error_msg}")
                    return None
            else:
                self.log_action(f"HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_action(f"API call exception: {e}")
            return None
    
    def get_managed_devices(self):
        """Get list of managed FortiGates"""
        devices = self.execute_api_call("get", "/dvmdb/device")
        if devices:
            self.log_action(f"Retrieved {len(devices)} managed devices")
            return devices
        return []
    
    def get_device_details(self, device_name: str):
        """Get detailed information about a specific device"""
        device_info = self.execute_api_call("get", f"/dvmdb/device/{device_name}")
        return device_info
    
    def install_policy_to_device(self, device_name: str, adom: str = "root"):
        """Install policy package to device"""
        self.log_action(f"Installing policy to device: {device_name}")
        
        install_data = {
            "adom": adom,
            "pkg": "default",  # Adjust package name as needed
            "scope": [{"name": device_name, "vdom": "root"}]
        }
        
        result = self.execute_api_call("exec", "/securityconsole/install/package", install_data)
        
        if result:
            # Monitor installation task
            task_id = result.get('task')
            if task_id:
                return self.monitor_task(task_id)
        
        return False
    
    def monitor_task(self, task_id: int, timeout: int = 300):
        """Monitor FortiManager task completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            task_status = self.execute_api_call("get", f"/task/task/{task_id}")
            
            if task_status:
                percent = task_status.get('percent', 0)
                state = task_status.get('state', 'unknown')
                
                self.log_action(f"Task {task_id}: {percent}% complete, state: {state}")
                
                if state == 'done' and percent == 100:
                    return True
                elif state == 'error':
                    return False
            
            time.sleep(10)
        
        self.log_action(f"Task {task_id} timeout after {timeout} seconds")
        return False
    
    def create_vlan_interface_policy(self, adom: str = "root"):
        """Create VLAN interface policy object"""
        vlan_config = {
            "name": "V118_ISOM",
            "vdom": "root",
            "type": "vlan",
            "interface": "internal",
            "vlanid": 118,
            "ip": ["10.118.1.1", "255.255.255.0"],
            "allowaccess": ["ping", "https", "ssh"]
        }
        
        result = self.execute_api_call(
            "add", 
            f"/pm/config/adom/{adom}/obj/system/interface", 
            vlan_config
        )
        
        if result is not None:
            self.log_action("VLAN interface policy created successfully")
            return True
        else:
            self.log_action("Failed to create VLAN interface policy")
            return False
    
    def create_switch_port_policy(self, adom: str = "root"):
        """Create switch port policy for V118_ISOM"""
        port_policy_config = {
            "name": "V118_ISOM_Policy",
            "description": "Port policy for V118_ISOM VLAN",
            "vlan": "V118_ISOM",
            "learning-limit": 10
        }
        
        result = self.execute_api_call(
            "add",
            f"/pm/config/adom/{adom}/obj/switch-controller/port-policy",
            port_policy_config
        )
        
        if result is not None:
            self.log_action("Switch port policy created successfully")
            return True
        else:
            self.log_action("Failed to create switch port policy")
            return False
    
    def get_switch_configuration(self, device_name: str, adom: str = "root"):
        """Get current switch configuration"""
        config = self.execute_api_call(
            "get",
            f"/pm/config/adom/{adom}/obj/switch-controller/managed-switch"
        )
        
        if config:
            self.log_action(f"Retrieved switch configuration for {device_name}")
            return config
        
        return None

class FortiManagerMigrationOrchestrator:
    def __init__(self, fmg_config: Dict):
        self.fmg = FortiManagerAPI(
            fmg_config['ip'],
            fmg_config['username'], 
            fmg_config['password']
        )
        self.migration_plan = None
        
    def load_migration_plan(self, csv_file: str):
        """Load migration plan from CSV"""
        try:
            self.migration_plan = pd.read_csv(csv_file)
            print(f"Loaded migration plan with {len(self.migration_plan)} devices")
            return True
        except Exception as e:
            print(f"Failed to load migration plan: {e}")
            return False
    
    def execute_migration_via_fortimanager(self):
        """Execute migration through FortiManager"""
        if not self.fmg.login():
            print("Failed to login to FortiManager")
            return False
        
        try:
            # Phase 1: Create infrastructure objects
            self.fmg.log_action("=== PHASE 1: CREATING POLICY OBJECTS ===")
            
            if not self.fmg.create_vlan_interface_policy():
                return False
            
            if not self.fmg.create_switch_port_policy():
                return False
            
            # Phase 2: Get managed devices
            self.fmg.log_action("=== PHASE 2: IDENTIFYING TARGET DEVICES ===")
            managed_devices = self.fmg.get_managed_devices()
            
            device_map = {}
            for device in managed_devices:
                device_map[device.get('name', '')] = device
            
            # Phase 3: Install policies to relevant FortiGates
            self.fmg.log_action("=== PHASE 3: INSTALLING POLICIES ===")
            
            target_devices = set()
            for _, row in self.migration_plan.iterrows():
                switch_name = row.get('switch_name', '')
                if switch_name:
                    # Extract FortiGate name from switch name
                    # Assuming format like "IBR_SONIC-01766-SW1"
                    fortigate_name = switch_name.split('-SW')[0] if '-SW' in switch_name else switch_name
                    target_devices.add(fortigate_name)
            
            for device_name in target_devices:
                if device_name in device_map:
                    self.fmg.log_action(f"Installing policy to {device_name}")
                    success = self.fmg.install_policy_to_device(device_name)
                    if not success:
                        self.fmg.log_action(f"Failed to install policy to {device_name}")
                else:
                    self.fmg.log_action(f"Device {device_name} not found in FortiManager")
            
            self.fmg.log_action("=== MIGRATION INFRASTRUCTURE READY ===")
            self.fmg.log_action("Note: Individual port migrations need to be done via jumpbox or FortiGate CLI")
            
            return True
            
        except Exception as e:
            self.fmg.log_action(f"Migration failed: {e}")
            return False
        finally:
            self.fmg.logout()
    
    def save_migration_log(self):
        """Save migration log to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"fortimanager_migration_log_{timestamp}.txt"
        
        with open(log_filename, 'w') as f:
            for log_entry in self.fmg.migration_log:
                f.write(log_entry + "\n")
        
        print(f"FortiManager migration log saved to: {log_filename}")

def create_sample_config():
    """Create sample FortiManager configuration file"""
    sample_config = {
        "fortimanager": {
            "ip": "YOUR_FORTIMANAGER_IP",
            "username": "admin",
            "password": "your_password"
        },
        "migration_settings": {
            "adom": "root",
            "vlan_name": "V118_ISOM",
            "vlan_id": 118,
            "vlan_subnet": "10.118.1.0/24",
            "policy_package": "default"
        }
    }
    
    with open('fortimanager_config.json', 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print("Sample FortiManager configuration created: fortimanager_config.json")
    print("Please edit this file with your actual FortiManager details")

def main():
    """Main function"""
    import sys
    import os
    
    # Check for configuration file
    config_file = 'fortimanager_config.json'
    
    if len(sys.argv) > 1 and sys.argv[1] == '--create-config':
        create_sample_config()
        return
    
    if not os.path.exists(config_file):
        print(f"Configuration file {config_file} not found.")
        print("Run with --create-config to create a sample configuration file.")
        return
    
    # Load configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        fmg_config = config['fortimanager']
        
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return
    
    # Check for migration plan
    migration_plan_file = 'port2_migration_plan.csv'
    if not os.path.exists(migration_plan_file):
        print(f"Migration plan file {migration_plan_file} not found.")
        print("Please run the device discovery script first to generate the migration plan.")
        return
    
    # Initialize orchestrator
    orchestrator = FortiManagerMigrationOrchestrator(fmg_config)
    
    try:
        # Load migration plan
        if orchestrator.load_migration_plan(migration_plan_file):
            # Execute FortiManager portion
            success = orchestrator.execute_migration_via_fortimanager()
            
            if success:
                print("\\nFortiManager infrastructure setup completed successfully!")
                print("Next steps:")
                print("1. Copy migration scripts to jumpbox")
                print("2. Execute individual port migrations via jumpbox")
                print("3. Verify device connectivity after migration")
            else:
                print("\\nFortiManager infrastructure setup failed. Check logs for details.")
        
    except KeyboardInterrupt:
        print("\\nOperation interrupted by user")
    except Exception as e:
        print(f"Operation failed: {e}")
    finally:
        orchestrator.save_migration_log()

if __name__ == "__main__":
    main()