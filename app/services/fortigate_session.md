# fortigate_session.md

## Purpose
The `fortigate_session.py` service is responsible for managing API sessions with a FortiGate device. It handles the entire lifecycle of a session, including authentication (login), storing and validating the session key, and automatic re-authentication when a session expires. This ensures a persistent and reliable connection to the FortiGate API.

## Dependencies
- **`os`**: To read configuration from environment variables.
- **`requests`**: To perform HTTP/HTTPS requests for login and API calls.
- **`json`**: For decoding JSON responses from the API.
- **`logging`**: For logging status messages and errors.
- **`datetime`, `timedelta`**: To manage session expiration and validity.

## API

### `get_session_manager() -> FortiGateSessionManager`
This function acts as a factory and provides a singleton instance of the `FortiGateSessionManager`, ensuring that session management is centralized.

### `FortiGateSessionManager` Class
This class encapsulates all the logic for session management.

#### `__init__()`
Initializes the `requests.Session` object and loads FortiGate credentials by calling `_load_credentials()`.

#### `login() -> bool`
Handles the authentication process by sending a POST request to the `/logincheck` endpoint of the FortiGate. If the login is successful, it extracts the session key from the response cookies and sets an expiration time.

#### `logout()`
Terminates the current session by sending a request to the `/logout` endpoint.

#### `get_session_key() -> Optional[str]`
This method returns a valid session key. If the current session key is expired or does not exist, it automatically calls `login()` to obtain a new one.

#### `make_api_request(endpoint: str) -> Dict[str, Any]`
This is the primary method for interacting with the FortiGate API. It takes an API `endpoint` string, ensures a valid session is active (by calling `get_session_key()`), and then makes the authenticated GET request. It also includes logic to re-authenticate and retry the request once if it fails due to an expired session (HTTP 401).

## Configuration
The service is configured using the following environment variables:

- **`FORTIGATE_HOST`**: The IP address or hostname of the FortiGate device.
- **`FORTIGATE_USERNAME`**: The username for API authentication.
- **`FORTIGATE_PASSWORD`**: The password for API authentication. It can also be loaded from a file at `/run/secrets/fortigate_password` or `./secrets/fortigate_password.txt`.

By default, SSL certificate verification is disabled to accommodate self-signed certificates often used on these devices.

## Data Flow
1. The application requests the singleton `FortiGateSessionManager` instance via `get_session_manager()`.
2. The manager loads credentials from the environment.
3. To make an API call, the application calls `make_api_request()` with the target endpoint.
4. The manager checks if the current session is valid using `_is_session_valid()`.
5. If the session is invalid, it calls `login()` to authenticate and get a new session key.
6. With a valid session, it makes the API request to the specified endpoint.
7. The JSON response is parsed and returned as a dictionary.
8. If the session expires mid-operation, the manager attempts to re-authenticate once and retries the request.

## Error Handling
- The service logs an error if essential credentials (IP, username, password) are missing.
- It gracefully handles `requests` exceptions like `Timeout` and `ConnectionError`.
- It detects login failures and logs relevant error information.
- It can handle JSON decoding errors if the API returns an invalid response.
- It includes a retry mechanism for expired sessions.

## Testing
This file does not include unit tests. A proper testing suite for this service would involve using `pytest` and mocking the `requests` library to simulate different API responses, including successful logins, failed logins, session expirations, and various network errors. This would validate the reliability of the session management and error handling logic.
