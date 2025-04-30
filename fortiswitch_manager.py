"""
FortiSwitch Manager Module

This module provides functionality to manage FortiSwitch devices connected to a FortiGate firewall
through the FortiOS API.
"""
import requests
import urllib3
import logging
from typing import Dict, Any, Optional, List, Union

# Set up logging
logger = logging.getLogger(__name__)

# Disable SSL warnings for development environments
# In production, you should properly handle certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class FortiSwitchManager:
    """
    A class to manage FortiSwitch devices connected to a FortiGate firewall.
    """
    
    def __init__(self, fortigate_ip: str, api_token: str, verify_ssl: bool = False):
        """
        Initialize the FortiSwitch manager.
        
        Args:
            fortigate_ip: IP address or hostname of the FortiGate
            api_token: API token for authentication
            verify_ssl: Whether to verify SSL certificates
        """
        self.fortigate_ip = fortigate_ip
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.base_url = f"https://{fortigate_ip}/api/v2"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        logger.debug(f"Initialized FortiSwitchManager for FortiGate at {fortigate_ip}")
    
    def get_managed_switches(self) -> Dict[str, Any]:
        """
        Get all FortiSwitches managed by the FortiGate.
        
        Returns:
            Dictionary containing the response from the API
        """
        url = f"{self.base_url}/cmdb/switch-controller/managed-switch"
        logger.debug(f"Getting managed switches from {url}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully retrieved {len(result.get('results', []))} managed switches")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting managed switches: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def get_switch_details(self, switch_id: str) -> Dict[str, Any]:
        """
        Get details for a specific FortiSwitch.
        
        Args:
            switch_id: Serial number or other ID of the FortiSwitch
            
        Returns:
            Dictionary containing the response from the API
        """
        url = f"{self.base_url}/cmdb/switch-controller/managed-switch/{switch_id}"
        logger.debug(f"Getting switch details from {url}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully retrieved details for switch {switch_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting switch details: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def change_switch_ip(self, switch_id: str, new_ip: str, new_netmask: str = "255.255.255.0") -> Dict[str, Any]:
        """
        Change the IP address of a FortiSwitch.
        
        Args:
            switch_id: Serial number or other ID of the FortiSwitch
            new_ip: New IP address to assign to the FortiSwitch
            new_netmask: Network mask to use with the new IP
            
        Returns:
            Dictionary containing the response from the API
        """
        url = f"{self.base_url}/cmdb/switch-controller/managed-switch/{switch_id}"
        logger.debug(f"Changing IP address for switch {switch_id} to {new_ip}/{new_netmask}")
        
        # Data payload for the API request
        data = {
            "fsw-wan1-admin": "enable",
            "fsw-wan1-ip": new_ip,
            "fsw-wan1-netmask": new_netmask
        }
        
        try:
            response = requests.put(
                url,
                headers=self.headers,
                json=data,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated IP of {switch_id} to {new_ip}")
            return {
                "success": True,
                "message": f"Successfully updated IP of {switch_id} to {new_ip}",
                "data": result
            }
        except requests.exceptions.HTTPError as e:
            error_data = {}
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                try:
                    error_data = e.response.json()
                except:
                    error_data = {"raw_response": e.response.text}
            
            logger.error(f"API error changing switch IP: {str(e)}")
            return {
                "success": False,
                "message": f"API Error: {str(e)}",
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
                "data": error_data
            }
        except Exception as e:
            logger.error(f"Unexpected error changing switch IP: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "data": None
            }
    
    def get_connected_devices(self, switch_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get devices connected to FortiSwitches.
        
        Args:
            switch_id: Optional ID of a specific switch to query
            
        Returns:
            Dictionary containing the response from the API
        """
        if switch_id:
            url = f"{self.base_url}/monitor/switch-controller/switch-info/by-id/{switch_id}/connected-devices"
            logger.debug(f"Getting devices connected to switch {switch_id}")
        else:
            url = f"{self.base_url}/monitor/switch-controller/switch-info/connected-devices"
            logger.debug("Getting all connected devices")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            result = response.json()
            
            device_count = len(result.get('results', []))
            if switch_id:
                logger.info(f"Found {device_count} devices connected to switch {switch_id}")
            else:
                logger.info(f"Found {device_count} connected devices across all switches")
                
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting connected devices: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }
    
    def get_switch_ports(self, switch_id: str) -> Dict[str, Any]:
        """
        Get port information for a specific FortiSwitch.
        
        Args:
            switch_id: Serial number or other ID of the FortiSwitch
            
        Returns:
            Dictionary containing the response from the API
        """
        url = f"{self.base_url}/monitor/switch-controller/switch-info/by-id/{switch_id}/ports"
        logger.debug(f"Getting port information for switch {switch_id}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully retrieved port information for switch {switch_id}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting switch ports: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
            }