# fortigate_inventory_service.md

## Purpose
The `fortigate_inventory_service.py` is responsible for managing a large-scale inventory of FortiGate devices across an enterprise. Unlike services that connect to a single device, this service loads its data from a CSV file (`downloaded_files/vlan10_interfaces.csv`), which contains a list of FortiGate devices at various physical locations (e.g., stores). This provides the application with a comprehensive, searchable database of all managed FortiGates, enabling operations at an enterprise scale.

## Dependencies
- **`logging`**: For logging status messages and errors.
- **`csv`**: The core library used for reading and parsing the inventory data from the CSV file.
- **`os`**: Used for constructing the absolute path to the CSV file.
- **`datetime`**: For timestamping status updates.
- **`dataclasses`**: To define the `FortiGateLocation` data class, which provides a structured way to hold the information for each location.
- **`ipaddress`**: A powerful library used for parsing, validating, and working with IP addresses, subnets, and networks from the inventory file.

## API

### `get_fortigate_inventory_service() -> FortiGateInventoryService`
A factory function that returns a singleton instance of the `FortiGateInventoryService`, ensuring the inventory is loaded only once and shared across the application.

### `FortiGateInventoryService` Class
This class holds the inventory data and provides methods to access and manage it.

#### `_load_fortigate_inventory()`
This private method is called upon initialization. It reads the CSV file, parses each row, validates the data (like IP addresses), and populates the in-memory inventory with `FortiGateLocation` objects.

#### `get_location(store_number: str) -> Optional[FortiGateLocation]`
Retrieves a single location's data from the inventory by its unique `store_number`.

#### `get_locations_by_brand(brand: str) -> List[FortiGateLocation]`
Filters the inventory and returns a list of all locations that belong to a specific `brand` (e.g., "Sonic", "BWW").

#### `get_inventory_summary() -> Dict[str, Any]`
Generates and returns a high-level statistical summary of the entire inventory, with counts broken down by brand, region, and IP address ranges.

#### `get_fortigate_connection_info(store_number: str) -> Optional[Dict[str, Any]]`
For a given `store_number`, this method returns a dictionary containing all the necessary details to establish a connection to that FortiGate, including its IP address, management ports, and API URLs.

#### `update_location_status(store_number: str, status: str, **kwargs) -> bool`
Allows for the in-memory status of a location to be updated (e.g., setting it to "online" or "offline"). This is not persistent and will be reset on the next application restart.

#### `search_locations(query: str) -> List[FortiGateLocation]`
Provides a simple search capability, allowing users to find locations by querying against the store number, IP address, brand, or region.

## Configuration
The primary configuration for this service is the path to the inventory file. This is provided as a default argument in the constructor: `csv_path: str = "downloaded_files/vlan10_interfaces.csv"`. The service's functionality is entirely dependent on the presence and correct formatting of this file.

## Data Flow
1. When the `FortiGateInventoryService` is first instantiated (via `get_fortigate_inventory_service()`), the `_load_fortigate_inventory()` method is automatically called.
2. The service opens and reads the specified CSV file from the disk.
3. Each row in the CSV is parsed, and a `FortiGateLocation` object is created. This object is then stored in an in-memory dictionary, `self.locations`, using the `store_number` as the key.
4. Once loaded, all other methods in the service (`get_location`, `search_locations`, etc.) operate on this in-memory dictionary. The CSV file is not read again unless the application is restarted.

## Error Handling
- The service checks for the existence of the CSV file at the specified path and logs an error if it is not found.
- The main file loading process is wrapped in a `try...except` block to catch any file I/O errors.
- The processing of each individual row from the CSV is also wrapped in a `try...except` block. This makes the loading process resilient, as a single malformed row will be skipped with a warning, rather than causing the entire inventory load to fail.

## Testing
This file does not contain its own unit tests. To properly test this service, you would create a temporary, sample CSV file during the test setup. You would then instantiate the `FortiGateInventoryService` with the path to this temporary file and write assertions to verify that the data is loaded correctly and that the various `get_*` and `search_*` methods return the expected results based on the sample data.
