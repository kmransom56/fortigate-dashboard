import os
import socket
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

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket connection to the Fortigate host to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't actually connect, just sets up the socket
        s.connect(('192.168.0.254', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.error(f"Error getting local IP: {e}")
        return "Unknown"

def check_ip_in_network(ip, network, netmask):
    """Check if an IP is in a network"""
    try:
        # Convert IP and network to integers
        ip_int = sum([int(octet) << (8 * (3 - i)) for i, octet in enumerate(ip.split('.'))])
        network_int = sum([int(octet) << (8 * (3 - i)) for i, octet in enumerate(network.split('.'))])
        netmask_int = sum([int(octet) << (8 * (3 - i)) for i, octet in enumerate(netmask.split('.'))])
        
        # Check if IP is in network
        return (ip_int & netmask_int) == (network_int & netmask_int)
    except Exception as e:
        logger.error(f"Error checking IP in network: {e}")
        return False

def test_api():
    # Get local IP
    local_ip = get_local_ip()
    logger.info(f"Local IP: {local_ip}")
    
    # Check if local IP is in allowed network
    in_allowed_network = check_ip_in_network(local_ip, '192.168.0.0', '255.255.255.0')
    logger.info(f"IP in allowed network (192.168.0.0/24): {in_allowed_network}")
    
    if not in_allowed_network:
        logger.error("Your IP is not in the allowed network (192.168.0.0/24)")
        logger.error("The Fortigate API is configured to only allow access from this network")
        logger.error("You need to either:")
        logger.error("1. Connect from a device in the 192.168.0.0/24 network")
        logger.error("2. Update the Fortigate API user trusthost configuration to include your IP")
        return
    
    # Make API request
    url = f"{FORTIGATE_HOST}/api/v2/monitor/system/interface"
    # UPDATED: Removed query parameter authentication
    headers = {"Accept": "application/json", "Authorization": f"Bearer {API_TOKEN}"}
    
    logger.info(f"Making request to: {url}")
    try:
        # First try with certificate
        if CERT_PATH and os.path.exists(CERT_PATH):
    try:
                logger.info(f"Using certificate: {CERT_PATH}")
                response = requests.get(url, headers=headers, verify=CERT_PATH)
                logger.info("Request with certificate verification succeeded")
            except requests.exceptions.SSLError as ssl_err:
                logger.error(f"SSL Error with certificate: {ssl_err}")
                logger.info("Trying without SSL verification...")
                response = requests.get(url, headers=headers, verify=False)
        else:
            logger.warning("No certificate path found or file doesn't exist. Disabling SSL verification.")
            response = requests.get(url, headers=headers, verify=False)
        
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.text[:200]}...")
        
        if response.status_code == 401:
            logger.error("Authentication failed (401 Unauthorized)")
            logger.error("Possible causes:")
            logger.error("1. Invalid API token")
            logger.error("2. IP restrictions: Only 192.168.0.0/24 network is allowed (trusthost)")
            logger.error("3. CORS restrictions: Only https://192.168.0.20:80 is allowed")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    # Suppress SSL warnings
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    test_api()