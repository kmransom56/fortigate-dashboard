import requests
import urllib3
import json
import csv
from pathlib import Path

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
FMG_HOST = "https://10.128.144.132:443/jsonrpc"
USERNAME = "ibadmin"
PASSWORD = "9m!e47IExO7syk@2"

# Create output directory
output_dir = Path("fmg_export")
output_dir.mkdir(exist_ok=True)

class FortiManagerAPI:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.session = self.login()

    def login(self):
        payload = {
            "id": 1,
            "method": "exec",
            "params": [
                {
                    "url": "/sys/login/user",
                    "data": {
                        "user": self.username,
                        "passwd": self.password
                    }
                }
            ]
        }
        response = requests.post(self.host, json=payload, verify=False)
        data = response.json()
        session = data.get("session")
        if not session:
            raise Exception("Login failed.")
        return session

    def call_api(self, url):
        payload = {
            "id": 1,
            "method": "get",
            "params": [{"url": url}],
            "session": self.session
        }
        response = requests.post(self.host, json=payload, verify=False)
        return response.json()

    def get_adoms(self):
        result = self.call_api("/dvmdb/adom")
        return [adom["name"] for adom in result.get("result", [{}])[0].get("data", [])]

    def get_policy_packages(self, adom):
        data = self.call_api(f"/pm/pkg/adom/{adom}")
        return [pkg["name"] for pkg in data.get("result", [{}])[0].get("data", [])]

    def get_firewall_policies(self, adom, package, filter_keyword=None):
        url = f"/pm/config/adom/{adom}/pkg/{package}/firewall/policy"
        data = self.call_api(url)
        policies = data.get("result", [{}])[0].get("data", [])
        if filter_keyword:
            policies = [p for p in policies if filter_keyword.lower() in p.get("name", "").lower()]
        return policies

    def get_url_filters(self, adom):
        url = f"/pm/config/adom/{adom}/obj/webfilter/urlfilter"
        return self.call_api(url).get("result", [{}])[0].get("data", [])

    def get_services(self, adom):
        url = f"/pm/config/adom/{adom}/obj/firewall/service/custom"
        return self.call_api(url).get("result", [{}])[0].get("data", [])

    def get_devices(self):
        url = "/dvmdb/device"
        data = self.call_api(url)
        return data.get("result", [{}])[0].get("data", [])

    def get_device_interfaces(self, device_name):
        url = f"/pm/config/device/{device_name}/global/system/interface"
        return self.call_api(url).get("result", [{}])[0].get("data", [])

    def export_json(self, filename, data):
        with open(output_dir / f"{filename}.json", "w") as f:
            json.dump(data, f, indent=2)

    def export_csv(self, filename, data):
        if not data:
            return

        # Collect all possible keys across all dictionaries
        all_keys = set()
        for entry in data:
            all_keys.update(entry.keys())
        keys = sorted(all_keys)

        with open(output_dir / f"{filename}.csv", "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

def main():
    fmg = FortiManagerAPI(FMG_HOST, USERNAME, PASSWORD)
    adoms = fmg.get_adoms()

    for adom in adoms:
        print(f"\n🔄 Processing ADOM: {adom}")
        packages = fmg.get_policy_packages(adom)

        for pkg in packages:
            print(f"  📦 Package: {pkg}")
            policies = fmg.get_firewall_policies(adom, pkg, filter_keyword="allow")
            fmg.export_json(f"{adom}_{pkg}_firewall_policies", policies)
            fmg.export_csv(f"{adom}_{pkg}_firewall_policies", policies)

        urlfilters = fmg.get_url_filters(adom)
        fmg.export_json(f"{adom}_urlfilters", urlfilters)
        fmg.export_csv(f"{adom}_urlfilters", urlfilters)

        services = fmg.get_services(adom)
        fmg.export_json(f"{adom}_services", services)
        fmg.export_csv(f"{adom}_services", services)

    devices = fmg.get_devices()
    for device in devices:
        interfaces = fmg.get_device_interfaces(device["name"])
        fmg.export_json(f"{device['name']}_interfaces", interfaces)
        fmg.export_csv(f"{device['name']}_interfaces", interfaces)

    print("\n✅ Export complete. Files saved in:", output_dir.resolve())

main()
