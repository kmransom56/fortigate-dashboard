#!/usr/bin/env python3
"""
FortiGate 7.6 Self-Documenting API Implementation

This script continuously documents and tracks device port connections from FortiGate
using the Device Inventory API. It maintains a local SQLite database for historical
tracking and change detection.

Features:
- Real-time device inventory sync from FortiGate
- Port assignment tracking and history
- Device change detection (port changes, status changes, IP changes)
- Topology documentation export
- Integration with existing FortiGate service patterns

Usage:
    python fortigate_self_api_doc.py sync              # Sync device inventory
    python fortigate_self_api_doc.py query --port port2 # Query device on port
    python fortigate_self_api_doc.py history --mac aa:bb:cc:dd:ee:ff  # Port history
    python fortigate_self_api_doc.py export            # Export topology JSON
    python fortigate_self_api_doc.py watch --interval 60 # Continuous monitoring
"""

import os
import sys
import sqlite3
import json
import logging
import argparse
import time
import urllib.parse
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../..")
sys.path.insert(0, project_root)

from app.services.fortigate_service import fgt_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FortiGateInventory:
    """
    FortiGate Device Inventory Manager
    
    Tracks device inventory from FortiGate 7.6 Device Inventory API and maintains
    a local SQLite database for historical tracking and change detection.
    """
    
    def __init__(self, db_path: str = "device_inventory.db", vdom: str = "root"):
        """
        Initialize FortiGate Inventory Manager
        
        Args:
            db_path: Path to SQLite database file
            vdom: FortiGate VDOM (default: "root")
        """
        self.vdom = vdom
        self.db_path = db_path
        self.conn = None
        self.init_database()
        
        # Get FortiGate host from environment
        fortigate_host = os.getenv("FORTIGATE_HOST", "192.168.0.254")
        if fortigate_host.startswith("https://"):
            self.fortigate_ip = fortigate_host[8:]
        elif fortigate_host.startswith("http://"):
            self.fortigate_ip = fortigate_host[7:]
        else:
            self.fortigate_ip = fortigate_host
        
        logger.info(f"Initialized FortiGate Inventory Manager (FortiGate: {self.fortigate_ip}, VDOM: {vdom})")
    
    def init_database(self):
        """Create SQLite database for device inventory tracking"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Devices table - stores current device state
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mac TEXT UNIQUE NOT NULL,
                ipv4_address TEXT,
                hostname TEXT,
                hardware_vendor TEXT,
                hardware_version TEXT,
                hardware_family TEXT,
                hardware_type TEXT,
                os_name TEXT,
                os_version TEXT,
                detected_interface TEXT,
                is_online BOOLEAN,
                host_src TEXT,
                last_seen INTEGER,
                vdom TEXT,
                fortiswitch_id TEXT,
                fortiswitch_port_id INTEGER,
                fortiswitch_port_name TEXT,
                fortiswitch_vlan_id INTEGER,
                fortiswitch_serial TEXT,
                fortiap_id TEXT,
                fortiap_ssid TEXT,
                fortiap_name TEXT,
                dhcp_lease_status TEXT,
                dhcp_lease_expire INTEGER,
                device_type TEXT,
                generation INTEGER,
                master_mac TEXT,
                is_master_device BOOLEAN,
                online_interfaces TEXT,  -- JSON array
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Port assignments table - tracks port assignment history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS port_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_mac TEXT NOT NULL,
                port_name TEXT NOT NULL,
                assignment_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assignment_end TIMESTAMP,
                FOREIGN KEY(device_mac) REFERENCES devices(mac)
            )
        ''')
        
        # Device changes table - tracks all device changes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_mac TEXT NOT NULL,
                change_type TEXT,  -- 'port_change', 'status_change', 'ip_change', 'hostname_change'
                old_value TEXT,
                new_value TEXT,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(device_mac) REFERENCES devices(mac)
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_devices_interface ON devices(detected_interface)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_devices_online ON devices(is_online)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_port_assignments_mac ON port_assignments(device_mac)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_changes_mac ON device_changes(device_mac)')
        
        self.conn.commit()
        logger.info(f"Database initialized: {self.db_path}")
    
    def get_device_inventory(self, start: int = 0, count: int = 0, filter_expr: Optional[str] = None) -> List[Dict]:
        """
        Fetch current device inventory from FortiGate
        
        Args:
            start: Starting index for pagination
            count: Number of devices to retrieve (0 = all)
            filter_expr: Filter expression (e.g., "ipv4_address==192.168.1.100")
        
        Returns:
            List of device dictionaries
        """
        try:
            endpoint = "monitor/user/device/query"
            
            # Build query parameters as URL query string
            query_parts = []
            if start > 0:
                query_parts.append(f"start={start}")
            if count > 0:
                query_parts.append(f"count={count}")
            if filter_expr:
                # URL encode filter expression
                query_parts.append(f"filter={urllib.parse.quote(filter_expr)}")
            
            # Append query string to endpoint if we have parameters
            if query_parts:
                endpoint = f"{endpoint}?{'&'.join(query_parts)}"
            
            # Use existing fgt_api function from fortigate_service
            # Note: fgt_api expects endpoint without /api/v2 prefix
            result = fgt_api(endpoint)
            
            if "error" in result:
                logger.error(f"API Error: {result}")
                return []
            
            # Handle different response formats
            if isinstance(result, dict):
                if result.get('status') == 'success':
                    return result.get('results', [])
                elif 'results' in result:
                    return result.get('results', [])
                else:
                    logger.warning(f"Unexpected API response format: {result.keys()}")
                    return []
            else:
                logger.error(f"Unexpected API response type: {type(result)}")
                return []
                
        except Exception as e:
            logger.error(f"Request failed: {e}", exc_info=True)
            return []
    
    def record_device(self, device: Dict):
        """
        Record or update device in local database
        
        Args:
            device: Device dictionary from FortiGate API
        """
        cursor = self.conn.cursor()
        
        try:
            mac = device.get('mac')
            if not mac:
                logger.warning(f"Device missing MAC address, skipping: {device}")
                return
            
            # Get current device state from database
            cursor.execute('SELECT * FROM devices WHERE mac = ?', (mac,))
            existing = cursor.fetchone()
            
            # Prepare device data
            online_interfaces = device.get('online_interfaces', [])
            if isinstance(online_interfaces, list):
                online_interfaces_json = json.dumps(online_interfaces)
            else:
                online_interfaces_json = str(online_interfaces)
            
            # Insert or update device
            cursor.execute('''
                INSERT OR REPLACE INTO devices 
                (mac, ipv4_address, hostname, hardware_vendor, hardware_version,
                 hardware_family, hardware_type, os_name, os_version,
                 detected_interface, is_online, host_src, last_seen, vdom,
                 fortiswitch_id, fortiswitch_port_id, fortiswitch_port_name,
                 fortiswitch_vlan_id, fortiswitch_serial,
                 fortiap_id, fortiap_ssid, fortiap_name,
                 dhcp_lease_status, dhcp_lease_expire, device_type,
                 generation, master_mac, is_master_device, online_interfaces,
                 updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                mac,
                device.get('ipv4_address'),
                device.get('hostname'),
                device.get('hardware_vendor'),
                device.get('hardware_version'),
                device.get('hardware_family'),
                device.get('hardware_type'),
                device.get('os_name'),
                device.get('os_version'),
                device.get('detected_interface'),
                device.get('is_online', False),
                device.get('host_src'),
                device.get('last_seen'),
                device.get('vdom', self.vdom),
                device.get('fortiswitch_id'),
                device.get('fortiswitch_port_id'),
                device.get('fortiswitch_port_name'),
                device.get('fortiswitch_vlan_id'),
                device.get('fortiswitch_serial'),
                device.get('fortiap_id'),
                device.get('fortiap_ssid'),
                device.get('fortiap_name'),
                device.get('dhcp_lease_status'),
                device.get('dhcp_lease_expire'),
                device.get('device_type'),
                device.get('generation'),
                device.get('master_mac'),
                device.get('is_master_device', False),
                online_interfaces_json
            ))
            
            # Detect and record changes
            if existing:
                existing_dict = dict(zip([col[0] for col in cursor.description], existing))
                self._detect_changes(cursor, mac, existing_dict, device)
            
            # Record port assignment
            detected_interface = device.get('detected_interface')
            if detected_interface:
                cursor.execute('''
                    SELECT port_name FROM port_assignments 
                    WHERE device_mac = ? AND assignment_end IS NULL
                ''', (mac,))
                
                current_port = cursor.fetchone()
                if current_port and current_port[0] != detected_interface:
                    # Device moved to different port
                    cursor.execute('''
                        UPDATE port_assignments 
                        SET assignment_end = CURRENT_TIMESTAMP
                        WHERE device_mac = ? AND assignment_end IS NULL
                    ''', (mac,))
                    
                    # Log change
                    cursor.execute('''
                        INSERT INTO device_changes 
                        (device_mac, change_type, old_value, new_value)
                        VALUES (?, 'port_change', ?, ?)
                    ''', (mac, current_port[0], detected_interface))
                    
                    logger.info(f"Device {mac} moved from {current_port[0]} to {detected_interface}")
                
                elif not current_port:
                    # New port assignment
                    cursor.execute('''
                        INSERT INTO port_assignments (device_mac, port_name)
                        VALUES (?, ?)
                    ''', (mac, detected_interface))
                    logger.debug(f"New port assignment: {mac} -> {detected_interface}")
            
            self.conn.commit()
            logger.debug(f"Recorded device: {device.get('hostname', 'Unknown')} ({mac}) on {detected_interface}")
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}", exc_info=True)
            self.conn.rollback()
        except Exception as e:
            logger.error(f"Error recording device: {e}", exc_info=True)
            self.conn.rollback()
    
    def _detect_changes(self, cursor, mac: str, old_device: Dict, new_device: Dict):
        """
        Detect and record device changes
        
        Args:
            cursor: Database cursor
            mac: Device MAC address
            old_device: Previous device state
            new_device: New device state
        """
        changes = []
        
        # Check for IP address change
        if old_device.get('ipv4_address') != new_device.get('ipv4_address'):
            changes.append(('ip_change', old_device.get('ipv4_address'), new_device.get('ipv4_address')))
        
        # Check for hostname change
        if old_device.get('hostname') != new_device.get('hostname'):
            changes.append(('hostname_change', old_device.get('hostname'), new_device.get('hostname')))
        
        # Check for status change
        old_online = bool(old_device.get('is_online', False))
        new_online = bool(new_device.get('is_online', False))
        if old_online != new_online:
            changes.append(('status_change', str(old_online), str(new_online)))
        
        # Record all changes
        for change_type, old_value, new_value in changes:
            cursor.execute('''
                INSERT INTO device_changes 
                (device_mac, change_type, old_value, new_value)
                VALUES (?, ?, ?, ?)
            ''', (mac, change_type, old_value, new_value))
            logger.info(f"Device {mac} change: {change_type} ({old_value} -> {new_value})")
    
    def sync_inventory(self, batch_size: int = 100):
        """
        Sync all devices from FortiGate to local database
        
        Args:
            batch_size: Number of devices to fetch per batch
        """
        logger.info("Starting device inventory sync...")
        total_devices = 0
        start = 0
        
        while True:
            devices = self.get_device_inventory(start=start, count=batch_size)
            if not devices:
                break
            
            logger.info(f"Processing batch: {len(devices)} devices (starting at {start})")
            
            for device in devices:
                self.record_device(device)
                total_devices += 1
            
            # If we got fewer devices than requested, we've reached the end
            if len(devices) < batch_size:
                break
            
            start += batch_size
        
        logger.info(f"Sync complete: {total_devices} devices processed")
        return total_devices
    
    def get_device_by_port(self, port_name: str) -> Optional[Dict]:
        """
        Get current device connected to specific port
        
        Args:
            port_name: Port/interface name (e.g., "port2", "internal")
        
        Returns:
            Device dictionary or None
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM devices
            WHERE detected_interface = ? AND is_online = 1
            ORDER BY updated_at DESC LIMIT 1
        ''', (port_name,))
        
        columns = [description[0] for description in cursor.description]
        result = cursor.fetchone()
        
        if result:
            device = dict(zip(columns, result))
            # Parse JSON fields
            if device.get('online_interfaces'):
                try:
                    device['online_interfaces'] = json.loads(device['online_interfaces'])
                except:
                    pass
            return device
        return None
    
    def get_port_history(self, device_mac: str) -> List[Dict]:
        """
        Get port assignment history for a device
        
        Args:
            device_mac: Device MAC address
        
        Returns:
            List of port assignment dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT port_name, assignment_start, assignment_end
            FROM port_assignments
            WHERE device_mac = ?
            ORDER BY assignment_start DESC
        ''', (device_mac,))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_device_changes(self, device_mac: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get device change history
        
        Args:
            device_mac: Optional MAC address to filter by
            limit: Maximum number of changes to return
        
        Returns:
            List of change dictionaries
        """
        cursor = self.conn.cursor()
        if device_mac:
            cursor.execute('''
                SELECT * FROM device_changes
                WHERE device_mac = ?
                ORDER BY changed_at DESC
                LIMIT ?
            ''', (device_mac, limit))
        else:
            cursor.execute('''
                SELECT * FROM device_changes
                ORDER BY changed_at DESC
                LIMIT ?
            ''', (limit,))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def export_documentation(self, output_file: str = "device_topology.json", online_only: bool = True) -> Dict:
        """
        Export current device documentation to JSON
        
        Args:
            output_file: Output file path
            online_only: Only export online devices
        
        Returns:
            Documentation dictionary
        """
        cursor = self.conn.cursor()
        
        if online_only:
            cursor.execute('''
                SELECT * FROM devices WHERE is_online = 1
                ORDER BY detected_interface
            ''')
        else:
            cursor.execute('''
                SELECT * FROM devices
                ORDER BY detected_interface
            ''')
        
        columns = [description[0] for description in cursor.description]
        devices = []
        for row in cursor.fetchall():
            device = dict(zip(columns, row))
            # Parse JSON fields
            if device.get('online_interfaces'):
                try:
                    device['online_interfaces'] = json.loads(device['online_interfaces'])
                except:
                    pass
            devices.append(device)
        
        # Group by port
        topology = {}
        for device in devices:
            port = device.get('detected_interface') or 'unknown'
            if port not in topology:
                topology[port] = []
            topology[port].append(device)
        
        documentation = {
            "exported_at": datetime.now().isoformat(),
            "fortigate_ip": self.fortigate_ip,
            "vdom": self.vdom,
            "total_devices": len(devices),
            "online_devices": sum(1 for d in devices if d.get('is_online')),
            "topology_by_port": topology
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(documentation, f, indent=2, default=str)
        
        logger.info(f"Documentation exported to {output_file} ({len(devices)} devices)")
        return documentation
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="FortiGate 7.6 Self-Documenting API - Device Inventory Tracker"
    )
    parser.add_argument(
        '--db',
        default='device_inventory.db',
        help='SQLite database path (default: device_inventory.db)'
    )
    parser.add_argument(
        '--vdom',
        default='root',
        help='FortiGate VDOM (default: root)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync device inventory from FortiGate')
    sync_parser.add_argument('--batch-size', type=int, default=100, help='Batch size for fetching devices')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query device information')
    query_parser.add_argument('--port', help='Query device on specific port')
    query_parser.add_argument('--mac', help='Query device by MAC address')
    query_parser.add_argument('--ip', help='Query device by IP address')
    
    # History command
    history_parser = subparsers.add_parser('history', help='View device history')
    history_parser.add_argument('--mac', help='Device MAC address')
    history_parser.add_argument('--limit', type=int, default=100, help='Maximum number of changes')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export topology documentation')
    export_parser.add_argument('--output', default='device_topology.json', help='Output file path')
    export_parser.add_argument('--all', action='store_true', help='Include offline devices')
    
    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Continuously monitor device inventory')
    watch_parser.add_argument('--interval', type=int, default=60, help='Sync interval in seconds')
    watch_parser.add_argument('--export-interval', type=int, help='Auto-export interval in seconds')
    watch_parser.add_argument('--export-path', default='device_topology.json', help='Auto-export file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize inventory manager
    inventory = FortiGateInventory(db_path=args.db, vdom=args.vdom)
    
    try:
        if args.command == 'sync':
            count = inventory.sync_inventory(batch_size=args.batch_size)
            print(f"✅ Synced {count} devices")
        
        elif args.command == 'query':
            if args.port:
                device = inventory.get_device_by_port(args.port)
                if device:
                    print(f"Device on {args.port}:")
                    print(json.dumps(device, indent=2, default=str))
                else:
                    print(f"No online device found on {args.port}")
            elif args.mac:
                # Query from API
                devices = inventory.get_device_inventory(filter_expr=f"mac=={args.mac}")
                if devices:
                    print(json.dumps(devices[0], indent=2, default=str))
                else:
                    print(f"Device not found: {args.mac}")
            elif args.ip:
                # Query from API
                devices = inventory.get_device_inventory(filter_expr=f"ipv4_address=={args.ip}")
                if devices:
                    print(json.dumps(devices[0], indent=2, default=str))
                else:
                    print(f"Device not found: {args.ip}")
            else:
                query_parser.print_help()
        
        elif args.command == 'history':
            if args.mac:
                history = inventory.get_port_history(args.mac)
                print(f"Port history for {args.mac}:")
                print(json.dumps(history, indent=2, default=str))
            else:
                changes = inventory.get_device_changes(limit=args.limit)
                print(f"Recent device changes (last {len(changes)}):")
                print(json.dumps(changes, indent=2, default=str))
        
        elif args.command == 'export':
            doc = inventory.export_documentation(
                output_file=args.output,
                online_only=not args.all
            )
            print(f"✅ Exported {doc['total_devices']} devices to {args.output}")
            print(f"   Online devices: {doc['online_devices']}")
            print(f"   Ports with devices: {len(doc['topology_by_port'])}")
        
        elif args.command == 'watch':
            print(f"Watching device inventory (sync every {args.interval}s)...")
            print("Press Ctrl+C to stop")
            
            last_export = time.time()
            export_interval = args.export_interval or 0
            
            try:
                while True:
                    count = inventory.sync_inventory()
                    print(f"[{datetime.now()}] Synced {count} devices")
                    
                    # Auto-export if enabled
                    if export_interval > 0:
                        if time.time() - last_export >= export_interval:
                            inventory.export_documentation(output_file=args.export_path)
                            last_export = time.time()
                    
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\nStopped watching")
    
    finally:
        inventory.close()


if __name__ == "__main__":
    main()
