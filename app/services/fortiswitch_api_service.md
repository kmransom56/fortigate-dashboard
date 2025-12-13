# fortiswitch_api_service.md

## Purpose
The `fortiswitch_api_service.py` is designed to discover and manage FortiSwitch devices within a network infrastructure where a FortiGate acts as the central controller (specifically tailored for "Sonic" restaurant locations). Instead of communicating with each FortiSwitch directly, this service leverages the FortiGate's API to gather comprehensive information about all connected and managed switches.

## Dependencies
- **`logging`**: For logging status and error messages.
- **`dataclasses`**: Used to define simple, structured data classes (`FortiSwitchPort` and `FortiSwitchDevice`), although the service's methods currently return dictionaries.
- **`.fortigate_service`**: This is the most critical dependency. This service does not make direct API calls itself but rather uses the `fgt_api` function from the `fortigate_service` to interact with the FortiGate. It also relies on the `load_api_token` function from the same service for authentication.

## API

### `get_fortiswitch_api_service() -> FortiSwitchAPIService`
A factory function that provides a singleton instance of the `FortiSwitchAPIService`, ensuring consistent access to the service.

### `FortiSwitchAPIService` Class
This class contains the methods for interacting with the FortiSwitch data.

#### `get_managed_switches() -> Dict[str, Any]`
This is the core method of the service. It queries the FortiGate API endpoint `cmdb/switch-controller/managed-switch` to retrieve a list of all managed FortiSwitch devices. It then processes the raw JSON response into a more structured and usable format.

#### `get_switch_by_serial(serial: str) -> Optional[Dict[str, Any]]`
Filters the list of managed switches to find and return the data for a single switch matching the given `serial` number.

#### `get_port_information(switch_serial: str, port_name: str) -> Optional[Dict[str, Any]]`
Allows for a targeted query to get the details of a specific `port_name` on a switch identified by `switch_serial`.

#### `get_active_ports(switch_serial: str = None) -> List[Dict[str, Any]]`
Returns a list of all ports that are currently in the "up" status. It can be used to get all active ports across the entire network or be filtered to a single switch by providing the `switch_serial`.

#### `get_network_summary() -> Dict[str, Any]`
Provides a high-level, aggregated summary of the network, including the total number of switches, total and active port counts, and overall network utilization percentage.

## Configuration
This service is indirectly configured. It relies entirely on the configuration of the `fortigate_service`. The essential pieces of configuration are:
- The FortiGate host address.
- A valid FortiGate API token.
The service initializes by calling `load_api_token()` to get the necessary authentication credential.

## Data Flow
1. The application gets the `FortiSwitchAPIService` instance.
2. A method, such as `get_managed_switches()`, is called.
3. The service uses the `fgt_api()` function (from `fortigate_service`) to make an API call to the FortiGate's `cmdb/switch-controller/managed-switch` endpoint.
4. The FortiGate returns a JSON payload containing an array of all managed switches and their detailed port information.
5. The `_process_switch_data()` helper method is used to iterate through the raw data, parsing and structuring it into a standardized dictionary format for switches and their ports.
6. The final, structured data is returned to the application.

## Error Handling
- The service checks for the presence of an API token upon initialization and logs a warning if it's missing.
- The primary `get_managed_switches()` method wraps the API call in a `try...except` block to catch and log any exceptions during the process.
- It inspects the response from the `fgt_api` call for an `error` key and, if present, logs the error and returns it in the response.

## Testing
This file does not contain its own unit tests. To effectively test this service, one would need to mock the `fgt_api` function from the `fortigate_service`. By providing mock JSON responses that mimic the real FortiGate API output, the data processing logic (`_process_switch_data`) and the various filtering functions (`get_switch_by_serial`, `get_active_ports`, etc.) can be validated.
