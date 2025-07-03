import requests
import json
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# FortiGate connection details
FORTIGATE_HOST = "https://192.168.0.254"
API_TOKEN = "hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N"  # From the .env file

def get_fortiswitches():
    """
    Get FortiSwitch information from FortiGate API.
    """
    url = f"{FORTIGATE_HOST}/api/v2/monitor/switch-controller/managed-switch/status"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    print(f"Making request to: {url}")
    
    # Disable SSL verification due to certificate issues
    response = requests.get(url, headers=headers, verify=False, timeout=10)
    
    print(f"Response status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    get_fortiswitches()