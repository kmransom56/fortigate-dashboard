import requests
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def test_fortiswitch_api():
    """Test accessing the FortiSwitch API endpoint"""
    url = "http://localhost:8001/fortigate/api/switches"
    logger.info(f"Accessing FortiSwitch API at: {url}")

    try:
        response = requests.get(url)
        logger.info(f"Status code: {response.status_code}")

        if response.status_code == 200:
            logger.info("FortiSwitch API accessed successfully!")
            data = response.json()
            logger.info(f"Found {len(data)} FortiSwitches")

            # Display some information about the switches
            for i, switch in enumerate(data):
                logger.info(
                    f"Switch {i+1}: {switch.get('name')} ({switch.get('model')})"
                )
                logger.info(f"  Status: {switch.get('status')}")
                logger.info(f"  IP: {switch.get('ip')}")
                logger.info(
                    f"  Connected devices: {len(switch.get('connected_devices', []))}"
                )
        else:
            logger.error(f"Failed to access FortiSwitch API: {response.status_code}")
            logger.error(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error accessing FortiSwitch API: {e}")


def test_switches_page():
    """Test accessing the FortiSwitch dashboard page"""
    url = "http://localhost:8001/switches"
    logger.info(f"Accessing FortiSwitch dashboard at: {url}")

    try:
        response = requests.get(url)
        logger.info(f"Status code: {response.status_code}")

        if response.status_code == 200:
            logger.info("FortiSwitch dashboard accessed successfully!")
            if "FortiSwitch Dashboard" in response.text:
                logger.info("FortiSwitch dashboard title found in the response")
            else:
                logger.warning("FortiSwitch dashboard title not found in the response")
        else:
            logger.error(
                f"Failed to access FortiSwitch dashboard: {response.status_code}"
            )
            logger.error(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error accessing FortiSwitch dashboard: {e}")


if __name__ == "__main__":
    # Test the API endpoint
    test_fortiswitch_api()
    print("\n" + "-" * 50 + "\n")

    # Test the dashboard page
    test_switches_page()
