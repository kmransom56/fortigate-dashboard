#!/usr/bin/env python3
import csv
import socket
import subprocess
import json
import os
import requests
import ipaddress
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import signal
import sys
import argparse

# parse CLI flags early
parser = argparse.ArgumentParser()
parser.add_argument('--download-ieee', action='store_true', help='Download IEEE OUI database')
args = parser.parse_args()
DOWNLOAD_IEEE = args.download_ieee


class CurlBasedMacLookup:
    """
    MAC address vendor lookup using curl, works behind Zscaler
    """
    def __init__(self):
        self.cache: Dict[str, str] = {}
        self.curl_available = self._test_curl()
        self.network_available: Optional[bool] = None
        self.ieee_db: Dict[str, str] = {}
        self.lookup_metadata: Dict[str, Dict] = {}
        if DOWNLOAD_IEEE:
            self.download_ieee_oui_database()

    def _test_curl(self) -> bool:
        try:
            res = subprocess.run(['curl', '--version'], capture_output=True, text=True, timeout=3)
            return res.returncode == 0
        except Exception:
            return False
    
    def test_network_connectivity(self) -> bool:
        """
        Test basic network connectivity before online lookups
        """
        if self.network_available is not None:
            return self.network_available
        test_urls = [
            'https://httpbin.org/get',
            'https://api.github.com',
            'https://www.google.com'
        ]
        for url in test_urls:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    self.network_available = True
                    return True
            except Exception:
                continue
        self.network_available = False
        print("Network offline: skipping online vendor lookups")
        return False

    def lookup(self, mac: str) -> Dict[str, Any]:
        """
        Try a short list of APIs with curl -k to ignore cert errors
        """
        if not self.test_network_connectivity():
            return {'vendor': None, 'source': 'offline', 'ssl_bypassed': False}
        if not self.curl_available:
            return {'vendor': None, 'source': 'no_curl', 'ssl_bypassed': False}
        clean = mac.replace(':', '').replace('-', '').upper()
        # IEEE DB lookup
        if clean[:6] in self.ieee_db:
            vendor = self.ieee_db[clean[:6]]
            return {'vendor': vendor, 'source': 'ieee_db', 'ssl_bypassed': False}

        apis = [
            ('MacVendors.com',    f"https://api.macvendors.com/{clean}", 8),
            ('MacVendors.co',     f"https://macvendors.co/api/{clean}", 10),
        ]
        for name, url, timeout_sec in apis:
            for attempt in range(3):
                print(f"🔍 [{name}] attempt {attempt+1} for MAC {clean}")
                try:
                    cmd = ['curl', '-s', '-k', '--max-time', str(timeout_sec),
                           '--user-agent', 'MAC-Lookup-Curl/1.0', url]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec + 2)
                    out = res.stdout.strip()
                    if res.returncode == 0 and len(out) > 3 and 'error' not in out.lower():
                        self.cache[clean] = out
                        return {'vendor': out, 'source': name, 'ssl_bypassed': False}
                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    break
        # Fallback: Python requests without SSL verify
        try:
            import urllib3
            urllib3.disable_warnings()
            resp = requests.get(f"https://api.macvendors.com/{clean}", timeout=10, verify=False,
                                headers={'User-Agent': 'MAC-Lookup-Requests/1.0'})
            if resp.status_code == 200:
                text = resp.text.strip()
                if len(text) > 3 and 'error' not in text.lower():
                    self.cache[clean] = text
                    return {'vendor': text, 'source': 'requests', 'ssl_bypassed': True}
        except Exception:
            pass
        # Pattern fallback
        pat = self._identify_pattern(clean[:6])
        vendor = pat if pat else f"Unknown Vendor (OUI: {clean[:6]})"
        return {'vendor': vendor, 'source': 'pattern', 'ssl_bypassed': False}

    def _load_oui_db(self) -> Dict[str, str]:
        db: Dict[str, str] = {
            '1866DA': 'Hangzhou Hikvision Digital Technology Co.,Ltd.',
            '0050F2': 'Microsoft Corporation',
            '001B63': 'Apple Inc.',
            '000C29': 'VMware Inc.',
            # add your full list here...
        }
        # Merge external local OUI database if available
        try:
            from curl_based_mac_lookup import CurlMacLookup
            ext_db = CurlMacLookup().local_oui_database
            db.update(ext_db)
            print(f"Merged {len(ext_db)} external OUIs from curl_based_mac_lookup")
        except Exception:
            pass
        print(f"Loaded {len(db)} total OUI mappings")
        return db
    
    def download_ieee_oui_database(self) -> None:
        """
        Download and parse the IEEE OUI database for offline lookups
        """
        url = 'https://standards-oui.ieee.org/oui.txt'
        try:
            resp = requests.get(url, timeout=20, verify=False)
            raw = resp.text.splitlines()
            for line in raw:
                if '(hex)' in line:
                    parts = line.split('(hex)')
                    oui = parts[0].strip().replace('-', '').upper()
                    vendor = parts[1].strip()
                    self.ieee_db[oui] = vendor
            print(f"Downloaded IEEE OUI DB: {len(self.ieee_db)} entries")
        except Exception as e:
            print(f"Failed to download IEEE DB: {e}")

    def get_mac_vendor(self, mac: str) -> str:
        clean = mac.replace(':', '').replace('-', '').upper()
        if len(clean) < 6:
            return "Invalid MAC"
        oui = clean[:6]

        # local DB
        if oui in self.oui_db:
            return self.oui_db[oui]

        # cache
        if oui in self.oui_cache:
            return self.oui_cache[oui]

        # curl lookup
        info = self.curl_lookup.lookup(clean)
        vendor = info.get('vendor')
        # record metadata per OUI if desired
        self.lookup_metadata[oui] = info
        if vendor:
            self.oui_cache[oui] = vendor
            return vendor

        # pattern match
        pat = self._identify_pattern(oui)
        if pat:
            self.oui_cache[oui] = pat
            return pat

        # fallback
        unk = f"Unknown Vendor (OUI: {oui})"
        self.oui_cache[oui] = unk
        return unk

    def _identify_pattern(self, oui: str) -> Optional[str]:
        if oui.startswith('000C29'):
            return "VMware Virtual Machine"
        if oui.startswith('0050F2'):
            return "Microsoft Corporation"
        if oui.startswith('1866'):
            return "Hikvision IP Camera/NVR"
        # ... add other patterns ...
        return None

    def ping(self, ip: str, timeout: int = 2) -> bool:
        try:
            cmd = ['ping', '-n', '1', '-w', str(timeout * 1000), ip]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0
        except Exception:
            return False

    def get_hostname(self, ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return "Unknown"

    def scan_ports(self, ip: str, ports: List[int] = None) -> List[int]:
        if ports is None:
            ports = [22, 80, 135, 443, 3389, 5985]

        def check_port(p: int) -> Optional[int]:
            try:
                s = socket.socket()
                s.settimeout(1)
                if s.connect_ex((ip, p)) == 0:
                    return p
            except Exception:
                pass
            return None

        open_ports: List[int] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_port, p) for p in ports]
            for future in concurrent.futures.as_completed(futures):
                port = future.result()
                if port:
                    open_ports.append(port)
        return sorted(open_ports)

    def identify_type(self, info: Dict) -> str:
        mac = info.get('mac_address', '').replace(':', '').upper()
        if mac.startswith('1866DA'):
            return "Hikvision IP Camera/NVR"
        ports = info.get('open_ports', [])
        if 3389 in ports or 5985 in ports:
            return "Windows Server"
        if 22 in ports and 80 in ports:
            return "Linux Server"
        vend = info.get('vendor', '').lower()
        if 'cisco' in vend:
            return "Cisco Network Device"
        # ... more rules ...
        return "Unknown Device"

    def risk_level(self, info: Dict) -> str:
        resp = info.get('responsive', False)
        typ = info.get('identified_type', '').lower()
        ports = info.get('open_ports', [])
        mac = info.get('mac_address', '').replace(':', '').upper()
        if mac.startswith('1866DA') and not resp:
            return "LOW - Device Not Responsive"
        if any(x in typ for x in ['server', 'firewall', 'router']):
            return "HIGH - Critical"
        if 22 in ports or 3389 in ports:
            return "MEDIUM - Admin Access"
        if not resp:
            return "LOW - Not Responsive"
        return "LOW - Standard"

