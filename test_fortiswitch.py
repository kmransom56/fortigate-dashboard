import os
import requests
import json

# ======== CONFIGURATION ========
FORTIGATE_IP = "192.168.0.254"  # FortiGate management IP
SWITCH_ID = "NETINTEGRATESW"    # Switch ID as known to FortiGate
API_TOKEN = os.getenv("FORTIGATE_API_TOKEN")

if not API_TOKEN:
    raise EnvironmentError(
        "Environment variable FORTIGATE_API_TOKEN not set. "
        "Use: export FORTIGATE_API_TOKEN=your-token"
    )

# Disable HTTPS warnings for demo purposes (optional)
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# ======== GENERIC API GET FUNCTION ========
def fortigate_api_get(endpoint, params=None):
    """Perform GET request to FortiGate API and return JSON."""
    url = f"https://{FORTIGATE_IP}:8443/api/v2/{endpoint}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
    
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} {response.text}")
    
    try:
        return response.json()
    except ValueError:
        raise Exception(f"Response was not JSON: {response.text}")

# ======== PULL SYSTEM STATUS ========
status_data = fortigate_api_get(
    "monitor/switch-controller/managed-switch/status",
    params={"switch-id": SWITCH_ID}
)

# ======== PULL INTERFACE INFO ========
interface_data = fortigate_api_get(
    "monitor/switch-controller/managed-switch/interface",
    params={"switch-id": SWITCH_ID}
)

# ======== MERGE INTO ONE OBJECT ========
consolidated = {
    "switch_id": SWITCH_ID,
    "system_status": status_data.get("results", {}),
    "interfaces": interface_data.get("results", [])
}

# ======== OUTPUT RESULT ========
print(json.dumps(consolidated, indent=4))
