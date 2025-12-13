# fortigate_redis_session.md

## Purpose
The `fortigate_redis_session.py` service is an advanced session manager for FortiGate devices that uses Redis for session persistence. This is a critical component for running the application in a distributed or multi-instance environment, as it allows different application instances to share the same API session, preventing repeated logins and potential lockouts. It builds upon the basic session management logic by integrating a Redis backend.

## Dependencies
- **`os`**: For reading configuration from environment variables.
- **`requests`**: For making HTTP/HTTPS requests to the FortiGate API.
- **`json`**: For parsing JSON data from API responses.
- **`logging`**: For application-wide logging.
- **`datetime`, `timedelta`**: For managing session timestamps and expirations.
- **`.redis_session_manager`**: This is a key internal dependency that provides the abstraction for interacting with the Redis data store.

## API

### `get_fortigate_redis_session_manager() -> FortiGateRedisSessionManager`
A factory function that returns a singleton instance of the `FortiGateRedisSessionManager`, ensuring centralized control over Redis-backed sessions.

### `FortiGateRedisSessionManager` Class
This class orchestrates FortiGate authentication and Redis session storage.

#### `login() -> bool`
Performs the authentication against the FortiGate `/logincheck` endpoint. If successful, it extracts the session key and calls `_store_session()` to persist it in Redis with a configured TTL.

#### `logout()`
Logs out from the FortiGate device and calls `_delete_session()` to remove the session data from Redis.

#### `get_session_key() -> Optional[str]`
This is the core method for retrieving a valid session key. It first queries Redis using `_get_stored_session()`. If a valid, non-expired session exists, it returns the key. Otherwise, it triggers a new login by calling `login()`.

#### `make_api_request(endpoint: str) -> Dict[str, Any]`
Makes an authenticated API request. It uses `get_session_key()` to ensure a valid session is available. It also includes logic to automatically re-authenticate if a request fails with a 401 Unauthorized status, indicating the session has expired on the FortiGate side.

#### `get_session_info() -> Dict[str, Any]`
Provides metadata about the currently stored session in Redis, such as its validity, expiration time, and usage stats.

#### `health_check() -> Dict[str, Any]`
Performs a health check on the service, including the status of the underlying Redis connection (by calling the health check of the `redis_session_manager`).

## Configuration
This service uses the following environment variables:

- **`FORTIGATE_HOST`**: The IP address or hostname of the FortiGate.
- **`FORTIGATE_USERNAME`**: The username for authentication (typically `admin` for session-based auth).
- **`FORTIGATE_PASSWORD`**: The password for the user. Can also be loaded from a file specified by `FORTIGATE_PASSWORD_FILE` or from standard secret paths.
- **`FORTIGATE_SESSION_TTL`**: The time-to-live (in minutes) for the session stored in Redis. Defaults to 30.

This service also depends on the configuration of the `redis_session_manager` service, which includes settings for the Redis host, port, and password.

## Data Flow
1. The application gets the `FortiGateRedisSessionManager` instance.
2. To make an API call, `make_api_request()` is invoked.
3. The manager calls `get_session_key()`, which first checks Redis for a valid session for the current FortiGate host and username.
4. **If a valid session exists in Redis**: The session key is returned immediately.
5. **If no valid session exists in Redis**: The manager calls `login()` to authenticate with the FortiGate.
6. The new session key obtained from the FortiGate is stored in Redis with a specific TTL.
7. The API request is then made using the session key.
8. If the API call fails with a 401 error, the session is deleted from Redis, and the login process is re-initiated.

## Error Handling
- The service handles missing FortiGate credentials.
- It manages `requests` library exceptions for network-related issues.
- It includes robust logic for handling login failures and API errors.
- It transparently handles session expiration and re-authentication.
- Errors related to Redis connectivity are managed by the underlying `redis_session_manager`.

## Testing
This file does not contain its own unit tests. Testing this service is more complex than the basic session manager. It would require mocking both the `requests` library (to simulate FortiGate API responses) and the `redis_session_manager` (to simulate Redis interactions). This would allow for testing the full lifecycle of a session, including caching, expiration, and re-authentication, in a controlled environment.
