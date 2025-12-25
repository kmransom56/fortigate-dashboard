# meraki_service.md

## Purpose
The `meraki_service.py` is responsible for integrating with the Cisco Meraki Dashboard API. It is a specialized service designed to handle the "hybrid" network infrastructure found in Buffalo Wild Wings (BWW) and Arby's locations, which use a combination of a FortiGate firewall and Meraki switches. The primary purpose of this service is to discover, gather data from, and manage these Meraki switches, allowing them to be represented and monitored within the dashboard alongside Fortinet devices.

## Dependencies
- **`logging`**: For standard application logging.
- **`requests`**: The core library used to make all HTTP/HTTPS requests to the Meraki Dashboard API.
- **`os`**: Used to retrieve the `MERAKI_API_KEY` from the environment variables.
- **`datetime`**: For timestamping discovery operations and health checks.
- **`json`**: For handling JSON data in API requests and responses.
- **`time`**: Used to implement the crucial rate-limiting logic required by the Meraki API.

## API

### `get_meraki_service() -> MerakiService`
A factory function that provides a singleton instance of the `MerakiService`, ensuring that API connections and rate-limiting state are managed centrally.

### `MerakiService` Class
This class encapsulates all interactions with the Meraki API.

#### `_make_request(...)`
A private helper method that is the single point of entry for all Meraki API calls. Its key feature is the built-in rate limiting, which ensures that the application does not exceed the Meraki API's limit of 5 requests per second. It also includes a simple retry mechanism for when a rate-limit error (HTTP 429) is encountered.

#### `discover_restaurant_meraki_switches(...)`
This is a high-level discovery method that orchestrates a series of API calls to build a complete picture of the Meraki infrastructure. It fetches organizations, then networks within those organizations, then devices (switches) within those networks, and finally port details for each switch.

#### `get_switch_topology_data(...)`
This method is crucial for integration. It first calls `discover_restaurant_meraki_switches()` to get the raw Meraki data, and then it **transforms** that data into a standardized, generic format. This allows the rest of the application's topology services to treat a Meraki switch just like any other switch, regardless of the vendor.

#### `health_check() -> Dict[str, Any]`
Performs a simple health check by making a basic call to the Meraki API to verify that the API key is valid and the connection is working.

## Configuration
The service's configuration is very simple and relies on a single environment variable:
- **`MERAKI_API_KEY`**: The API key required to authenticate with the Cisco Meraki Dashboard. If this key is not present, the service will not be able to function.

## Data Flow
1. The `MerakiService` is initialized, and it configures its `requests.Session` with the API key.
2. A high-level method like `get_switch_topology_data()` is called.
3. This triggers the `discover_restaurant_meraki_switches()` method, which begins a chain of API calls.
4. The service calls `_make_request()` for each step: getting organizations, networks, devices, and port statuses. The `_make_request` method ensures there is at least a 200ms delay between each call to respect API rate limits.
5. The data from all these calls is aggregated into a detailed list of Meraki switch objects.
6. This detailed list is then transformed into a standardized format that the main application can use for topology mapping and monitoring.
7. The final, standardized data is returned.

## Error Handling
- The service explicitly checks for the `MERAKI_API_KEY` and will return an error if it is not configured.
- The central `_make_request()` method handles non-200 HTTP status codes and general network exceptions, returning a structured error dictionary.
- It has specific logic to handle the Meraki API's rate-limiting response (HTTP 429) by pausing and retrying the request once, making the service more resilient.

## Testing
This file does not contain its own unit tests. A proper test suite would involve mocking the `requests.Session` object to simulate responses from the various Meraki API endpoints. This would allow for testing the data aggregation logic, the data transformation logic in `get_switch_topology_data`, and the rate-limiting and error-handling mechanisms of the `_make_request` method.
