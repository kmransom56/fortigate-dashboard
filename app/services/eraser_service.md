# eraser_service.md

## Purpose
The `eraser_service.py` acts as a client for an external, third-party API called "Eraser". Its primary purpose is to take a 2D image, provided as a URL, and use the Eraser API to generate a corresponding 3D asset, such as a texture map. This service is designed as an optional enhancement, likely for creating 3D visualizations of network topology diagrams.

## Dependencies
- **`os`**: To read configuration settings from environment variables.
- **`requests`**: The library used to make HTTP POST requests to the external Eraser API.
- **`logging`**: For logging information and warnings, especially about API call attempts and failures.
- **`dotenv`**: To load configuration from a `.env` file during development.

## API

### `is_enabled() -> bool`
A helper function that checks the `ERASER_ENABLED` environment variable to determine if the service should be active.

### `export_topology(payload: dict) -> dict`
This is the main entry point for the service. It inspects the incoming `payload`. If a key named `imageUrl` is present, it triggers the 3D generation process by calling `generate_3d_from_image`. Otherwise, it simply returns a status message acknowledging receipt of the payload.

### `generate_3d_from_image(image_url: str) -> Dict`
This is the core function of the service. It orchestrates the interaction with the Eraser API. It is designed to be resilient and tries multiple strategies to get a successful response:
1.  It first checks if the service is enabled and configured. If not, it returns a "fallback" response.
2.  It then iterates through a list of known Eraser API endpoints (e.g., `/api/render/prompt`, `/api/render/elements`).
3.  For each endpoint, it iterates through a list of different, pre-formatted JSON payloads, trying each one until it gets a successful (HTTP 200) response.
This trial-and-error approach suggests the Eraser API may be experimental or have evolving specifications.

## Configuration
The service is configured entirely through environment variables:
- **`ERASER_ENABLED`**: Must be set to `"true"` to enable the service.
- **`ERASER_API_URL`**: The base URL of the Eraser API.
- **`ERASER_API_KEY`**: The authentication token for the API.
- **`ERASER_API_KEY_FILE`**: An alternative method to provide the key, by specifying the path to a file that contains it.

## Data Flow
1. An external call is made to `export_topology()` with a payload containing an `imageUrl`.
2. The `generate_3d_from_image()` function is invoked.
3. The function checks for the required configuration (`ERASER_ENABLED`, URL, and API key).
4. **If not configured**: It immediately returns a fallback dictionary, where the original `imageUrl` is simply returned as the `textureUrl`. This allows the calling application to proceed without a 3D asset, perhaps by using the 2D image as a flat texture.
5. **If configured**: It begins a loop, trying different API endpoints and payload structures.
6. It sends a POST request to the Eraser API with a payload.
7. **If the request is successful**: It returns the JSON response from the Eraser API, which presumably contains the URL to the generated 3D asset.
8. **If the request fails**: It logs the failure and continues to the next attempt (either a different payload or a different endpoint).
9. If all attempts are exhausted without success, it returns the same fallback response as in step 4.

## Error Handling
The service is designed to be highly resilient and to "fail gracefully".
- It will not crash the application if it is disabled or misconfigured; it will simply provide a fallback response.
- It wraps its API calls in `try...except` blocks to handle network errors like timeouts.
- It checks the HTTP status code of each API response and will only stop on a success (200). For failures, it logs a warning and continues trying other options.

## Testing
This file does not contain its own unit tests. To test this service, one would need to use a library like `pytest` and mock the `requests.post` method. The tests would simulate various scenarios:
- The service being disabled.
- The Eraser API returning a successful response on the first try.
- The API failing on the first few attempts but succeeding on a later one.
- The API returning different error codes.
- The API timing out.
In each case, the test would assert that the service returns the expected dictionary (either a success response or a fallback response).
