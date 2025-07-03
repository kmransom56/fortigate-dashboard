import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_switches_api():
    """
    Test the /fortigate/api/switches endpoint to see what it returns.
    """
    url = "http://localhost:8001/fortigate/api/switches"
    logger.info(f"Making request to {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response data type: {type(data)}")
            logger.info(f"Number of switches: {len(data)}")
            
            # Check if any switches have connected devices
            for i, switch in enumerate(data):
                logger.info(f"Switch {i+1}: {switch.get('name', 'Unknown')}")
                connected_devices = switch.get('connected_devices', [])
                logger.info(f"  Connected devices: {len(connected_devices)}")
                
                # Log the first few connected devices if any
                for j, device in enumerate(connected_devices[:3]):
                    logger.info(f"  Device {j+1}: {device}")
            
            # Pretty print the full response
            with open("switches_api_response.json", "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Full response saved to switches_api_response.json")
            
            return data
        else:
            logger.error(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception: {e}")
        return None

if __name__ == "__main__":
    test_switches_api()