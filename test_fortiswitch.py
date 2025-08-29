import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ======== CONFIGURATION ========
FORTIGATE_IP = "192.168.0.254"  # FortiGate management IP
SWITCH_ID = os.getenv("FORTIGATE_SWITCH_NAME", "NETINTEGRATESW")  # Switch ID from .env

# Load API token from file
API_TOKEN_FILE = os.getenv("FORTIGATE_API_TOKEN_FILE", "./secrets/fortigate_api_token.txt")
if os.path.exists(API_TOKEN_FILE):
    with open(API_TOKEN_FILE, 'r') as f:
        API_TOKEN = f.read().strip()
else:
    API_TOKEN = os.getenv("FORTIGATE_API_TOKEN")

if not API_TOKEN:
    raise EnvironmentError(
        f"API token not found in {API_TOKEN_FILE} or FORTIGATE_API_TOKEN environment variable. "
        "Please check your .env file and secrets directory."
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
    
    print(f"Making request to: {url}")
    if params:
        print(f"With parameters: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=15)
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"Response text: {response.text}")
            raise Exception(f"API request failed: {response.status_code} {response.text}")
        
        try:
            return response.json()
        except ValueError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response.text}")
            raise Exception(f"Response was not JSON: {response.text}")
            
    except requests.exceptions.Timeout:
        raise Exception(f"Request timed out after 15 seconds for endpoint: {endpoint}")
    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Connection error: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error: {e}")

# ======== PULL SYSTEM STATUS ========
status_data = fortigate_api_get(
    "monitor/switch-controller/managed-switch/status",
    params={"switch-id": SWITCH_ID}
)

# ======== EXTRACT INTERFACE INFO FROM STATUS ========
# The interface data is included in the status response
switch_info = status_data.get("results", [{}])[0] if status_data.get("results") else {}
interfaces = switch_info.get("ports", [])

# ======== MERGE INTO ONE OBJECT ========
consolidated = {
    "switch_id": SWITCH_ID,
    "system_status": {
        "status": switch_info.get("status"),
        "os_version": switch_info.get("os_version"),
        "connecting_from": switch_info.get("connecting_from"),
        "join_time": switch_info.get("join_time"),
        "serial": switch_info.get("serial"),
        "state": switch_info.get("state")
    },
    "interfaces": interfaces
}

# ======== OUTPUT RESULT ========
print(json.dumps(consolidated, indent=4))