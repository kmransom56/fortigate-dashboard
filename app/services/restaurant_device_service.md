# restaurant_device_service.md

## Purpose
The `restaurant_device_service.py` is a highly specialized classification engine. Its primary function is to identify and categorize network devices that are specific to restaurant environments, such as those found in Arby's, Buffalo Wild Wings, and Sonic locations. It acts as a knowledge base, using a device's MAC address, hostname, or manufacturer to determine if it is a Point-of-Sale (POS) terminal, a kitchen display system, a payment terminal, a security camera, or another common restaurant appliance.

## Dependencies
- **`logging`**: Used for standard application logging.
- This service is notably self-contained and has no external dependencies for its core logic (like `requests` or database connectors).

## API

### `get_restaurant_device_service() -> RestaurantDeviceService`
A factory function that provides a singleton instance of the `RestaurantDeviceService`, ensuring the internal databases are loaded only once.

### `RestaurantDeviceService` Class
This class contains the data and logic for the classification engine.

#### `identify_restaurant_device(mac: str, hostname: Optional[str] = None, manufacturer: Optional[str] = None) -> Dict[str, str]`
This is the core method of the service. It takes basic information about a discovered network device and attempts to classify it. The logic works in a hierarchical manner:
1.  It first checks the device's MAC address against an internal database of Organizationally Unique Identifiers (OUIs) known to belong to restaurant equipment manufacturers. This provides a "high" confidence match.
2.  If no OUI match is found, it checks the device's `hostname` against a list of common naming patterns (e.g., a hostname starting with "pos-" is likely a POS terminal). This provides a "medium" confidence match.
3.  Finally, it can do a simple check on the `manufacturer` string.
The method returns a dictionary containing the device's identified type, category, an icon hint, and a confidence score for the match.

#### `get_restaurant_device_icon_path(device_info: Dict[str, str]) -> Tuple[str, str]`
This method takes the classification dictionary produced by `identify_restaurant_device` and returns a tuple containing the appropriate icon path and a display title for that device type.

#### `get_device_risk_assessment(device_info: Dict[str, str]) -> str`
This method performs a simple security risk assessment based on the device's identified category. For example, a device in the `payment_processing` category is assigned a "critical" risk level due to its role in handling sensitive cardholder data.

## Configuration
This service has **no external configuration**. All of its "knowledge" is hardcoded into two internal dictionaries:
- `_load_restaurant_ouis()`: Contains the mapping of MAC address prefixes to device types.
- `_load_device_patterns()`: Contains the mapping of hostname patterns to device types.
To update the service's identification capabilities, one would need to modify these methods directly within the code.

## Data Flow
1. The `RestaurantDeviceService` is instantiated, and its internal OUI and hostname pattern dictionaries are loaded into memory.
2. Another service, such as the `fortigate_monitor_service`, discovers a new device on the network and obtains its MAC address and hostname.
3. The monitoring service then calls `identify_restaurant_device()` on the restaurant service, passing in the discovered device's information.
4. The restaurant service performs its classification logic (checking OUI, then hostname).
5. It returns a classification dictionary to the monitoring service.
6. The monitoring service can then use this classification to enrich its own data, for example, by calling `get_restaurant_device_icon_path()` to get the correct icon for the device before sending the data to the UI.

## Error Handling
This service is very simple and operates on its own internal data. As it does not perform any network I/O or file operations (other than its own loading), its potential for errors is minimal, and it does not contain complex error handling logic.

## Testing
This file does not contain its own unit tests. Testing this service would be straightforward. A test suite would instantiate the service and then call the `identify_restaurant_device` method with a series of known inputs (e.g., a MAC address known to belong to an NCR POS terminal, a hostname like "kds-01") and assert that the method returns the expected classification dictionary in each case.
