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
CERT_PATH = "app/certs/fortigate.pem"

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
        # Use the certificate for verification
        if os.path.exists(CERT_PATH):
            logger.info(f"Using certificate file: {CERT_PATH}")
            response = requests.get(url, headers=headers, params=params, verify=CERT_PATH, timeout=10)
        else:
            logger.warning(f"Certificate file not found at {CERT_PATH}, disabling SSL verification")
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
        # Use the certificate for verification
        if os.path.exists(CERT_PATH):
            logger.info(f"Using certificate file: {CERT_PATH}")
            response = requests.get(url, headers=headers, verify=CERT_PATH, timeout=10)
        else:
            logger.warning(f"Certificate file not found at {CERT_PATH}, disabling SSL verification")
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
        
        # Check if we're in the allowed range (192.168.0.0/24)
        if local_ip.startswith('192.168.0.'):
            logger.info("Local IP is within the allowed range (192.168.0.0/24)")
        else:
            logger.warning("Local IP is NOT within the allowed range (192.168.0.0/24)")
            
        return external_ip, local_ip
    except Exception as e:
        logger.error(f"Error getting IP addresses: {e}")
        return None, None

if __name__ == "__main__":
    logger.info("Starting FortiGate API tests")
    
    # Get client IP information
    external_ip, local_ip = get_client_ip()
    
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