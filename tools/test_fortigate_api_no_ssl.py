import requests
import os
import logging
import sys
from urllib3.exceptions import InsecureRequestWarning

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# FortiGate connection details
FORTIGATE_HOST = "https://192.168.0.254"
API_TOKEN = "hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N"

def test_with_query_param():
    """Test API access using token as a query parameter (like in the curl command)"""
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/interface"
    params = {"access_token": API_TOKEN}
    headers = {"Accept": "application/json"}
    
    logger.info("=== Testing with token as query parameter ===")
    logger.info(f"Request URL: {url}")
    logger.info(f"Request params: {params}")
    logger.info(f"Request headers: {headers}")
    
    try:
        # Disable SSL verification
        logger.info("Disabling SSL verification for this test")
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        logger.info(f"Response content: {response.text[:500]}...")
        
        return response.status_code, response.text
    except Exception as e:
        logger.error(f"Error: {e}")
        return None, str(e)

def test_with_auth_header():
    """Test API access using token in Authorization header (like in the application code)"""
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/interface"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    logger.info("=== Testing with token in Authorization header ===")
    logger.info(f"Request URL: {url}")
    logger.info(f"Request headers: {headers}")
    
    try:
        # Disable SSL verification
        logger.info("Disabling SSL verification for this test")
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        logger.info(f"Response content: {response.text[:500]}...")
        
        return response.status_code, response.text
    except Exception as e:
        logger.error(f"Error: {e}")
        return None, str(e)

def get_client_ip():
    """Try to determine the client IP address"""
    try:
        # Use a public service to get our external IP
        response = requests.get('https://api.ipify.org', timeout=5)
        external_ip = response.text
        logger.info(f"External IP address: {external_ip}")
        
        # Get local IP addresses
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        logger.info(f"Local hostname: {hostname}")
        logger.info(f"Local IP address: {local_ip}")
        
        # Try to get all local IPs
        all_ips = []
        try:
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        all_ips.append(addr['addr'])
            logger.info(f"All local IPs: {all_ips}")
        except ImportError:
            logger.warning("netifaces module not available, can't get all local IPs")
            # Alternative method to get all IPs
            try:
                import subprocess
                output = subprocess.check_output("ip -4 addr show | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}'", shell=True).decode('utf-8')
                all_ips = output.strip().split('\n')
                logger.info(f"All local IPs (from ip command): {all_ips}")
            except Exception as e:
                logger.warning(f"Could not get all IPs using ip command: {e}")
        
        # Check if any of our IPs are in the allowed range (192.168.0.0/24)
        in_allowed_range = False
        for ip in all_ips + [local_ip]:
            if ip.startswith('192.168.0.'):
                logger.info(f"IP {ip} is within the allowed range (192.168.0.0/24)")
                in_allowed_range = True
                
        if not in_allowed_range:
            logger.warning("None of the local IPs are within the allowed range (192.168.0.0/24)")
            
        return external_ip, local_ip, all_ips
    except Exception as e:
        logger.error(f"Error getting IP addresses: {e}")
        return None, None, []

if __name__ == "__main__":
    logger.info("Starting FortiGate API tests (without SSL verification)")
    
    # Get client IP information
    external_ip, local_ip, all_ips = get_client_ip()
    
    # Test with query parameter (like curl command)
    query_status, query_response = test_with_query_param()
    
    # Test with Authorization header (like application code)
    auth_status, auth_response = test_with_auth_header()
    
    # Summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Query parameter test status: {query_status}")
    logger.info(f"Authorization header test status: {auth_status}")
    
    if query_status == 200:
        logger.info("Query parameter authentication SUCCEEDED")
    else:
        logger.info("Query parameter authentication FAILED")
        
    if auth_status == 200:
        logger.info("Authorization header authentication SUCCEEDED")
    else:
        logger.info("Authorization header authentication FAILED")
        
    # Provide diagnosis
    logger.info("\n=== Diagnosis ===")
    
    # Check IP restrictions
    if not any(ip.startswith('192.168.0.') for ip in all_ips + [local_ip]):
        logger.error("ISSUE: IP Restriction - Your machine is not in the allowed network range (192.168.0.0/24)")
        logger.error("The FortiGate API is configured to only allow connections from 192.168.0.0/24")
        logger.error("You need to connect from a machine within that network or modify the API trusthost settings")
    
    # Check authentication method
    if query_status != 200 and auth_status == 200:
        logger.error("ISSUE: Authentication Method - The API requires the token in the Authorization header")
        logger.error("Modify your curl command to use: -H 'Authorization: Bearer hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N'")
    elif query_status == 200 and auth_status != 200:
        logger.error("ISSUE: Authentication Method - The API requires the token as a query parameter")
        logger.error("Modify your application code to use the token as a query parameter")
    elif query_status != 200 and auth_status != 200:
        logger.error("ISSUE: Authentication Failed - Both methods failed, likely due to:")
        logger.error("1. Invalid or expired API token")
        logger.error("2. IP restrictions (must be in 192.168.0.0/24 network)")
        logger.error("3. API user permissions issue")