# fortigate_monitor_service.md

## Purpose
The `fortigate_monitor_service.py` is responsible for providing real-time network monitoring and device discovery. It utilizes the "monitor" section of the FortiGate API, which provides dynamic, real-time data about the network state. This is distinct from the "cmdb" API, which provides configuration data. This service is crucial for understanding what devices are currently on the network, where they are connected, and how much traffic is passing through the ports.

## Dependencies
- **`logging`**: For standard application logging.
- **`dataclasses`**, **`datetime`**: For data structuring and timestamping.
- **`.fortigate_service`**: This is the core dependency for API communication. The service uses the `fgt_api` function to make all its calls to the FortiGate.
- **`app.utils.oui_lookup`**: An internal utility used to look up the manufacturer of a device based on the OUI (Organizationally Unique Identifier) of its MAC address.
- **`app.utils.icon_db`**: An internal utility used to assign an appropriate icon to a device based on its manufacturer or type.

## API

### `get_fortigate_monitor_service() -> FortiGateMonitorService`
A factory function that returns a singleton instance of the `FortiGateMonitorService`.

### `FortiGateMonitorService` Class
This class orchestrates the calls to the FortiGate's monitor API endpoints.

#### `get_detected_devices() -> Dict[str, Any]`
Queries the `/monitor/switch-controller/detected-device` endpoint to get a list of all devices that the FortiGate has seen on the switch ports. The raw data is then enriched with:
- An `is_active` status, based on when the device was last seen.
- The device's manufacturer, via an OUI lookup.
- An appropriate icon for the device.

#### `get_port_statistics(switch_id: Optional[str] = None) -> Dict[str, Any]`
Queries the `/monitor/switch-controller/managed-switch/port-stats` endpoint to get detailed traffic statistics for switch ports, including bytes/packets sent and received, and error counts. It can be filtered to a specific switch.

#### `get_comprehensive_device_data() -> Dict[str, Any]`
This is a powerful method that combines the outputs of `get_detected_devices()` and `get_port_statistics()`. It correlates the traffic statistics of a port with the device(s) connected to it, providing a unified and comprehensive view of the network's real-time state.

#### `get_device_by_mac(mac_address: str) -> Optional[Dict[str, Any]]`
A convenience method to search the comprehensive device data for a specific device by its MAC address.

#### `get_port_devices(switch_id: str, port_name: str) -> List[Dict[str, Any]]`
A convenience method to find all devices connected to a single, specific switch port.

## Configuration
- This service is indirectly configured via the `fortigate_service`, which provides the necessary FortiGate host and API token.
- It has an internal configuration setting, `active_threshold`, which is set to 300 seconds (5 minutes). Any device seen within this window is considered "active".

## Data Flow
1. The application calls a method like `get_comprehensive_device_data()`.
2. The service first calls the `/monitor/switch-controller/detected-device` API endpoint via `fgt_api`.
3. The list of detected devices is processed: activity is determined, and manufacturer/icon data is added.
4. The service then calls the `/monitor/switch-controller/managed-switch/port-stats` endpoint.
5. The port statistics are processed and organized into a lookup dictionary for efficient access.
6. The service then merges the two datasets, adding the relevant port statistics to each detected device.
7. The final, enriched, and combined dataset is returned to the application.

## Error Handling
- All public methods are wrapped in `try...except` blocks to handle and log any exceptions that occur during the API calls or data processing.
- The service checks the API response for an `error` key and propagates it if found.
- The optional data enrichment steps (OUI and icon lookup) are also wrapped in `try...except` blocks, ensuring that a failure in these non-critical steps does not prevent the primary device data from being returned.

## Testing
This file does not contain unit tests. To test this service, you would need to mock the `fgt_api` function to return sample JSON data representing the output of the two monitor API endpoints. Additionally, the `oui_lookup` and `icon_db` utility functions would need to be mocked to test the data enrichment logic in isolation.
