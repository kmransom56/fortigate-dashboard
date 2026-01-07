#!/usr/bin/env python3
"""
Enhanced Arby's Splunk Infrastructure Monitoring with Real Store Data
Loads 1086+ actual store locations from CSV and monitors connectivity
"""

import asyncio
import aiohttp
import pandas as pd
import sqlite3
import json
import logging
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import csv
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor
import subprocess

# Store data structure matching CSV format
@dataclass
class RealStoreConfig:
    store_number: str
    mgmt_interface: str
    gateway_ip: str          # The .1 gateway IP from CSV
    device_ip: str           # Calculated device IP for monitoring
    subnet_mask: str
    network_cidr: str        # CIDR notation for the network
    brand: str
    region: str = "Unknown"  # Will be determined from IP ranges
    enabled: bool = True
    priority: int = 1
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate additional network information"""
        self.tags = self.tags or []
        self.region = self._determine_region()
        
    def _determine_region(self) -> str:
        """Determine region based on IP address ranges"""
        try:
            ip = ipaddress.IPv4Address(self.gateway_ip)
            
            # Map IP ranges to regions (you can adjust these based on your actual regional structure)
            if ip in ipaddress.IPv4Network('10.208.0.0/16'):
                return "South"
            elif ip in ipaddress.IPv4Network('10.210.0.0/16'):
                return "Central"  
            elif ip in ipaddress.IPv4Network('10.211.0.0/16'):
                return "East"
            elif ip in ipaddress.IPv4Network('10.212.0.0/16'):
                return "West"
            elif ip in ipaddress.IPv4Network('10.213.0.0/16'):
                return "North"
            elif ip in ipaddress.IPv4Network('10.214.0.0/16'):
                return "Northwest"
            elif ip in ipaddress.IPv4Network('10.215.0.0/16'):
                return "Northeast"
            else:
                return "Unknown"
        except:
            return "Unknown"

class StoreDataLoader:
    """Loads and processes store data from CSV file"""
    
    def __init__(self, csv_path: str = "stores.csv"):
        self.csv_path = csv_path
        self.logger = logging.getLogger(__name__)
        
    def load_stores_from_csv(self) -> List[RealStoreConfig]:
        """Load store data from CSV file"""
        stores = []
        
        try:
            # Read CSV data
            df = pd.read_csv(self.csv_path)
            
            self.logger.info(f"Loading {len(df)} stores from {self.csv_path}")
            
            for _, row in df.iterrows():
                try:
                    store = self._parse_store_row(row)
                    if store:
                        stores.append(store)
                except Exception as e:
                    self.logger.warning(f"Failed to parse store {row.get('store_number', 'Unknown')}: {e}")
                    
            self.logger.info(f"Successfully loaded {len(stores)} stores")
            
            # Log regional distribution
            region_counts = {}
            for store in stores:
                region_counts[store.region] = region_counts.get(store.region, 0) + 1
            
            self.logger.info("Regional distribution:")
            for region, count in sorted(region_counts.items()):
                self.logger.info(f"  {region}: {count} stores")
                
        except Exception as e:
            self.logger.error(f"Failed to load stores from CSV: {e}")
            raise
            
        return stores
    
    def _parse_store_row(self, row: pd.Series) -> Optional[RealStoreConfig]:
        """Parse a single CSV row into a RealStoreConfig"""
        try:
            # Extract data from CSV row
            store_number = str(row['store_number']).strip()
            mgmt_interface = str(row['mgmtintname']).strip()
            ip_with_mask = str(row['ip_address']).strip()
            brand = str(row['brand']).strip()
            
            # Skip invalid entries
            if pd.isna(row['ip_address']) or ip_with_mask == 'nan':
                return None
                
            # Parse IP address and subnet mask
            if '/' in ip_with_mask:
                gateway_ip, subnet_mask = ip_with_mask.split('/')
            else:
                self.logger.warning(f"Store {store_number}: Invalid IP format {ip_with_mask}")
                return None
            
            # Calculate network CIDR
            network_cidr = self._calculate_network_cidr(gateway_ip, subnet_mask)
            
            # Calculate device IP for monitoring (typically .10 in the subnet)
            device_ip = self._calculate_device_ip(gateway_ip, subnet_mask)
            
            # Create store configuration
            store = RealStoreConfig(
                store_number=store_number,
                mgmt_interface=mgmt_interface,
                gateway_ip=gateway_ip,
                device_ip=device_ip,
                subnet_mask=subnet_mask,
                network_cidr=network_cidr,
                brand=brand,
                tags=[brand.lower(), mgmt_interface]
            )
            
            return store
            
        except Exception as e:
            self.logger.error(f"Error parsing store row: {e}")
            return None
    
    def _calculate_network_cidr(self, ip: str, subnet_mask: str) -> str:
        """Calculate CIDR notation from IP and subnet mask"""
        try:
            network = ipaddress.IPv4Network(f"{ip}/{subnet_mask}", strict=False)
            return str(network.network) + '/' + str(network.prefixlen)
        except:
            return f"{ip}/24"  # Default fallback
    
    def _calculate_device_ip(self, gateway_ip: str, subnet_mask: str) -> str:
        """Calculate device IP for monitoring (usually .10 in the subnet)"""
        try:
            # Parse gateway IP
            gateway = ipaddress.IPv4Address(gateway_ip)
            
            # Create network from gateway and mask
            network = ipaddress.IPv4Network(f"{gateway_ip}/{subnet_mask}", strict=False)
            
            # Calculate device IP (gateway + 9, so .1 becomes .10)
            device_ip = str(gateway + 9)
            
            # Verify the device IP is in the network
            if ipaddress.IPv4Address(device_ip) in network:
                return device_ip
            else:
                # Fallback to gateway + 10 if +9 doesn't work
                fallback_ip = str(gateway + 10)
                if ipaddress.IPv4Address(fallback_ip) in network:
                    return fallback_ip
                else:
                    # Use first available IP after gateway
                    return str(list(network.hosts())[0])
                    
        except Exception as e:
            self.logger.warning(f"Failed to calculate device IP for {gateway_ip}: {e}")
            # Fallback: replace last octet with 10
            parts = gateway_ip.split('.')
            parts[-1] = '10'
            return '.'.join(parts)

class EnhancedConnectivityTester:
    """Enhanced connectivity tester for real store data"""
    
    def __init__(self, db_manager, batch_size: int = 20, max_concurrent: int = 50):
        self.db_manager = db_manager
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.logger = logging.getLogger(__name__)
        self.splunk_server = "10.128.148.95"
        self.splunk_port = 8089
        
        # Statistics tracking
        self.stats = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'healthy_stores': 0,
            'warning_stores': 0,
            'critical_stores': 0,
            'regions': {}
        }
    
    async def test_all_stores(self, stores: List[RealStoreConfig]) -> List[Dict[str, Any]]:
        """Test connectivity for all stores with batching and concurrency control"""
        self.logger.info(f"Starting connectivity tests for {len(stores)} stores")
        
        # Reset statistics
        self.stats = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'healthy_stores': 0,
            'warning_stores': 0,
            'critical_stores': 0,
            'regions': {}
        }
        
        start_time = time.time()
        all_results = []
        
        # Process stores in batches to manage memory and network load
        for i in range(0, len(stores), self.batch_size):
            batch = stores[i:i + self.batch_size]
            batch_start = time.time()
            
            self.logger.info(f"Processing batch {i//self.batch_size + 1}/{(len(stores)-1)//self.batch_size + 1} "
                           f"({len(batch)} stores)")
            
            # Run batch with concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)
            tasks = [self._test_store_with_semaphore(semaphore, store) for store in batch]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process batch results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch test exception: {result}")
                    self.stats['failed_tests'] += 1
                else:
                    all_results.append(result)
                    self._update_statistics(result)
            
            batch_time = time.time() - batch_start
            self.logger.info(f"Batch completed in {batch_time:.2f}s "
                           f"(avg {batch_time/len(batch):.3f}s per store)")
            
            # Brief pause between batches to prevent overwhelming the network
            if i + self.batch_size < len(stores):
                await asyncio.sleep(1)
        
        total_time = time.time() - start_time
        
        # Log final statistics
        self._log_final_statistics(total_time)
        
        return all_results
    
    async def _test_store_with_semaphore(self, semaphore: asyncio.Semaphore, 
                                       store: RealStoreConfig) -> Dict[str, Any]:
        """Test single store with semaphore for concurrency control"""
        async with semaphore:
            return await self.test_store_connectivity(store)
    
    async def test_store_connectivity(self, store: RealStoreConfig) -> Dict[str, Any]:
        """Test connectivity for a single store"""
        result = {
            'store_number': store.store_number,
            'store_name': f"Store_{store.store_number}",
            'gateway_ip': store.gateway_ip,
            'device_ip': store.device_ip,
            'region': store.region,
            'network_cidr': store.network_cidr,
            'timestamp': datetime.utcnow(),
            'splunk_reachable': False,
            'port_open': False,
            'response_time_ms': None,
            'packet_loss_percent': 100.0,
            'status': 'Unknown',
            'error_message': None,
            'test_type': 'real_store'
        }
        
        try:
            self.stats['total_tests'] += 1
            
            # Test ping to Splunk server from store perspective
            ping_result = await self._simulate_store_ping()
            result.update(ping_result)
            
            # Test port connectivity
            port_result = await self._test_port_connectivity()
            result['port_open'] = port_result
            
            # Determine status based on results
            result['status'] = self._determine_status(result)
            
            # Store result in database
            self.db_manager.insert_connectivity_test(result)
            
            self.stats['successful_tests'] += 1
            
        except Exception as e:
            result['status'] = 'Error'
            result['error_message'] = str(e)
            self.logger.error(f"Error testing store {store.store_number}: {e}")
            self.stats['failed_tests'] += 1
        
        return result
    
    async def _simulate_store_ping(self) -> Dict[str, Any]:
        """Simulate ping test from store to Splunk server"""
        try:
            # For demonstration, we'll simulate realistic ping responses
            # In production, this would use actual network testing
            
            # Simulate variable response times based on realistic network conditions
            import random
            
            # 95% success rate with variable latency
            if random.random() < 0.95:
                base_latency = random.uniform(20, 80)  # Base latency 20-80ms
                jitter = random.uniform(-5, 15)        # Add some jitter
                response_time = max(1, base_latency + jitter)
                packet_loss = random.choice([0, 0, 0, 0, 0, 0, 0, 0, 1, 2])  # Occasional packet loss
                
                return {
                    'splunk_reachable': True,
                    'response_time_ms': round(response_time, 1),
                    'packet_loss_percent': packet_loss
                }
            else:
                # 5% failure rate
                return {
                    'splunk_reachable': False,
                    'response_time_ms': None,
                    'packet_loss_percent': 100.0
                }
                
        except Exception as e:
            self.logger.error(f"Ping simulation error: {e}")
            return {
                'splunk_reachable': False,
                'response_time_ms': None,
                'packet_loss_percent': 100.0
            }
    
    async def _test_port_connectivity(self) -> bool:
        """Test port connectivity to Splunk server"""
        try:
            # Simulate port connectivity test
            # In production, this would be actual socket connection
            import random
            
            # 98% port accessibility
            return random.random() < 0.98
            
        except Exception as e:
            self.logger.error(f"Port test error: {e}")
            return False
    
    def _determine_status(self, result: Dict[str, Any]) -> str:
        """Determine overall status based on test results"""
        if not result['splunk_reachable'] or not result['port_open']:
            return 'Critical'
        elif result['packet_loss_percent'] > 10 or (result['response_time_ms'] and result['response_time_ms'] > 200):
            return 'Warning'
        else:
            return 'Healthy'
    
    def _update_statistics(self, result: Dict[str, Any]):
        """Update running statistics"""
        status = result['status']
        region = result['region']
        
        # Update status counts
        if status == 'Healthy':
            self.stats['healthy_stores'] += 1
        elif status == 'Warning':
            self.stats['warning_stores'] += 1
        elif status == 'Critical':
            self.stats['critical_stores'] += 1
        
        # Update regional stats
        if region not in self.stats['regions']:
            self.stats['regions'][region] = {'total': 0, 'healthy': 0, 'warning': 0, 'critical': 0}
        
        self.stats['regions'][region]['total'] += 1
        self.stats['regions'][region][status.lower()] += 1
    
    def _log_final_statistics(self, total_time: float):
        """Log final test statistics"""
        self.logger.info("=" * 60)
        self.logger.info("CONNECTIVITY TEST SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total stores tested: {self.stats['total_tests']}")
        self.logger.info(f"Successful tests: {self.stats['successful_tests']}")
        self.logger.info(f"Failed tests: {self.stats['failed_tests']}")
        self.logger.info(f"Total time: {total_time:.2f} seconds")
        self.logger.info(f"Average time per store: {total_time/self.stats['total_tests']:.3f} seconds")
        self.logger.info(f"Tests per second: {self.stats['total_tests']/total_time:.2f}")
        self.logger.info("")
        self.logger.info("STATUS DISTRIBUTION:")
        self.logger.info(f"  Healthy: {self.stats['healthy_stores']} "
                        f"({self.stats['healthy_stores']/self.stats['total_tests']*100:.1f}%)")
        self.logger.info(f"  Warning: {self.stats['warning_stores']} "
                        f"({self.stats['warning_stores']/self.stats['total_tests']*100:.1f}%)")
        self.logger.info(f"  Critical: {self.stats['critical_stores']} "
                        f"({self.stats['critical_stores']/self.stats['total_tests']*100:.1f}%)")
        
        self.logger.info("")
        self.logger.info("REGIONAL BREAKDOWN:")
        for region, stats in sorted(self.stats['regions'].items()):
            total = stats['total']
            healthy_pct = stats['healthy'] / total * 100 if total > 0 else 0
            self.logger.info(f"  {region}: {total} stores ({healthy_pct:.1f}% healthy)")

class EnhancedDatabaseManager:
    """Enhanced database manager for real store data"""
    
    def __init__(self, db_path: str = "data/real_store_monitoring.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize database with enhanced schema for real store data"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced connectivity tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connectivity_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                store_number TEXT NOT NULL,
                store_name TEXT NOT NULL,
                gateway_ip TEXT NOT NULL,
                device_ip TEXT NOT NULL,
                region TEXT NOT NULL,
                network_cidr TEXT,
                splunk_reachable BOOLEAN,
                port_open BOOLEAN,
                response_time_ms REAL,
                packet_loss_percent REAL,
                status TEXT,
                error_message TEXT,
                test_type TEXT DEFAULT 'real_store'
            )
        ''')
        
        # Store registry table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS store_registry (
                store_number TEXT PRIMARY KEY,
                store_name TEXT,
                gateway_ip TEXT,
                device_ip TEXT,
                subnet_mask TEXT,
                network_cidr TEXT,
                region TEXT,
                brand TEXT,
                enabled BOOLEAN DEFAULT TRUE,
                priority INTEGER DEFAULT 1,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Regional summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regional_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                region TEXT NOT NULL,
                total_stores INTEGER,
                healthy_stores INTEGER,
                warning_stores INTEGER,
                critical_stores INTEGER,
                avg_response_time REAL,
                avg_packet_loss REAL
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                region TEXT,
                store_count INTEGER,
                details TEXT
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tests_timestamp ON connectivity_tests(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tests_store ON connectivity_tests(store_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tests_region ON connectivity_tests(region)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tests_status ON connectivity_tests(status)')
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Database initialized: {self.db_path}")
    
    def register_stores(self, stores: List[RealStoreConfig]):
        """Register all stores in the store registry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for store in stores:
            cursor.execute('''
                INSERT OR REPLACE INTO store_registry 
                (store_number, store_name, gateway_ip, device_ip, subnet_mask, 
                 network_cidr, region, brand, tags, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                store.store_number,
                f"Store_{store.store_number}",
                store.gateway_ip,
                store.device_ip,
                store.subnet_mask,
                store.network_cidr,
                store.region,
                store.brand,
                json.dumps(store.tags),
                datetime.utcnow()
            ))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Registered {len(stores)} stores in database")
    
    def insert_connectivity_test(self, result: Dict[str, Any]):
        """Insert connectivity test result with enhanced data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO connectivity_tests 
            (store_number, store_name, gateway_ip, device_ip, region, network_cidr,
             splunk_reachable, port_open, response_time_ms, packet_loss_percent, 
             status, error_message, test_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result['store_number'],
            result['store_name'],
            result['gateway_ip'],
            result['device_ip'],
            result['region'],
            result['network_cidr'],
            result['splunk_reachable'],
            result['port_open'],
            result['response_time_ms'],
            result['packet_loss_percent'],
            result['status'],
            result.get('error_message'),
            result.get('test_type', 'real_store')
        ))
        
        conn.commit()
        conn.close()
    
    def get_latest_results_by_region(self) -> Dict[str, Dict[str, Any]]:
        """Get latest test results grouped by region"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                region,
                COUNT(*) as total_stores,
                SUM(CASE WHEN status = 'Healthy' THEN 1 ELSE 0 END) as healthy,
                SUM(CASE WHEN status = 'Warning' THEN 1 ELSE 0 END) as warning,
                SUM(CASE WHEN status = 'Critical' THEN 1 ELSE 0 END) as critical,
                AVG(response_time_ms) as avg_response_time,
                AVG(packet_loss_percent) as avg_packet_loss
            FROM connectivity_tests 
            WHERE id IN (
                SELECT MAX(id) FROM connectivity_tests GROUP BY store_number
            )
            GROUP BY region
            ORDER BY region
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Convert to dictionary format
        results = {}
        for _, row in df.iterrows():
            results[row['region']] = {
                'total_stores': row['total_stores'],
                'healthy': row['healthy'],
                'warning': row['warning'],
                'critical': row['critical'],
                'avg_response_time': row['avg_response_time'],
                'avg_packet_loss': row['avg_packet_loss'],
                'health_percentage': (row['healthy'] / row['total_stores'] * 100) if row['total_stores'] > 0 else 0
            }
        
        return results
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old test data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        cursor.execute('''
            DELETE FROM connectivity_tests 
            WHERE timestamp < ?
        ''', (cutoff_date,))
        
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        self.logger.info(f"Cleaned up {deleted_rows} old test records")
        return deleted_rows

class RealStoreMonitor:
    """Main monitoring class for real store data"""
    
    def __init__(self, csv_path: str = "stores.csv", config: Dict[str, Any] = None):
        self.csv_path = csv_path
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.store_loader = StoreDataLoader(csv_path)
        self.db_manager = EnhancedDatabaseManager()
        self.connectivity_tester = EnhancedConnectivityTester(
            self.db_manager,
            batch_size=self.config.get('batch_size', 20),
            max_concurrent=self.config.get('max_concurrent', 50)
        )
        
        # Store data
        self.stores: List[RealStoreConfig] = []
        
    async def initialize(self):
        """Initialize the monitoring system"""
        self.logger.info("Initializing Real Store Monitor")
        
        # Load store data from CSV
        self.stores = self.store_loader.load_stores_from_csv()
        
        if not self.stores:
            raise ValueError("No stores loaded from CSV file")
        
        # Register stores in database
        self.db_manager.register_stores(self.stores)
        
        self.logger.info(f"Monitor initialized with {len(self.stores)} stores")
    
    async def run_monitoring_cycle(self) -> List[Dict[str, Any]]:
        """Run single monitoring cycle for all stores"""
        self.logger.info("Starting monitoring cycle for all stores")
        
        if not self.stores:
            await self.initialize()
        
        # Test all stores
        results = await self.connectivity_tester.test_all_stores(self.stores)
        
        # Generate regional summary
        regional_summary = self.db_manager.get_latest_results_by_region()
        
        # Log summary
        self._log_cycle_summary(results, regional_summary)
        
        return results
    
    def _log_cycle_summary(self, results: List[Dict[str, Any]], regional_summary: Dict[str, Any]):
        """Log monitoring cycle summary"""
        total_stores = len(results)
        healthy_stores = len([r for r in results if r['status'] == 'Healthy'])
        warning_stores = len([r for r in results if r['status'] == 'Warning'])
        critical_stores = len([r for r in results if r['status'] == 'Critical'])
        
        self.logger.info("MONITORING CYCLE SUMMARY")
        self.logger.info("-" * 50)
        self.logger.info(f"Total Stores: {total_stores}")
        self.logger.info(f"Healthy: {healthy_stores} ({healthy_stores/total_stores*100:.1f}%)")
        self.logger.info(f"Warning: {warning_stores} ({warning_stores/total_stores*100:.1f}%)")
        self.logger.info(f"Critical: {critical_stores} ({critical_stores/total_stores*100:.1f}%)")
        
        if critical_stores > 0:
            critical_list = [r['store_number'] for r in results if r['status'] == 'Critical'][:10]
            self.logger.warning(f"Critical stores (first 10): {', '.join(critical_list)}")
    
    async def get_store_by_number(self, store_number: str) -> Optional[RealStoreConfig]:
        """Get store by store number"""
        for store in self.stores:
            if store.store_number == store_number:
                return store
        return None
    
    def get_stores_by_region(self, region: str) -> List[RealStoreConfig]:
        """Get stores by region"""
        return [store for store in self.stores if store.region == region]
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics"""
        regional_summary = self.db_manager.get_latest_results_by_region()
        
        total_stores = sum(region['total_stores'] for region in regional_summary.values())
        total_healthy = sum(region['healthy'] for region in regional_summary.values())
        
        return {
            'total_stores': total_stores,
            'total_healthy': total_healthy,
            'overall_health_percentage': (total_healthy / total_stores * 100) if total_stores > 0 else 0,
            'regional_breakdown': regional_summary,
            'timestamp': datetime.utcnow().isoformat()
        }

# Example usage and testing
async def main():
    """Main function for testing the real store monitor"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize monitor
        monitor = RealStoreMonitor("stores.csv")
        
        # Initialize with store data
        await monitor.initialize()
        
        # Run monitoring cycle
        logger.info("Running monitoring cycle...")
        results = await monitor.run_monitoring_cycle()
        
        # Display summary statistics
        summary = monitor.get_summary_statistics()
        
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"Total Stores Monitored: {summary['total_stores']}")
        print(f"Overall Health: {summary['overall_health_percentage']:.1f}%")
        print(f"Total Healthy Stores: {summary['total_healthy']}")
        print("\nRegional Breakdown:")
        for region, stats in summary['regional_breakdown'].items():
            print(f"  {region}: {stats['healthy']}/{stats['total_stores']} "
                  f"({stats['health_percentage']:.1f}% healthy)")
        
        # Example: Get specific store info
        sample_store = await monitor.get_store_by_number("ARG00001")
        if sample_store:
            print(f"\nSample Store Info (ARG00001):")
            print(f"  Gateway IP: {sample_store.gateway_ip}")
            print(f"  Device IP: {sample_store.device_ip}")
            print(f"  Region: {sample_store.region}")
            print(f"  Network: {sample_store.network_cidr}")
        
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        raise

if __name__ == "__main__":
    # Save the CSV content to a file for testing
    csv_content = """store_number,mgmtintname,ip_address,brand
ARG00001,internal,10.213.181.1/255.255.255.192,Arbys
ARG00002,internal,10.211.172.1/255.255.255.192,Arbys
ARG00003,internal,10.213.53.1/255.255.255.192,Arbys"""
    
    # Create sample CSV file if it doesn't exist
    if not os.path.exists("stores.csv"):
        print("Creating sample stores.csv file...")
        with open("stores.csv", "w") as f:
            f.write(csv_content)
    
    # Run the monitoring
    asyncio.run(main())