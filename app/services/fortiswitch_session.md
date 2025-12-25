# fortiswitch_session.md

## Purpose
The `fortiswitch_session.py` service manages API sessions for FortiSwitch devices. It provides a centralized manager for handling authentication and making API requests. It supports both basic authentication (username/password) and bearer token authentication.

## Dependencies
- **`os`**: Used to access environment variables for configuration.
- **`requests`**: The primary library used to make HTTP/HTTPS requests to the FortiSwitch API.
- **`logging`**: Used for logging information, warnings, and errors.
- **`urllib3`**: Used to suppress insecure request warnings when SSL verification is disabled.

## API

### `get_fortiswitch_session_manager() -> FortiSwitchSessionManager`
This function returns a singleton instance of the `FortiSwitchSessionManager` class, ensuring that a single session manager is used throughout the application.

### `FortiSwitchSessionManager` Class
This class contains the logic for managing FortiSwitch API sessions.

#### `__init__()`
The constructor initializes the `requests.Session` object and calls `_load_credentials()` to load the necessary configuration.

#### `make_api_request(endpoint: str, session_token: Optional[str] = None, api_token: Optional[str] = None) -> Dict[str, Any]`
This is the main method for making API calls.
- It takes an API `endpoint` as a string.
- It can optionally take a `session_token` or `api_token` for bearer token authentication.
- If no token is provided, it falls back to using basic authentication with the configured username and password.
- It returns a dictionary containing the JSON response from the API or an error message.

## Configuration
This service is configured through environment variables:

- **`FORTISWITCH_HOST`**: The hostname or IP address of the FortiSwitch device.
- **`FORTISWITCH_USERNAME`**: The username for API authentication.
- **`FORTISWITCH_PASSWORD`**: The password for API authentication. This can also be loaded from a file at `/run/secrets/fortiswitch_password` (for Docker secrets) or `./secrets/fortiswitch_password.txt`.
- **`FORTISWITCH_VERIFY_SSL`**: Set to `"true"` to enable SSL certificate verification. It defaults to `false`.

## Data Flow
1. An application component calls `get_fortiswitch_session_manager()` to get the session manager instance.
2. On first call, the `FortiSwitchSessionManager` is instantiated, and it loads its configuration from environment variables and files.
3. The application calls the `make_api_request()` method on the session manager instance, providing the desired API endpoint.
4. The session manager constructs the full URL and headers for the request.
5. It makes the API call using the `requests` library, handling authentication automatically.
6. The JSON response from the FortiSwitch API is parsed and returned as a dictionary.
7. If any errors occur during the process, an error dictionary is returned instead.

## Error Handling
The service is designed to be resilient and provides clear error messages.
- It logs warnings if the host or credentials are not configured.
- It handles various `requests` exceptions, including `Timeout`, `SSLError`, and `ConnectionError`, returning a structured error dictionary.
- It checks for non-200 HTTP status codes and returns specific error messages for authentication failures (401) and not-found errors (404).
- All errors are logged using the standard `logging` module.

## Testing
This file does not contain its own unit tests. To test this service, you would typically use a testing framework like `pytest` and mock the `requests` library to simulate API responses and network errors. This would allow you to test the authentication logic, error handling, and data parsing without needing a live FortiSwitch device.
