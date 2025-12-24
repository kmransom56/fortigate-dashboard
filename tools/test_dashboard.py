import requests
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def test_dashboard():
    """Test accessing the dashboard endpoint"""
    url = "http://localhost:8001/dashboard"
    logger.info(f"Accessing dashboard at: {url}")

    try:
        response = requests.get(url)
        logger.info(f"Status code: {response.status_code}")

        if response.status_code == 200:
            logger.info("Dashboard accessed successfully!")
            # Check if the response contains interface data
            if "interfaces" in response.text:
                logger.info("Interface data found in the response")
            else:
                logger.warning("No interface data found in the response")
        else:
            logger.error(f"Failed to access dashboard: {response.status_code}")
            logger.error(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error accessing dashboard: {e}")


if __name__ == "__main__":
    test_dashboard()
