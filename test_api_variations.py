import requests
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FortiGate API details
FORTIGATE_HOST = 'https://192.168.0.254'
API_TOKEN = 'fhk0ch856np81NhsNjGjgf3nxrj0gh'

def test_variation(description, url, headers=None, params=None):
    logger.info(f"Testing: {description}")
    logger.info(f"URL: {url}")
    logger.info(f"Headers: {headers}")
    logger.info(f"Params: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error: {e}")
    
    logger.info("-" * 50)

if __name__ == "__main__":
    # Suppress SSL warnings
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    # Test different API versions
    test_variation(
        "API v1 with token in query param",
        f"{FORTIGATE_HOST}/api/v1/monitor/system/status",
        
    )
    
    test_variation(
        "API v2 with token in query param",
        f"{FORTIGATE_HOST}/api/v2/monitor/system/status",
        
    )
    
    # Test with token in Authorization header (different formats)
    test_variation(
        "API v2 with Bearer token",
        f"{FORTIGATE_HOST}/api/v2/monitor/system/status",
        headers={"Authorization": f"Bearer {API_TOKEN}"}
    )
    
    test_variation(
        "API v2 with token in header without Bearer prefix",
        f"{FORTIGATE_HOST}/api/v2/monitor/system/status",
        headers={"Authorization": API_TOKEN}
    )
    
    # Test with different URL format
    test_variation(
        "API v2 with token in URL path",
        f"{FORTIGATE_HOST}/api/v2/monitor/system/status/token/{API_TOKEN}"
    )
    
    # Test with different port
    test_variation(
        "API on port 80 (HTTP)",
        f"http://192.168.0.254:80/api/v2/monitor/system/status",
        
    )
    
    # Test with different hostname format
    test_variation(
        "API with IP in different format",
        f"https://192.168.0.254/api/v2/monitor/system/status",
        
    )