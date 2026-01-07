Self‑documenting “API schema downloader” script
You want something that hits FortiGate’s self‑documenting REST API endpoints and writes schemas/examples into a folder so your code can reuse them (for type hints, validation, or offline dev). FortiOS 7.6 exposes REST API references via the API admin framework and “Using APIs” section.​

Pattern for FortiOS:

Use an API admin account/token (System → Administrators → REST API Admin) with at least read on all required paths.

Call the “schema” endpoints or use the inline API preview endpoints, typically under /api/v2/cmdb/... and /api/v2/monitor/....

Save both a “schema” view and a “sample payload” view to disk in a structured folder layout (e.g. fortios_schemas/cmdb/firewall/policy.json).

Example Python script (single file) to do that:

python
import os
import json
import requests
from urllib.parse import quote

FORTIGATE_HOST = os.getenv("FGT_HOST", "192.0.2.1")
API_TOKEN      = os.getenv("FGT_TOKEN", "YOUR_TOKEN")
OUTPUT_DIR     = os.getenv("FGT_SCHEMA_DIR", "./fortios_api_schemas")

# Minimal set of endpoints you care about initially
ENDPOINTS = {
    # Device inventory (wired + wireless)
    "device_inventory": "/api/v2/monitor/user/device/query",
    # FortiSwitch managed switch status
    "switch_status": "/api/v2/monitor/switch-controller/managed-switch/status",
    # Wireless clients / WiFi controller (varies by model; example monitor path)
    "wifi_clients": "/api/v2/monitor/wireless-controller/clients",
    # Interfaces (for port names)
    "interfaces": "/api/v2/cmdb/system/interface",
}

session = requests.Session()
session.verify = False  # lab / self-signed; change for prod

def fortios_get(path: str, params=None):
    url = f"https://{FORTIGATE_HOST}{path}"
    params = dict(params or {})
    params["access_token"] = API_TOKEN
    resp = session.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def save_json(rel_path: str, payload):
    full_path = os.path.join(OUTPUT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def main():
    # 1) Save “live sample” responses for known endpoints
    for name, path in ENDPOINTS.items():
        try:
            data = fortios_get(path)
            save_json(f"samples/{name}.json", data)
            print(f"Saved sample for {name} from {path}")
        except Exception as e:
            print(f"Failed to fetch {name} ({path}): {e}")

    # 2) Discover and save CMDB schemas for objects you care about
    # Note: schema discovery strategy – call ?schema=1 or ?action=schema if supported in your build.
    cmdb_paths = [
        "/api/v2/cmdb/system/interface",
        "/api/v2/cmdb/wireless-controller/wtp",
        "/api/v2/cmdb/wireless-controller/vap",
        "/api/v2/cmdb/switch-controller/managed-switch",
    ]

    for path in cmdb_paths:
        try:
            # Many FortiOS builds support ?schema=1 on CMDB endpoints
            data = fortios_get(path, params={"schema": "1"})
            safe_path = quote(path.strip("/").replace("/", "_"), safe="")
            save_json(f"schemas/{safe_path}.json", data)
            print(f"Saved schema for {path}")
        except Exception as e:
            print(f"Failed to fetch schema for {path}: {e}")

if __name__ == "__main__":
    main()
How you reuse this:

Point FGT_HOST, FGT_TOKEN, and FGT_SCHEMA_DIR at your PoC box and project repo.

Run it once per firmware you care about (e.g. 7.6.0, 7.6.4) and commit the schema/samples directory into your codebase.

In your main app, load JSON from fortios_api_schemas/samples/device_inventory.json etc. for:

Quick mocking

Input/output validation (pydantic, Marshmallow)

Tests that don’t need live FortiGate access.

Tying in wireless clients and location APIs
For wireless, you can:

Pull WiFi clients via FortiGate’s WiFi & Switch Controller monitors (GUI view is “WiFi Clients”; backend monitor endpoints reflect the same data).​

For advanced location/BLE, FortiAP 7.6 provides a dedicated API (LBS station info) which you enable per AP (wireless-controller WTP and BLE profile).

Add those monitor and LBS endpoints into the ENDPOINTS list above, run the schema downloader, and your self‑documenting layer will always have current wireless client payload shapes alongside wired device inventory.​