# Bulk MAC lookup with caching per OUI
def bulk_mac_lookup(macs: List[str]) -> Dict[str, str]:
    print(f"Bulk MAC lookup for {len(macs)} addresses")
    disc = DeviceDiscovery()
    result: Dict[str, str] = {}
    groups: Dict[str, List[str]] = {}
    for m in macs:
        key = m.replace(':', '').upper()[:6]
        groups.setdefault(key, []).append(m)
    for idx, (oui, group) in enumerate(groups.items(), start=1):
        print(f"[{idx}/{len(groups)}] Lookup OUI {oui} for {len(group)} MACs")
        vend = disc.get_mac_vendor(group[0])
        for m in group:
            result[m] = vend
    return result

# Analyze devices: ping, hostname, ports, type, risk
def analyze_port2_devices(devs: List[Dict]) -> List[Dict]:
    print(f"Analyzing {len(devs)} devices...")
    disc = DeviceDiscovery()
    macs = [d.get('mac_address') for d in devs if d.get('mac_address')]
    vendor_map = bulk_mac_lookup(macs) if macs else {}
    records: List[Dict] = []
    for idx, d in enumerate(devs, start=1):
        mac = d.get('mac_address', '')
        ip = d.get('ip_address', '')
        print(f"[{idx}/{len(devs)}] Processing MAC {mac}, IP {ip}")
        rec = d.copy()
        rec['vendor'] = vendor_map.get(mac, "No MAC")
        if ip and ip not in ['', 'None', 'Unknown']:
            rec['responsive'] = disc.ping(ip)
            if rec['responsive']:
                rec['hostname'] = disc.get_hostname(ip)
                rec['open_ports'] = disc.scan_ports(ip)
            else:
                rec['hostname'] = "Not Responsive"
                rec['open_ports'] = []
        else:
            rec['responsive'] = False
            rec['hostname'] = "No IP"
            rec['open_ports'] = []
        rec['identified_type'] = disc.identify_type(rec)
        rec['migration_risk'] = disc.risk_level(rec)
        records.append(rec)
    return records

def create_migration_plan(records: List[Dict]) -> None:
    print("\nMIGRATION PLAN")
    groups: Dict[str, List[Dict]] = {}
    for rec in records:
        groups.setdefault(rec.get('migration_risk', 'Unknown'), []).append(rec)
    for level, grp in groups.items():
        print(f"\n{level} ({len(grp)} devices)")
        for row in grp:
            print(f"  {row.get('mac_address')} → {row.get('identified_type')} ({row.get('vendor')})")

def save_report(records: List[Dict]) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"port2_migration_plan_{ts}.csv"
    if records:
        keys = records[0].keys()
        with open(fname, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
    print(f"Saved report to {fname}")

def main() -> None:
    try:
        with open('port2_devices_report.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            devs = list(reader)
    except FileNotFoundError:
        print("Error: 'port2_devices_report.csv' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    enhanced = analyze_port2_devices(devs)
    create_migration_plan(enhanced)
    save_report(enhanced)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    main()
