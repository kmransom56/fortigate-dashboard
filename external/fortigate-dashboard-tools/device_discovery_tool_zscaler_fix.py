import socket
import subprocess
import json
import csv
import pandas as pd
import requests
import ipaddress
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Optional
import time


class CurlBasedMacLookup:
    """
    MAC address vendor lookup using curl, works behind Zscaler
    """
    def __init__(self):
        self.cache: Dict[str,str] = {}
        self.curl_available = self._test_curl()

    def _test_curl(self) -> bool:
        try:
            res = subprocess.run(['curl','--version'],
                                 capture_output=True, text=True, timeout=3)
            return res.returncode == 0
        except:
            return False

    def lookup(self, mac: str) -> Optional[str]:
        """
        Try a short list of APIs with curl -k to ignore cert errors
        """
        if not self.curl_available:
            return None
        if mac in self.cache:
            return self.cache[mac]

        apis = [
            ('MacVendors.com',    f"https://api.macvendors.com/{mac}", 8),
            ('MacVendors.co',     f"https://macvendors.co/api/{mac}", 10),
        ]
        for name, url, to in apis:
            for attempt in range(3):
                try:
                    cmd = [
                        'curl','-s','-k','--max-time',str(to),
                        '--user-agent','MAC-Lookup-Curl/1.0',
                        url
                    ]
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=to+2)
                    out = res.stdout.strip()
                    if res.returncode == 0 and len(out)>3 and 'error' not in out.lower():
                        self.cache[mac] = out
                        return out
                except subprocess.TimeoutExpired:
                    continue
                except:
                    break
        return None


class DeviceDiscovery:
    """
    Discover vendor, hostname, open ports, type, and migration risk.
    """
    def __init__(self):
        self.oui_cache: Dict[str,str] = {}
        self.oui_db = self._load_oui_db()
        self.curl_lookup = CurlBasedMacLookup()

    def _load_oui_db(self) -> Dict[str,str]:
        db: Dict[str,str] = {
            '1866DA': 'Hangzhou Hikvision Digital Technology Co.,Ltd.',
            # ... (other mappings as before) ...
            '0050F2': 'Microsoft Corporation',
            '001B63': 'Apple Inc.',
            '000C29': 'VMware Inc.',
            # add your full list here...
        }
        print(f"Loaded {len(db)} OUI mappings")
        return db

    def get_mac_vendor(self, mac: str) -> str:
        clean = mac.replace(':','').replace('-','').upper()
        if len(clean) < 6:
            return "Invalid MAC"
        oui = clean[:6]

        # 1) local DB
        if oui in self.oui_db:
            return self.oui_db[oui]

        # 2) cache
        if oui in self.oui_cache:
            return self.oui_cache[oui]

        # 3) curl lookup
        vendor = self.curl_lookup.lookup(clean)
        if vendor:
            self.oui_cache[oui] = vendor
            return vendor

        # 4) pattern match
        pat = self._identify_pattern(oui)
        if pat:
            self.oui_cache[oui] = pat
            return pat

        # 5) fallback
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

    def ping(self, ip: str, timeout: int=2) -> bool:
        try:
            cmd = ['ping','-n','1','-w',str(timeout*1000),ip]
            res = subprocess.run(cmd,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
            return res.returncode == 0
        except:
            return False

    def get_hostname(self, ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "Unknown"

    def scan_ports(self, ip: str, ports: List[int]=None) -> List[int]:
        if ports is None:
            ports = [22,80,135,443,3389,5985]
        def chk(p):
            try:
                s = socket.socket()
                s.settimeout(1)
                if s.connect_ex((ip,p))==0:
                    return p
            except:
                pass
            return None

        openp: List[int] = []
        with concurrent.futures.ThreadPoolExecutor(10) as ex:
            futures = [ex.submit(chk,p) for p in ports]
            for f in concurrent.futures.as_completed(futures):
                r = f.result()
                if r:
                    openp.append(r)
        return sorted(openp)

    def identify_type(self, info: Dict) -> str:
        mac = info.get('mac_address','').replace(':','').upper()
        if mac.startswith('1866DA'):
            return "Hikvision IP Camera/NVR"
        ports = info.get('open_ports',[])
        if 3389 in ports or 5985 in ports:
            return "Windows Server"
        if 22 in ports and 80 in ports:
            return "Linux Server"
        vend = info.get('vendor','').lower()
        if 'cisco' in vend:
            return "Cisco Network Device"
        # ... more rules ...
        return "Unknown Device"

    def risk_level(self, info: Dict) -> str:
        resp = info.get('responsive',False)
        typ  = info.get('identified_type','').lower()
        ports= info.get('open_ports',[])
        mac  = info.get('mac_address','').replace(':','').upper()
        if mac.startswith('1866DA') and not resp:
            return "LOW - Device Not Responsive"
        if any(x in typ for x in ['server','firewall','router']):
            return "HIGH - Critical"
        if 22 in ports or 3389 in ports:
            return "MEDIUM - Admin Access"
        if not resp:
            return "LOW - Not Responsive"
        return "LOW - Standard"

# Bulk lookup
def bulk_mac_lookup(macs: List[str]) -> Dict[str,str]:
    disc = DeviceDiscovery()
    res: Dict[str,str] = {}
    groups: Dict[str,List[str]] = {}
    for m in macs:
        c = m.replace(':','').upper()[:6]
        groups.setdefault(c, []).append(m)
    for grp in groups.values():
        vend = disc.get_mac_vendor(grp[0])
        for m in grp:
            res[m] = vend
    return res

def analyze_port2_devices(devs: List[Dict]) -> pd.DataFrame:
    disc = DeviceDiscovery()
    macs = [d.get('mac_address') for d in devs if d.get('mac_address')]
    vendor_map = bulk_mac_lookup(macs) if macs else {}
    records: List[Dict] = []

    for i,d in enumerate(devs,1):
        rec = d.copy()
        mac = rec.get('mac_address','')
        rec['vendor'] = vendor_map.get(mac,"No MAC")
        ip = rec.get('ip_address','')
        if ip and ip not in ['','None','Unknown']:
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
    return pd.DataFrame(records)

def create_migration_plan(df: pd.DataFrame) -> None:
    print("\nMIGRATION PLAN")
    for level,grp in df.groupby('migration_risk'):
        print(f"\n{level} ({len(grp)} devices)")
        for _,row in grp.iterrows():
            print(f"  {row.mac_address} → {row.identified_type} ({row.vendor})")

def save_report(df: pd.DataFrame) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"port2_migration_plan_{ts}.csv"
    df.to_csv(fname, index=False)
    print(f"Saved {fname}")

def main():
    try:
        df = pd.read_csv('port2_devices_report.csv')
    except FileNotFoundError:
        print("port2_devices_report.csv not found.")
        return
    devs = df.to_dict('records')
    enhanced = analyze_port2_devices(devs)
    create_migration_plan(enhanced)
    save_report(enhanced)

if __name__ == "__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="help":
        print("Usage: python device_discovery_tool_enhanced.py")
    else:
        main()