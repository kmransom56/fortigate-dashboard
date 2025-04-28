import os
import sys
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FortiGate API details
FORTIGATE_HOST = 'https://192.168.0.254'
API_TOKEN = 'fhk0ch856np81NhsNjGjgf3nxrj0gh'

def test_auth_methods():
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/interface"
    
    # Method 1: Query parameter (current method)
    logger.info("Testing Method 1: Query parameter")
    params = {"access_token": API_TOKEN}
    try:
        response = requests.get(url, params=params, verify=False)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Method 2: Authorization header with Bearer token
    logger.info("\nTesting Method 2: Authorization header with Bearer token")
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.get(url, headers=headers, verify=False)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    # Method 3: Both query parameter and Authorization header
    logger.info("\nTesting Method 3: Both query parameter and Authorization header")
    try:
        response = requests.get(url, params=params, headers=headers, verify=False)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    # Suppress SSL warnings
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    test_auth_methods()