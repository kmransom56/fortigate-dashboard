#!/usr/bin/env python3
"""
Test script to verify that the detected devices are being processed correctly.
"""

import os
import sys
import json
import logging
from app.services.fortiswitch_service import (
    get_detected_devices,
    get_dhcp_info,
    process_fortiswitch_data,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main function to test detected devices processing."""
    logger.info("Starting detected devices test")

    # Get detected devices
    logger.info("Fetching detected devices...")
    detected_devices = get_detected_devices()

    # Get DHCP information
    logger.info("Fetching DHCP information...")
    dhcp_info = get_dhcp_info()

    # Create a dummy switch data structure
    switch_data = {
        "results": [
            {
                "switch-id": "S124EPTQ22000276",
                "serial": "S124EPTQ22000276",
                "status": "Connected",
                "ports": [],
            }
        ]
    }

    # Add ports to the switch
    port_names = ["port1", "port2", "port19", "port20", "port21", "port22", "port23"]
    for port_name in port_names:
        switch_data["results"][0]["ports"].append(
            {
                "interface": port_name,
                "status": "up",
                "speed": 1000,
                "duplex": "full",
                "vlan": "VLAN1000",
            }
        )

    # Process the data
    logger.info("Processing switch data with detected devices...")
    switches = process_fortiswitch_data(switch_data, dhcp_info, detected_devices)

    # Check the results
    if switches and len(switches) > 0:
        switch = switches[0]
        logger.info(f"Switch: {switch['name']} (Serial: {switch['serial']})")
        logger.info(f"Connected devices: {len(switch['connected_devices'])}")

        # Log each connected device
        for device in switch["connected_devices"]:
            logger.info(
                f"  - Device on port {device['port']}: {device['device_name']} (MAC: {device['device_mac']}, IP: {device['device_ip']})"
            )
    else:
        logger.error("No switches found in processed data")

    logger.info("Detected devices test completed")


if __name__ == "__main__":
    main()
