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
API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', 'hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N')

def test_api():
    """Test the API with the correct authentication method"""
    # Use Authorization header with Bearer token
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/interface"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    logger.info(f"Making request to: {url}")
    logger.info(f"Using Authorization header with Bearer token")
    
    try:
        # Disable SSL verification
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        
        logger.info(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("SUCCESS! The API request was successful.")
            logger.info(f"Response: {response.text[:200]}...")
            
            # Parse the response to show some interface data
            data = response.json()
            if 'results' in data:
                interfaces = data['results']
                logger.info(f"Found {len(interfaces)} interfaces:")
                # Interfaces are in a dictionary, not a list
                count = 0
                for name, iface in interfaces.items():
                    if count < 5:  # Show first 5 interfaces
                        logger.info(f"  {count+1}. {name} - Link: {iface.get('link', 'Unknown')}")
                    count += 1
                if count > 5:
                    logger.info(f"  ... and {count - 5} more interfaces")
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            logger.error(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    # Suppress SSL warnings
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    test_api()