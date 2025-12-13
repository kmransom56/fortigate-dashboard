# fortigate-auth.js

## Purpose
The `fortigate-auth.js` module provides a reusable JavaScript class, `FortiGateAuth`, for handling authentication and API communication with a FortiGate device. It is designed to be used in Node.js environments. The class manages session-based authentication by logging in and using cookies for subsequent requests. It also contains high-level methods specifically for fetching and normalizing topology data from the FortiGate Security Fabric API.

## Dependencies
- **`axios`**: Used to make HTTP/HTTPS requests to the FortiGate API.
- **`https`**: A built-in Node.js module used to create a custom HTTPS agent that can be configured to ignore self-signed certificates, which are common on FortiGate devices.
- **`../utils/logger`**: A local utility for logging messages.

## API

### `new FortiGateAuth(config)`
The constructor creates a new instance of the authentication manager.
- **`config`**: An object containing connection details: `host`, `username`, `password`, `port` (optional), and `vdom` (optional).

### `async authenticate()`
Performs the login process by sending a POST request to the `/logincheck` endpoint. If successful, it extracts and stores the `ccsrftoken` session cookie for future requests.

### `async testConnection()`
Makes a simple, authenticated API call to `/api/v2/monitor/system/status` to verify that the credentials are valid and the connection is working.

### `async makeRequest(endpoint, method, data)`
This is the primary method for making authenticated API calls. It ensures a valid session exists (calling `authenticate()` if needed) and includes logic to automatically re-authenticate and retry the request once if it fails with a 401 Unauthorized error.

### `async getTopologyData()`
A high-level method that fetches data from the `/api/v2/monitor/system/security-fabric/topology` endpoint and runs it through the `normalizeTopologyData` method.

### `normalizeTopologyData(rawData)`
A crucial helper method that transforms the raw, vendor-specific JSON response from the FortiGate API into a standardized, generic topology format consisting of a `nodes` array and a `links` array.

## Configuration
The service is configured by passing a configuration object to the `FortiGateAuth` constructor. This object must contain:
- `host`: The IP address or domain of the FortiGate.
- `username`: The username for authentication.
- `password`: The password for authentication.

## Data Flow
1.  An instance of `FortiGateAuth` is created with the required credentials.
2.  A method like `getTopologyData()` is called.
3.  The request is routed through `makeRequest()`, which checks for an active session.
4.  If no session exists, `authenticate()` is called to log in and retrieve a session cookie.
5.  The API request is made to the specified FortiGate endpoint using the session cookie for authentication.
6.  If the API responds with a 401 error, the session is cleared, and the authentication process is re-attempted once.
7.  The raw JSON data from the API is returned.
8.  In the case of `getTopologyData()`, the raw data is then passed to `normalizeTopologyData()` to be converted into a standard format before being returned to the caller.

## Error Handling
- The module uses `async/await` with `try...catch` blocks to handle errors during API requests and authentication.
- It has specific logic to handle 401 Unauthorized errors by attempting to re-authenticate, which makes the session management more resilient.
- It disables SSL/TLS certificate validation (`rejectUnauthorized: false`) to prevent errors from self-signed certificates.

## Testing
This file does not contain its own unit tests. To test this class, one would use a testing framework like Jest or Mocha and mock the `axios` client. This would allow for simulating various FortiGate API responses (e.g., successful login, failed login, 401 errors) to verify that the class handles each scenario correctly.
