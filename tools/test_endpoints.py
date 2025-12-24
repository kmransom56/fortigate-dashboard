import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FortiGate API details
FORTIGATE_HOST = "https://192.168.0.254"
API_TOKEN = "fhk0ch856np81NhsNjGjgf3nxrj0gh"
CERT_PATH = "./app/certs/fortigate.pem"


def test_endpoint(endpoint):
    url = f"{FORTIGATE_HOST}{endpoint}"
    # UPDATED: Removed query parameter authentication
    headers = {"Accept": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

    logger.info(f"Testing endpoint: {endpoint}")
    try:
        # Try with certificate verification
        response = requests.get(url, verify=CERT_PATH)
        logger.info(f"Status code (with cert): {response.status_code}")
        logger.info(f"Response (with cert): {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Error with cert: {e}")

        # Try without certificate verification
        try:
            response = requests.get(url, verify=False)
            logger.info(f"Status code (without cert): {response.status_code}")
            logger.info(f"Response (without cert): {response.text[:200]}...")
        except Exception as e:
            logger.error(f"Error without cert: {e}")


if __name__ == "__main__":
    # Suppress SSL warnings
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning
    )

    # Test different endpoints
    endpoints = [
        "/api/v2/monitor/system/status",
        "/api/v2/monitor/system/time",
        "/api/v2/monitor/system/firmware",
        "/api/v2/monitor/system/interface",  # Original endpoint
        "/api/v2/cmdb/system/interface",  # Try CMDB endpoint instead of monitor
        "/api/v2/monitor/system/available-interfaces",
        "/api/v2/monitor/system/resource/usage",
    ]

    for endpoint in endpoints:
        test_endpoint(endpoint)
        print("\n" + "-" * 50 + "\n")
