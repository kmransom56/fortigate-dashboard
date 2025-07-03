import os
import requests
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get environment variables
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', 'https://192.168.0.254')
API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', 'fhk0ch856np81NhsNjGjgf3nxrj0gh')
CERT_PATH = os.environ.get('FORTIGATE_CERT_PATH')

logger.info(f"FortiGate host: {FORTIGATE_HOST}")
logger.info(f"API token: {API_TOKEN}")
logger.info(f"Certificate path: {CERT_PATH}")

def test_api_with_ssl_verification():
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/interface"
    # UPDATED: Removed query parameter authentication
    headers = {"Accept": "application/json", "Authorization": f"Bearer {API_TOKEN}"}
    
    logger.info("Testing with SSL verification...")
    try:
        response = requests.get(url, headers=headers, verify=CERT_PATH)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error with SSL verification: {e}")

def test_api_without_ssl_verification():
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/interface"
    # UPDATED: Removed query parameter authentication
    headers = {"Accept": "application/json", "Authorization": f"Bearer {API_TOKEN}"}
    
    logger.info("Testing without SSL verification...")
    try:
        response = requests.get(url, headers=headers, verify=False)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error without SSL verification: {e}")

if __name__ == "__main__":
    # Suppress SSL warnings
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    # Test with SSL verification
    test_api_with_ssl_verification()
    
    # Test without SSL verification
    test_api_without_ssl_verification()