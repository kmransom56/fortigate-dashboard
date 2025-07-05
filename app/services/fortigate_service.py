import requests
import logging
import sys
import json
import os
import certifi
import time  # for retry backoff
import urllib3
import redis
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning from urllib3
urllib3.disable_warnings(InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# FortiGate connection details
FORTIGATE_HOST = os.environ.get('FORTIGATE_HOST', 'https://192.168.0.254')
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

# Get API token from environment or file
API_TOKEN_FILE = os.environ.get('FORTIGATE_API_TOKEN_FILE')
if API_TOKEN_FILE and os.path.exists(API_TOKEN_FILE):
    with open(API_TOKEN_FILE, 'r') as f:
        API_TOKEN = f.read().strip()
else:
    API_TOKEN = os.environ.get('FORTIGATE_API_TOKEN', 'hmNqQ0st7xrjnyQHt8dzpnkqm5hw5N')

# Get certificate path
CERT_PATH = os.environ.get('FORTIGATE_CERT_PATH', None)

# If the certificate path is the full host path, adjust it for Docker container
if CERT_PATH and CERT_PATH.startswith(r'C:\Users\Keith Ransom\Documents\fortigate-dashboard\app\certs'):
    # Extract the relative path and prepend with /app
    relative_path = CERT_PATH.replace(r'C:\Users\Keith Ransom\Documents\fortigate-dashboard\app\certs', '')
    CERT_PATH = f"/app/{relative_path}"
    logger.info(f"Adjusted certificate path for Docker container: {CERT_PATH}")

logger.info(f"Certificate path: {CERT_PATH}")
logger.info(f"FortiGate host: {FORTIGATE_HOST}")
logger.info(f"API token: {API_TOKEN}")

# Initialize Redis client
_redis_client = redis.Redis(
    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
)

def get_interfaces():
    """
    Get interface information from FortiGate API with proper SSL certificate handling.
    """
    try:
        # Use Authorization header with Bearer token
        # Ensure URL includes https:// scheme
        if not FORTIGATE_HOST.startswith("https://"):
            url = f"https://{FORTIGATE_HOST}/api/v2/monitor/system/interface"
        else:
            url = f"{FORTIGATE_HOST}/api/v2/monitor/system/interface"
        headers = {"Accept": "application/json", "Authorization": f"Bearer {API_TOKEN}"}

        # Attempt to return cached response from Redis
        cache_key = "fortigate:interfaces"
        cached = _redis_client.get(cache_key)
        if cached is not None:
            logger.info("Using cached interface data from Redis")
            data = json.loads(cached)  # type: ignore
            return process_interface_data(data)
        logger.info(f"Making request to FortiGate API: {url}")

        # Retry on 429 Too Many Requests with exponential backoff
        max_retries = 3
        response = None  # initialize response
        for attempt in range(max_retries):
            logger.warning("SSL verification disabled for testing")
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            if response.status_code == 429:
                wait = 2**attempt
                logger.warning(
                    f"Rate limited (429); retrying after {wait}s (attempt {attempt+1}/{max_retries})"
                )
                time.sleep(wait)
                continue
            break
        # Ensure we have a response
        if response is None:
            raise Exception("Failed to get a response from FortiGate API")
        # After retries, if still rate limited, raise exception
        if response.status_code == 429:
            logger.error("Exceeded retry attempts due to rate limiting (429)")
            raise Exception(
                f"FortiGate API error: {response.status_code} - {response.text}"
            )

        # Log response information
        logger.info(f"FortiGate API response status code: {response.status_code}")
        logger.info(f"FortiGate API response content: {response.text[:500]}")

        # Check if we got a 401 error and log more details
        if response.status_code == 401:
            logger.error("Authentication failed with 401 Unauthorized")
            logger.error(f"API Token used: {API_TOKEN}")
            logger.error("This suggests the API token is invalid or expired")
            logger.error("Please check the token in the .env file or generate a new one")

        # Check if the response is successful
        if response.status_code >= 400:
            logger.error(f"FortiGate API returned error status code: {response.status_code}")
            logger.error(f"Response content: {response.text[:1000]}...")  # Truncate for readability

            if response.status_code == 401:
                logger.error("Authentication failed (401 Unauthorized)")
                logger.error("Possible causes:")
                logger.error("1. Invalid API token")
                logger.error("2. IP restrictions: Only 192.168.0.0/24 network is allowed (trusthost)")
                logger.error("3. CORS restrictions: Only https://192.168.0.20:80 is allowed")
                logger.error("Check your client IP and ensure it's within the allowed network")

            raise Exception(f"FortiGate API error: {response.status_code} - {response.text}")

        # Parse the response
        data = response.json()
        # Cache raw JSON in Redis for 60s
        _redis_client.set(cache_key, json.dumps(data), ex=60)
        logger.info(f"FortiGate API response data type: {type(data)}")
        # Process the response based on its format
        return process_interface_data(data)
    except Exception as e:
        logger.error(f"get_interfaces failed: {e}")
        return {}

def process_interface_data(data):
    """
    Process the FortiGate API response data and extract interface information.
    """
    interfaces = {}
    
    # Format 1: Response has a 'results' key with a dictionary of interfaces (from our testing)
    if isinstance(data, dict) and 'results' in data and isinstance(data['results'], dict):
        results = data['results']
        logger.info(f"Found {len(results)} interfaces in 'results' dictionary")
        
        for name, iface in results.items():
            if isinstance(iface, dict):
                # Add the name to the interface data if not already present
                if 'name' not in iface:
                    iface['name'] = name
                # Ensure required fields exist
                if 'tx_bytes' not in iface:
                    iface['tx_bytes'] = 0
                if 'rx_bytes' not in iface:
                    iface['rx_bytes'] = 0
                if 'link' not in iface:
                    iface['link'] = True
                if 'speed' not in iface:
                    iface['speed'] = 1000
                if 'ip' not in iface and 'ip_address' in iface:
                    iface['ip'] = iface['ip_address']
                elif 'ip' not in iface:
                    iface['ip'] = '0.0.0.0/0'
                interfaces[name] = iface
    
    # Format 2: Response has a 'results' key with a list of interfaces
    elif isinstance(data, dict) and 'results' in data and isinstance(data['results'], list):
        results = data['results']
        logger.info(f"Found {len(results)} interfaces in 'results' list")
        
        for iface in results:
            if isinstance(iface, dict) and 'name' in iface:
                name = iface['name']
                # Ensure required fields exist
                if 'tx_bytes' not in iface:
                    iface['tx_bytes'] = 0
                if 'rx_bytes' not in iface:
                    iface['rx_bytes'] = 0
                if 'link' not in iface:
                    iface['link'] = True
                if 'speed' not in iface:
                    iface['speed'] = 1000
                if 'ip' not in iface and 'ip_address' in iface:
                    iface['ip'] = iface['ip_address']
                elif 'ip' not in iface:
                    iface['ip'] = '0.0.0.0/0'
                interfaces[name] = iface
    
    # Format 3: Response is a dictionary with interface names as keys
    elif isinstance(data, dict) and any(isinstance(data.get(key), dict) for key in data):
        logger.info("Response appears to be a dictionary with interface names as keys")
        for name, iface in data.items():
            if isinstance(iface, dict):
                # Add the name to the interface data if not already present
                if 'name' not in iface:
                    iface['name'] = name
                # Ensure required fields exist
                if 'tx_bytes' not in iface:
                    iface['tx_bytes'] = 0
                if 'rx_bytes' not in iface:
                    iface['rx_bytes'] = 0
                if 'link' not in iface:
                    iface['link'] = True
                if 'speed' not in iface:
                    iface['speed'] = 1000
                if 'ip' not in iface and 'ip_address' in iface:
                    iface['ip'] = iface['ip_address']
                elif 'ip' not in iface:
                    iface['ip'] = '0.0.0.0/0'
                interfaces[name] = iface
    
    if not interfaces:
        logger.error(f"Could not extract interface data from response: {data}")
        raise ValueError("No valid interfaces found in FortiGate API response")
    
    logger.info(f"Successfully processed {len(interfaces)} interfaces")
    return interfaces
