import os
import base64
import requests
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get environment variables
FORTIGATE_HOST = os.environ.get("FORTIGATE_HOST", "https://192.168.0.254")
API_TOKEN = os.environ.get("FORTIGATE_API_TOKEN", "fhk0ch856np81NhsNjGjgf3nxrj0gh")


def test_token_format(description, token_value, auth_method="query"):
    """Test different token formats"""
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/status"

    if auth_method == "query":
        # UPDATED: Removed query parameter authentication
        headers = {"Accept": "application/json", "Authorization": f"Bearer token_value"}
        logger.info(f"Testing {description} with query parameter: {token_value}")
    elif auth_method == "header":
        params = {}
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token_value}",
        }
        logger.info(
            f"Testing {description} with Authorization header: Bearer {token_value}"
        )
    elif auth_method == "header_raw":
        params = {}
        headers = {"Accept": "application/json", "Authorization": token_value}
        logger.info(
            f"Testing {description} with Authorization header (raw): {token_value}"
        )

    try:
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error: {e}")

    logger.info("-" * 50)


if __name__ == "__main__":
    # Suppress SSL warnings
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning
    )

    # Test original token
    test_token_format("Original token", API_TOKEN)

    # Test with "api-dev-user" as username
    test_token_format("Username as token", "api-dev-user")

    # Test with username:token format
    test_token_format("Username:token format", f"api-dev-user:{API_TOKEN}")

    # Test with base64 encoded token
    base64_token = base64.b64encode(API_TOKEN.encode()).decode()
    test_token_format("Base64 encoded token", base64_token)

    # Test with base64 encoded username:token
    base64_user_token = base64.b64encode(f"api-dev-user:{API_TOKEN}".encode()).decode()
    test_token_format("Base64 encoded username:token", base64_user_token)

    # Test with Authorization header
    test_token_format("Authorization header", API_TOKEN, "header")

    # Test with Basic auth header
    test_token_format("Basic auth header", f"Basic {base64_user_token}", "header_raw")
